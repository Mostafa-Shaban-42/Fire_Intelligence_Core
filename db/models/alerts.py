import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, UUIDPrimaryKeyMixin


class Alert(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "alerts"

    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # telegram, whatsapp, webhook, email, push
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", nullable=False)  # QUEUED, DISPATCHING, SENT, FAILED
    
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )