import logging
import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from core.engine.async_queue_manager import global_frame_queue
from shared.schemas import DetailedTelemetry, IngestResponse, RawDetectionPayload
from shared.telemetry import global_profiler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion Plane"])


@router.post(
    "/raw",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_raw_detections(payload: RawDetectionPayload) -> IngestResponse:
    """
    High-Throughput Non-Blocking Frame Ingestion Endpoint.
    Validates incoming detection payloads and immediately queues them.
    Returns HTTP 202 Accepted instantly.
    """
    req_received_ts = time.monotonic()

    # 1. TRACE ID GENERATION / PROPAGATION
    trace_id = getattr(payload, "trace_id", None) or f"tr-{uuid.uuid4().hex[:12]}"

    # 2. INSTANT NON-BLOCKING ENQUEUE
    success = await global_frame_queue.enqueue(
        camera_id=payload.camera_id,
        frame_id=payload.frame_id or 0,
        detections=payload.detections,
        temperature_celsius=getattr(payload, "temperature_celsius", None),
        smoke_ppm=getattr(payload, "smoke_ppm", None),
        received_ts=req_received_ts,
        trace_id=trace_id,
    )

    ingestion_latency_ms = (time.monotonic() - req_received_ts) * 1000.0

    if not success:
        # Emergency Backpressure Safety Net (Only if Queue Strategy Hard Refuses)
        logger.error(
            "[INGEST_OVERLOAD] Queue rejected frame | trace_id=%s | camera_id=%s | frame_id=%d",
            trace_id,
            payload.camera_id,
            payload.frame_id or 0,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System overload: Queue capacity exceeded. Frame dropped for real-time stability.",
        )

    logger.debug(
        "[INGEST_ACK] trace_id=%s | camera_id=%s | frame_id=%d | ingest_ms=%.3f",
        trace_id,
        payload.camera_id,
        payload.frame_id or 0,
        ingestion_latency_ms,
    )

    return IngestResponse(
        status="accepted",
        camera_id=payload.camera_id,
        telemetry=DetailedTelemetry(
            ingestion_latency_ms=round(ingestion_latency_ms, 3),
            trace_id=trace_id,
        ),
    )


@router.get("/telemetry", response_model=Dict[str, Any])
async def get_ingest_telemetry() -> Dict[str, Any]:
    """
    Returns aggregated profiling metrics specifically for the raw ingestion plane.
    """
    return {
        "profiler": global_profiler.get_summary(),
        "queue_depth": global_frame_queue.size(),
    }