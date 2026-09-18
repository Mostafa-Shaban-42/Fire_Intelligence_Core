# fusion/fusion_engine.py

import logging
from typing import Any, Dict, List

from fusion.sensor_state import SensorStateRegistry
from shared.enums import DetectionType

logger = logging.getLogger(__name__)


class SensorFusionEngine:
    """
    Stateless multi-sensor fusion engine.

    Combines:

    1. Visual cross-class corroboration.
    2. Auxiliary temperature telemetry.
    3. Auxiliary smoke telemetry.
    """

    def __init__(
        self,
        sensor_registry: SensorStateRegistry,
    ) -> None:
        self.sensor_registry = sensor_registry

    def fuse_track_data(
        self,
        camera_id: str,
        active_tracks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Produces fused track records without mutating the original tracks.
        """

        if not active_tracks:
            return []

        sensor_data = (
            self.sensor_registry.get_sensor_reading(
                camera_id
            )
        )

        detection_types = {
            track["detection_type"]
            for track in active_tracks
        }

        has_dual_visual = (
            DetectionType.FIRE.value
            in detection_types
            and DetectionType.SMOKE.value
            in detection_types
        )

        fused_tracks: List[
            Dict[str, Any]
        ] = []

        for track in active_tracks:

            corroboration_score = 1.0

            corroboration_factors: List[
                str
            ] = []

            # -----------------------------------------------------
            # 1. FIRE + SMOKE VISUAL CORROBORATION
            # -----------------------------------------------------

            if has_dual_visual:

                corroboration_score += 0.20

                corroboration_factors.append(
                    "DUAL_VISUAL_CORROBORATION"
                )

            # -----------------------------------------------------
            # 2. TEMPERATURE CORROBORATION
            # -----------------------------------------------------

            if (
                sensor_data is not None
                and sensor_data.temperature_celsius
                is not None
                and sensor_data.temperature_celsius > 55.0
            ):
                corroboration_score += 0.25

                corroboration_factors.append(
                    "HIGH_TEMPERATURE_TELEMETRY"
                )

            # -----------------------------------------------------
            # 3. SMOKE TELEMETRY CORROBORATION
            # -----------------------------------------------------

            if (
                sensor_data is not None
                and sensor_data.smoke_ppm
                is not None
                and sensor_data.smoke_ppm > 150.0
            ):
                corroboration_score += 0.20

                corroboration_factors.append(
                    "HIGH_SMOKE_PPM_TELEMETRY"
                )

            final_corroboration = min(
                1.50,
                round(corroboration_score, 2),
            )

            fused_track = dict(track)

            fused_track[
                "corroboration_factor"
            ] = final_corroboration

            fused_track[
                "corroboration_evidence"
            ] = corroboration_factors

            fused_tracks.append(
                fused_track
            )

        return fused_tracks