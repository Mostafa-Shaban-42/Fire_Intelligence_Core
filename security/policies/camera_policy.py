import uuid
from typing import Optional
from security.schemas import TokenData


class CameraPolicy:
    """Resource Scope Level Authorization Policy for Cameras."""

    @staticmethod
    def can_access_camera(user: TokenData, site_id: Optional[uuid.UUID] = None) -> bool:
        if "Admin" in user.roles or "camera.read" in user.permissions:
            return True
        return False