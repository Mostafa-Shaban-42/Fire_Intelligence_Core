import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional
from shared.schemas import RawDetection

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class QueueItem:
    camera_id: str
    frame_id: int
    detections: List[RawDetection]
    temperature_celsius: Optional[float] = None
    smoke_ppm: Optional[float] = None
    received_ts: float = field(default_factory=time.monotonic)
    enqueued_ts: float = field(default_factory=time.monotonic)
    trace_id: str = field(default_factory=str)


class ProductionFrameQueue:
    """Bounded Low-Latency Drop-Oldest Queue Engine (<1ms overhead)."""

    def __init__(self, maxsize: int = 100) -> None:
        self.maxsize = maxsize
        self.queue: asyncio.Queue[QueueItem] = asyncio.Queue(maxsize=maxsize)
        self.dropped_frames: int = 0
        self.processed_frames: int = 0

    def size(self) -> int:
        """Returns current queue depth safely to support both method and attribute calls."""
        return self.queue.qsize()

    def qsize(self) -> int:
        """Alias for size() for standard asyncio.Queue compatibility."""
        return self.queue.qsize()

    def enqueue(
        self,
        camera_id: str,
        frame_id: int,
        detections: List[RawDetection],
        temperature_celsius: Optional[float] = None,
        smoke_ppm: Optional[float] = None,
        received_ts: Optional[float] = None,
        trace_id: str = "",
    ) -> bool:
        now = time.monotonic()
        item = QueueItem(
            camera_id=camera_id,
            frame_id=frame_id,
            detections=detections,
            temperature_celsius=temperature_celsius,
            smoke_ppm=smoke_ppm,
            received_ts=received_ts if received_ts is not None else now,
            enqueued_ts=now,
            trace_id=trace_id or f"{camera_id}-{frame_id}",
        )

        # Drop Oldest Strategy for Zero Queue Latency
        if self.queue.full():
            try:
                self.queue.get_nowait()
                self.dropped_frames += 1
            except Exception:
                pass

        try:
            self.queue.put_nowait(item)
            return True
        except Exception:
            return False

    async def dequeue(self) -> QueueItem:
        item = await self.queue.get()
        self.processed_frames += 1
        return item

    async def dequeue_batch(
        self, 
        max_batch_size: int = 16, 
        timeout: float = 0.05,
        **kwargs
    ) -> List[QueueItem]:
        """Collects up to max_batch_size items or returns immediately when timeout expires."""
        limit = kwargs.get("batch_size", max_batch_size)
        items: List[QueueItem] = []
        try:
            first_item = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            items.append(first_item)
            self.processed_frames += 1
            
            while len(items) < limit and not self.queue.empty():
                item = self.queue.get_nowait()
                items.append(item)
                self.processed_frames += 1
        except asyncio.TimeoutError:
            pass

        return items

    def task_done(self) -> None:
        try:
            self.queue.task_done()
        except ValueError:
            pass


global_frame_queue = ProductionFrameQueue(maxsize=100)