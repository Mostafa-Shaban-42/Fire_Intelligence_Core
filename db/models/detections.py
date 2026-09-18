import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, UUIDPrimaryKeyMixin


class Detection(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "detections"

    camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    class_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # fire, smoke
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Bounding Box coordinates [x1, y1, x2, y2]
    bbox: Mapped[dict] = mapped_column(JSON, nullable=False)
    track_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    frame_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    camera: Mapped["Camera"] = relationship("Camera", back_populates="detections")