from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FrameCapturedEvent(BaseModel):
    """Event emitted when a raw frame is successfully captured."""
    frame_id: int
    camera_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acquisition_latency_ms: float = 0.0
    width: int = 0
    height: int = 0


class DetectionEvent(BaseModel):
    """Event representing AI detection results produced on an ingested frame."""
    frame_id: int
    camera_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detections: list = Field(default_factory=list)
    risk_level: str = "NORMAL"
    processing_latency_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)