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

from config_loader import cfg, resolve_path

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Wraps the YOLO model and watches hot_swap_dir for new .pt files.
    Thread-safe model access via a read lock.
    """

    POLL_INTERVAL = 5.0   # seconds between directory checks

    def __init__(self):
        model_cfg = cfg["model"]
        self._model_path = resolve_path(model_cfg["path"])
        self._hot_swap_dir = resolve_path(model_cfg["hot_swap_dir"])
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
            if self._model is None:
                return []
            return self._model.track(frame, **kwargs)

    @property
    def names(self) -> dict:
        with self._lock:
            if self._model is not None and hasattr(self._model, "names"):
                return self._model.names
            return {0: "car", 1: "vehicle"}

    def get_status(self) -> dict:
        with self._lock:
            return {
                "current_model":  str(self._current_path) if self._current_path else None,
                "model_loaded":   self._model is not None,
                "swap_count":     self._swap_count,
                "last_swap_ts":   self._last_swap_ts,
            }

    def swap(self, new_path: str) -> bool:
        """
        Explicitly swap to a new model file.
        Returns True on success.
        """
        path = resolve_path(new_path)
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

        target_path = path
        if not target_path.exists():
            # Check for any other .pt in hot_swap_dir or models/
            available_pts = list(self._hot_swap_dir.glob("*.pt"))
            if available_pts:
                target_path = available_pts[0]
                logger.warning(
                    f"Configured model '{path}' not found. Using available weights: '{target_path.name}'"
                )
            else:
                # Attempt standard YOLO fallback (auto-download nano weights if online)
                fallback_name = "yolo11n.pt"
                logger.warning(
                    f"Model '{path}' not found! Attempting fallback to standard '{fallback_name}'."
                )
                try:
                    new_model = YOLO(fallback_name)
                    with self._lock:
                        self._model = new_model
                        self._current_path = Path(fallback_name)
                        self._swap_count += 1
                        self._last_swap_ts = time.time()
                    logger.info(f"Fallback model '{fallback_name}' loaded successfully.")
                    return
                except Exception as fb_exc:
                    logger.warning(
                        f"Could not load fallback weights '{fallback_name}': {fb_exc}. "
                        f"Detector running in standby mode until a model is placed in '{self._hot_swap_dir}'."
                    )
                    with self._lock:
                        self._model = None
                        self._current_path = None
                    return

        try:
            logger.info(f"Loading YOLO model: {target_path}")
            new_model = YOLO(str(target_path))

            with self._lock:
                self._model = new_model
                self._current_path = target_path
                self._swap_count += 1
                self._last_swap_ts = time.time()

            logger.info(f"Model loaded: {target_path.name} (swap #{self._swap_count})")
        except Exception as exc:
            logger.error(f"Failed to load YOLO model '{target_path}': {exc}")
            with self._lock:
                self._model = None
                self._current_path = None

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
                    if self._current_path is None or f != self._current_path
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

