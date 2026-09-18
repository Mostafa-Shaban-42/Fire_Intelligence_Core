from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from security.schemas import TokenData
from security.services.token_service import TokenService
from security.services.session_service import SessionService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = TokenService.decode_token(token)
    if not payload:
        raise credentials_exception

    token_data = TokenService.extract_token_data(payload)
    if not token_data:
        raise credentials_exception

    # Check active session state in Database
    session_service = SessionService(db)
    if not await session_service.is_session_active(token_data.session_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or logged out",
        )

    return token_data