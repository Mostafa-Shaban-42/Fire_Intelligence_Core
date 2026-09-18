from enum import Enum


class DetectionType(str, Enum):
    """
    Supported computer vision detection target classes.
    """
    FIRE = "fire"
    SMOKE = "smoke"


class IncidentState(str, Enum):
    """
    Lifecycle states for automated fire incident detection and escalation.
    """
    DETECTED = "DETECTED"
    VALIDATING = "VALIDATING"
    CONFIRMED = "CONFIRMED"
    ESCALATED = "ESCALATED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CameraHealthState(str, Enum):
    """
    Health status of connected edge camera streams.
    """
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"