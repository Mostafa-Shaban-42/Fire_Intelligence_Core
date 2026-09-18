from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from shared.enums import IncidentState

@dataclass
class IncidentDomainEvent:
    event_id: str
    incident_id: str
    camera_id: str
    previous_state: Optional[str]
    new_state: IncidentState
    risk_score: float
    severity: str
    timestamp: datetime = datetime.now(timezone.utc)
    metadata: Optional[Dict[str, Any]] = None