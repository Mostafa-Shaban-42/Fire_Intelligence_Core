import time
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["System Health"])

START_TIME = time.time()


class HealthCheckResponse(BaseModel):
    status: str
    uptime_seconds: float
    version: str


@router.get(
    "", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK
)
async def health_check():
    """
    Returns API node health metrics and total uptime duration.
    """
    return HealthCheckResponse(
        status="healthy",
        uptime_seconds=round(time.time() - START_TIME, 2),
        version="1.0.0",
    )