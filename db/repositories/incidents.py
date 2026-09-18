from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models.incidents import Incident, IncidentEvent
from db.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, session: AsyncSession):
        super().__init__(Incident, session)

    async def get_active_incidents(self) -> List[Incident]:
        result = await self.session.execute(
            select(Incident).where(Incident.state.notin_(["RESOLVED", "CLOSED"]))
        )
        return list(result.scalars().all())

    async def transition_state(
        self,
        incident_id: uuid.UUID,
        new_state: str,
        reason: Optional[str] = None,
        actor_user_id: Optional[uuid.UUID] = None
    ) -> Optional[Incident]:
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        previous_state = incident.state
        incident.state = new_state
        if new_state in ["RESOLVED", "CLOSED"]:
            incident.resolved_at = datetime.now(timezone.utc)

        event = IncidentEvent(
            incident_id=incident.id,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason,
            actor_user_id=actor_user_id
        )
        self.session.add(event)
        await self.session.flush()

        return incident