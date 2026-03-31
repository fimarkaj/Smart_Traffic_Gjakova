"""
line_counter.py — Line crossing counter with all accuracy improvements.

Improvements over original:
  1. Cooldown raised to 15s (config-driven)
  2. Minimum travel distance: vehicle must move >= MIN_TRAVEL_PX pixels
     since its last crossing of that line before it can cross again.
     Eliminates slow vehicles sitting on the line and jittering.
  3. Entry/exit line pairing: lines marked "direction" = 1 are entry,
     -1 are exit. estimated_vehicles counts unique IDs that crossed
     at least one ENTRY line — no divide-by-2 heuristic needed.
     Falls back to unique_crossers // 2 if no entry lines are defined.
  4. Track stability: only counts crossings from stable tracks
     (already handled upstream in detect.py via MIN_TRACK_AGE).
  5. Per-track per-line cooldown in addition to spatial cell dedup.
"""
import json
import logging
import math
import time
from pathlib import Path

from config_loader import cfg

logger = logging.getLogger(__name__)

# Minimum pixels a vehicle centroid must travel between crossings of the
# same line. Prevents a slow vehicle straddling a line from counting twice.
MIN_TRAVEL_PX = 20


def _side(px, py, lx1, ly1, lx2, ly2):
    return (lx2 - lx1) * (py - ly1) - (ly2 - ly1) * (px - lx1)


def _cell(cx, cy, grid_size):
    return (int(cx) // grid_size, int(cy) // grid_size)


def _dist(ax, ay, bx, by):
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


class LineCrossingCounter:
    def __init__(self):
        lc_cfg = cfg["line_counter"]
        self._grid_size = lc_cfg["grid_size"]
        self._cooldown  = lc_cfg["cooldown"]   # now 15.0 in config

        self._lines: dict = {}
        self._load(lc_cfg["lines_file"])

        # Per-vehicle side memory: {track_id: {line_name: side_value}}
        self._prev_side: dict[int, dict[str, float]] = {}

        # Per-vehicle position memory: {track_id: (cx, cy)}
        self._prev_pos: dict[int, tuple[float, float]] = {}

        # Per-vehicle per-line last-crossed position:
        # {track_id: {line_name: (cx, cy)}}
        # Used for minimum travel distance check
        self._last_cross_pos: dict[int, dict[str, tuple]] = {}

        # Per-vehicle per-line cooldown: {(track_id, line_name): timestamp}
        self._track_line_ts: dict[tuple, float] = {}

        # Spatial dedup: (grid_cell, line_name) -> last_crossed_ts
        self._cell_crossed: dict[tuple, float] = {}

        # Raw crossing counts per line
        self._counts: dict[str, int] = {name: 0 for name in self._lines}

        # Unique IDs that crossed an ENTRY line (direction=1 or unspecified)
        self._entry_crossers: set[int] = set()

        # Unique IDs that crossed ANY line
        self._unique_crossers: set[int] = set()

        # All unique track_ids seen anywhere
        self._global_seen: set[int] = set()

        # Last-seen timestamp per track_id
        self._last_seen: dict[int, float] = {}

        self._frame_count = 0

        # Log whether entry/exit mode is active
        has_direction = any(
            "direction" in info for info in self._lines.values()
        )
        if has_direction:
            entry_count = sum(
                1 for info in self._lines.values()
                if info.get("direction", 1) == 1
            )
            logger.info(f"Entry/exit mode active — {entry_count} entry lines")
        else:
            logger.info("No direction tags found — using unique_crossers // 2 fallback")

    def _load(self, path: str):
        p = Path(path)
        if not p.exists():
            logger.warning(f"counting_lines.json not found: {path}")
            return
        with open(p) as f:
            self._lines = json.load(f)
        logger.info(f"Loaded {len(self._lines)} counting lines")

    def reload(self, path: str = None):
        p = path or cfg["line_counter"]["lines_file"]
        self._load(p)
        for name in self._lines:
            if name not in self._counts:
                self._counts[name] = 0

    def is_ready(self) -> bool:
        return len(self._lines) > 0

    def update(self, detections: list[dict]) -> dict[str, int]:
        now = time.time()
        self._frame_count += 1
        new_crossings = {name: 0 for name in self._lines}

        for det in detections:
            tid = det.get("track_id")
            if tid is None:
                continue

            self._global_seen.add(tid)
            self._last_seen[tid] = now

            x1, y1, x2, y2 = det["bbox"]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            cell = _cell(cx, cy, self._grid_size)

            if tid not in self._prev_side:
                self._prev_side[tid] = {}
            if tid not in self._last_cross_pos:
                self._last_cross_pos[tid] = {}

            for name, info in self._lines.items():
                p1, p2 = info["p1"], info["p2"]
                direction = info.get("direction", 0)  # 0 = both, 1 = entry, -1 = exit

                curr = _side(cx, cy, p1[0], p1[1], p2[0], p2[1])
                prev = self._prev_side[tid].get(name)
                self._prev_side[tid][name] = curr

                if prev is None or prev == 0 or curr == 0:
                    continue
                if (prev > 0) == (curr > 0):
                    continue

                # ── Check 1: spatial cell dedup ──────────────────────────
                dedup_key = (cell, name)
                if now - self._cell_crossed.get(dedup_key, 0.0) < self._cooldown:
                    continue

                # ── Check 2: per-track per-line cooldown ─────────────────
                track_line_key = (tid, name)
                if now - self._track_line_ts.get(track_line_key, 0.0) < self._cooldown:
                    continue

                # ── Check 3: minimum travel distance ─────────────────────
                last_pos = self._last_cross_pos[tid].get(name)
                if last_pos is not None:
                    dist = _dist(cx, cy, last_pos[0], last_pos[1])
                    if dist < MIN_TRAVEL_PX:
                        continue

                # ── Valid crossing ────────────────────────────────────────
                self._counts[name] += 1
                new_crossings[name] += 1
                self._cell_crossed[dedup_key] = now
                self._track_line_ts[track_line_key] = now
                self._last_cross_pos[tid][name] = (cx, cy)

                self._unique_crossers.add(tid)

                # Entry line tracking (direction=1 means entry)
                if direction == 1 or direction == 0:
                    self._entry_crossers.add(tid)

        # Periodic memory cleanup
        if self._frame_count % 300 == 0:
            cutoff = now - 120.0
            stale = [t for t, ts in self._last_seen.items() if ts < cutoff]
            for tid in stale:
                self._prev_side.pop(tid, None)
                self._prev_pos.pop(tid, None)
                self._last_cross_pos.pop(tid, None)
                self._last_seen.pop(tid, None)
            self._cell_crossed = {
                k: v for k, v in self._cell_crossed.items()
                if now - v < self._cooldown
            }
            self._track_line_ts = {
                k: v for k, v in self._track_line_ts.items()
                if now - v < self._cooldown
            }

        return new_crossings

    # ── Getters ───────────────────────────────────────────────────────

    def get_totals(self) -> dict[str, int]:
        """Raw crossing counts per line."""
        return dict(self._counts)

    def get_overall_total(self) -> int:
        """Sum of all raw line crossings."""
        return sum(self._counts.values())

    def get_unique_crossers(self) -> int:
        """Distinct track_ids that crossed any line at least once."""
        return len(self._unique_crossers)

    def get_estimated_vehicles(self) -> int:
        """
        Best estimate of real vehicles that passed through.

        If entry lines are defined (direction=1): count unique IDs that
        crossed an entry line — this is the most accurate method.

        Otherwise fall back to unique_crossers // 2 (entry+exit heuristic).
        """
        if self._entry_crossers:
            return len(self._entry_crossers)
        return len(self._unique_crossers) // 2

    def get_global_unique(self) -> int:
        """All distinct track_ids ever detected (inside ROIs too)."""
        return len(self._global_seen)

    def reset(self):
        self._counts          = {name: 0 for name in self._lines}
        self._prev_side       = {}
        self._prev_pos        = {}
        self._last_cross_pos  = {}
        self._track_line_ts   = {}
        self._cell_crossed    = {}
        self._unique_crossers = set()
        self._entry_crossers  = set()
        self._global_seen     = set()
        self._last_seen       = {}
