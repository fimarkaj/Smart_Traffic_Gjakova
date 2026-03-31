"""
config_router.py — Endpoints to read and update ROI polygons, counting lines, thresholds.
Changes are persisted to disk so they survive restarts.
"""
import json
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
from config_loader import cfg

router = APIRouter(prefix="/api/config", tags=["config"])


# ---------------------------------------------------------------------------
# Counting lines
# ---------------------------------------------------------------------------

class LinePoint(BaseModel):
    x: float
    y: float

class CountingLine(BaseModel):
    name: str
    p1: list[float]
    p2: list[float]
    direction: int = 1


@router.get("/lines")
def get_lines(user: str = Depends(get_current_user)):
    lines_file = Path(cfg["line_counter"]["lines_file"])
    if not lines_file.exists():
        return {}
    return json.loads(lines_file.read_text())


@router.put("/lines")
def save_lines(lines: dict, user: str = Depends(get_current_user)):
    lines_file = Path(cfg["line_counter"]["lines_file"])
    lines_file.parent.mkdir(parents=True, exist_ok=True)
    lines_file.write_text(json.dumps(lines, indent=2))
    # Hot-reload in detector
    try:
        from main import line_counter
        line_counter.reload()
    except Exception:
        pass
    return {"status": "saved", "count": len(lines)}


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

class Thresholds(BaseModel):
    green: int
    yellow: int


@router.get("/thresholds")
def get_thresholds(user: str = Depends(get_current_user)):
    return cfg["thresholds"]


@router.put("/thresholds")
def save_thresholds(thresholds: Thresholds, user: str = Depends(get_current_user)):
    cfg["thresholds"]["green"]  = thresholds.green
    cfg["thresholds"]["yellow"] = thresholds.yellow
    # Persist back to config.yaml
    import yaml
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    full_cfg = yaml.safe_load(config_path.read_text())
    full_cfg["thresholds"] = {"green": thresholds.green, "yellow": thresholds.yellow}
    config_path.write_text(yaml.dump(full_cfg, default_flow_style=False))
    return {"status": "saved", "thresholds": thresholds.dict()}


# ---------------------------------------------------------------------------
# Stream URL (runtime override)
# ---------------------------------------------------------------------------

class StreamConfig(BaseModel):
    url: str


@router.get("/stream")
def get_stream(user: str = Depends(get_current_user)):
    return {"url": cfg["stream"]["url"]}


@router.put("/stream")
def set_stream(stream: StreamConfig, user: str = Depends(get_current_user)):
    cfg["stream"]["url"] = stream.url
    return {"status": "updated", "url": stream.url}
