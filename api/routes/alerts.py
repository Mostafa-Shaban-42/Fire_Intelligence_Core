from typing import List
from fastapi import APIRouter
from api.schemas.alert import AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts Management"])

@router.get("", response_model=List[AlertResponse])
async def list_alerts():
    return []