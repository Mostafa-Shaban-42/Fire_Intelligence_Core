# risk/risk_engine.py

import logging
from typing import Any, Dict, List, Tuple

from risk.confidence import ConfidenceEvaluator
from risk.severity import SeverityEvaluator
from shared.schemas import RiskFactorBreakdown

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Stateless deterministic risk calculation engine.

    Converts fused temporal tracks into explainable risk scores
    in the range 0.0 to 100.0.
    """

    def __init__(self) -> None:

        self.confidence_evaluator = (
            ConfidenceEvaluator()
        )

        self.severity_evaluator = (
            SeverityEvaluator()
        )

    def evaluate_track_risk(
        self,
        fused_track: Dict[str, Any],
    ) -> Tuple[
        float,
        RiskFactorBreakdown,
    ]:
        """
        Calculates deterministic risk for one fused track.
        """

        bbox = fused_track["bbox"]

        detection_type = (
            fused_track["detection_type"]
        )

        smoothed_confidence = (
            fused_track[
                "smoothed_confidence"
            ]
        )

        persistence_duration_sec = (
            fused_track[
                "persistence_duration_sec"
            ]
        )

        corroboration_factor = (
            fused_track.get(
                "corroboration_factor",
                1.0,
            )
        )

        # ---------------------------------------------------------
        # 1. CONFIDENCE EVALUATION
        # ---------------------------------------------------------

        aggregated_confidence = (
            self.confidence_evaluator.evaluate_confidence(
                smoothed_confidence=(
                    smoothed_confidence
                ),
                persistence_duration_sec=(
                    persistence_duration_sec
                ),
                corroboration_factor=(
                    corroboration_factor
                ),
            )
        )

        # ---------------------------------------------------------
        # 2. SPATIAL SEVERITY
        # ---------------------------------------------------------

        affected_area_ratio = (
            self.severity_evaluator.calculate_area_ratio(
                bbox
            )
        )

        spatial_severity = (
            self.severity_evaluator.evaluate_severity(
                bbox=bbox,
                detection_type=detection_type,
            )
        )

        # ---------------------------------------------------------
        # 3. FINAL RISK SCORE
        # ---------------------------------------------------------

        raw_risk_score = (
            (
                aggregated_confidence * 0.60
                + spatial_severity * 0.40
            )
            * 100.0
        )

        final_risk_score = round(
            min(
                100.0,
                max(
                    0.0,
                    raw_risk_score,
                ),
            ),
            2,
        )

        # ---------------------------------------------------------
        # 4. EXPLAINABILITY BREAKDOWN
        # ---------------------------------------------------------

        breakdown = RiskFactorBreakdown(
            detection_confidence_weight=round(
                smoothed_confidence,
                4,
            ),
            temporal_persistence_weight=round(
                persistence_duration_sec,
                2,
            ),
            affected_area_ratio=(
                affected_area_ratio
            ),
            risk_score=final_risk_score,
        )

        return (
            final_risk_score,
            breakdown,
        )

    def process_scene_risk(
        self,
        fused_tracks: List[
            Dict[str, Any]
        ],
    ) -> Tuple[
        float,
        List[Dict[str, Any]],
    ]:
        """
        Evaluates all active tracks and returns the highest
        scene risk score.
        """

        if not fused_tracks:
            return 0.0, []

        evaluations: List[
            Dict[str, Any]
        ] = []

        max_scene_risk = 0.0

        for track in fused_tracks:

            score, breakdown = (
                self.evaluate_track_risk(
                    track
                )
            )

            evaluation_record = dict(track)

            evaluation_record[
                "risk_score"
            ] = score

            evaluation_record[
                "risk_factors"
            ] = breakdown

            evaluations.append(
                evaluation_record
            )

            max_scene_risk = max(
                max_scene_risk,
                score,
            )

        return (
            max_scene_risk,
            evaluations,
        )