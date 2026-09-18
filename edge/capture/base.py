from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class BaseFrameCapture(ABC):
    """Abstract Base Class for all video frame acquisition drivers."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the video source."""
        pass

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], float]:
        """
        Reads next frame from stream.
        Returns: (success_bool, frame_ndarray_or_none, latency_ms)
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """Release underlying system resources."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if source stream is active."""
        pass