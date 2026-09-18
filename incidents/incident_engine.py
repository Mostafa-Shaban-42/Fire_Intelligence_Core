import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from configs.settings import settings
from incidents.incident_lifecycle import IncidentLifecycleManager, IncidentRecord
from incidents.deduplication import IncidentDeduplicator
from incidents.aggregates import IncidentAggregate
from shared.enums import IncidentState
from shared.schemas import IncidentEvent, RiskFactorBreakdown

logger = logging.getLogger(__name__)

class IncidentEngine:
    def __init__(
        self,
        trigger_risk_threshold: float = 60.0,
        escalation_risk_threshold: float = 85.0,
    ) -> None:
        self.trigger_risk_threshold = trigger_risk_threshold
        self.escalation_risk_threshold = escalation_risk_threshold
        self.lifecycle_manager = IncidentLifecycleManager(cooldown_seconds=settings.INCIDENT_COOLDOWN_SEC)
        self.deduplicator = IncidentDeduplicator()
        self._camera_locks: Dict[str, asyncio.Lock] = {}
        self._locks_registry_lock = asyncio.Lock()

    async def _get_camera_lock(self, camera_id: str) -> asyncio.Lock:
        lock = self._camera_locks.get(camera_id)
        if lock is not None:
            return lock
        async with self._locks_registry_lock:
            lock = self._camera_locks.get(camera_id)
            if lock is None:
                lock = asyncio.Lock()
                self._camera_locks[camera_id] = lock
            return lock

    async def process_risk_evaluation(
        self,
        camera_id: str,
        scene_risk: float,
        evaluated_tracks: List[Dict[str, Any]],
    ) -> Optional[IncidentEvent]:
        camera_lock = await self._get_camera_lock(camera_id)
        async with camera_lock:
            active_record = self.lifecycle_manager.get_active_incident(camera_id)

            if not active_record and scene_risk < self.trigger_risk_threshold:
                return None

            if not active_record and self.lifecycle_manager.is_in_cooldown(camera_id):
                return None

            top_factors = self._extract_top_factors(evaluated_tracks, scene_risk)

            if not active_record and scene_risk >= self.trigger_risk_threshold:
                incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
                new_record = IncidentRecord(
                    incident_id=incident_id,
                    camera_id=camera_id,
                    risk_score=scene_risk,
                    factors=top_factors,
                )
                new_record.state_machine.transition_to(IncidentState.VALIDATING)
                new_record.state_machine.transition_to(IncidentState.CONFIRMED)
                self.lifecycle_manager.register_incident(new_record)
                return self._build_incident_event(new_record)

            if active_record:
                active_record.update_risk(scene_risk, top_factors)
                if (
                    scene_risk >= self.escalation_risk_threshold
                    and active_record.state_machine.current_state == IncidentState.CONFIRMED
                ):
                    active_record.state_machine.transition_to(IncidentState.ESCALATED)
                return self._build_incident_event(active_record)

            return None

    def _extract_top_factors(
        self,
        evaluated_tracks: List[Dict[str, Any]],
        scene_risk: float,
    ) -> RiskFactorBreakdown:
        if evaluated_tracks:
            top_track = max(evaluated_tracks, key=lambda track: track.get("risk_score", 0.0))
            return top_track["risk_factors"]
        return RiskFactorBreakdown(
            detection_confidence_weight=0.0,
            temporal_persistence_weight=0.0,
            affected_area_ratio=0.0,
            risk_score=scene_risk,
        )

    def _build_incident_event(self, record: IncidentRecord) -> IncidentEvent:
        return IncidentEvent(
            incident_id=record.incident_id,
            camera_id=record.camera_id,
            state=record.state_machine.current_state,
            risk_score=record.risk_score,
            factors=record.factors,
            model_name=record.model_name,
            model_version=record.model_version,
            timestamp=datetime.now(timezone.utc),
        )