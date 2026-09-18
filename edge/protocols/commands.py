from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class CommandType(str, Enum):
    START_WORKER = "START_WORKER"
    STOP_WORKER = "STOP_WORKER"
    RESTART_WORKER = "RESTART_WORKER"
    UPDATE_CONFIG = "UPDATE_CONFIG"


class CameraCommand(BaseModel):
    """Command payload sent to control camera workers or runtime execution."""
    command_type: CommandType
    camera_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)