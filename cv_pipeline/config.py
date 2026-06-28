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
        "conf_threshold": 0.4,
        "iou_threshold": 0.45,
        "imgsz": 960,
        "pollen_min_conf": 0.55,
    },
    "varroa_classifier": {
        "enabled": True,
        "model_path": "cv_pipeline/weights/varroa_cls.pt",
        "conf_threshold": 0.85,
        "min_crop_size": 24,
        "vote_window": 5,
        "min_track_hits": 2,
    },
    "tracker": {"track_buffer": 30, "match_thresh": 0.8},
    "analytics": {
        "varroa_penalty_per_pct": 2.5,
        "low_pollen_penalty": 5.0,
        "low_pollen_threshold": 1.0,
        "healthy_score": 70,
        "warning_score": 40,
    },
    "visualize": {
        "draw_trails": False,
        "max_trail_length": 20,
        "colors": {
            "bee": [0, 200, 0],
            "pollen_bee": [0, 220, 255],
            "varroa_bee": [0, 0, 220],
        }
    },
    "motion": {
        "history": 500,
        "var_threshold": 16,
        "detect_shadows": True,
        "kernel_size": 3,
    },
    "video": {"frame_skip": 2},
    "preprocess": {
        "white_balance": True,
        "clahe_clip_limit": 2.0,
        "denoise_strength": 10,
    },
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
