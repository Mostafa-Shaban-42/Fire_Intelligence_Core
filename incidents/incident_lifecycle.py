import logging
import time
from typing import Dict, Optional
from incidents.incident_state import IncidentStateMachine
from shared.enums import IncidentState
from shared.schemas import RiskFactorBreakdown

logger = logging.getLogger(__name__)

class IncidentRecord:
    def __init__(
        self,
        incident_id: str,
        camera_id: str,
        risk_score: float,
        factors: RiskFactorBreakdown,
        model_name: str = "fire-intelligence-v1",
        model_version: str = "v1.0.0",
    ):
        self.incident_id = incident_id
        self.camera_id = camera_id
        self.state_machine = IncidentStateMachine()
        self.risk_score = risk_score
        self.factors = factors
        self.model_name = model_name
        self.model_version = model_version
        self.created_at = time.time()
        self.last_updated_at = time.time()

    def update_risk(self, risk_score: float, factors: RiskFactorBreakdown) -> None:
        self.risk_score = risk_score
        self.factors = factors
        self.last_updated_at = time.time()

class IncidentLifecycleManager:
    def __init__(self, cooldown_seconds: float = 30.0, auto_resolve_timeout_seconds: float = 15.0):
        self.cooldown_seconds = cooldown_seconds
        self.auto_resolve_timeout_seconds = auto_resolve_timeout_seconds
        self._active_incidents: Dict[str, IncidentRecord] = {}
        self._last_resolved_times: Dict[str, float] = {}

    def get_active_incident(self, camera_id: str) -> Optional[IncidentRecord]:
        record = self._active_incidents.get(camera_id)
        if not record:
            return None

        if (time.time() - record.last_updated_at) > self.auto_resolve_timeout_seconds:
            logger.info(f"Incident {record.incident_id} timed out. Auto-resolving.")
            self.resolve_incident(camera_id)
            return None

        return record

    def is_in_cooldown(self, camera_id: str) -> bool:
        last_time = self._last_resolved_times.get(camera_id)
        if not last_time:
            return False
        return (time.time() - last_time) < self.cooldown_seconds

    def register_incident(self, record: IncidentRecord) -> None:
        self._active_incidents[record.camera_id] = record

    def resolve_incident(self, camera_id: str) -> Optional[IncidentRecord]:
        record = self._active_incidents.pop(camera_id, None)
        if record:
            try:
                if record.state_machine.current_state not in (IncidentState.RESOLVED, IncidentState.CLOSED):
                    record.state_machine.transition_to(IncidentState.RESOLVED)
            except Exception:
                pass
            self._last_resolved_times[camera_id] = time.time()
        return record