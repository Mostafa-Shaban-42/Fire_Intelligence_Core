import time
from typing import Any, Dict, Optional


class WorkerRegistry:
    """Registry maintaining active workers state and heartbeat references."""

    def __init__(self):
        self._workers: Dict[str, Dict[str, Any]] = {}

    def register(self, camera_id: str, pid: int, metadata: Optional[Dict[str, Any]] = None) -> None:
        self._workers[camera_id] = {
            "pid": pid,
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
            "metadata": metadata or {},
        }

    def update_heartbeat(self, camera_id: str) -> None:
        if camera_id in self._workers:
            self._workers[camera_id]["last_heartbeat"] = time.time()

    def unregister(self, camera_id: str) -> None:
        self._workers.pop(camera_id, None)

    def get_worker(self, camera_id: str) -> Optional[Dict[str, Any]]:
        return self._workers.get(camera_id)

    def active_workers(self) -> Dict[str, Dict[str, Any]]:
        return self._workers.copy()