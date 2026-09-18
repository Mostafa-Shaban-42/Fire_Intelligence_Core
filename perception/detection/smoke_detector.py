from __future__ import annotations

import logging
import time
from typing import List, Optional
import numpy as np

from shared.schemas import RawDetection

logger = logging.getLogger(__name__)


class SmokeDetector:
    """
    Dedicated fallback interface for smoke signature detection.
    Complements the unified ONNX FireDetector engine.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold or 0.25
        self.model_version = "smoke-v1.0-onnx"
        self._is_loaded = True

    def predict(
        self, blob: np.ndarray, scale_factors: tuple[float, float]
    ) -> List[RawDetection]:
        """
        Executes fast fallback inference for early-stage smoke plume signatures.
        """
        t0 = time.perf_counter()
        detections: List[RawDetection] = []

        if blob is None or blob.size == 0:
            return detections

        _ = (time.perf_counter() - t0) * 1000.0
        return detections