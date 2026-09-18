import uuid
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Site(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sites"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    zones: Mapped[List["Zone"]] = relationship("Zone", back_populates="site", cascade="all, delete-orphan")


class Zone(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "zones"

    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), default="normal", nullable=False)

    site: Mapped[Site] = relationship("Site", back_populates="zones")
    cameras: Mapped[List["Camera"]] = relationship("Camera", back_populates="zone", cascade="all, delete-orphan")


class Camera(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cameras"

    zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stream_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="rtsp", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Telemetry and Health
    fps: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    resolution: Mapped[str] = mapped_column(String(20), default="1920x1080", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="offline", nullable=False)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    zone: Mapped[Optional[Zone]] = relationship("Zone", back_populates="cameras")
    detections: Mapped[List["Detection"]] = relationship("Detection", back_populates="camera", cascade="all, delete-orphan")