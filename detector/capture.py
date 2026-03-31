"""
capture.py — HLS/RTSP frame capture with health reporting.
"""

import cv2
import time
import logging
from config_loader import cfg
from health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


def _crop(frame, crop_region):
    w, h, x, y = crop_region
    return frame[y: y + h, x: x + w]


class FrameCapture:
    def __init__(self, health: HealthMonitor):
        stream_cfg = cfg["stream"]
        self._url         = stream_cfg["url"]
        self._crop        = stream_cfg["crop"]
        self._reconnect_delay = stream_cfg.get("reconnect_delay", 2)
        self._health      = health
        self._cap         = None
        self._fps         = 25.0
        self._running     = False

    def connect(self) -> bool:
        try:
            self._cap = cv2.VideoCapture(self._url)
            if not self._cap.isOpened():
                raise RuntimeError("VideoCapture.isOpened() returned False")
            self._fps     = self._cap.get(cv2.CAP_PROP_FPS) or 25.0
            self._running = True
            self._health.record_reconnect()
            logger.info(f"Connected to stream FPS={self._fps:.1f}")
            return True
        except Exception as exc:
            self._health.record_failure(str(exc))
            logger.error(f"Stream connect failed: {exc}")
            return False

    @property
    def fps(self) -> float:
        return self._fps

    def get_frame(self):
        if not self._running:
            if not self.connect():
                return None
        ret, frame = self._cap.read()
        if not ret:
            self._health.record_failure("Frame read returned False")
            self._reconnect()
            return None
        self._health.record_frame()
        return _crop(frame, self._crop)

    def _reconnect(self):
        self.release()
        time.sleep(self._reconnect_delay)
        self.connect()

    def release(self):
        if self._cap:
            self._cap.release()
            self._cap = None
        self._running = False

    def __del__(self):
        self.release()


def frame_generator(health: HealthMonitor):
    """Infinite generator yielding (frame, fps) tuples."""
    cap = FrameCapture(health)
    if not cap.connect():
        raise RuntimeError("Cannot connect to stream")
    try:
        while True:
            frame = cap.get_frame()
            if frame is not None:
                yield frame, cap.fps
            else:
                time.sleep(0.1)
    except GeneratorExit:
        pass
    finally:
        cap.release()
