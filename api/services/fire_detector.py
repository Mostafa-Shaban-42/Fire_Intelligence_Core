from __future__ import annotations
import logging, threading, os, queue, time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CUSTOM_WEIGHTS_PATH = PROJECT_ROOT / "weights" / "best.pt"

class FireDetector:
    def __init__(self, confidence_threshold=0.25, iou_threshold=0.45):
        self.model_path = CUSTOM_WEIGHTS_PATH if os.path.exists(CUSTOM_WEIGHTS_PATH) else Path("models/fire_detector.pt")
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self._model = None
        self._lock = threading.Lock()
        self.latest_raw_boxes = []
        self.frame_queue = queue.Queue(maxsize=1)
        self.is_running = False
        self.worker_thread = None
        self.processed_frames_count = 0

    def load(self) -> bool:
        with self._lock:
            if self._model is not None:
                return True
            try:
                self._model = YOLO(str(self.model_path), task="detect")
                dummy = np.zeros((640, 640, 3), dtype=np.uint8)
                self._model.predict(dummy, imgsz=640, verbose=False)
                self.start_worker()
                return True
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                return False

    def is_ready(self) -> bool:
        return self._model is not None or self.load()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def start_worker(self):
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()

    def _process_queue(self):
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=0.03)
                if frame is None:
                    continue
                
                results = self._model.predict(
                    source=frame,
                    conf=self.confidence_threshold,
                    iou=self.iou_threshold,
                    imgsz=640,
                    verbose=False
                )

                dets = []
                if results and len(results) > 0:
                    for box in results[0].boxes:
                        c = float(box.conf.item())
                        cls_id = int(box.cls.item())
                        # Normalized Bounding Box coordinates (0.0 to 1.0)
                        xyxy_norm = box.xyxyn[0].tolist()
                        cls_name = results[0].names.get(cls_id, "fire")
                        dets.append({
                            "norm_box": xyxy_norm,
                            "confidence": c,
                            "class_name": cls_name
                        })
                self.latest_raw_boxes = dets
                self.processed_frames_count += 1
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")

    def detect_and_draw(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        if frame is None or frame.size == 0:
            return frame, []
            
        if self._model is None:
            self.load()

        h, w = frame.shape[:2]

        if self.frame_queue.empty():
            try:
                self.frame_queue.put_nowait(frame.copy())
            except queue.Full:
                pass

        annotated_frame = frame.copy()
        current_dets = []
        raw_boxes = list(self.latest_raw_boxes)

        for item in raw_boxes:
            nx1, ny1, nx2, ny2 = item["norm_box"]
            # Scale coordinates back to original frame size
            x1, y1 = int(nx1 * w), int(ny1 * h)
            x2, y2 = int(nx2 * w), int(ny2 * h)
            c = item["confidence"]
            label = item["class_name"]

            color = (0, 0, 255) if "fire" in label.lower() else (255, 165, 0)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)

            text = f"{label.upper()} {c*100:.1f}%"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_frame, (x1, max(y1 - 25, 0)), (x1 + tw, max(y1, 25)), color, -1)
            cv2.putText(annotated_frame, text, (x1, max(y1 - 5, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            current_dets.append({
                "detection_type": label.lower(),
                "confidence": c,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            })

        return annotated_frame, current_dets

_detector_instance = None
def get_fire_detector():
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FireDetector()
    return _detector_instance
