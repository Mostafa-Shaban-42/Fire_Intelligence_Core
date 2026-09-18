from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AlertResponse(BaseModel):
    alert_id: str
    incident_id: str
    channel: str
    status: str
    recipient: str
    created_at: datetime