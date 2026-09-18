import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Incident(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "incidents"

    camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), default="DETECTED", nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), default="LOW", nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    events: Mapped[List["IncidentEvent"]] = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")


class IncidentEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "incident_events"

    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_state: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    incident: Mapped[Incident] = relationship("Incident", back_populates="events")