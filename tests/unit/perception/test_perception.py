import pytest
from shared.enums import DetectionType
from shared.schemas import BoundingBox, RawDetection


def test_raw_detection_creation():
    bbox = BoundingBox(xmin=10.0, ymin=10.0, xmax=100.0, ymax=100.0)
    detection = RawDetection(bbox=bbox, confidence=0.88, detection_type=DetectionType.FIRE)
    
    assert detection.confidence == 0.88
    assert detection.detection_type == DetectionType.FIRE
    assert detection.bbox.xmin == 10.0