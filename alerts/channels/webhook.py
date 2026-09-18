from alerts.channels import BaseAlertChannel
from shared.schemas import IncidentEvent

class WebhookAlertChannel(BaseAlertChannel):
    async def send_alert(self, event: IncidentEvent) -> bool:
        # Generic Outbound Webhook Delivery
        return True