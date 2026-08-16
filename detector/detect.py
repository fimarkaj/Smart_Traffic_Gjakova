"""
detect.py — YOLOv11 detector using ModelManager for hot-swap support.
"""

import logging
import numpy as np
import torch
from config_loader import cfg
from model_manager import ModelManager

logger = logging.getLogger(__name__)


def _get_optimal_device() -> str:
    """Dynamically determine optimal compute device (CUDA -> MPS -> CPU)."""
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        logger.info(f"Using CUDA GPU device: {device_name}")
        return "0"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        logger.info("Using Apple Silicon MPS device")
        return "mps"
    logger.info("Using CPU device for YOLO inference")
    return "cpu"


class YOLODetector:
    def __init__(self, model_manager: ModelManager):
        self._mgr    = model_manager
        self._cls_id = cfg["model"]["car_class_id"]
        self._conf   = cfg["model"]["confidence"]
        self._device = _get_optimal_device()

    def detect(self, frame: np.ndarray) -> list[dict]:
        try:
            results = self._mgr.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                conf=self._conf,
                classes=[self._cls_id],
                device=self._device,
                verbose=False,
            )
        except Exception as exc:
            logger.error(f"Inference error with device '{self._device}': {exc}")
            return []

        if not results:
            return []

        detections = []
        for r in results:
            if getattr(r, "boxes", None) is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id != self._cls_id:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                names = self._mgr.names
                class_name = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else str(cls_id)
                detections.append({
                    "bbox":       [x1, y1, x2, y2],
                    "confidence": float(box.conf[0]),
                    "class_id":   cls_id,
                    "class_name": class_name,
                    "track_id":   int(box.id[0]) if box.id is not None else None,
                })
        return detections

