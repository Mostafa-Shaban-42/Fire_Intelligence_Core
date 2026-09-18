from alerts.channels import BaseAlertChannel
from shared.schemas import IncidentEvent

class PushAlertChannel(BaseAlertChannel):
    async def send_alert(self, event: IncidentEvent) -> bool:
        # FCM / Mobile Push Delivery
        return True