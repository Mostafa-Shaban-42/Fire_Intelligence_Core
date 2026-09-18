import time
from typing import Dict

class IncidentDeduplicator:
    def __init__(self, time_window_seconds: float = 10.0):
        self.time_window = time_window_seconds
        self._recent_keys: Dict[str, float] = {}

    def is_duplicate(self, camera_id: str, zone_id: str) -> bool:
        key = f"{camera_id}:{zone_id}"
        now = time.time()
        last_seen = self._recent_keys.get(key, 0.0)
        
        if now - last_seen < self.time_window:
            return True
            
        self._recent_keys[key] = now
        return False