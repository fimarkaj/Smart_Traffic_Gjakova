"""
main.py — FastAPI application entry point.
Runs the detector in a background thread so shared_state is in the same process.

Start with:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
import sys
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add detector to path
DETECTOR_PATH = str(Path(__file__).parent.parent / "detector")
sys.path.insert(0, DETECTOR_PATH)

from config_loader import PROJECT_ROOT, cfg, resolve_path
from db import init_db, open_db, seed_rois, sync_default_alert_rules
from shared_state import state as shared_state  # noqa: F401

# ---------------------------------------------------------------------------
# Ensure required runtime directories exist
# ---------------------------------------------------------------------------

(PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "data" / "clips").mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "models").mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# App-level singletons
# ---------------------------------------------------------------------------

db_conn = open_db(cfg["database"]["path"])
init_db(db_conn)
seed_rois(db_conn)
sync_default_alert_rules(db_conn, cfg.get("alerts", {}).get("default_rules", []))

try:
    from model_manager import ModelManager
    model_manager = ModelManager()
except Exception as exc:
    logging.getLogger(__name__).warning(f"ModelManager initialization notice: {exc}")
    model_manager = None

try:
    from clip_recorder import ClipRecorder
    clip_recorder = ClipRecorder()
except Exception:
    clip_recorder = None

try:
    from line_counter import LineCrossingCounter
    line_counter = LineCrossingCounter()
except Exception:
    line_counter = None

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Traffic AI",
    description="Real-time traffic monitoring API",
    version="2.0.0",
)

configured_origins = cfg.get("api", {}).get("cors_origins", [])
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:80",
    "http://localhost",
    "http://127.0.0.1:80",
    "http://127.0.0.1",
    "http://localhost:3000",
]
all_origins = list(set(configured_origins + default_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from routers.auth          import router as auth_router
from routers.live          import router as live_router
from routers.analytics     import router as analytics_router
from routers.cameras       import router as cameras_router
from routers.clips         import router as clips_router
from routers.config_router import router as config_router
from routers.alerts        import router as alerts_router
from routers.model         import router as model_router
from routers.forecast      import router as forecast_router

app.include_router(auth_router)
app.include_router(live_router)
app.include_router(analytics_router)
app.include_router(cameras_router)
app.include_router(clips_router)
app.include_router(config_router)
app.include_router(alerts_router)
app.include_router(model_router)
app.include_router(forecast_router)

# ---------------------------------------------------------------------------
# Background services + detector thread
# ---------------------------------------------------------------------------

def _run_detector():
    """Run the detection loop in a background thread."""
    try:
        from detector import run
        run()
    except Exception as exc:
        logger.error(f"Detector thread crashed: {exc}", exc_info=True)


@app.on_event("startup")
async def startup():
    logger.info("Starting background services…")

    # Re-verify directories on startup
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "clips").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "models").mkdir(parents=True, exist_ok=True)

    from services.alert_engine import AlertEngine
    from services.retention    import RetentionScheduler

    alert_engine = AlertEngine(db_conn, shared_state)
    retention    = RetentionScheduler(db_conn)

    asyncio.create_task(alert_engine.run())
    asyncio.create_task(retention.run())

    # Start detector in a daemon thread — dies when the API process exits
    detector_thread = threading.Thread(
        target=_run_detector,
        name="detector",
        daemon=True,
    )
    detector_thread.start()
    logger.info("Detector thread started")

    # Start predictor thread (loads model, runs live inference)
    from predictor import start_predictor_thread
    start_predictor_thread()

    logger.info("Smart Traffic AI API ready")



@app.on_event("shutdown")
async def shutdown():
    logger.info("API shutting down")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    frame = shared_state.get_latest()
    return {
        "api":           "ok",
        "detector":      "ok" if shared_state.is_alive() else "no_data",
        "last_frame_ts": frame.timestamp if frame else None,
    }
