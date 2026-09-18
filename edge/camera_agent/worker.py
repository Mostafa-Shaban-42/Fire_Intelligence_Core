import asyncio
from datetime import datetime, timezone
import logging
import os
import threading
import time
from typing import Optional, Union

from configs.settings import settings
from edge.buffering.frame_buffer import NonBlockingFrameBuffer
from edge.camera_agent.health import CameraHealthMonitor
from edge.capture.rtsp import RTSPCapture
from edge.capture.usb import USBCapture
from shared.schemas import FramePacket

logger = logging.getLogger(__name__)


class CameraWorker:
    """Standalone Camera Ingestion Worker running in a dedicated thread/process."""

    def __init__(
        self,
        source: Union[str, int],
        camera_id: str,
        buffer: NonBlockingFrameBuffer,
        health_monitor: CameraHealthMonitor,
        loop: asyncio.AbstractEventLoop,
    ):
        self.source = int(source) if str(source).isdigit() else str(source)
        self.camera_id = camera_id
        self.buffer = buffer
        self.health = health_monitor
        self.loop = loop

        self.driver: Union[USBCapture, RTSPCapture]
        if isinstance(self.source, int) or str(self.source).isdigit():
            self.driver = USBCapture(device_index=int(self.source))
        else:
            self.driver = RTSPCapture(rtsp_url=str(self.source))

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._frame_counter: int = 0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"Worker-{self.camera_id}",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"CameraWorker PID [{os.getpid()}] started for camera: {self.camera_id}")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.driver.release()
        logger.info(f"CameraWorker stopped for camera: {self.camera_id}")

    def _run_loop(self) -> None:
        while self._running:
            if not self.driver.is_connected():
                self.health.record_reconnect()
                connected = self.driver.connect()
                if not connected:
                    time.sleep(settings.RTSP_RECONNECT_INTERVAL_SEC)
                    continue

            ret, frame, acquisition_latency = self.driver.read_frame()

            if not ret or frame is None:
                self.health.record_error("Empty or corrupted frame received.")
                self.driver.release()
                time.sleep(0.5)
                continue

            self._frame_counter += 1
            self.health.record_frame()

            packet = FramePacket(
                frame_id=self._frame_counter,
                camera_id=self.camera_id,
                timestamp=datetime.now(timezone.utc),
                raw_frame_ref=frame,
                acquisition_latency_ms=round(acquisition_latency, 2),
            )

            asyncio.run_coroutine_threadsafe(self.buffer.put(packet), self.loop)

            if settings.TARGET_FPS > 0:
                target_delay = 1.0 / settings.TARGET_FPS
                time.sleep(target_delay)