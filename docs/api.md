# Fire Intelligence Core API Reference

## Base URL
`http://localhost:8000`

---

## Authentication
HTTP Requests must contain the security API Key header:
```http
X-API-Key: your-configured-api-key
Endpoints
1. Ingest Frame Detections
Accepts structured vision bounding box detections and optional IoT telemetry for a camera frame.

Method: POST

Path: /detections/ingest

Request Header: Content-Type: application/json

Request Payload
JSON
{
  "camera_id": "cam-warehouse-east",
  "frame_id": 48201,
  "timestamp": 1700000000.521,
  "detections": [
    {
      "bbox": {
        "xmin": 120.5,
        "ymin": 200.0,
        "xmax": 450.2,
        "ymax": 510.8
      },
      "confidence": 0.89,
      "detection_type": "fire"
    }
  ],
  "temperature_celsius": 45.2,
  "smoke_ppm": 120.0
}
Response Payload (200 OK)
JSON
{
  "camera_id": "cam-warehouse-east",
  "frame_id": 48201,
  "active_tracks_count": 1,
  "scene_risk_score": 78.4,
  "incident_triggered": true,
  "incident_id": "INC-8A91F2C3",
  "processed_at": 1700000000.535
}
2. List Active Incidents
Retrieves a filtered list of tracked incidents across camera zones.

Method: GET

Path: /incidents

Query Parameters:

camera_id (optional, string): Filter by camera identifier.

state (optional, string): Filter by lifecycle state (DETECTED, VALIDATING, CONFIRMED, ESCALATED, RESOLVED, CLOSED).

Response Payload (200 OK)
JSON
{
  "total": 1,
  "incidents": [
    {
      "incident_id": "INC-8A91F2C3",
      "camera_id": "cam-warehouse-east",
      "state": "CONFIRMED",
      "risk_score": 78.4,
      "created_at": 1700000000.0,
      "updated_at": 1700000000.535,
      "factor_breakdown": {
        "confidence_factor": 0.89,
        "temporal_factor": 0.75,
        "spatial_factor": 0.62,
        "sensor_factor": 0.80
      }
    }
  ]
}
3. Transition Incident State
Updates the lifecycle state of an active incident.

Method: PATCH

Path: /incidents/{incident_id}/state

Request Payload
JSON
{
  "target_state": "ACKNOWLEDGED",
  "operator_notes": "Safety officer dispatched to inspect eastern warehouse quadrant."
}
Response Payload (200 OK)
JSON
{
  "incident_id": "INC-8A91F2C3",
  "previous_state": "CONFIRMED",
  "current_state": "ACKNOWLEDGED",
  "updated_at": 1700000015.102,
  "operator_notes": "Safety officer dispatched to inspect eastern warehouse quadrant."
}
4. System Health Check
Exposes liveness and readiness probes for service orchestrators.

Method: GET

Path: /health

Response Payload (200 OK)
JSON
{
  "status": "healthy",
  "uptime_seconds": 3600.5,
  "version": "1.0.0",
  "components": {
    "temporal_tracker": "active",
    "telemetry_registry": "active",
    "alert_dispatcher": "active"
  }
}