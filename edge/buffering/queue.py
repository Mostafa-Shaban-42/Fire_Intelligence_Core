import asyncio
from typing import Optional
from shared.schemas import FramePacket


class MediaBoundedQueue:
    def __init__(self, maxsize: int = 2):
        self.maxsize = maxsize
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)

    async def push(self, packet: FramePacket) -> bool:
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        try:
            self._queue.put_nowait(packet)
            return True
        except Exception:
            return False

    async def pop(self) -> Optional[FramePacket]:
        try:
            return await self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    def is_full(self) -> bool:
        return self._queue.full()

    def qsize(self) -> int:
        return self._queue.qsize()