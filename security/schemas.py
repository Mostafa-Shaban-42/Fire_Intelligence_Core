from typing import Optional, List, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth & Login Schemas ---
class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or Email address")
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: uuid.UUID
    username: str
    session_id: uuid.UUID
    roles: List[str] = []
    permissions: List[str] = []


# --- User Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role_names: List[str] = ["Operator"]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    status: str
    roles: List[str] = []
    permissions: List[str] = []


class UserStatusUpdate(BaseModel):
    status: str  # ACTIVE, SUSPENDED, DISABLED, LOCKED
    is_active: bool


# --- Role & Permission Schemas ---
class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    resource: str
    action: str


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: List[uuid.UUID] = []


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    permissions: List[PermissionRead] = []


# --- Password Management ---
class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)