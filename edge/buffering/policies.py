import asyncio
from enum import Enum
import logging
from shared.schemas import FramePacket

logger = logging.getLogger(__name__)


class DropPolicy(str, Enum):
    DROP_OLDEST = "DROP_OLDEST"
    DROP_NEWEST = "DROP_NEWEST"


class FrameDropStrategy:
    """Implements queue overflow management policies."""

    @staticmethod
    def apply_policy(queue: asyncio.Queue, policy: DropPolicy = DropPolicy.DROP_OLDEST) -> bool:
        if not queue.full():
            return False

        if policy == DropPolicy.DROP_OLDEST:
            try:
                queue.get_nowait()
                return True
            except asyncio.QueueEmpty:
                return False
        elif policy == DropPolicy.DROP_NEWEST:
            return True
        return False