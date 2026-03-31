import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from config_loader import cfg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/forecast", tags=["forecast"])
MODEL_PATH = Path(cfg.get("forecast", {}).get("model_path", Path(__file__).resolve().parents[2] / "training" / "out" / "traffic_congestion_model.pkl")).expanduser()


@router.get("/live")
def get_live_forecast():
    try:
        from predictor import predictor_state
        result = predictor_state.get()
        if result is None:
            return {"ready": False, "reason": "No prediction yet — model may still be loading"}
        return result
    except Exception as exc:
        logger.error(f"Forecast endpoint error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status")
def get_forecast_status():
    try:
        from predictor import predictor_state
        return predictor_state.get_model_info()
    except Exception:
        return {
            "model_file_exists": MODEL_PATH.exists(),
            "model_path": str(MODEL_PATH),
            "predictor_ready": False,
            "model_type": "sklearn",
            "algorithm": None,
            "feature_count": 0,
            "classes": [],
            "last_loaded_at": None,
            "last_error": None,
            "upload_supported": False,
        }


@router.get("/history")
def get_forecast_history():
    try:
        from predictor import predictor_state
        return {"items": predictor_state.get_history()}
    except Exception as exc:
        logger.error(f"Forecast history error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/model/meta")
def get_forecast_model_meta():
    return get_forecast_status()
