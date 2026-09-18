import logging
import time

from fastapi import Request

logger = logging.getLogger(__name__)


async def request_timing_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    logger.info(
        "[REQUEST_TIMING] method=%s path=%s total=%.2fms status=%s",
        request.method,
        request.url.path,
        duration_ms,
        response.status_code,
    )

    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"

    return response