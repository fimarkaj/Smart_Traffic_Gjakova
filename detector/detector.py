"""
detector.py — Main detection loop. Runs as a standalone process.

Start with:
    python detector.py

Writes live results to shared_state.state (read by FastAPI via import).
Writes historical data to SQLite.
Triggers clip recording on congestion events.
"""

import base64
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure local modules resolve correctly
sys.path.insert(0, str(Path(__file__).parent))

from capture import frame_generator
from clip_recorder import ClipRecorder
from config_loader import cfg
from detect import YOLODetector
from health_monitor import HealthMonitor
from line_counter import LineCrossingCounter
from model_manager import ModelManager
from roi import count_occupancy, load_rois
from shared_state import LiveFrame, state
from utils import draw_detections, draw_rois, draw_status_overlay, encode_frame

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _should_trigger_clip(roi_counts: dict, crossings_per_minute: float) -> str | None:
    """Return reason string if clip should be triggered, else None."""
    clip_cfg = cfg["clips"]
    for name, count in roi_counts.items():
        if count >= clip_cfg["trigger_occupancy"]:
            return f"high_occupancy_{name}_{count}"
    if crossings_per_minute >= clip_cfg["trigger_crossing_rate"]:
        return f"crossing_spike_{crossings_per_minute:.0f}pm"
    return None


def run():
    logger.info("=== Smart Traffic AI — Detector starting ===")

    # --- Initialise components -------------------------------------------
    health        = HealthMonitor(camera_id="main")
    model_mgr     = ModelManager()
    detector      = YOLODetector(model_mgr)
    rois          = load_rois()
    line_counter  = LineCrossingCounter()
    clip_recorder = ClipRecorder()

    # --- DB setup -----------------------------------------------------------
    # Import here to avoid circular imports with API layer
    import sqlite3
    sys.path.insert(0, str(Path(__file__).parent.parent / "api"))
    from db import init_db, open_db, seed_rois, upsert_counts_bulk, upsert_crossings_bulk, floor_to_second
    db_conn = open_db(cfg["database"]["path"])
    init_db(db_conn)
    seed_rois(db_conn)

    LINE_NAME_TO_ROI_ID = {
        "Lane 1": "1", "Lane 2": "2", "Lane 3": "3", "Lane 4": "4",
        "Lane 5": "5", "Lane 6": "6", "Lane 7": "7", "Lane 8": "8",
    }

    # --- Crossing rate tracker (for clip trigger) --------------------------
    crossing_timestamps: list[float] = []

    logger.info("Detector initialised — entering main loop")

    for frame, fps in frame_generator(health):
        try:
            detections    = detector.detect(frame)
            roi_counts    = count_occupancy(detections, rois)
            new_crossings = line_counter.update(detections)
            timestamp     = datetime.now()

            # --- Crossing rate (per minute) --------------------------------
            now = time.time()
            new_count = sum(new_crossings.values())
            crossing_timestamps.extend([now] * new_count)
            crossing_timestamps = [t for t in crossing_timestamps if now - t < 60]
            crossings_per_minute = len(crossing_timestamps)

            # --- Clip trigger ----------------------------------------------
            reason = _should_trigger_clip(roi_counts, crossings_per_minute)
            clip_recorder.push_frame(frame, fps)
            if reason:
                clip_recorder.trigger(reason)

            # --- Annotate frame -------------------------------------------
            vis = frame.copy()
            draw_detections(vis, detections)
            draw_rois(vis, rois, roi_counts)
            draw_status_overlay(vis, roi_counts)
            jpeg = encode_frame(vis)

            # --- Publish to shared state ----------------------------------
            if jpeg:
                state.update(LiveFrame(
                    jpeg_bytes        = jpeg,
                    timestamp         = timestamp.timestamp(),
                    roi_counts        = roi_counts,
                    crossing_totals   = line_counter.get_totals(),
                    new_crossings     = new_crossings,
                    overall_crossings  = line_counter.get_overall_total(),
                    unique_crossers    = line_counter.get_unique_crossers(),
                    estimated_vehicles = line_counter.get_estimated_vehicles(),
                    global_unique      = line_counter.get_global_unique(),
                    total_cars         = sum(roi_counts.values()),
                    camera_health      = health.get_health(),
                ))

            # --- Persist to SQLite ----------------------------------------
            ts_sec = floor_to_second(timestamp)
            upsert_counts_bulk(db_conn, [
                {"ts_second": ts_sec, "roi_id": k, "car_count": v}
                for k, v in roi_counts.items()
            ])

            cross_rows = [
                {"ts_second": ts_sec,
                 "roi_id": LINE_NAME_TO_ROI_ID[name],
                 "crossing_count": cnt}
                for name, cnt in new_crossings.items()
                if cnt > 0 and name in LINE_NAME_TO_ROI_ID
            ]
            if cross_rows:
                upsert_crossings_bulk(db_conn, cross_rows)

        except Exception as exc:
            logger.error(f"Frame processing error: {exc}", exc_info=True)

    logger.info("Detector loop exited")


if __name__ == "__main__":
    run()
