from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CUSTOM_WEIGHTS_PATH = PROJECT_ROOT / "weights" / "best.onnx"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "fire_detector.onnx"

# ألوان BGR معتمدة وخفيفة
COLOR_FIRE_BGR = (0, 0, 255)      # أحمر ناصع للنار
COLOR_SMOKE_BGR = (128, 128, 128) # رصاصي للدخان


class FireDetector:
    def __init__(
        self,
        confidence_threshold: float = 0.08,  # خفض العتبة لزيادة الاكتشاف
        iou_threshold: float = 0.45,
        target_imgsz: int = 640,
    ):
        self.model_path = CUSTOM_WEIGHTS_PATH if os.path.exists(CUSTOM_WEIGHTS_PATH) else DEFAULT_MODEL_PATH
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.target_imgsz = target_imgsz

        self._session: Optional[ort.InferenceSession] = None
        self._input_name: Optional[str] = None
        self._lock = threading.Lock()

    def load(self) -> bool:
        with self._lock:
            if self._session is not None:
                return True
            try:
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 4
                opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                self._session = ort.InferenceSession(str(self.model_path), sess_options=opts, providers=providers)
                self._input_name = self._session.get_inputs()[0].name
                return True
            except Exception as e:
                logger.error(f"Failed to load ONNX session: {e}")
                return False

    def is_ready(self) -> bool:
        return self._session is not None or self.load()

    def process_frame_sync(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        if frame is None or frame.size == 0 or not self.is_ready():
            return []

        orig_h, orig_w = frame.shape[:2]
        img = cv2.resize(frame, (self.target_imgsz, self.target_imgsz))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.transpose((2, 0, 1)).astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)

        with self._lock:
            outputs = self._session.run(None, {self._input_name: img})[0]

        predictions = np.squeeze(outputs)
        if predictions.ndim == 2 and predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        boxes, confidences, class_ids = [], [], []
        scale_w, scale_h = orig_w / float(self.target_imgsz), orig_h / float(self.target_imgsz)

        for pred in predictions:
            scores = pred[4:]
            cls_id = int(np.argmax(scores))
            c = float(scores[cls_id])

            if c < self.confidence_threshold:
                continue

            cx, cy, bw, bh = pred[:4]
            x1 = int((cx - bw / 2.0) * scale_w)
            y1 = int((cy - bh / 2.0) * scale_h)
            w = int(bw * scale_w)
            h = int(bh * scale_h)

            boxes.append([x1, y1, w, h])
            confidences.append(c)
            class_ids.append(cls_id)

        dets: List[Dict[str, Any]] = []
        if boxes:
            indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.iou_threshold)
            if len(indices) > 0:
                for i in indices.flatten():
                    x1, y1, w, h = boxes[i]
                    raw_cls = class_ids[i]
                    det_type = "smoke" if raw_cls == 0 else "fire"

                    dets.append({
                        "detection_type": det_type,
                        "confidence": confidences[i],
                        "bbox": {
                            "x1": max(0, min(orig_w, x1)),
                            "y1": max(0, min(orig_h, y1)),
                            "x2": max(0, min(orig_w, x1 + w)),
                            "y2": max(0, min(orig_h, y1 + h)),
                        },
                    })
        return dets

    def annotate_frame_in_place(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> None:
        """
        رسم المربعات الحدودية والنصوص فقط بأعلى سرعة وبدون تظليل.
        """
        if not detections:
            return

        orig_h, orig_w = frame.shape[:2]

        for det in detections:
            bbox = det.get("bbox", {})
            x1 = max(0, min(orig_w, int(bbox.get("x1", 0))))
            y1 = max(0, min(orig_h, int(bbox.get("y1", 0))))
            x2 = max(0, min(orig_w, int(bbox.get("x2", 0))))
            y2 = max(0, min(orig_h, int(bbox.get("y2", 0))))

            if x2 <= x1 or y2 <= y1:
                continue

            det_type = det.get("detection_type", "fire").lower()
            conf = det.get("confidence", 0.0)

            # تحديد اللون بناءً على النوع
            color = COLOR_FIRE_BGR if det_type == "fire" else COLOR_SMOKE_BGR

            # 1. رسم المربع المحيط فقط
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

            # 2. رسم بطاقة اسم الفئة والنسبة
            label = f" {det_type.upper()}: {conf:.2f} "
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)

            cv2.rectangle(frame, (x1, max(y1 - 20, 0)), (x1 + tw + 4, max(y1, 20)), color, -1)
            cv2.putText(
                frame,
                label,
                (x1 + 2, max(y1 - 5, 14)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )


_detector_instance: Optional[FireDetector] = None

def get_fire_detector() -> FireDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FireDetector()
    return _detector_instance