import logging
from typing import List, Tuple
import numpy as np

from shared.schemas import BoundingBox, RawDetection

logger = logging.getLogger(__name__)


def calculate_iou(boxA: BoundingBox, boxB: BoundingBox) -> float:
    """
    Computes Exact Intersection over Union (IoU) ratio between two bounding boxes.
    """
    xA = max(boxA.xmin, boxB.xmin)
    yA = max(boxA.ymin, boxB.ymin)
    xB = min(boxA.xmax, boxB.xmax)
    yB = min(boxA.ymax, boxB.ymax)

    inter_area = max(0.0, xB - xA) * max(0.0, yB - yA)
    if inter_area == 0.0:
        return 0.0

    boxA_area = (boxA.xmax - boxA.xmin) * (boxA.ymax - boxA.ymin)
    boxB_area = (boxB.xmax - boxB.xmin) * (boxB.ymax - boxB.ymin)

    union_area = boxA_area + boxB_area - inter_area
    if union_area <= 0.0:
        return 0.0

    return inter_area / union_area


class ByteTrackTarget:
    """
    State container for a temporal persistent object track.
    """

    def __init__(
        self,
        track_id: int,
        bbox: BoundingBox,
        confidence: float,
        detection_type: str,
    ):
        self.track_id = track_id
        self.bbox = bbox
        self.confidence = confidence
        self.detection_type = detection_type
        self.hits = 1
        self.time_since_update = 0

    def update(self, bbox: BoundingBox, confidence: float) -> None:
        self.bbox = bbox
        self.confidence = confidence
        self.hits += 1
        self.time_since_update = 0


class ByteTracker:
    """
    Deterministic implementation of ByteTrack bounding-box data association.
    Uses two-stage greedy IoU matching for high and low confidence detection pools.
    """

    def __init__(
        self,
        high_thresh: float = 0.50,
        low_thresh: float = 0.20,
        match_iou_thresh: float = 0.25,
        max_lost_frames: int = 15,
    ):
        self.high_thresh = high_thresh
        self.low_thresh = low_thresh
        self.match_iou_thresh = match_iou_thresh
        self.max_lost_frames = max_lost_frames
        self._next_id = 1
        self.tracked_targets: List[ByteTrackTarget] = []

    def update(self, detections: List[RawDetection]) -> List[ByteTrackTarget]:
        """
        Updates tracked targets using two-stage IoU association.
        """
        for target in self.tracked_targets:
            target.time_since_update += 1

        # Partition detections into high and low confidence pools
        high_dets = [d for d in detections if d.confidence >= self.high_thresh]
        low_dets = [
            d
            for d in detections
            if self.low_thresh <= d.confidence < self.high_thresh
        ]

        # Stage 1: Associate high-confidence detections with existing tracks
        unmatched_tracks, unmatched_high_dets = self._associate(
            self.tracked_targets, high_dets
        )

        # Stage 2: Associate remaining unmatched tracks with low-confidence detections
        remaining_tracks = [self.tracked_targets[i] for i in unmatched_tracks]
        unmatched_low_tracks, _ = self._associate(
            remaining_tracks, low_dets, is_second_stage=True
        )

        # Initialize new tracks for unassociated high-confidence detections
        for det_idx in unmatched_high_dets:
            det = high_dets[det_idx]
            new_target = ByteTrackTarget(
                track_id=self._next_id,
                bbox=det.bbox,
                confidence=det.confidence,
                detection_type=det.detection_type.value,
            )
            self._next_id += 1
            self.tracked_targets.append(new_target)

        # Evict stale tracks
        self.tracked_targets = [
            t
            for t in self.tracked_targets
            if t.time_since_update <= self.max_lost_frames
        ]

        return [t for t in self.tracked_targets if t.time_since_update == 0]

    def _associate(
        self,
        targets: List[ByteTrackTarget],
        detections: List[RawDetection],
        is_second_stage: bool = False,
    ) -> Tuple[List[int], List[int]]:
        """
        Bipartite matching via greedy IoU evaluation.
        """
        if not targets or not detections:
            return list(range(len(targets))), list(range(len(detections)))

        iou_matrix = np.zeros((len(targets), len(detections)), dtype=np.float32)
        for t_idx, target in enumerate(targets):
            for d_idx, det in enumerate(detections):
                iou_matrix[t_idx, d_idx] = calculate_iou(target.bbox, det.bbox)

        unmatched_targets = set(range(len(targets)))
        unmatched_detections = set(range(len(detections)))

        while True:
            if len(unmatched_targets) == 0 or len(unmatched_detections) == 0:
                break

            max_iou = 0.0
            best_t, best_d = -1, -1

            for t_idx in unmatched_targets:
                for d_idx in unmatched_detections:
                    if iou_matrix[t_idx, d_idx] > max_iou:
                        max_iou = float(iou_matrix[t_idx, d_idx])
                        best_t, best_d = t_idx, d_idx

            if max_iou < self.match_iou_thresh:
                break

            targets[best_t].update(
                detections[best_d].bbox, detections[best_d].confidence
            )
            unmatched_targets.remove(best_t)
            unmatched_detections.remove(best_d)

        return list(unmatched_targets), list(unmatched_detections)