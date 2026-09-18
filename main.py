import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import uvicorn

from api.routes.detections import router as detections_router
from core.engine.pipeline_worker import pipeline_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fire_intelligence_api")

MAX_CONCURRENT_REQUESTS = 1000
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Fire Intelligence Core Engine...")
    await pipeline_worker.start()
    yield
    logger.info("Shutting down Fire Intelligence Core Engine...")
    await pipeline_worker.stop()


app = FastAPI(
    title="Google Production-Grade Fire Intelligence Core",
    version="2.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_catchall_exception_handler(request: Request, exc: Exception):
    """Zero Unhandled 500 Internal Server Errors Protection."""
    logger.error(f"Global Exception Caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "degraded",
            "message": "Engine processing overloaded or recovering. Backpressure drop applied.",
            "detail": str(exc),
        },
    )


@app.middleware("http")
async def backpressure_middleware(request: Request, call_next):
    try:
        async with asyncio.timeout(1.5):
            async with semaphore:
                return await call_next(request)
    except TimeoutError:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "System saturated. High-density traffic throttled."},
        )


app.include_router(detections_router)


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy", "engine": "fire_intelligence_core_onnx"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        loop="asyncio",
        http="httptools",
        limit_concurrency=2000,
        backlog=4096,
        timeout_keep_alive=30,
        access_log=False,
    )