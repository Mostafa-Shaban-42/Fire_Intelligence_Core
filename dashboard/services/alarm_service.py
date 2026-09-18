from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from dashboard.config import (
    ALARM_COOLDOWN_SECONDS,
    ALARM_SOUND_PATH,
)


logger = logging.getLogger(__name__)


class AlarmService:
    """
    Controls local dashboard alarm behavior.

    The alarm runs asynchronously in a background thread
    so it does not block Streamlit rendering.
    """

    def __init__(
        self,
        sound_path: Path = ALARM_SOUND_PATH,
        cooldown_seconds: float = (
            ALARM_COOLDOWN_SECONDS
        ),
    ) -> None:

        self.sound_path = sound_path
        self.cooldown_seconds = (
            cooldown_seconds
        )

        self._last_alarm_time = 0.0

        self._lock = threading.Lock()

    def trigger(self) -> bool:
        """
        Triggers the alarm if cooldown allows.

        Returns True if an alarm was started.
        """

        with self._lock:

            now = time.monotonic()

            if (
                now
                - self._last_alarm_time
                < self.cooldown_seconds
            ):

                return False

            self._last_alarm_time = now

        thread = threading.Thread(
            target=self._play_alarm,
            daemon=True,
        )

        thread.start()

        return True

    def _play_alarm(self) -> None:
        """
        Plays alarm sound.

        Falls back to Windows system beep when
        alarm.wav is unavailable.
        """

        try:

            import winsound

            if self.sound_path.exists():

                winsound.PlaySound(
                    str(self.sound_path),
                    winsound.SND_FILENAME,
                )

            else:

                winsound.Beep(
                    1200,
                    700,
                )

        except Exception as exception:

            logger.warning(
                "Alarm playback failed: %s",
                exception,
            )


_default_alarm_service: AlarmService | None = None


def get_alarm_service() -> AlarmService:

    global _default_alarm_service

    if _default_alarm_service is None:

        _default_alarm_service = (
            AlarmService()
        )

    return _default_alarm_service