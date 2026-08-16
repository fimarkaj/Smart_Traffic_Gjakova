"""
config_loader.py — Loads and validates config.yaml.
Provides a single cfg object imported everywhere.
"""
import os
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG = PROJECT_ROOT / "config.yaml"


def resolve_path(path: str | Path | None) -> Path:
    """Resolve a path relative to the project root unless it is already absolute."""
    if path is None:
        return PROJECT_ROOT
    p = Path(path).expanduser()
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def load_config(path: str = None) -> dict:
    config_path = resolve_path(path or os.environ.get("CONFIG_PATH", _DEFAULT_CONFIG))
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Module-level singleton — import this everywhere
cfg = load_config()

