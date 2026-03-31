"""
model_manager.py — Hot-swap YOLO model without restarting the detector.

Usage:
  - Drop a new .pt file into the hot_swap_dir defined in config.yaml
  - ModelManager detects it, loads it, swaps atomically
  - Old model is released
  - A swap event is logged and published to shared state
"""

import logging
import threading
import time
from pathlib import Path
from typing import Optional

from config_loader import cfg

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Wraps the YOLO model and watches hot_swap_dir for new .pt files.
    Thread-safe model access via a read lock.
    """

    POLL_INTERVAL = 5.0   # seconds between directory checks

    def __init__(self):
        model_cfg = cfg["model"]
        self._model_path = Path(model_cfg["path"])
        self._hot_swap_dir = Path(model_cfg["hot_swap_dir"])
        self._hot_swap_dir.mkdir(parents=True, exist_ok=True)

        self._model = None
        self._lock = threading.RLock()
        self._current_path: Optional[Path] = None
        self._swap_count: int = 0
        self._last_swap_ts: Optional[float] = None
        self._watcher_thread: Optional[threading.Thread] = None

        self._load(self._model_path)
        self._start_watcher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def track(self, frame, **kwargs):
        """Run model.track() with current model. Thread-safe."""
        with self._lock:
            return self._model.track(frame, **kwargs)

    @property
    def names(self) -> dict:
        with self._lock:
            return self._model.names

    def get_status(self) -> dict:
        with self._lock:
            return {
                "current_model":  str(self._current_path),
                "swap_count":     self._swap_count,
                "last_swap_ts":   self._last_swap_ts,
            }

    def swap(self, new_path: str) -> bool:
        """
        Explicitly swap to a new model file.
        Returns True on success.
        """
        path = Path(new_path)
        if not path.exists():
            logger.error(f"Model swap failed: file not found: {path}")
            return False
        try:
            self._load(path)
            return True
        except Exception as exc:
            logger.error(f"Model swap failed: {exc}")
            return False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self, path: Path):
        from ultralytics import YOLO
        if not path.exists():
            raise FileNotFoundError(f"YOLO model not found: {path}")

        logger.info(f"Loading model: {path}")
        new_model = YOLO(str(path))

        with self._lock:
            self._model = new_model
            self._current_path = path
            self._swap_count += 1
            self._last_swap_ts = time.time()

        logger.info(f"Model loaded: {path.name} (swap #{self._swap_count})")

    def _start_watcher(self):
        self._watcher_thread = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name="model-watcher"
        )
        self._watcher_thread.start()

    def _watch_loop(self):
        """
        Polls hot_swap_dir for .pt files newer than the current model.
        When found, loads the newest one and deletes it from the swap dir
        (unless it IS the current model path).
        """
        logger.info(f"Model watcher started, watching: {self._hot_swap_dir}")
        while True:
            time.sleep(self.POLL_INTERVAL)
            try:
                pt_files = [
                    f for f in self._hot_swap_dir.glob("*.pt")
                    if f != self._current_path
                ]
                if not pt_files:
                    continue

                # Pick the newest file
                newest = max(pt_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"New model detected: {newest.name} — hot-swapping")
                self._load(newest)

                # Remove other .pt files in swap dir that aren't the main model
                for old in pt_files:
                    if old != self._current_path and old != self._model_path:
                        try:
                            old.unlink()
                            logger.info(f"Removed old swap file: {old.name}")
                        except Exception:
                            pass

            except Exception as exc:
                logger.error(f"Model watcher error: {exc}")
