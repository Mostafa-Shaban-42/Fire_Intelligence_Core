import time
from incidents.domain import SeverityLevel
from incidents.policies import EscalationPolicy

class EscalationEngine:
    def __init__(self):
        self.policy = EscalationPolicy()

    def check_escalation(self, risk_score: float, start_time: float) -> SeverityLevel:
        duration = time.time() - start_time
        return self.policy.evaluate_severity(risk_score, duration)