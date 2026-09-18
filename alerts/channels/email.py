from alerts.channels import BaseAlertChannel
from shared.schemas import IncidentEvent

class EmailAlertChannel(BaseAlertChannel):
    async def send_alert(self, event: IncidentEvent) -> bool:
        # SMTP / SendGrid Delivery Implementation
        return True