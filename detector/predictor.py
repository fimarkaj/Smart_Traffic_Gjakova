import logging
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

from config_loader import cfg

logger = logging.getLogger(__name__)
MODEL_PATH = Path(cfg.get("forecast", {}).get("model_path", Path(__file__).resolve().parents[1] / "training" / "out" / "traffic_congestion_model.pkl")).expanduser()

ROI_TO_FEATURE = {
    "Lane 1": "lane_1", "1": "lane_1",
    "Lane 2": "lane_2", "2": "lane_2",
    "Lane 3": "lane_3", "3": "lane_3",
    "Lane 4": "lane_4", "4": "lane_4",
    "Lane 5": "lane_5", "5": "lane_5",
    "Lane 6": "lane_6", "6": "lane_6",
    "Lane 7": "lane_7", "7": "lane_7",
    "Lane 8": "lane_8", "8": "lane_8",
}

COUNT_FEATURES = [
    "lane_1_count", "lane_2_count", "lane_3_count", "lane_4_count",
    "lane_5_count", "lane_6_count", "lane_7_count", "lane_8_count",
]
ALL_FEATURES = COUNT_FEATURES + ["total_cars", "hour", "minute", "weekday"]


class PredictorState:
    def __init__(self):
        self._lock = threading.Lock()
        self._latest = None
        self._history = deque(maxlen=60)
        self._model_info = {
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

    def update(self, result: dict):
        with self._lock:
            self._latest = result
            if result.get("ready"):
                self._history.append({
                    "timestamp": result.get("timestamp"),
                    "prediction": result.get("prediction"),
                    "max_conf": result.get("max_conf"),
                    "total_cars": result.get("total_cars"),
                })
                self._model_info["predictor_ready"] = True
                self._model_info["last_error"] = None

    def get(self):
        with self._lock:
            return self._latest

    def get_history(self):
        with self._lock:
            return list(self._history)

    def set_model_info(self, **kwargs):
        with self._lock:
            self._model_info.update(kwargs)

    def get_model_info(self):
        with self._lock:
            return dict(self._model_info)


predictor_state = PredictorState()


class LivePredictor:
    def __init__(self):
        self._model = None
        self._feature_cols = list(ALL_FEATURES)
        self._classes = []
        self._ready = False
        self._loaded_mtime = None

    def _normalise_bundle(self, obj):
        if isinstance(obj, dict) and "model" in obj:
            model = obj["model"]
            feature_columns = obj.get("feature_columns") or list(getattr(model, "feature_names_in_", ALL_FEATURES))
            classes = obj.get("classes") or list(getattr(model, "classes_", []))
            meta = obj.get("meta") or {}
            return model, list(feature_columns), list(classes), meta
        model = obj
        feature_columns = list(getattr(model, "feature_names_in_", ALL_FEATURES))
        classes = list(getattr(model, "classes_", []))
        return model, feature_columns, classes, {}

    def load(self, force=False):
        predictor_state.set_model_info(model_file_exists=MODEL_PATH.exists(), model_path=str(MODEL_PATH))
        if not MODEL_PATH.exists():
            predictor_state.set_model_info(predictor_ready=False, last_error=f"Model not found at {MODEL_PATH}")
            logger.warning(f"Predictor: model not found at {MODEL_PATH}")
            self._ready = False
            return False
        mtime = MODEL_PATH.stat().st_mtime
        if not force and self._loaded_mtime == mtime and self._ready:
            return True
        try:
            import joblib
            obj = joblib.load(MODEL_PATH)
            model, feature_columns, classes, meta = self._normalise_bundle(obj)
            self._model = model
            self._feature_cols = feature_columns
            self._classes = classes
            self._ready = True
            self._loaded_mtime = mtime
            predictor_state.set_model_info(
                predictor_ready=True,
                algorithm=type(model).__name__,
                feature_count=len(feature_columns),
                classes=classes,
                last_loaded_at=datetime.now().isoformat(timespec="seconds"),
                last_error=None,
                meta=meta,
            )
            logger.info(f"Predictor: model loaded from {MODEL_PATH}")
            return True
        except Exception as exc:
            self._ready = False
            predictor_state.set_model_info(predictor_ready=False, last_error=str(exc))
            logger.error(f"Predictor: failed to load model: {exc}")
            return False

    def _build_features(self, roi_counts, ts):
        row = {f: 0 for f in ALL_FEATURES}
        for roi_name, count in (roi_counts or {}).items():
            feat = ROI_TO_FEATURE.get(str(roi_name))
            if feat:
                row[f"{feat}_count"] = int(count)
        row["total_cars"] = int(sum((roi_counts or {}).values()))
        row["hour"] = ts.hour
        row["minute"] = ts.minute
        row["weekday"] = ts.weekday()
        return row

    def predict(self, roi_counts, ts):
        if not self._ready:
            return {"ready": False}
        try:
            import pandas as pd
            row = self._build_features(roi_counts, ts)
            safe_row = {col: row.get(col, 0) for col in self._feature_cols}
            X = pd.DataFrame([safe_row], columns=self._feature_cols)
            pred = self._model.predict(X)[0]
            conf = {}
            max_conf = None
            if hasattr(self._model, "predict_proba") and self._classes:
                proba = self._model.predict_proba(X)[0]
                conf = dict(zip(self._classes, [round(float(p), 4) for p in proba]))
                max_conf = round(float(max(proba)), 4)
            return {
                "ready": True,
                "prediction": pred,
                "confidence": conf,
                "max_conf": max_conf,
                "timestamp": ts.isoformat(),
                "total_cars": row["total_cars"],
            }
        except Exception as exc:
            logger.error(f"Predictor inference error: {exc}")
            predictor_state.set_model_info(last_error=str(exc))
            return {"ready": False, "error": str(exc)}


def run_predictor_loop():
    predictor = LivePredictor()
    while not predictor.load(force=True):
        logger.info("Predictor: waiting for model... (retrying in 30s)")
        time.sleep(30)
    logger.info("Predictor: entering live inference loop")
    while True:
        try:
            predictor.load()
            from main import shared_state
            frame = shared_state.get_latest()
            if frame is not None:
                ts = datetime.fromtimestamp(frame.timestamp)
                result = predictor.predict(frame.roi_counts, ts)
                predictor_state.update(result)
        except Exception as exc:
            logger.error(f"Predictor loop error: {exc}")
            predictor_state.set_model_info(last_error=str(exc))
        time.sleep(1.0)


def start_predictor_thread():
    t = threading.Thread(target=run_predictor_loop, daemon=True, name="predictor")
    t.start()
    logger.info("Predictor thread started")
    return t
