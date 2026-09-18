import logging
from typing import List, Optional
from alerts.channels import BaseAlertChannel, TelegramAlertChannel
from alerts.router import AlertRouter
from alerts.dispatcher import AlertDispatcher
from alerts.rate_limiter import RateLimiter
from alerts.retry import RetryHandler
from shared.schemas import IncidentEvent

logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(
        self,
        channels: Optional[List[BaseAlertChannel]] = None,
        max_retries: int = 3,
        min_alert_interval_sec: float = 10.0,
    ):
        self.channels = channels or [TelegramAlertChannel()]
        self.router = AlertRouter()
        self.rate_limiter = RateLimiter(min_interval_sec=min_alert_interval_sec)
        self.retry_handler = RetryHandler(max_retries=max_retries)

    async def dispatch_incident_alert(self, event: IncidentEvent) -> bool:
        key = f"{event.camera_id}:{event.incident_id}"
        if not self.rate_limiter.is_allowed(key):
            logger.debug(f"Alert throttled for {key}")
            return False

        target_channels = self.router.route(event)
        dispatcher = AlertDispatcher(target_channels)
        return await self.retry_handler.execute(lambda: dispatcher.dispatch(event))