from incidents.domain import SeverityLevel

class EscalationPolicy:
    @staticmethod
    def evaluate_severity(risk_score: float, active_duration_sec: float) -> SeverityLevel:
        if risk_score >= 90.0 or active_duration_sec > 600:
            return SeverityLevel.EMERGENCY
        if risk_score >= 80.0 or active_duration_sec > 300:
            return SeverityLevel.CRITICAL
        if risk_score >= 60.0:
            return SeverityLevel.HIGH
        if risk_score >= 40.0:
            return SeverityLevel.WARNING
        return SeverityLevel.LOW