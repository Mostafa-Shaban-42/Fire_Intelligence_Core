import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager, suppress
import logging
import multiprocessing

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from api.middleware.request_timing import request_timing_middleware
except ImportError:
    request_timing_middleware = None

from api.routes import (
    cameras_router,
    detections_router,
)

try:
    from api.routes import health_router, incidents_router
except ImportError:
    health_router = None
    incidents_router = None

try:
    from configs.settings import settings
    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
except Exception:
    log_level = logging.INFO

from core.engine.pipeline_worker import pipeline_worker

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fire_intelligence_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Fire Intelligence Platform Engine...")
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
    title="Fire Intelligence Platform API",
    version="2.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def api_global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "error", "message": "Service handling load shed", "detail": str(exc)},
    )


if request_timing_middleware:
    app.middleware("http")(request_timing_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras_router)
app.include_router(detections_router)

if health_router:
    app.include_router(health_router)
if incidents_router:
    app.include_router(incidents_router)