"""
Edge Communication Protocols and Event Definitions
"""

from edge.protocols.commands import CameraCommand, CommandType
from edge.protocols.events import DetectionEvent, FrameCapturedEvent
from edge.protocols.health import CameraHealthReport, HeartbeatMessage

__all__ = [
    "FrameCapturedEvent",
    "DetectionEvent",
    "CameraCommand",
    "CommandType",
    "HeartbeatMessage",
    "CameraHealthReport",
]