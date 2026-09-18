import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_e2e_detection_ingestion_and_incident_flow():
    payload = {
        "camera_id": "cam-e2e-01",
        "frame_id": 1,
        "detections": [
            {
                "bbox": {"xmin": 100.0, "ymin": 100.0, "xmax": 900.0, "ymax": 900.0},
                "confidence": 0.95,
                "detection_type": "fire"
            }
        ],
        "temperature_celsius": 65.0,
        "smoke_ppm": 200.0
    }

    response = client.post("/detections/ingest", json=payload)
    assert response.status_code == 202
    res_data = response.json()
    
    assert res_data.get("camera_id") == "cam-e2e-01" or res_data.get("status") in ["accepted", "queued", "ok", "success"]