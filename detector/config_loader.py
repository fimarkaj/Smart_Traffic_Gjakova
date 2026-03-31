"""
config_loader.py — Loads and validates config.yaml.
Provides a single cfg object imported everywhere.
"""
import os
from pathlib import Path
import yaml

_DEFAULT_CONFIG = Path(__file__).parent.parent / "config.yaml"


def load_config(path: str = None) -> dict:
    config_path = Path(path or os.environ.get("CONFIG_PATH", _DEFAULT_CONFIG))
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# Module-level singleton — import this everywhere
cfg = load_config()
