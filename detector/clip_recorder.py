"""
clip_recorder.py — Circular buffer that saves incident clips automatically.

How it works:
  - Every frame is pushed into a circular buffer (ring buffer of JPEG bytes).
  - When a trigger condition is met (high occupancy, spike in crossings),
    saveClip() is called.
  - It waits post_event_seconds more frames, then writes:
      pre_event + post_event frames → MP4 file
  - Clips are named by timestamp and trigger reason.
  - Old clips are pruned to keep disk usage bounded.
"""

import cv2
import logging
import os
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

from config_loader import cfg, resolve_path

logger = logging.getLogger(__name__)


class ClipRecorder:
    def __init__(self):
        clip_cfg = cfg.get("clips", {})
        self._output_dir = resolve_path(clip_cfg.get("output_dir", "data/clips"))
        self._output_dir.mkdir(parents=True, exist_ok=True)


        # Assume 25fps for buffer sizing; updated when first frame arrives
        self._fps = 25.0
        self._pre_seconds  = clip_cfg["pre_event_seconds"]
        self._post_seconds = clip_cfg["post_event_seconds"]
        self._max_clips    = 100    # prune oldest when exceeded

        # Circular buffer: deque of (timestamp, jpeg_bytes)
        self._buffer: deque = deque()
        self._lock = threading.Lock()

        # Clip saving state
        self._saving = False
        self._post_frames_remaining = 0
        self._clip_frames: list = []
        self._clip_reason: str = ""
        self._clip_start_ts: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push_frame(self, frame, fps: float = 25.0):
        """Push a raw BGR frame into the circular buffer."""
        self._fps = fps
        max_pre_frames = int(self._pre_seconds * fps)

        ret, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            return

        now = time.time()
        with self._lock:
            self._buffer.append((now, buf.tobytes()))
            # Keep only the last pre_event_seconds worth of frames
            while len(self._buffer) > max_pre_frames:
                self._buffer.popleft()

            # If currently recording post-event frames
            if self._saving:
                self._clip_frames.append((now, buf.tobytes()))
                self._post_frames_remaining -= 1
                if self._post_frames_remaining <= 0:
                    self._saving = False
                    frames_snapshot = list(self._clip_frames)
                    reason = self._clip_reason
                    start_ts = self._clip_start_ts
                    self._clip_frames = []
                    # Write in background thread so detector isn't blocked
                    t = threading.Thread(
                        target=self._write_clip,
                        args=(frames_snapshot, reason, start_ts),
                        daemon=True
                    )
                    t.start()

    def trigger(self, reason: str = "manual"):
        """
        Trigger a clip save.
        Captures everything in the pre-event buffer + next post_event_seconds.
        """
        with self._lock:
            if self._saving:
                logger.debug("Clip already recording, skipping trigger")
                return

            self._saving = True
            self._post_frames_remaining = int(self._post_seconds * self._fps)
            self._clip_reason = reason
            self._clip_start_ts = time.time()
            # Start clip with whatever's in the pre-event buffer
            self._clip_frames = list(self._buffer)
            logger.info(f"Clip triggered: {reason} (pre-buffer: {len(self._clip_frames)} frames)")

    def list_clips(self) -> list[dict]:
        """Return metadata for all saved clips, newest first."""
        clips = []
        for f in sorted(self._output_dir.glob("*.mp4"), reverse=True):
            stat = f.stat()
            clips.append({
                "filename":   f.name,
                "path":       str(f),
                "size_mb":    round(stat.st_size / 1_048_576, 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
        return clips

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _write_clip(self, frames: list, reason: str, start_ts: float):
        if not frames:
            return

        ts_str = datetime.fromtimestamp(start_ts).strftime("%Y%m%d_%H%M%S")
        safe_reason = reason.replace(" ", "_").replace("/", "-")[:40]
        filename = self._output_dir / f"clip_{ts_str}_{safe_reason}.mp4"

        # Decode first frame to get dimensions
        first = cv2.imdecode(
            __import__("numpy").frombuffer(frames[0][1], dtype="uint8"),
            cv2.IMREAD_COLOR
        )
        if first is None:
            return
        h, w = first.shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(filename), fourcc, self._fps, (w, h))

        import numpy as np
        for _, jpeg_bytes in frames:
            frame = cv2.imdecode(np.frombuffer(jpeg_bytes, dtype="uint8"), cv2.IMREAD_COLOR)
            if frame is not None:
                writer.write(frame)

        writer.release()
        size_mb = filename.stat().st_size / 1_048_576
        logger.info(f"Clip saved: {filename.name} ({len(frames)} frames, {size_mb:.1f} MB)")

        self._prune_old_clips()

    def _prune_old_clips(self):
        clips = sorted(self._output_dir.glob("*.mp4"), key=lambda f: f.stat().st_ctime)
        while len(clips) > self._max_clips:
            oldest = clips.pop(0)
            oldest.unlink()
            logger.info(f"Pruned old clip: {oldest.name}")
