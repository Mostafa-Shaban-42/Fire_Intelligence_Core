import asyncio
import logging
import time
from typing import Any, Dict, Optional
from edge.buffering.policies import DropPolicy, FrameDropStrategy
from shared.schemas import FramePacket

logger = logging.getLogger(__name__)


class NonBlockingFrameBuffer:
    """
    Non-blocking frame buffer ensuring zero delay latency accumulation using Drop-Oldest policy.
    """

    def __init__(self, maxsize: int = 2, policy: DropPolicy = DropPolicy.DROP_OLDEST):
        self.maxsize = maxsize
        self.policy = policy
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._dropped_frames: int = 0
        self._processed_frames: int = 0
        self._last_fps_calc: float = time.time()
        self._current_fps: float = 0.0

    async def put(self, frame_packet: FramePacket) -> None:
        """Inserts a new frame. If buffer is full, drops frame based on drop policy."""
        if self._queue.full():
            dropped = FrameDropStrategy.apply_policy(self._queue, self.policy)
            if dropped:
                self._dropped_frames += 1
                if self.policy == DropPolicy.DROP_NEWEST:
                    return

        await self._queue.put(frame_packet)

    async def get(self) -> Optional[FramePacket]:
        """Fetches the latest available frame from the buffer."""
        try:
            packet = self._queue.get_nowait()
            self._processed_frames += 1
            self._update_fps()
            return packet
        except asyncio.QueueEmpty:
            return None

    def _update_fps(self) -> None:
        now = time.time()
        elapsed = now - self._last_fps_calc
        if elapsed >= 1.0:
            self._current_fps = self._processed_frames / elapsed
            self._processed_frames = 0
            self._last_fps_calc = now

    def clear(self) -> None:
        """Clears all pending frames in queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    @property
    def metrics(self) -> Dict[str, Any]:
        return {
            "queue_depth": self._queue.qsize(),
            "max_depth": self.maxsize,
            "dropped_frames_total": self._dropped_frames,
            "processing_fps": round(self._current_fps, 2),
        }