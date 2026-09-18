from datetime import datetime, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from shared.enums import DetectionType, IncidentState


class PhaseProfilingTelemetry(BaseModel):
    """
    Microsecond-level latency breakdown for decoupled pipeline profiling.
    All fields are measured in milliseconds (ms).
    """

    ingestion_latency_ms: float = Field(
        default=0.0, description="Time to validate and enqueue request"
    )
    queue_wait_ms: float = Field(
        default=0.0, description="Time spent waiting inside async queue"
    )
    tracking_latency_ms: float = Field(
        default=0.0, description="Time spent in ByteTrack & spatial state update"
    )
    pipeline_latency_ms: float = Field(
        default=0.0, description="Total backend processing time"
    )
    total_e2e_ms: float = Field(
        default=0.0, description="Total end-to-end elapsed time since request receipt"
    )


class DetailedTelemetry(BaseModel):
    """
    HTTP Ingestion Telemetry payload returned to client.
    """

    ingestion_latency_ms: float = Field(
        default=0.0, description="Time to receive and enqueue request"
    )


class BoundingBox(BaseModel):
    """
    Normalized spatial coordinates [xmin, ymin, xmax, ymax] for object localization.
    """

    xmin: float = Field(..., ge=0.0)
    ymin: float = Field(..., ge=0.0)
    xmax: float = Field(..., ge=0.0)
    ymax: float = Field(..., ge=0.0)


class RawDetection(BaseModel):
    """
    Inference detection bounding box output from visual vision models.
    """

    bbox: BoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0)
    detection_type: DetectionType


class RawDetectionPayload(BaseModel):
    """
    HTTP Ingestion request payload representing frame detections from a camera.
    """

    camera_id: str = Field(..., min_length=1)
    frame_id: Optional[int] = Field(default=0)
    detections: List[RawDetection] = Field(default_factory=list)


class IngestResponse(BaseModel):
    """
    API Response for frame detection ingestion (HTTP 202 Accepted).
    """

    status: str = "accepted"
    camera_id: str
    telemetry: DetailedTelemetry


class RiskFactorBreakdown(BaseModel):
    """
    Explainable risk scoring mathematical factor metrics.
    """

    detection_confidence_weight: float = Field(..., ge=0.0, le=1.0)
    temporal_persistence_weight: float = Field(..., ge=0.0)
    affected_area_ratio: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=100.0)


class IncidentEvent(BaseModel):
    """
    Immutable domain incident payload emitted across pipeline layers.
    """

    incident_id: str
    camera_id: str
    state: IncidentState
    risk_score: float
    factors: RiskFactorBreakdown
    model_name: str = "fire-intelligence-v1"
    model_version: str = "v1.0.0"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class FramePacket(BaseModel):
    """
    In-memory data packet carrying raw video frame matrix and ingestion latency metrics.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    frame_id: int
    camera_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    raw_frame_ref: Optional[Any] = Field(default=None, exclude=True)
    acquisition_latency_ms: float = 0.0