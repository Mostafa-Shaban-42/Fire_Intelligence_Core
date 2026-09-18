from typing import List
from alerts.channels import BaseAlertChannel, TelegramAlertChannel, EmailAlertChannel
from shared.schemas import IncidentEvent


class AlertRouter:
    def route(self, event: IncidentEvent) -> List[BaseAlertChannel]:
        channels: List[BaseAlertChannel] = [TelegramAlertChannel()]
        if event.risk_score >= 85.0:
            channels.append(EmailAlertChannel())
        return channels