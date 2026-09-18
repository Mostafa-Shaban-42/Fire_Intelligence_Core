from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.schemas import RawDetection


class DetectionIngestRequest(
    BaseModel
):

    """
    Schema for frame-level detections.
    """

    camera_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Unique source camera ID"
        ),
    )

    frame_id: int = Field(
        ...,
        ge=0,
        description=(
            "Sequential frame index"
        ),
    )

    detections: List[
        RawDetection
    ] = Field(
        default_factory=list,
    )

    temperature_celsius: Optional[
        float
    ] = None

    smoke_ppm: Optional[
        float
    ] = None


class DetectionIngestResponse(
    BaseModel
):

    camera_id: str

    frame_id: int

    active_tracks_count: int

    scene_risk_score: float

    incident_triggered: bool

    incident_id: Optional[
        str
    ] = None

    processed_tracks: List[
        Dict[str, Any]
    ] = Field(
        default_factory=list
    )