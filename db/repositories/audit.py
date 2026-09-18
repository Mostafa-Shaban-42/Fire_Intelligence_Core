from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models.audit import AuditLog
from db.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def log(
        self,
        action: str,
        resource_type: str,
        actor_user_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata_payload: Optional[dict] = None,
        result: str = "SUCCESS"
    ) -> AuditLog:
        audit_entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_payload=metadata_payload,
            result=result
        )
        self.session.add(audit_entry)
        await self.session.flush()
        return audit_entry

    async def get_logs_by_resource(self, resource_type: str, limit: int = 50) -> List[AuditLog]:
        query = select(AuditLog).where(AuditLog.resource_type == resource_type).order_by(AuditLog.timestamp.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())