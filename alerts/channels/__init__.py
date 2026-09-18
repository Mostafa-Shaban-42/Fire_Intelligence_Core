from abc import ABC, abstractmethod
from shared.schemas import IncidentEvent

class BaseAlertChannel(ABC):
    @abstractmethod
    async def send_alert(self, event: IncidentEvent) -> bool:
        pass

from alerts.channels.telegram import TelegramAlertChannel
from alerts.channels.whatsapp import WhatsAppAlertChannel
from alerts.channels.email import EmailAlertChannel
from alerts.channels.webhook import WebhookAlertChannel
from alerts.channels.push import PushAlertChannel

__all__ = [
    "BaseAlertChannel",
    "TelegramAlertChannel",
    "WhatsAppAlertChannel",
    "EmailAlertChannel",
    "WebhookAlertChannel",
    "PushAlertChannel",
]