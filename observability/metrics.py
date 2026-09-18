from prometheus_client import Counter, Gauge, Histogram, CONTENT_TYPE_LATEST, generate_latest

# Prometheus Metrics Definitions
INFERENCES_TOTAL = Counter(
    "fire_intel_inferences_total",
    "Total frame detection inferences processed",
    ["camera_id"]
)

SCENE_RISK_GAUGE = Gauge(
    "fire_intel_scene_risk_score",
    "Current scene risk score per camera zone",
    ["camera_id"]
)

INCIDENTS_TRIGGERED_TOTAL = Counter(
    "fire_intel_incidents_triggered_total",
    "Total incidents triggered by risk engine",
    ["camera_id", "state"]
)

PIPELINE_LATENCY_SECONDS = Histogram(
    "fire_intel_pipeline_latency_seconds",
    "End-to-end detection to risk processing latency in seconds",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

FRAME_DROPS_TOTAL = Counter(
    "fire_intel_frame_drops_total",
    "Total frames dropped due to backpressure or overload",
    ["camera_id", "reason"]
)

QUEUE_DEPTH_GAUGE = Gauge(
    "fire_intel_queue_depth",
    "Current number of pending frames in ingestion queue"
)


class MetricsCollector:
    """
    Utility wrapper to record platform runtime telemetry into Prometheus registries.
    """

    @staticmethod
    def record_inference(camera_id: str) -> None:
        INFERENCES_TOTAL.labels(camera_id=camera_id).inc()

    @staticmethod
    def set_scene_risk(camera_id: str, risk_score: float) -> None:
        SCENE_RISK_GAUGE.labels(camera_id=camera_id).set(risk_score)

    @staticmethod
    def record_incident(camera_id: str, state: str) -> None:
        INCIDENTS_TRIGGERED_TOTAL.labels(camera_id=camera_id, state=state).inc()

    @staticmethod
    def record_pipeline_latency(seconds: float) -> None:
        PIPELINE_LATENCY_SECONDS.observe(seconds)

    @staticmethod
    def record_frame_drop(camera_id: str, reason: str = "queue_full") -> None:
        FRAME_DROPS_TOTAL.labels(camera_id=camera_id, reason=reason).inc()

    @staticmethod
    def set_queue_depth(depth: int) -> None:
        QUEUE_DEPTH_GAUGE.set(depth)

    @staticmethod
    def get_latest_metrics() -> tuple[bytes, str]:
        """Returns serialized Prometheus metrics buffer and content type header."""
        return generate_latest(), CONTENT_TYPE_LATEST