import time
from typing import Dict

class RateLimiter:
    def __init__(self, min_interval_sec: float = 10.0):
        self.min_interval = min_interval_sec
        self._last_times: Dict[str, float] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        last = self._last_times.get(key, 0.0)
        if now - last < self.min_interval:
            return False
        self._last_times[key] = now
        return True