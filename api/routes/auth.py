from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from security.schemas import LoginRequest, TokenResponse, RefreshTokenRequest, UserRead
from security.services.auth_service import AuthService
from security.dependencies import get_current_user
from security.schemas import TokenData

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(
        username_or_email=payload.username_or_email,
        password=payload.password,
        request=request,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(
        refresh_token_str=payload.refresh_token,
        request=request,
    )


@router.get("/me", response_model=TokenData)
async def get_current_user_profile(
    current_user: TokenData = Depends(get_current_user),
):
    return current_user