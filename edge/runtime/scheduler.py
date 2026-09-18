import asyncio
import logging

logger = logging.getLogger(__name__)


class StreamScheduler:
    """Schedules execution rates and frame sampling intervals."""

    def __init__(self, fps_limit: float = 30.0):
        self.interval = 1.0 / fps_limit if fps_limit > 0 else 0.0

    async def throttle(self) -> None:
        if self.interval > 0:
            await asyncio.sleep(self.interval)