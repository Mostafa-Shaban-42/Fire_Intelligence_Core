import logging
from shared.enums import DetectionType
from shared.schemas import BoundingBox

logger = logging.getLogger(__name__)


class SeverityEvaluator:
    """
    Calculates physical hazard severity based on target surface area ratio
    relative to frame boundaries and threat type severity class.
    """

    def __init__(
        self,
        reference_frame_width: float = 1920.0,
        reference_frame_height: float = 1080.0,
    ):
        self.frame_area = reference_frame_width * reference_frame_height

    def calculate_area_ratio(self, bbox: BoundingBox) -> float:
        """Calculates bounding box area ratio relative to full camera frame resolution."""
        box_width = max(0.0, bbox.xmax - bbox.xmin)
        box_height = max(0.0, bbox.ymax - bbox.ymin)
        box_area = box_width * box_height

        return round(min(1.0, box_area / self.frame_area), 4)

    def evaluate_severity(
        self, bbox: BoundingBox, detection_type: str
    ) -> float:
        """
        Calculates spatial hazard severity score normalized between [0.0, 1.0].
        """
        area_ratio = self.calculate_area_ratio(bbox)

        # Base hazard severity multiplier based on detection class
        type_multiplier = 1.0 if detection_type == DetectionType.FIRE.value else 0.75

        # Non-linear area scaling (larger area coverage indicates exponential fire growth)
        spatial_severity = min(1.0, (area_ratio * 10.0) ** 0.5) * type_multiplier

        return round(float(spatial_severity), 4)