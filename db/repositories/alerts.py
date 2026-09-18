from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models.alerts import Alert
from db.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self, session: AsyncSession):
        super().__init__(Alert, session)

    async def create_alert_record(
        self,
        incident_id: uuid.UUID,
        channel: str,
        recipient: str,
        payload: dict,
        status: str = "QUEUED",
    ) -> Alert:
        alert = Alert(
            incident_id=incident_id,
            channel=channel,
            recipient=recipient,
            payload=payload,
            status=status,
        )
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def update_status(
        self,
        alert_id: uuid.UUID,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[Alert]:
        alert = await self.get_by_id(alert_id)
        if alert:
            alert.status = status
            if error_message:
                alert.error_message = error_message
            if status == "SENT":
                alert.sent_at = datetime.now(timezone.utc)
            await self.session.flush()
        return alert