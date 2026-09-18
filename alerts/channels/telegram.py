import asyncio
import json
import logging
import urllib.request
from typing import Optional
from alerts.channels import BaseAlertChannel
from configs.settings import settings
from shared.schemas import IncidentEvent

logger = logging.getLogger(__name__)


class TelegramAlertChannel(BaseAlertChannel):
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or getattr(settings, "TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)
        self.api_url: Optional[str] = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.enabled else None

    async def send_alert(self, event: IncidentEvent) -> bool:
        if not self.enabled or not self.api_url:
            return True
        payload = {
            "chat_id": self.chat_id,
            "text": f"🚨 FIRE ALERT [{event.incident_id}] Risk: {event.risk_score:.1f}%",
        }
        return await asyncio.to_thread(self._send_sync, payload)

    def _send_sync(self, payload: dict) -> bool:
        if not self.api_url:
            return False
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.api_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return resp.status == 200
        except Exception:
            return False