from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from shared.schemas import IncidentEvent, RawDetection


class BaseEvent(BaseModel):
    """Base payload for internal event stream messaging."""
    event_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FrameIngestedEvent(BaseEvent):
    """Emitted when a video frame detection batch is ingested."""
    camera_id: str
    frame_id: int
    detections: List[RawDetection]


class IncidentTriggeredEvent(BaseEvent):
    """Emitted when a new incident is confirmed or escalated."""
    incident: IncidentEvent