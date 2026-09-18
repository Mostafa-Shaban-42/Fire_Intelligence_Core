import asyncio
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class RetryHandler:
    def __init__(self, max_retries: int = 3, backoff_base: float = 1.0):
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    async def execute(self, func: Callable[[], Any]) -> bool:
        for attempt in range(1, self.max_retries + 1):
            try:
                res = await func()
                if res:
                    return True
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {e}")
            
            if attempt < self.max_retries:
                await asyncio.sleep(self.backoff_base * (2 ** (attempt - 1)))
        return False