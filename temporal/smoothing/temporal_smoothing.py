import logging
from collections import deque
from typing import Dict

logger = logging.getLogger(__name__)


class TemporalSmoother:
    """
    Applies sliding-window Exponential Moving Average (EMA) and Hysteresis thresholding
    to confidence values across consecutive video frames to prevent alert flickering.
    """

    def __init__(
        self,
        window_size: int = 5,
        ema_alpha: float = 0.4,
        activation_threshold: float = 0.65,
        deactivation_threshold: float = 0.35,
    ):
        self.window_size = window_size
        self.alpha = ema_alpha
        self.activation_threshold = activation_threshold
        self.deactivation_threshold = deactivation_threshold

        self._history: Dict[int, deque] = {}
        self._active_states: Dict[int, bool] = {}

    def update_track_confidence(
        self, track_id: int, raw_confidence: float
    ) -> float:
        """
        Calculates exponentially smoothed confidence for a tracked target ID.
        """
        if track_id not in self._history:
            self._history[track_id] = deque(maxlen=self.window_size)
            self._active_states[track_id] = False

        history = self._history[track_id]
        history.append(raw_confidence)

        # Compute Exponential Moving Average
        smoothed_conf = history[0]
        for conf in list(history)[1:]:
            smoothed_conf = (self.alpha * conf) + (
                (1.0 - self.alpha) * smoothed_conf
            )

        # Apply Hysteresis state transition logic
        current_state = self._active_states[track_id]
        if not current_state and smoothed_conf >= self.activation_threshold:
            self._active_states[track_id] = True
        elif current_state and smoothed_conf < self.deactivation_threshold:
            self._active_states[track_id] = False

        return round(float(smoothed_conf), 4)

    def is_stably_active(self, track_id: int) -> bool:
        """
        Checks if the target has satisfied temporal hysteresis stability requirements.
        """
        return self._active_states.get(track_id, False)

    def cleanup_track(self, track_id: int) -> None:
        """
        Purges memory allocation when a target track is terminated.
        """
        self._history.pop(track_id, None)
        self._active_states.pop(track_id, None)