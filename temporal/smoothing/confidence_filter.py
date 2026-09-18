import logging
from typing import List
from shared.schemas import RawDetection

logger = logging.getLogger(__name__)


class ConfidenceFilter:
    """
    Filters out transient noise spikes and isolated sub-threshold detections
    before passing signals to the temporal tracking pipeline.
    """

    def __init__(
        self, min_threshold: float = 0.35, high_threshold: float = 0.70
    ):
        self.min_threshold = min_threshold
        self.high_threshold = high_threshold

    def filter_detections(
        self, detections: List[RawDetection]
    ) -> List[RawDetection]:
        """
        Evaluates raw detections against configured safety noise floors.
        """
        valid_detections = [
            d for d in detections if d.confidence >= self.min_threshold
        ]
        return valid_detections