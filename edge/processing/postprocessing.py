from typing import Any, Dict, List


class FramePostprocessor:
    """Filters, formats, and standardizes AI inference outputs."""

    def filter_detections(
        self, detections: List[Dict[str, Any]], min_confidence: float = 0.10
    ) -> List[Dict[str, Any]]:
        """Filters out low-confidence detections with maximum responsiveness."""
        return [det for det in detections if det.get("confidence", 0.0) >= min_confidence]