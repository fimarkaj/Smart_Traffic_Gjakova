"""
roi.py — ROI loading and occupancy counting.

The CSV 'cropped_points' column uses JSON format: [[x,y],[x,y],...]
Coordinates are relative to the cropped frame.

config.yaml roi.offset_x / offset_y can be used to fine-tune alignment
if the polygon coordinates have a systematic shift vs the actual feed.
"""
import csv
import json
import logging
from pathlib import Path

import cv2
import numpy as np

from config_loader import cfg

logger = logging.getLogger(__name__)


def _parse_points(points_str: str) -> np.ndarray:
    """
    Parse points from the CSV column.
    Supports:
      - JSON array: [[x,y],[x,y], ...]   (primary — rois_polygons.csv)
      - Legacy semicolon: x:y;x:y        (fallback)
    Returns shape (N, 1, 2) float32 for cv2.polylines / pointPolygonTest.
    """
    s = points_str.strip()
    if s.startswith("["):
        parsed = json.loads(s)
        points = []
        for p in parsed:
            if isinstance(p[0], (list, tuple)):
                points.append([int(p[0][0]), int(p[0][1])])
            else:
                points.append([int(p[0]), int(p[1])])
        return np.array(points, dtype=np.float32).reshape((-1, 1, 2))
    else:
        points = []
        for token in s.split(";"):
            token = token.strip()
            if not token:
                continue
            x, y = token.split(":")
            points.append([[int(x), int(y)]])
        return np.array(points, dtype=np.float32)


def _apply_offset(contour: np.ndarray, ox: int, oy: int) -> np.ndarray:
    """Shift all polygon points by (ox, oy)."""
    if ox == 0 and oy == 0:
        return contour
    shifted = contour.copy()
    shifted[:, 0, 0] += ox
    shifted[:, 0, 1] += oy
    return shifted


def load_rois() -> dict[str, np.ndarray]:
    roi_cfg  = cfg["roi"]
    csv_path = Path(roi_cfg["csv_path"])
    col      = roi_cfg["points_column"]
    ox       = int(roi_cfg.get("offset_x", 0))
    oy       = int(roi_cfg.get("offset_y", 0))

    if not csv_path.exists():
        csv_path = Path(__file__).parent / csv_path.name
    if not csv_path.exists():
        raise FileNotFoundError(f"ROI CSV not found: {roi_cfg['csv_path']}")

    rois = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["name"].strip()
            pts  = _parse_points(row[col])
            pts  = _apply_offset(pts, ox, oy)
            rois[name] = pts

    logger.info(f"Loaded {len(rois)} ROIs (offset: x={ox}, y={oy})")
    return rois


def count_occupancy(detections: list[dict], rois: dict[str, np.ndarray]) -> dict[str, int]:
    counts = {name: 0 for name in rois}
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        for name, contour in rois.items():
            if cv2.pointPolygonTest(contour, (cx, cy), False) >= 0:
                counts[name] += 1
    return counts
