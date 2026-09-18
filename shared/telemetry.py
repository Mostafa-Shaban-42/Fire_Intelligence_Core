import dataclasses
from collections import defaultdict
from typing import Dict, List


@dataclasses.dataclass
class PipelineMetrics:
    queue_wait_ms: float = 0.0
    sensor_ms: float = 0.0
    tracking_ms: float = 0.0
    fusion_ms: float = 0.0
    risk_ms: float = 0.0
    incident_ms: float = 0.0
    alert_ms: float = 0.0
    total_ms: float = 0.0
    e2e_ms: float = 0.0


class PipelineProfiler:
    """In-memory thread-safe profiler to aggregate detailed timing stats
    across cameras for bottleneck diagnosis.
    """

    def __init__(self):
        self._records: Dict[str, List[PipelineMetrics]] = defaultdict(list)

    def record(self, camera_id: str, metrics: PipelineMetrics) -> None:
        if len(self._records[camera_id]) > 500:
            self._records[camera_id].pop(0)  # Ring buffer for memory safety
        self._records[camera_id].append(metrics)

    def get_summary(self) -> Dict[str, Dict[str, float]]:
        summary = {}
        for cam_id, metrics_list in self._records.items():
            if not metrics_list:
                continue
            count = len(metrics_list)
            summary[cam_id] = {
                "avg_queue_wait_ms": round(
                    sum(m.queue_wait_ms for m in metrics_list) / count, 2
                ),
                "avg_sensor_ms": round(
                    sum(m.sensor_ms for m in metrics_list) / count, 2
                ),
                "avg_tracking_ms": round(
                    sum(m.tracking_ms for m in metrics_list) / count, 2
                ),
                "avg_fusion_ms": round(
                    sum(m.fusion_ms for m in metrics_list) / count, 2
                ),
                "avg_risk_ms": round(
                    sum(m.risk_ms for m in metrics_list) / count, 2
                ),
                "avg_incident_ms": round(
                    sum(m.incident_ms for m in metrics_list) / count, 2
                ),
                "avg_alert_ms": round(
                    sum(m.alert_ms for m in metrics_list) / count, 2
                ),
                "avg_processing_total_ms": round(
                    sum(m.total_ms for m in metrics_list) / count, 2
                ),
                "avg_e2e_total_ms": round(
                    sum(m.e2e_ms for m in metrics_list) / count, 2
                ),
                "samples_count": count,
            }
        return summary


global_profiler = PipelineProfiler()