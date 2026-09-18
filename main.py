import asyncio
from contextlib import asynccontextmanager
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api.routes.cameras import router as cameras_router
from api.routes.detections import router as detections_router
try:
    from api.routes.incidents import router as incidents_router
except ImportError:
    incidents_router = None

try:
    from api.routes.health import router as health_router
except ImportError:
    health_router = None

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
    logger.info("Initializing Google Production-Grade Fire Intelligence Core Engine...")
    cpu_count = max(1, multiprocessing.cpu_count() - 1)
    process_pool = ProcessPoolExecutor(max_workers=cpu_count)
    app.state.process_pool = process_pool

    await pipeline_worker.start()
    yield
    logger.info("Graceful Shutdown Sequence Started...")
    await pipeline_worker.stop()
    process_pool.shutdown(wait=True)
    logger.info("Shutdown completed.")


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تضمين كافة مسارات الكاميرات واكتشاف الحرائق
app.include_router(cameras_router)
app.include_router(detections_router)

if incidents_router:
    app.include_router(incidents_router)

if health_router:
    app.include_router(health_router)


@app.get("/health", status_code=200, tags=["Health"])
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