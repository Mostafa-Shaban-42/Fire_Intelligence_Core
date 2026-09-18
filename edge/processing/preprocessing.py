from typing import Tuple
import cv2
import numpy as np


class FramePreprocessor:
    """Prepares and resizes incoming frames before sending to perception models."""

    def __init__(self, target_size: Tuple[int, int] = (640, 640)):
        self.target_size = target_size

    def preprocess(self, raw_frame: np.ndarray) -> np.ndarray:
        """Resizes and normalizes frame matrix."""
        if raw_frame is None or raw_frame.size == 0:
            return raw_frame
        resized = cv2.resize(raw_frame, self.target_size, interpolation=cv2.INTER_LINEAR)
        return resized