"""
health_monitor.py — Tracks stream health and publishes status.
"""
import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CameraHealth:
    camera_id: str
    status: str = "unknown"          # "ok" | "degraded" | "down"
    last_frame_ts: float = 0.0
    fps_actual: float = 0.0
    reconnect_count: int = 0
    consecutive_failures: int = 0
    uptime_seconds: float = 0.0
    started_at: float = field(default_factory=time.time)
    last_error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "camera_id":           self.camera_id,
            "status":              self.status,
            "last_frame_ts":       self.last_frame_ts,
            "last_frame_age_s":    round(time.time() - self.last_frame_ts, 1) if self.last_frame_ts else None,
            "fps_actual":          round(self.fps_actual, 1),
            "reconnect_count":     self.reconnect_count,
            "consecutive_failures": self.consecutive_failures,
            "uptime_seconds":      round(time.time() - self.started_at, 0),
            "last_error":          self.last_error,
        }


class HealthMonitor:
    """
    Tracks per-frame timing to compute actual FPS and stream health.
    Thread-safe — read from API thread, written by detector thread.
    """

    DEGRADED_AFTER_SECONDS = 5.0
    DOWN_AFTER_SECONDS = 15.0

    def __init__(self, camera_id: str = "main"):
        self._health = CameraHealth(camera_id=camera_id)
        self._lock = threading.Lock()
        self._frame_times: list[float] = []
        self._fps_window = 30       # compute FPS over last N frames

    def record_frame(self):
        now = time.time()
        with self._lock:
            self._health.last_frame_ts = now
            self._health.consecutive_failures = 0
            self._health.status = "ok"

            self._frame_times.append(now)
            if len(self._frame_times) > self._fps_window:
                self._frame_times.pop(0)
            if len(self._frame_times) >= 2:
                elapsed = self._frame_times[-1] - self._frame_times[0]
                if elapsed > 0:
                    self._health.fps_actual = (len(self._frame_times) - 1) / elapsed

    def record_failure(self, error: str = None):
        with self._lock:
            self._health.consecutive_failures += 1
            self._health.last_error = error
            self._frame_times.clear()
            self._health.fps_actual = 0.0
            logger.warning(f"Stream failure #{self._health.consecutive_failures}: {error}")

    def record_reconnect(self):
        with self._lock:
            self._health.reconnect_count += 1
            logger.info(f"Stream reconnected (total reconnects: {self._health.reconnect_count})")

    def tick(self):
        """Call periodically to update status based on time since last frame."""
        now = time.time()
        with self._lock:
            if self._health.last_frame_ts == 0:
                return
            age = now - self._health.last_frame_ts
            if age > self.DOWN_AFTER_SECONDS:
                self._health.status = "down"
            elif age > self.DEGRADED_AFTER_SECONDS:
                self._health.status = "degraded"
            else:
                self._health.status = "ok"

    def get_health(self) -> dict:
        self.tick()
        with self._lock:
            return self._health.to_dict()

    def is_healthy(self) -> bool:
        self.tick()
        with self._lock:
            return self._health.status == "ok"
