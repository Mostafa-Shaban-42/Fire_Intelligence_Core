"""
Multi-Sensor Fusion Layer: Corroborates visual tracking signals with auxiliary
environmental sensor readings (e.g., thermal, gas, smoke) and cross-class spatial evidence.
"""
from fusion.fusion_engine import SensorFusionEngine
from fusion.sensor_state import AuxiliarySensorReading, SensorStateRegistry

__all__ = [
    "AuxiliarySensorReading",
    "SensorStateRegistry",
    "SensorFusionEngine",
]