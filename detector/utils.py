"""
utils.py — Drawing helpers and traffic status logic.
"""
import cv2
import numpy as np
from config_loader import cfg


def get_traffic_status(car_count: int) -> tuple[str, str]:
    t = cfg["thresholds"]
    if car_count <= t["green"]:
        return "GREEN", "Low"
    elif car_count <= t["yellow"]:
        return "YELLOW", "Moderate"
    return "RED", "Heavy"


def status_emoji(color: str) -> str:
    return {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(color, "⚪")


def draw_detections(frame: np.ndarray, detections: list):
    """Draw bounding boxes only — no ID or confidence label."""
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        # Clean white box, no text
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)


def draw_rois(frame: np.ndarray, rois: dict, roi_counts: dict):
    """Draw ROI polygons in white with a minimal zone name + count label."""
    WHITE = (255, 255, 255)
    for name, contour in rois.items():
        pts = contour.astype(int).reshape((-1, 1, 2))

        # White outline, always
        cv2.polylines(frame, [pts], True, WHITE, 1, cv2.LINE_AA)

        # Label at centroid — small, dark background for readability
        count = roi_counts.get(name, 0)
        cx = int(pts[:, 0, 0].mean())
        cy = int(pts[:, 0, 1].mean())

        label = f"{name}: {count}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)
        # Dark backing rect
        cv2.rectangle(frame,
                      (cx - 2, cy - th - 4),
                      (cx + tw + 2, cy + 2),
                      (0, 0, 0), -1)
        cv2.putText(frame, label, (cx, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, WHITE, 1, cv2.LINE_AA)


def draw_status_overlay(frame: np.ndarray, roi_counts: dict):
    """Intentionally empty — total cars removed from feed overlay."""
    pass


def encode_frame(frame: np.ndarray, quality: int = 85) -> bytes | None:
    ret, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes() if ret else None
