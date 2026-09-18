import time
from typing import Any, Dict
from shared.enums import CameraHealthState


class CameraHealthMonitor:
    """
    Camera health and live stream monitoring and evaluation unit.
    State transitions: ONLINE / DEGRADED / OFFLINE
    """

    def __init__(self, camera_id: str, heartbeat_timeout_sec: float = 5.0):
        self.camera_id = camera_id
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.state = CameraHealthState.OFFLINE
        self.last_frame_time = 0.0
        self.total_frames_received = 0
        self.total_reconnections = 0
        self.last_error = ""

    def record_frame(self) -> None:
        """New frame successfully checked in"""
        self.last_frame_time = time.time()
        self.total_frames_received += 1
        self.state = CameraHealthState.ONLINE

    def record_error(self, error_msg: str) -> None:
        """Logging read errors or interruptions"""
        self.last_error = error_msg
        if self.state == CameraHealthState.ONLINE:
            self.state = CameraHealthState.DEGRADED

    def record_reconnect(self) -> None:
        """Logging reconnection attempts"""
        self.total_reconnections += 1
        self.state = CameraHealthState.DEGRADED

    def check_health(self) -> CameraHealthState:
        """Checking camera status based on the timeout period"""
        now = time.time()
        if (
            self.last_frame_time == 0.0
            or (now - self.last_frame_time) > self.heartbeat_timeout_sec
        ):
            self.state = CameraHealthState.OFFLINE
        return self.state

    def get_telemetry(self) -> Dict[str, Any]:
        """Return live tracking data for performance monitoring"""
        return {
            "camera_id": self.camera_id,
            "state": self.check_health().value,
            "total_frames_received": self.total_frames_received,
            "total_reconnections": self.total_reconnections,
            "last_frame_timestamp": self.last_frame_time,
            "last_error": self.last_error,
        }