import logging
import time
from typing import Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuxiliarySensorReading(BaseModel):
    """
    Schema for external IoT telemetry inputs (e.g., thermal cameras, CO2, temperature sensors).
    """
    sensor_id: str
    camera_id: str
    temperature_celsius: Optional[float] = None
    smoke_ppm: Optional[float] = None
    co2_ppm: Optional[float] = None
    timestamp: float = Field(default_factory=time.time)


class SensorStateRegistry:
    """
    Thread-safe in-memory cache for auxiliary sensor readings, with automatic staleness eviction.
    """

    def __init__(self, ttl_seconds: float = 10.0):
        self.ttl_seconds = ttl_seconds
        self._registry: Dict[str, AuxiliarySensorReading] = {}

    def update_sensor_reading(self, reading: AuxiliarySensorReading) -> None:
        """Stores or updates telemetry for a specific camera/zone."""
        self._registry[reading.camera_id] = reading
        logger.debug(f"Updated sensor telemetry for camera {reading.camera_id}")

    def get_sensor_reading(self, camera_id: str) -> Optional[AuxiliarySensorReading]:
        """Retrieves active telemetry, returning None if data is stale or missing."""
        reading = self._registry.get(camera_id)
        if not reading:
            return None

        if (time.time() - reading.timestamp) > self.ttl_seconds:
            logger.warning(f"Sensor telemetry for camera {camera_id} expired. Discarding.")
            self._registry.pop(camera_id, None)
            return None

        return reading