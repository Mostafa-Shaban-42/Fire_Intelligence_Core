import logging
import time
from typing import Optional, Tuple, Union
import cv2
import numpy as np

from edge.capture.base import BaseFrameCapture

logger = logging.getLogger(__name__)


class RTSPCapture(BaseFrameCapture):
    """RTSP Stream Capture Driver with connection handling."""

    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self._cap: Optional[cv2.VideoCapture] = None

    def connect(self) -> bool:
        self.release()
        try:
            self._cap = cv2.VideoCapture(self.rtsp_url)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if self._cap.isOpened():
                ret, _ = self._cap.read()
                return ret
        except Exception as e:
            logger.error(f"Failed to connect to RTSP URL {self.rtsp_url}: {e}")
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
                logger.error(f"Error releasing RTSP VideoCapture: {e}")
            self._cap = None

    def is_connected(self) -> bool:
        return self._cap is not None and self._cap.isOpened()