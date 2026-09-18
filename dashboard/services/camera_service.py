from __future__ import annotations

import logging
import threading
from typing import Optional, Tuple

import cv2
import numpy as np

from dashboard.config import (
    DEFAULT_CAMERA_INDEX,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    DEFAULT_TARGET_FPS,
)


logger = logging.getLogger(__name__)


class CameraService:
    """
    Manages a physical camera device.

    This class isolates OpenCV camera handling from the UI.
    """

    def __init__(
        self,
        camera_index: int = DEFAULT_CAMERA_INDEX,
        width: int = DEFAULT_FRAME_WIDTH,
        height: int = DEFAULT_FRAME_HEIGHT,
        fps: int = DEFAULT_TARGET_FPS,
    ) -> None:

        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps

        self._capture: Optional[
            cv2.VideoCapture
        ] = None

        self._lock = threading.Lock()

    def start(self) -> bool:
        """
        Opens the camera.
        """

        with self._lock:

            if (
                self._capture is not None
                and self._capture.isOpened()
            ):
                return True

            logger.info(
                "Opening camera index=%s",
                self.camera_index,
            )

            capture = cv2.VideoCapture(
                self.camera_index
            )

            capture.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                self.width,
            )

            capture.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                self.height,
            )

            capture.set(
                cv2.CAP_PROP_FPS,
                self.fps,
            )

            if not capture.isOpened():

                logger.error(
                    "Unable to open camera index=%s",
                    self.camera_index,
                )

                capture.release()

                return False

            self._capture = capture

            return True

    def stop(self) -> None:
        """
        Releases the camera.
        """

        with self._lock:

            if self._capture is not None:

                logger.info(
                    "Releasing camera index=%s",
                    self.camera_index,
                )

                self._capture.release()

                self._capture = None

    def is_running(self) -> bool:

        return bool(
            self._capture is not None
            and self._capture.isOpened()
        )

    def read_frame(
        self,
    ) -> Tuple[
        bool,
        Optional[np.ndarray],
    ]:
        """
        Reads one frame from the camera.
        """

        with self._lock:

            if not self.is_running():

                return False, None

            success, frame = (
                self._capture.read()
            )

            if not success:

                logger.warning(
                    "Failed to read frame."
                )

                return False, None

            return True, frame

    def get_resolution(
        self,
    ) -> Tuple[int, int]:

        if not self.is_running():

            return 0, 0

        width = int(
            self._capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            self._capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        return width, height

    def __del__(self) -> None:

        try:
            self.stop()

        except Exception:
            pass