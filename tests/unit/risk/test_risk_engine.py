import pytest
from risk.risk_engine import RiskEngine
from shared.enums import DetectionType
from shared.schemas import BoundingBox


def test_risk_engine_calculation():
    risk_engine = RiskEngine()
    
    fused_track = {
        "track_id": 1,
        "detection_type": DetectionType.FIRE.value,
        "bbox": BoundingBox(xmin=100.0, ymin=100.0, xmax=1000.0, ymax=1000.0),
        "smoothed_confidence": 0.90,
        "persistence_duration_sec": 8.0,
        "corroboration_factor": 1.20
    }
    
    score, breakdown = risk_engine.evaluate_track_risk(fused_track)
    
    assert score > 50.0
    assert breakdown.risk_score == score
    assert breakdown.affected_area_ratio > 0.0