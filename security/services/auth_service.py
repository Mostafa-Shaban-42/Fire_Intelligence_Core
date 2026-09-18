import uuid
from typing import Optional
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from db.models.users import User, Role
from security.authentication import hash_password, verify_password
from security.services.token_service import TokenService
from security.services.session_service import SessionService
from security.audit import record_audit_event
from security.schemas import TokenResponse, UserCreate


class AuthService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_service = SessionService(session)

    async def authenticate_user(
        self,
        username_or_email: str,
        password: str,
        request: Optional[Request] = None,
    ) -> TokenResponse:
        # 1. Fetch User with Roles & Permissions
        query = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where((User.email == username_or_email) | (User.username == username_or_email))
        )
        result = await self.session.execute(query)
        user = result.scalars().first()

        # Dynamic fallback to read whichever password attribute is defined on User model
        stored_hash = getattr(
            user, "hashed_password", getattr(user, "password_hash", getattr(user, "password", ""))
        ) if user else ""

        if not user or not verify_password(password, stored_hash):
            await record_audit_event(
                self.session,
                action="USER_LOGIN_FAILED",
                resource_type="USER",
                request=request,
                metadata_payload={"identifier": username_or_email},
                result="FAILURE",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # 2. Verify User Account State Safely
        user_status = getattr(user, "status", "ACTIVE")
        if not user.is_active or user_status != "ACTIVE":
            await record_audit_event(
                self.session,
                action="USER_LOGIN_BLOCKED",
                resource_type="USER",
                actor_user_id=user.id,
                request=request,
                result="DENIED",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {str(user_status).lower()}",
            )

        # 3. Extract Roles & Permissions
        roles = [role.name for role in user.roles]
        permissions = list(
            {f"{p.resource}.{p.action}" for role in user.roles for p in role.permissions}
        )

        # 4. Create Active Session & Tokens
        user_session = await self.session_service.create_session(
            user_id=user.id,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )

        access_token = TokenService.create_access_token(
            user_id=user.id,
            username=user.username,
            session_id=user_session.id,
            roles=roles,
            permissions=permissions,
        )

        refresh_str, jti, expire = TokenService.create_refresh_token(
            user_id=user.id,
            session_id=user_session.id,
        )
        await self.session_service.register_refresh_token(
            session_id=user_session.id,
            token_jti=jti,
            expires_at=expire,
        )

        # 5. Audit Record
        await record_audit_event(
            self.session,
            action="USER_LOGIN_SUCCESS",
            resource_type="USER",
            actor_user_id=user.id,
            request=request,
            result="SUCCESS",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_str,
            expires_in=15 * 60,
        )

    async def refresh_tokens(
        self,
        refresh_token_str: str,
        request: Optional[Request] = None,
    ) -> TokenResponse:
        payload = TokenService.decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
        jti = payload["jti"]

        # Validate Refresh Token and rotate
        valid = await self.session_service.validate_refresh_token_and_rotate(
            session_id=session_id,
            token_jti=jti,
        )
        if not valid:
            await record_audit_event(
                self.session,
                action="REFRESH_TOKEN_REUSE_DETECTED",
                resource_type="SESSION",
                actor_user_id=user_id,
                request=request,
                result="SECURITY_ALERT",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reused or session revoked",
            )

        # Re-fetch user
        query = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        result = await self.session.execute(query)
        user = result.scalars().first()

        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

        roles = [role.name for role in user.roles]
        permissions = list({f"{p.resource}.{p.action}" for role in user.roles for p in role.permissions})

        # Generate new pair
        new_access = TokenService.create_access_token(
            user.id, user.username, session_id, roles, permissions
        )
        new_refresh, new_jti, new_exp = TokenService.create_refresh_token(user.id, session_id)
        await self.session_service.register_refresh_token(session_id, new_jti, new_exp)

        return TokenResponse(access_token=new_access, refresh_token=new_refresh, expires_in=15 * 60)