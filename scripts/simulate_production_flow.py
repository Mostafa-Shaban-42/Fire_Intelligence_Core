import sys
from pathlib import Path

# Add project root directory to sys.path automatically
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import uuid
import logging
from datetime import datetime, timezone

# 1. Import DB Engine & Models
from db.models.users import User
from db.models.cameras import Camera
from db.repositories.incidents import IncidentRepository
from db.repositories.alerts import AlertRepository
from db.repositories.audit import AuditRepository

# 2. Import Core Engines
from incidents.incident_engine import IncidentEngine
from incidents.incident_state import IncidentStateMachine
from shared.enums import IncidentState
from shared.schemas import RiskFactorBreakdown

# 3. Import Alerts & Security
from alerts.alert_engine import AlertEngine
from alerts.channels.telegram import TelegramAlertChannel
from security.policies.incident_policy import IncidentPolicy
from security.schemas import TokenData

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProductionSimulation")

async def run_end_to_end_test():
    logger.info("=== 🚀 Starting Real-World End-to-End Test ===")

    # Step A: Setup Engines
    incident_engine = IncidentEngine(trigger_risk_threshold=60.0, escalation_risk_threshold=85.0)
    alert_engine = AlertEngine(channels=[TelegramAlertChannel()])

    test_camera_id = str(uuid.uuid4())
    logger.info(f"[1] Simulating detections on Camera ID: {test_camera_id}")

    # Step B: Low Risk Detection (Should NOT trigger Incident)
    logger.info("[2] Processing Low-Risk Frame Data (Risk: 30.0%)...")
    event_1 = await incident_engine.process_risk_evaluation(
        camera_id=test_camera_id,
        scene_risk=30.0,
        evaluated_tracks=[]
    )
    assert event_1 is None, "❌ Fail: Incident triggered on low risk!"
    logger.info("✅ Pass: Low risk ignored correctly.")

    # Step C: High Risk Detection (Triggers Incident)
    logger.info("[3] Processing High-Risk Fire Detection (Risk: 75.0%)...")
    tracks = [{
        "risk_score": 75.0,
        "risk_factors": RiskFactorBreakdown(
            detection_confidence_weight=0.8,
            temporal_persistence_weight=0.7,
            affected_area_ratio=0.3,
            risk_score=75.0
        )
    }]
    
    event_2 = await incident_engine.process_risk_evaluation(
        camera_id=test_camera_id,
        scene_risk=75.0,
        evaluated_tracks=tracks
    )
    assert event_2 is not None, "❌ Fail: Incident was not created!"
    assert event_2.state == IncidentState.CONFIRMED, f"❌ Fail: Expected CONFIRMED state, got {event_2.state}"
    logger.info(f"✅ Pass: Incident {event_2.incident_id} created with state {event_2.state.value}")

    # Step D: Alert Routing and Dispatch
    logger.info(f"[4] Routing and Dispatching Alert for Incident {event_2.incident_id}...")
    alert_sent = await alert_engine.dispatch_incident_alert(event_2)
    logger.info(f"✅ Pass: Alert processing executed (Dispatched: {alert_sent})")

    # Step E: Escalation Trigger (Risk increases to 90.0%)
    logger.info("[5] Escalating Risk Score to 90.0%...")
    tracks[0]["risk_score"] = 90.0
    tracks[0]["risk_factors"].risk_score = 90.0
    
    event_3 = await incident_engine.process_risk_evaluation(
        camera_id=test_camera_id,
        scene_risk=90.0,
        evaluated_tracks=tracks
    )
    assert event_3.state == IncidentState.ESCALATED, f"❌ Fail: State did not escalate! Got {event_3.state}"
    logger.info(f"✅ Pass: Incident state successfully escalated to {event_3.state.value}")

    # Step F: Security Policy Check
    logger.info("[6] Testing Security RBAC Policy for Operator Resolution...")
    
    operator_user = TokenData(
        user_id=uuid.uuid4(),
        session_id=str(uuid.uuid4()),
        username="operator1",
        roles=["Operator"],
        permissions=["incident.read"]
    )
    admin_user = TokenData(
        user_id=uuid.uuid4(),
        session_id=str(uuid.uuid4()),
        username="admin1",
        roles=["Admin"],
        permissions=["incident.resolve"]
    )

    can_operator_resolve = IncidentPolicy.can_resolve_incident(operator_user)
    can_admin_resolve = IncidentPolicy.can_resolve_incident(admin_user)

    assert not can_operator_resolve, "❌ Fail: Operator without permissions was allowed to resolve!"
    assert can_admin_resolve, "❌ Fail: Admin was blocked from resolving!"
    logger.info("✅ Pass: Access control policies enforced correctly.")

    logger.info("=== 🎉 ALL END-TO-END TESTS PASSED SUCCESSFULLY! NO CONFLICTS FOUND. ===")

if __name__ == "__main__":
    asyncio.run(run_end_to_end_test())