"""
shared_state.py — In-memory live state shared between detector and API.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from config_loader import cfg


@dataclass
class LiveFrame:
    jpeg_bytes:          bytes
    timestamp:           float
    roi_counts:          dict[str, int]
    crossing_totals:     dict[str, int]
    new_crossings:       dict[str, int]
    overall_crossings:   int
    unique_crossers:     int    # distinct IDs that crossed any line
    estimated_vehicles:  int    # unique_crossers // 2  ← the accurate vehicle count
    global_unique:       int    # all distinct IDs seen anywhere
    total_cars:          int
    camera_health:       dict


class SharedState:
    def __init__(self):
        self._lock        = threading.Lock()
        self._latest: Optional[LiveFrame] = None
        self._max_history = cfg["dashboard"]["history_max_points"]
        self._history: dict[str, deque] = {}
        self.alert_last_fired: dict[str, float] = {}

    def update(self, frame: LiveFrame):
        with self._lock:
            self._latest = frame
            for name, count in frame.roi_counts.items():
                if name not in self._history:
                    self._history[name] = deque(maxlen=self._max_history)
                self._history[name].append((frame.timestamp, count))

    def get_latest(self) -> Optional[LiveFrame]:
        with self._lock:
            return self._latest

    def get_history(self) -> dict[str, list]:
        with self._lock:
            return {name: list(dq) for name, dq in self._history.items()}

    def is_alive(self) -> bool:
        with self._lock:
            if self._latest is None:
                return False
            return time.time() - self._latest.timestamp < 10.0


state = SharedState()
