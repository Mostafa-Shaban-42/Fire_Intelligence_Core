import asyncio
import logging
from typing import Dict, Optional
from edge.buffering.frame_buffer import NonBlockingFrameBuffer
from edge.camera_agent.health import CameraHealthMonitor
from edge.camera_agent.registry import WorkerRegistry
from edge.camera_agent.worker import CameraWorker

logger = logging.getLogger(__name__)


class CameraSupervisor:
    """Supervises active CameraWorkers, auto-restarts failed nodes."""

    def __init__(self):
        self.registry = WorkerRegistry()
        self.workers: Dict[str, CameraWorker] = {}
        self.health_monitors: Dict[str, CameraHealthMonitor] = {}

    def spawn_worker(
        self,
        camera_id: str,
        source: str,
        buffer: NonBlockingFrameBuffer,
        loop: asyncio.AbstractEventLoop,
    ) -> CameraWorker:
        health_monitor = CameraHealthMonitor(camera_id=camera_id)
        worker = CameraWorker(
            source=source,
            camera_id=camera_id,
            buffer=buffer,
            health_monitor=health_monitor,
            loop=loop,
        )
        self.workers[camera_id] = worker
        self.health_monitors[camera_id] = health_monitor
        worker.start()
        self.registry.register(camera_id, pid=0)
        return worker

    def stop_worker(self, camera_id: str) -> None:
        if camera_id in self.workers:
            self.workers[camera_id].stop()
            del self.workers[camera_id]
            self.registry.unregister(camera_id)
            logger.info(f"Supervisor stopped worker for camera {camera_id}")