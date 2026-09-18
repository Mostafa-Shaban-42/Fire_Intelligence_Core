import time
from incidents.escalation import EscalationEngine
from incidents.domain import SeverityLevel

def test_escalation_level():
    eng = EscalationEngine()
    sev = eng.check_escalation(risk_score=95.0, start_time=time.time())
    assert sev == SeverityLevel.EMERGENCY