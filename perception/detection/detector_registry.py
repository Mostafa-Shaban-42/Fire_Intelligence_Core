import logging
from typing import Any, Dict, Optional

from perception.detection.fire_detector import FireDetector
from perception.detection.smoke_detector import SmokeDetector

logger = logging.getLogger(__name__)


class DetectorRegistry:
    """
    Central registry pattern to dynamically register, update, and fetch
    active detection model instances at runtime.
    """

    def __init__(self):
        self._detectors: Dict[str, Any] = {}
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Loads core fire and smoke detectors upon startup."""
        self.register("fire", FireDetector())
        self.register("smoke", SmokeDetector())

    def register(self, name: str, detector_instance: Any) -> None:
        """Registers a new model detector instance."""
        self._detectors[name] = detector_instance
        logger.info(f"Detector registered under key: '{name}'")

    def get(self, name: str) -> Optional[Any]:
        """Retrieves a registered detector by key."""
        detector = self._detectors.get(name)
        if not detector:
            logger.error(f"Detector '{name}' not found in registry.")
        return detector

    def list_detectors(self) -> Dict[str, str]:
        """Returns metadata of all registered models."""
        return {
            name: getattr(inst, "model_version", "unknown")
            for name, inst in self._detectors.items()
        }