from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid

class SeverityLevel(str, Enum):
    LOW = "LOW"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

@dataclass
class IncidentDomainModel:
    incident_id: str
    camera_ids: List[str]
    zone_id: Optional[str]
    state: str
    severity: SeverityLevel
    risk_score: float
    detections_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)