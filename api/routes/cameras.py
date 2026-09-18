from __future__ import annotations

import logging
import os
import time
from typing import Dict, List, Optional

import cv2
import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from perception.detection.fire_detector import get_fire_detector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cameras", tags=["Camera Streams"])


async def get_user_location_async() -> tuple[float, float, str]:
    """Non-blocking IP Geolocation lookup using httpx async client."""
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            response = await client.get("https://ipapi.co/json/")
            if response.status_code == 200:
                data = response.json()
                return (
                    float(data.get("latitude", 30.0444)),
                    float(data.get("longitude", 31.2357)),
                    f"{data.get('city', '')}, {data.get('country_name', '')}".strip(", "),
                )
    except Exception as exc:
        logger.warning(f"Failed to resolve IP location asynchronously: {exc}")
    return 30.0444, 31.2357, "Default System"


CAMERA_REGISTRY: Dict[str, dict] = {
    "cam_default": {
        "camera_id": "cam_default",
        "location": "Local System (Default)",
        "rtsp_url": "0",
        "latitude": 30.0444,
        "longitude": 31.2357,
        "is_active": True,
        "has_fire": False,
        "registered_at": time.time(),
    }
}


class CameraRegisterRequest(BaseModel):
    camera_id: str = Field(..., min_length=3, max_length=64)
    location: str = Field(..., min_length=3, max_length=128)
    rtsp_url: str = Field(..., min_length=1)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    is_active: bool = True


class CameraResponse(BaseModel):
    camera_id: str
    location: str
    rtsp_url: str
    latitude: float
    longitude: float
    is_active: bool
    registered_at: float
    has_fire: bool = False


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def register_camera(payload: CameraRegisterRequest):
    if payload.camera_id in CAMERA_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Camera '{payload.camera_id}' is already registered.",
        )

    record = payload.model_dump()
    if record["latitude"] is None or record["longitude"] is None:
        auto_lat, auto_lng, _ = await get_user_location_async()
        record["latitude"] = auto_lat
        record["longitude"] = auto_lng

    record["registered_at"] = time.time()
    record["has_fire"] = False
    CAMERA_REGISTRY[payload.camera_id] = record
    return record


@router.get("", response_model=List[CameraResponse])
async def list_cameras():
    return list(CAMERA_REGISTRY.values())


@router.get("/metrics")
async def get_live_metrics():
    detector = get_fire_detector()
    return JSONResponse(content=detector.get_metrics())


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: str):
    if camera_id not in CAMERA_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found.",
        )
    return CAMERA_REGISTRY[camera_id]


def generate_camera_stream(camera_id: str, source: str | int = 0):
    if isinstance(source, str) and source.isdigit():
        source = int(source)

    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    detector = get_fire_detector()
    if not detector.is_ready():
        detector.load()

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                if isinstance(source, str) and os.path.exists(source):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            annotated_frame, detections = detector.detect_and_draw(frame)

            fire_active = any(d.get("detection_type") == "fire" for d in detections)
            if camera_id in CAMERA_REGISTRY:
                CAMERA_REGISTRY[camera_id]["has_fire"] = fire_active

            ret, buffer = cv2.imencode(".jpg", annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )
    finally:
        if camera_id in CAMERA_REGISTRY:
            CAMERA_REGISTRY[camera_id]["has_fire"] = False
        cap.release()


@router.get("/stream/{camera_id}")
async def stream_camera(camera_id: str):
    source = 0
    if camera_id in CAMERA_REGISTRY:
        source = CAMERA_REGISTRY[camera_id].get("rtsp_url", 0)

    return StreamingResponse(
        generate_camera_stream(camera_id=camera_id, source=source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )