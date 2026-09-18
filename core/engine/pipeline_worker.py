import asyncio
import logging
import time
from typing import List, Optional

from alerts.alert_engine import AlertEngine
from core.engine.async_queue_manager import QueueItem, global_frame_queue
from fusion.fusion_engine import SensorFusionEngine
from fusion.sensor_state import AuxiliarySensorReading, SensorStateRegistry
from incidents.incident_engine import IncidentEngine
from observability.metrics import MetricsCollector
from risk.risk_engine import RiskEngine
from shared.telemetry import PipelineMetrics, global_profiler
from temporal.tracking.track_manager import TrackManager

logger = logging.getLogger(__name__)


class PipelineWorker:
    """
    Production-Grade Decoupled Background Pipeline Worker Engine.
    Executes Spatial Tracking, Sensor Fusion, Risk Assessment, Incident Lifecycle,
    and Alert Dispatch asynchronously using Native Non-Blocking Micro-Batches.
    """

    def __init__(self, batch_size: int = 32, flush_interval_sec: float = 0.002) -> None:
        self.sensor_registry = SensorStateRegistry()
        self.fusion_engine = SensorFusionEngine(self.sensor_registry)
        self.track_manager = TrackManager()
        self.risk_engine = RiskEngine()
        self.incident_engine = IncidentEngine()
        self.alert_engine = AlertEngine()

        self.batch_size = batch_size
        self.flush_interval_sec = flush_interval_sec
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Starts the background worker loop."""
        self.is_running = True
        self._task = asyncio.create_task(self._worker_loop(), name="pipeline_worker_loop")
        logger.info("Pipeline Background Worker initialized with Pure Native Async Execution.")

    async def stop(self) -> None:
        """Gracefully stops background worker operations."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Pipeline Background Worker stopped gracefully.")

    async def _worker_loop(self) -> None:
        """High-Performance Non-Blocking Micro-Batch Consumer Loop."""
        while self.is_running:
            try:
                batch: List[QueueItem] = await global_frame_queue.dequeue_batch(
                    max_batch_size=self.batch_size,
                    timeout=self.flush_interval_sec,
                )

                if not batch:
                    await asyncio.sleep(0.001)
                    continue

                for item in batch:
                    await self._process_single_frame(item)
                    global_frame_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error inside Pipeline Worker execution loop: %s", exc, exc_info=True)
                await asyncio.sleep(0.005)

    async def _process_single_frame(self, item: QueueItem) -> None:
        """Executes full intelligence processing pipeline natively without event loop overhead."""
        dequeued_ts = time.monotonic()
        queue_wait_ms = (dequeued_ts - item.enqueued_ts) * 1000.0

        # 1. SENSOR TELEMETRY REGISTRATION
        t0 = time.monotonic()
        if item.temperature_celsius is not None or item.smoke_ppm is not None:
            self.sensor_registry.update_sensor_reading(
                AuxiliarySensorReading(
                    sensor_id=f"sensor-{item.camera_id}",
                    camera_id=item.camera_id,
                    temperature_celsius=item.temperature_celsius,
                    smoke_ppm=item.smoke_ppm,
                )
            )
        t1 = time.monotonic()

        # 2. CAMERA-ISOLATED TEMPORAL TRACKING
        tracked_objects = await self.track_manager.process_detections(
            camera_id=item.camera_id,
            raw_detections=item.detections,
        )
        t2 = time.monotonic()

        # 3. MULTI-SENSOR FUSION
        fused_tracks = self.fusion_engine.fuse_track_data(
            camera_id=item.camera_id,
            active_tracks=tracked_objects,
        )
        t3 = time.monotonic()

        # 4. SCENE RISK EVALUATION
        scene_risk, evaluated_tracks = self.risk_engine.process_scene_risk(fused_tracks)
        t4 = time.monotonic()

        # 5. INCIDENT LIFECYCLE EVALUATION
        incident_event = await self.incident_engine.process_risk_evaluation(
            camera_id=item.camera_id,
            scene_risk=scene_risk,
            evaluated_tracks=evaluated_tracks,
        )
        t5 = time.monotonic()

        # 6. ALERT DISPATCH
        if incident_event is not None:
            await self.alert_engine.dispatch_incident_alert(incident_event)
        t6 = time.monotonic()

        # COMPUTATION METRICS
        sensor_ms = (t1 - t0) * 1000.0
        tracking_ms = (t2 - t1) * 1000.0
        fusion_ms = (t3 - t2) * 1000.0
        risk_ms = (t4 - t3) * 1000.0
        incident_ms = (t5 - t4) * 1000.0
        alert_ms = (t6 - t5) * 1000.0
        processing_total_ms = (t6 - dequeued_ts) * 1000.0
        total_e2e_ms = (t6 - item.received_ts) * 1000.0

        # RECORD PROMETHEUS METRICS
        MetricsCollector.record_inference(item.camera_id)
        MetricsCollector.set_scene_risk(item.camera_id, getattr(scene_risk, "overall_score", 0.0))
        MetricsCollector.record_pipeline_latency(total_e2e_ms / 1000.0)

        # RECORD TELEMETRY TO GLOBAL PROFILER
        global_profiler.record(
            item.camera_id,
            PipelineMetrics(
                queue_wait_ms=queue_wait_ms,
                sensor_ms=sensor_ms,
                tracking_ms=tracking_ms,
                fusion_ms=fusion_ms,
                risk_ms=risk_ms,
                incident_ms=incident_ms,
                alert_ms=alert_ms,
                total_ms=processing_total_ms,
                e2e_ms=total_e2e_ms,
            ),
        )

        logger.debug(
            "[WORKER_E2E_METRICS] trace_id=%s | cam=%s | frame=%d | queue_wait=%.2fms | "
            "tracking=%.2fms | proc_total=%.2fms | E2E_TOTAL=%.2fms",
            getattr(item, "trace_id", "N/A"),
            item.camera_id,
            item.frame_id,
            queue_wait_ms,
            tracking_ms,
            processing_total_ms,
            total_e2e_ms,
        )


# Singleton Instance tuned for non-blocking high-concurrency stream ingestion
pipeline_worker = PipelineWorker(batch_size=32, flush_interval_sec=0.002)