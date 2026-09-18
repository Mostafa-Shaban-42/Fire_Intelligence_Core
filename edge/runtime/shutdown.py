import asyncio
import logging

logger = logging.getLogger(__name__)


class GracefulShutdownHandler:
    """Manages orderly resource teardown on runtime termination."""

    @staticmethod
    async def shutdown(buffer, supervisor) -> None:
        logger.info("Executing graceful shutdown for Edge Runtime...")
        buffer.clear()
        for camera_id in list(supervisor.workers.keys()):
            supervisor.stop_worker(camera_id)
        logger.info("Graceful shutdown completed successfully.")