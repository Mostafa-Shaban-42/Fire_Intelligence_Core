import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from shared.schemas import RawDetection
from temporal.smoothing.confidence_filter import ConfidenceFilter
from temporal.smoothing.temporal_smoothing import TemporalSmoother
from temporal.tracking.bytetrack import ByteTracker, ByteTrackTarget

logger = logging.getLogger(__name__)


@dataclass
class CameraTrackingState:
    """
    Holds completely isolated temporal tracking state for one camera.
    """

    tracker: ByteTracker
    smoother: TemporalSmoother
    track_start_times: Dict[int, float]
    lock: asyncio.Lock
    last_activity: float


class TrackManager:
    """
    Multi-camera tracking coordinator optimized for high concurrency.
    """

    def __init__(self) -> None:
        self.filter = ConfidenceFilter()
        self._camera_states: Dict[str, CameraTrackingState] = {}
        self._registry_lock = asyncio.Lock()

    async def _get_or_create_camera_state(
        self,
        camera_id: str,
    ) -> CameraTrackingState:
        state = self._camera_states.get(camera_id)
        if state is not None:
            return state

        async with self._registry_lock:
            state = self._camera_states.get(camera_id)
            if state is None:
                logger.info(
                    "Creating isolated tracking pipeline for camera=%s",
                    camera_id,
                )
                state = CameraTrackingState(
                    tracker=ByteTracker(),
                    smoother=TemporalSmoother(),
                    track_start_times={},
                    lock=asyncio.Lock(),
                    last_activity=time.monotonic(),
                )
                self._camera_states[camera_id] = state
            return state

    def _sync_process(
        self,
        state: CameraTrackingState,
        raw_detections: List[RawDetection],
    ) -> List[Dict[str, Any]]:
        """
        Executes CPU-bound tracking & filtering computations.
        Offloaded to ThreadPool to prevent blocking FastAPI event loop.
        """
        now_wall = time.time()
        now_monotonic = time.monotonic()
        state.last_activity = now_monotonic

        # 1. NOISE SUPPRESSION
        filtered_detections = self.filter.filter_detections(raw_detections)

        # 2. SPATIAL ASSOCIATION / BYTE TRACKING
        active_targets: List[ByteTrackTarget] = state.tracker.update(
            filtered_detections
        )

        processed_tracks: List[Dict[str, Any]] = []

        # 3. TEMPORAL SMOOTHING + PERSISTENCE
        for target in active_targets:
            track_id = target.track_id

            if track_id not in state.track_start_times:
                state.track_start_times[track_id] = now_wall

            persistence_sec = round(
                now_wall - state.track_start_times[track_id],
                2,
            )

            smoothed_confidence = state.smoother.update_track_confidence(
                track_id=track_id,
                raw_confidence=target.confidence,
            )

            is_stably_active = state.smoother.is_stably_active(track_id)

            processed_tracks.append(
                {
                    "track_id": track_id,
                    "detection_type": target.detection_type,
                    "bbox": target.bbox,
                    "raw_confidence": target.confidence,
                    "smoothed_confidence": smoothed_confidence,
                    "is_stably_active": is_stably_active,
                    "persistence_duration_sec": persistence_sec,
                    "total_hits": target.hits,
                }
            )

        # 4. CLEANUP EXPIRED TRACK STATE
        active_track_ids = {track["track_id"] for track in processed_tracks}
        stale_track_ids = (
            set(state.track_start_times.keys()) - active_track_ids
        )

        for stale_track_id in stale_track_ids:
            state.track_start_times.pop(stale_track_id, None)
            state.smoother.cleanup_track(stale_track_id)

        state.last_activity = time.monotonic()
        return processed_tracks

    async def process_detections(
        self,
        camera_id: str,
        raw_detections: List[RawDetection],
    ) -> List[Dict[str, Any]]:
        state = await self._get_or_create_camera_state(camera_id)

        async with state.lock:
            # Yield CPU execution to thread pool so event loop stays 100% free
            return await asyncio.to_thread(
                self._sync_process, state, raw_detections
            )

    async def cleanup_inactive_cameras(
        self,
        max_idle_seconds: float = 300.0,
    ) -> int:
        now = time.monotonic()
        inactive_camera_ids: List[str] = []

        async with self._registry_lock:
            for camera_id, state in list(self._camera_states.items()):
                idle_duration = now - state.last_activity
                if (
                    idle_duration >= max_idle_seconds
                    and not state.lock.locked()
                ):
                    inactive_camera_ids.append(camera_id)

            for camera_id in inactive_camera_ids:
                self._camera_states.pop(camera_id, None)

        if inactive_camera_ids:
            logger.info(
                "Removed %d inactive camera tracking state(s)",
                len(inactive_camera_ids),
            )

        return len(inactive_camera_ids)

    def get_active_camera_count(self) -> int:
        return len(self._camera_states)

    def has_camera_state(self, camera_id: str) -> bool:
        return camera_id in self._camera_states