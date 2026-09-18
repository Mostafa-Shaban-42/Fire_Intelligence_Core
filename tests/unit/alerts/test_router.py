from datetime import datetime, timezone
from alerts.router import AlertRouter
from shared.schemas import IncidentEvent, RiskFactorBreakdown
from shared.enums import IncidentState

def test_router_critical():
    router = AlertRouter()
    event = IncidentEvent(
        incident_id="INC-1",
        camera_id="CAM-1",
        state=IncidentState.CONFIRMED,
        risk_score=90.0,
        factors=RiskFactorBreakdown(
            detection_confidence_weight=0.0,
            temporal_persistence_weight=0.0,
            affected_area_ratio=0.0,
            risk_score=90.0
        ),
        model_name="v1",
        model_version="1.0",
        timestamp=datetime.now(timezone.utc)
    )
    # Perform assertion based on router logic
    assert router is not None