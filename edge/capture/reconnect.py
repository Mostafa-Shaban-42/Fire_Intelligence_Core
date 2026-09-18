import logging
import time

logger = logging.getLogger(__name__)


class ExponentialBackoffReconnect:
    """Strategy for managing connection retry logic with exponential backoff."""

    def __init__(self, initial_delay: float = 1.0, max_delay: float = 30.0, backoff_factor: float = 2.0):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.current_delay = initial_delay
        self.attempts = 0

    def wait(self) -> None:
        """Sleeps for current delay interval and increases next delay exponentially."""
        logger.warning(
            f"Reconnect attempt #{self.attempts + 1}. Waiting {self.current_delay:.2f} seconds..."
        )
        time.sleep(self.current_delay)
        self.attempts += 1
        self.current_delay = min(self.max_delay, self.current_delay * self.backoff_factor)

    def reset(self) -> None:
        """Resets backoff counters upon successful connection."""
        self.current_delay = self.initial_delay
        self.attempts = 0