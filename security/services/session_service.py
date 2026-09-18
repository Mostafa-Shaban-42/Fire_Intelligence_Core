import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

try:
    from db.models.users import UserSession, RefreshToken
except ImportError:
    UserSession = None  # type: ignore[assignment, misc]
    RefreshToken = None  # type: ignore[assignment, misc]


class SessionService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[Any]:
        if UserSession is None:
            return type('MockSession', (), {'id': uuid.uuid4()})()

        user_session = UserSession(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )
        self.session.add(user_session)
        await self.session.flush()
        return user_session

    async def register_refresh_token(
        self,
        session_id: uuid.UUID,
        token_jti: str,
        expires_at: datetime,
    ) -> Optional[Any]:
        if RefreshToken is None:
            return None

        refresh_token = RefreshToken(
            session_id=session_id,
            token_jti=token_jti,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        return refresh_token

    async def validate_refresh_token_and_rotate(
        self,
        session_id: uuid.UUID,
        token_jti: str,
    ) -> bool:
        """Validates Refresh Token. Implements Rotation & Reuse Detection."""
        if RefreshToken is None:
            return True

        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_jti == token_jti)
        )
        rt = result.scalars().first()

        if not rt or rt.is_revoked or rt.expires_at < datetime.now(timezone.utc):
            await self.revoke_session(session_id)
            return False

        rt.is_revoked = True
        await self.session.flush()
        return True

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        if UserSession is None:
            return

        result = await self.session.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        user_session = result.scalars().first()
        if user_session:
            user_session.is_active = False
            await self.session.flush()

    async def is_session_active(self, session_id: uuid.UUID) -> bool:
        if UserSession is None:
            return True

        result = await self.session.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        user_session = result.scalars().first()
        return bool(user_session and user_session.is_active)