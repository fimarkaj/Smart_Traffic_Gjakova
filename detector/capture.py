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
    if frame is None or getattr(frame, "size", 0) == 0:
        return None
    h_orig, w_orig = frame.shape[:2]
    w, h, x, y = crop_region
    # Safe bounds clamping
    x = max(0, min(int(x), w_orig - 1))
    y = max(0, min(int(y), h_orig - 1))
    w = max(1, min(int(w), w_orig - x))
    h = max(1, min(int(h), h_orig - y))
    return frame[y : y + h, x : x + w]


class FrameCapture:
    def __init__(self, health: HealthMonitor):
        stream_cfg = cfg.get("stream", {})
        self._url         = stream_cfg.get("url", "")
        self._crop        = stream_cfg.get("crop", [800, 600, 0, 250])
        self._reconnect_delay = stream_cfg.get("reconnect_delay", 2)
        self._health      = health
        self._cap         = None
        self._fps         = 25.0
        self._running     = False

    def connect(self) -> bool:
        try:
            self.release()
            self._cap = cv2.VideoCapture(self._url)
            if not self._cap or not self._cap.isOpened():
                raise RuntimeError("VideoCapture.isOpened() returned False")
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            self._fps = fps if (fps and fps > 0 and fps < 120) else 25.0
            self._running = True
            self._health.record_reconnect()
            logger.info(f"Connected to stream FPS={self._fps:.1f}")
            return True
        except Exception as exc:
            self._health.record_failure(str(exc))
            logger.warning(f"Stream connect failed: {exc}")
            self._running = False
            return False

    @property
    def fps(self) -> float:
        return self._fps

    def get_frame(self):
        if not self._running or self._cap is None:
            if not self.connect():
                return None
        try:
            ret, frame = self._cap.read()
            if not ret or frame is None or frame.size == 0:
                self._health.record_failure("Frame read returned False or empty frame")
                self._reconnect()
                return None
            self._health.record_frame()
            return _crop(frame, self._crop)
        except Exception as exc:
            self._health.record_failure(f"Frame capture exception: {exc}")
            self._reconnect()
            return None

    def _reconnect(self):
        self.release()
        time.sleep(self._reconnect_delay)
        self.connect()

    def release(self):
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._running = False

    def __del__(self):
        self.release()


def frame_generator(health: HealthMonitor):
    """Infinite generator yielding (frame, fps) tuples without dying on stream drops."""
    cap = FrameCapture(health)
    cap.connect()
    try:
        while True:
            frame = cap.get_frame()
            if frame is not None:
                yield frame, cap.fps
            else:
                time.sleep(0.2)
    except GeneratorExit:
        pass
    except Exception as exc:
        logger.error(f"Unexpected frame generator error: {exc}")
    finally:
        cap.release()

