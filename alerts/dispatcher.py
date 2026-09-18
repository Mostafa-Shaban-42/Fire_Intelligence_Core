import asyncio
from typing import List
from alerts.channels import BaseAlertChannel
from shared.schemas import IncidentEvent

class AlertDispatcher:
    def __init__(self, channels: List[BaseAlertChannel]):
        self.channels = channels

    async def dispatch(self, event: IncidentEvent) -> bool:
        results = await asyncio.gather(*[ch.send_alert(event) for ch in self.channels], return_exceptions=True)
        return all(r is True for r in results if not isinstance(r, Exception))