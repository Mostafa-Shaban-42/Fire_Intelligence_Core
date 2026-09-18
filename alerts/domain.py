from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any

class AlertStatus(str, Enum):
    QUEUED = "QUEUED"
    DISPATCHING = "DISPATCHING"
    SENT = "SENT"
    FAILED = "FAILED"

@dataclass
class AlertDomainModel:
    alert_id: str
    incident_id: str
    channel: str
    recipient: str
    status: AlertStatus
    payload: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))