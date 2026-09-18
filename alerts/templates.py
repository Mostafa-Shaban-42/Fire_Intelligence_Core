from shared.schemas import IncidentEvent

class AlertTemplates:
    @staticmethod
    def render_text(event: IncidentEvent) -> str:
        state_val = event.state.value if hasattr(event.state, "value") else str(event.state)
        return (
            f"🚨 FIRE INTELLIGENCE ALERT\n"
            f"Incident ID: {event.incident_id}\n"
            f"Camera ID: {event.camera_id}\n"
            f"Status: {state_val}\n"
            f"Risk Score: {event.risk_score:.1f}%\n"
            f"Timestamp: {event.timestamp.isoformat()}"
        )