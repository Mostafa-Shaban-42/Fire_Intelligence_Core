from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from api.schemas.incident import IncidentResponse, IncidentStateUpdate
from shared.enums import IncidentState

router = APIRouter(prefix="/incidents", tags=["Incident Management"])

@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    camera_id: Optional[str] = Query(None),
    state: Optional[IncidentState] = Query(None),
):
    return []

@router.patch("/{incident_id}/state", response_model=dict)
async def update_incident_state(incident_id: str, payload: IncidentStateUpdate):
    return {"status": "success", "incident_id": incident_id, "state": payload.target_state}