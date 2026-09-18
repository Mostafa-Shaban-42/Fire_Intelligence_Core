from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models.cameras import Camera, Site, Zone
from db.repositories.base import BaseRepository


class CameraRepository(BaseRepository[Camera]):
    def __init__(self, session: AsyncSession):
        super().__init__(Camera, session)

    async def get_active_cameras(self) -> List[Camera]:
        result = await self.session.execute(
            select(Camera).where(Camera.is_active == True)
        )
        return list(result.scalars().all())

    async def update_status(self, camera_id: uuid.UUID, status: str, fps: Optional[int] = None) -> Optional[Camera]:
        camera = await self.get_by_id(camera_id)
        if camera:
            camera.status = status
            if fps is not None:
                camera.fps = fps
            await self.session.flush()
        return camera


class SiteRepository(BaseRepository[Site]):
    def __init__(self, session: AsyncSession):
        super().__init__(Site, session)


class ZoneRepository(BaseRepository[Zone]):
    def __init__(self, session: AsyncSession):
        super().__init__(Zone, session)