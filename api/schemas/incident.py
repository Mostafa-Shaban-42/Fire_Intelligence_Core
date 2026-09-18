from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from shared.enums import IncidentState
from shared.schemas import RiskFactorBreakdown

class IncidentStateUpdate(BaseModel):
    target_state: IncidentState = Field(..., description="Desired lifecycle state transition")
    operator_notes: Optional[str] = Field(None, max_length=500, description="Audit notes for transition log")

class IncidentResponse(BaseModel):
    incident_id: str
    camera_id: str
    state: IncidentState
    risk_score: float
    factors: RiskFactorBreakdown
    model_name: str
    model_version: str
    timestamp: datetime