import logging
import time
from typing import Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FrameProcessor:
    """
    Handles image spatial transformations, resizing, color conversion,
    and normalization required for neural network inference.
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640),
        normalize: bool = True,
    ):
        self.target_size = target_size
        self.normalize = normalize

    def preprocess(
        self, raw_frame: np.ndarray
    ) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """
        Preprocesses a raw OpenCV frame (BGR) into a model-ready blob tensor.

        Returns:
            Tuple[processed_blob, latency_ms, (scale_x, scale_y)]
        """
        t0 = time.perf_counter()

        if raw_frame is None or raw_frame.size == 0:
            raise ValueError("Cannot preprocess an empty or invalid frame.")

        orig_h, orig_w = raw_frame.shape[:2]
        target_w, target_h = self.target_size

        # Calculate scale ratios for bounding box rescaling later
        scale_x = orig_w / float(target_w)
        scale_y = orig_h / float(target_h)

        # Resize image
        resized = cv2.resize(
            raw_frame, self.target_size, interpolation=cv2.INTER_LINEAR
        )

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Convert HWC to CHW (Channel-First layout for ONNX/TensorRT)
        blob = np.transpose(rgb_frame, (2, 0, 1)).astype(np.float32)

        # Normalize pixel values [0, 255] -> [0.0, 1.0]
        if self.normalize:
            blob /= 255.0

        # Add batch dimension: (1, C, H, W)
        blob = np.expand_dims(blob, axis=0)

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return blob, round(latency_ms, 2), (scale_x, scale_y)