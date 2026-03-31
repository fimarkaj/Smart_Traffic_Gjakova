"""
detect.py — YOLOv11 detector using ModelManager for hot-swap support.
"""

import logging
import numpy as np
from config_loader import cfg
from model_manager import ModelManager

logger = logging.getLogger(__name__)


class YOLODetector:
    def __init__(self, model_manager: ModelManager):
        self._mgr    = model_manager
        self._cls_id = cfg["model"]["car_class_id"]
        self._conf   = cfg["model"]["confidence"]

    def detect(self, frame: np.ndarray) -> list[dict]:
        results = self._mgr.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=self._conf,
            classes=[self._cls_id],
            verbose=False,
        )

        detections = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id != self._cls_id:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    "bbox":       [x1, y1, x2, y2],
                    "confidence": float(box.conf[0]),
                    "class_id":   cls_id,
                    "class_name": self._mgr.names[cls_id],
                    "track_id":   int(box.id[0]) if box.id is not None else None,
                })
        return detections
