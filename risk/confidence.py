import logging

logger = logging.getLogger(__name__)


class ConfidenceEvaluator:
    """
    Evaluates aggregated confidence weight by combining smoothed visual confidence,
    temporal persistence duration, and multi-sensor corroboration.
    """

    def __init__(self, persistence_saturation_sec: float = 10.0):
        self.persistence_saturation_sec = persistence_saturation_sec

    def evaluate_confidence(
        self,
        smoothed_confidence: float,
        persistence_duration_sec: float,
        corroboration_factor: float = 1.0,
    ) -> float:
        """
        Calculates a aggregated confidence factor normalized between [0.0, 1.0].
        """
        # Temporal persistence weight increases up to a defined saturation limit
        persistence_weight = min(
            1.0, persistence_duration_sec / self.persistence_saturation_sec
        )

        # Base confidence combining spatial signal certainty and time persistence
        base_confidence = (smoothed_confidence * 0.70) + (persistence_weight * 0.30)

        # Scale by sensor fusion corroboration factor
        boosted_confidence = base_confidence * corroboration_factor

        return round(min(1.0, boosted_confidence), 4)