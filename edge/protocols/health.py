from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from shared.enums import CameraHealthState


class HeartbeatMessage(BaseModel):
    """Periodic status heartbeat sent by camera processes."""
    camera_id: str
    worker_pid: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: CameraHealthState
    fps: float = 0.0


class CameraHealthReport(BaseModel):
    """Detailed telemetry and health report for a target camera."""
    camera_id: str
    state: CameraHealthState
    total_frames_received: int = 0
    total_reconnections: int = 0
    last_frame_timestamp: float = 0.0
    last_error: str = ""
    telemetry: Dict[str, Any] = Field(default_factory=dict)