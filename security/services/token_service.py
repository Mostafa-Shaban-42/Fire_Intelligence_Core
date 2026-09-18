import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from security.schemas import TokenData

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "FIRE_INTELLIGENCE_PRODUCTION_SECRET_KEY_MUST_BE_CHANGED")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class TokenService:

    @staticmethod
    def create_access_token(
        user_id: uuid.UUID,
        username: str,
        session_id: uuid.UUID,
        roles: list[str],
        permissions: list[str],
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": str(user_id),
            "username": username,
            "sid": str(session_id),
            "roles": roles,
            "permissions": permissions,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> tuple[str, str, datetime]:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jti = str(uuid.uuid4())
        
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "type": "refresh",
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
        token_str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token_str, jti, expire

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.PyJWTError:
            return None

    @staticmethod
    def extract_token_data(payload: Dict[str, Any]) -> Optional[TokenData]:
        if not payload or payload.get("type") != "access":
            return None
        try:
            return TokenData(
                user_id=uuid.UUID(payload["sub"]),
                username=payload["username"],
                session_id=uuid.UUID(payload["sid"]),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
            )
        except (ValueError, KeyError):
            return None