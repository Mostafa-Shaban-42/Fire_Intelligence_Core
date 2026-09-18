import logging
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from edge.capture.base import BaseFrameCapture

logger = logging.getLogger(__name__)


class USBCapture(BaseFrameCapture):
    """USB/Local Webcam Capture Driver."""

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self._cap: Optional[cv2.VideoCapture] = None

    def connect(self) -> bool:
        self.release()
        try:
            self._cap = cv2.VideoCapture(self.device_index)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return self._cap.isOpened()
        except Exception as e:
            logger.error(f"Failed to connect to USB Camera index {self.device_index}: {e}")
            return False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], float]:
        if self._cap is None or not self._cap.isOpened():
            return False, None, 0.0

        t_start = time.time()
        ret, frame = self._cap.read()
        latency = (time.time() - t_start) * 1000.0

        if not ret or frame is None:
            return False, None, latency

        return True, frame, latency

    def release(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception as e:
                logger.error(f"Error releasing USB VideoCapture: {e}")
            self._cap = None

    def is_connected(self) -> bool:
        return self._cap is not None and self._cap.isOpened()