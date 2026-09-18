from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH_ONNX = PROJECT_ROOT / "models" / "fire_detector.onnx"


class FireDetector:
    def __init__(
        self,
        model_path: Path = MODEL_PATH_ONNX,
        confidence_threshold: float = 0.20,
        iou_threshold: float = 0.40,
        image_size: int = 640,
    ) -> None:
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        self._session: Optional[ort.InferenceSession] = None
        self._input_name: Optional[str] = None
        self._lock = threading.Lock()

    def load(self) -> None:
        with self._lock:
            if self._session is not None:
                return

            if not self.model_path.exists():
                self.model_path = PROJECT_ROOT / "weights" / "best.onnx"

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 2
            opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self._session = ort.InferenceSession(str(self.model_path), sess_options=opts, providers=providers)
            self._input_name = self._session.get_inputs()[0].name

    @property
    def is_loaded(self) -> bool:
        return self._session is not None

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        if frame is None or frame.size == 0:
            return []

        if not self.is_loaded:
            self.load()

        h_orig, w_orig = frame.shape[:2]
        img = cv2.resize(frame, (self.image_size, self.image_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.transpose((2, 0, 1)).astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)

        with self._lock:
            outputs = self._session.run(None, {self._input_name: img})[0]

        predictions = np.squeeze(outputs)
        if predictions.ndim == 2 and predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        boxes, confidences, class_ids = [], [], []
        scale_w, scale_h = w_orig / float(self.image_size), h_orig / float(self.image_size)

        for pred in predictions:
            scores = pred[4:]
            cls_id = int(np.argmax(scores))
            conf = float(scores[cls_id])

            if conf < self.confidence_threshold:
                continue

            cx, cy, bw, bh = pred[:4]
            x1 = int((cx - bw / 2.0) * scale_w)
            y1 = int((cy - bh / 2.0) * scale_h)
            w = int(bw * scale_w)
            h = int(bh * scale_h)

            boxes.append([x1, y1, w, h])
            confidences.append(conf)
            class_ids.append(cls_id)

        results = []
        if boxes:
            indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.iou_threshold)
            if len(indices) > 0:
                for i in indices.flatten():
                    x1, y1, w, h = boxes[i]
                    det_type = "smoke" if class_ids[i] == 1 else "fire"
                    results.append({
                        "detection_type": det_type,
                        "confidence": confidences[i],
                        "bbox": {"x1": max(0, x1), "y1": max(0, y1), "x2": min(w_orig, x1 + w), "y2": min(h_orig, y1 + h)},
                    })

        return results


_default_detector: Optional[FireDetector] = None

def get_fire_detector() -> FireDetector:
    global _default_detector
    if _default_detector is None:
        _default_detector = FireDetector()
    return _default_detector