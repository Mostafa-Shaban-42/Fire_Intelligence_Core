import asyncio
import logging
from typing import Any, Dict, Optional

from configs.settings import settings
from edge.buffering.frame_buffer import NonBlockingFrameBuffer
from edge.camera_agent.health import CameraHealthMonitor
from edge.camera_agent.supervisor import CameraSupervisor
from edge.camera_agent.worker import CameraWorker
from edge.processing.frame_processor import FrameProcessor
from shared.schemas import FramePacket

logger = logging.getLogger(__name__)


class EdgeRuntimeEngine:
    """
    Independent Execution Engine orchestrating stream capture, processing, and health telemetry.
    """

    def __init__(self):
        self.buffer = NonBlockingFrameBuffer(maxsize=settings.MAX_FRAME_BUFFER_SIZE)
        self.health = CameraHealthMonitor(camera_id=settings.CAMERA_ID)
        self.processor = FrameProcessor(pipeline_id=f"Pipe-{settings.CAMERA_ID}")
        self.supervisor = CameraSupervisor()
        self.camera_worker: Optional[CameraWorker] = None
        self._is_running: bool = False
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._is_running:
            logger.warning("Edge Runtime Engine is already active.")
            return

        self._is_running = True
        loop = asyncio.get_running_loop()

        self.camera_worker = self.supervisor.spawn_worker(
            camera_id=settings.CAMERA_ID,
            source=settings.RTSP_URL,
            buffer=self.buffer,
            loop=loop,
        )

        self._worker_task = asyncio.create_task(self._runtime_loop())
        logger.info("⚡ Edge Runtime Engine successfully initialized and running.")

    async def stop(self) -> None:
        self._is_running = False
        if self.camera_worker:
            self.camera_worker.stop()

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        self.buffer.clear()
        logger.info("🛑 Edge Runtime Engine cleanly stopped.")

    async def _runtime_loop(self) -> None:
        logger.info("Edge Runtime processing loop active.")
        while self._is_running:
            try:
                frame_packet: Optional[FramePacket] = await self.buffer.get()
                if frame_packet is None:
                    await asyncio.sleep(0.005)
                    continue

                processed_packet = await self.processor.process_frame(frame_packet)
                if processed_packet is None:
                    continue

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Unexpected error in Edge Runtime loop: {str(e)}",
                    exc_info=True,
                )
                await asyncio.sleep(0.01)

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "runtime_active": self._is_running,
            "health": self.health.get_telemetry(),
            "buffer": self.buffer.metrics,
            "pipeline": self.processor.get_metrics(),
        }


# Forward compatibility alias for previous imports
EdgeRuntime = EdgeRuntimeEngine