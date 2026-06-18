"""Configuration loader for the Buzzlytics CV pipeline.

Loads thresholds, colors, and weights from a YAML file, deep-merged
over built-in defaults so the application runs even if the file is
absent or partial. This is the single source of truth for tunable
values — pipeline modules read from here instead of hardcoding.
"""

from __future__ import annotations

import copy
import logging
import os
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

_DEFAULTS: Dict[str, Any] = {
    "detector": {
        "model_path": "cv_pipeline/weights/best.pt",
        "conf_threshold": 0.25,
        "iou_threshold": 0.45,
        "imgsz": 640,
    },
    "tracker": {"max_age": 30, "min_hits": 3, "iou_match": 0.3},
    "analytics": {
        "pollen_good_threshold": 0.1,
        "varroa_warn_threshold": 0.15,
        "wasp_threat_threshold": 0.05,
        "low_activity_threshold": 0.3,
        "health_weights": {
            "base": 70,
            "pollen_bonus": 10,
            "varroa_penalty": 20,
            "wasp_penalty": 25,
            "low_activity_penalty": 10,
        },
    },
    "visualize": {
        "colors": {
            "bee": [0, 200, 0],
            "pollen_bee": [0, 220, 255],
            "varroa_bee": [0, 0, 220],
            "wasp": [0, 140, 255],
        }
    },
    "video": {"frame_skip": 2},
}


def get_default_config() -> Dict[str, Any]:
    """Return a deep copy of the built-in default configuration."""
    return copy.deepcopy(_DEFAULTS)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``override`` into ``base`` and return ``base``."""
    for key, value in override.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from ``path`` merged over defaults.

    Args:
        path: Path to a YAML config file.

    Returns:
        Configuration dict. If the file is missing or empty, the
        built-in defaults are returned unchanged.
    """
    cfg = get_default_config()
    if not os.path.isfile(path):
        logger.warning("Config file '%s' not found; using defaults.", path)
        return cfg
    with open(path, "r", encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh) or {}
    if not isinstance(loaded, dict):
        logger.warning("Config file '%s' is not a mapping; using defaults.", path)
        return cfg
    return _deep_merge(cfg, loaded)
