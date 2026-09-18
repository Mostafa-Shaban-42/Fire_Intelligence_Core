from typing import List
from fastapi import HTTPException, status, Depends
from security.schemas import TokenData
from security.dependencies import get_current_user


class PermissionChecker:
    """Default Deny Authorization Permission Engine."""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: TokenData = Depends(get_current_user)) -> TokenData:
        # Admin Bypass Rule
        if "Admin" in current_user.roles or current_user.username == "admin":
            return current_user

        # Default Deny Check
        if self.required_permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied. Missing permission: '{self.required_permission}'",
            )

        return current_user


def require_permission(permission: str):
    return PermissionChecker(permission)