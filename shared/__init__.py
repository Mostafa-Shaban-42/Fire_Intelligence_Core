"""
Shared Layer: Enterprise data models, enumerations, custom exception classes,
and domain event definitions utilized across all platform modules.
"""

from shared.enums import CameraHealthState, DetectionType, IncidentState
from shared.events import BaseEvent, FrameIngestedEvent, IncidentTriggeredEvent
from shared.exceptions import (
    AuthenticationError,
    CameraNotFoundError,
    FireIntelException,
    InvalidStateTransitionError,
    SensorDataInvalidError,
)
from shared.schemas import (
    BoundingBox,
    FramePacket,
    IncidentEvent,
    RawDetection,
    RiskFactorBreakdown,
)

__all__ = [
    "DetectionType",
    "IncidentState",
    "CameraHealthState",
    "BaseEvent",
    "FrameIngestedEvent",
    "IncidentTriggeredEvent",
    "FireIntelException",
    "InvalidStateTransitionError",
    "CameraNotFoundError",
    "AuthenticationError",
    "SensorDataInvalidError",
    "BoundingBox",
    "RawDetection",
    "RiskFactorBreakdown",
    "IncidentEvent",
    "FramePacket",
]