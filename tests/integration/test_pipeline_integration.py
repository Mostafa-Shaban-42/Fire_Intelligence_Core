import pytest
from fusion.fusion_engine import SensorFusionEngine
from fusion.sensor_state import SensorStateRegistry
from incidents.incident_engine import IncidentEngine
from risk.risk_engine import RiskEngine
from shared.enums import DetectionType
from shared.schemas import BoundingBox, RawDetection
from temporal.tracking.track_manager import TrackManager


@pytest.mark.asyncio
async def test_full_pipeline_flow():
    sensor_registry = SensorStateRegistry()
    fusion_engine = SensorFusionEngine(sensor_registry)
    track_manager = TrackManager()
    risk_engine = RiskEngine()
    incident_engine = IncidentEngine(trigger_risk_threshold=40.0)

    raw_detections = [
        RawDetection(
            bbox=BoundingBox(xmin=200.0, ymin=200.0, xmax=800.0, ymax=800.0),
            confidence=0.85,
            detection_type=DetectionType.FIRE,
        )
    ]

    # Step 1: Async Temporal tracking
    tracked = await track_manager.process_detections("cam-01", raw_detections)
    assert tracked is not None

    # Step 2: Multi-sensor fusion
    fused = fusion_engine.fuse_track_data("cam-01", tracked)
    assert fused is not None

    # Step 3: Risk score calculation
    scene_risk, evaluated_tracks = risk_engine.process_scene_risk(fused)
    assert scene_risk > 0.0

    # Step 4: Async Incident evaluation
    incident_event = await incident_engine.process_risk_evaluation("cam-01", scene_risk, evaluated_tracks)
    assert incident_event is not None
    assert incident_event.camera_id == "cam-01"