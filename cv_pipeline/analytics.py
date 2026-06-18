"""
Statistical analytics module for the Buzzlytics CV Pipeline.

Computes hive health metrics from detected/tracked bee populations:
a composite health score, activity rate, and varroa infection rate.
Thresholds and weights come from config.yaml.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .config import load_config
from .tracker import Track

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Computes hive health statistics from tracked bee detections.

    Counts the four unified classes (bee, pollen_bee, varroa_bee,
    wasp) per frame and derives a composite health score (0-100).

    Health score formula (weights/thresholds from config.yaml):
        base
        + pollen_bonus        if pollen_ratio > pollen_good_threshold
        - varroa_penalty      if varroa_ratio > varroa_warn_threshold
        - wasp_penalty        if wasp_ratio   > wasp_threat_threshold
        - low_activity_penalty if activity_rate < low_activity_threshold

    Health status: >70 Healthy, 40-70 Warning, <40 Critical.

    Args:
        config: Optional pre-loaded config dict. Loaded from
            config.yaml when omitted.
    """

    def __init__(self, config: Optional[Dict] = None) -> None:
        cfg = config if config is not None else load_config()
        a = cfg["analytics"]
        self._pollen_good = a["pollen_good_threshold"]
        self._varroa_warn = a["varroa_warn_threshold"]
        self._wasp_threat = a["wasp_threat_threshold"]
        self._low_activity = a["low_activity_threshold"]
        self._w = a["health_weights"]

        self._bees: int = 0
        self._pollen_bees: int = 0
        self._varroa_bees: int = 0
        self._wasps: int = 0
        self._total_bees: int = 0

    def update(self, tracks: List[Track]) -> None:
        """Replace current frame counts from a list of tracks."""
        bees = pollen = varroa = wasps = 0
        for track in tracks:
            name = track.class_name
            if name == "bee":
                bees += 1
            elif name == "pollen_bee":
                pollen += 1
            elif name == "varroa_bee":
                varroa += 1
            elif name == "wasp":
                wasps += 1

        self._bees = bees
        self._pollen_bees = pollen
        self._varroa_bees = varroa
        self._wasps = wasps
        self._total_bees = bees + pollen + varroa + wasps

    def compute_health_score(self) -> float:
        """Compute a composite hive health score in [0, 100]."""
        if self._total_bees == 0:
            return 0.0

        pollen_ratio = self._pollen_bees / self._total_bees
        varroa_ratio = self._varroa_bees / self._total_bees
        wasp_ratio = self._wasps / self._total_bees
        activity_rate = (self._bees + self._pollen_bees) / self._total_bees

        score: float = float(self._w["base"])
        if pollen_ratio > self._pollen_good:
            score += self._w["pollen_bonus"]
        if varroa_ratio > self._varroa_warn:
            score -= self._w["varroa_penalty"]
        if wasp_ratio > self._wasp_threat:
            score -= self._w["wasp_penalty"]
        if activity_rate < self._low_activity:
            score -= self._w["low_activity_penalty"]

        return max(0.0, min(100.0, score))

    def _compute_health_status(self, health_score: float) -> str:
        """Map a health score to Healthy/Warning/Critical."""
        if health_score > 70:
            return "Healthy"
        if health_score >= 40:
            return "Warning"
        return "Critical"

    def get_summary(self) -> Dict[str, object]:
        """Return current hive metrics as a summary dict."""
        health_score = self.compute_health_score()

        activity_rate = 0.0
        infection_rate = 0.0
        if self._total_bees > 0:
            activity_rate = (
                (self._bees + self._pollen_bees) / self._total_bees
            )
            infection_rate = self._varroa_bees / self._total_bees

        return {
            "total_bees": self._total_bees,
            "active_bees": self._bees,
            "pollen_bees": self._pollen_bees,
            "varroa_bees": self._varroa_bees,
            "wasps": self._wasps,
            "health_score": round(health_score, 1),
            "health_status": self._compute_health_status(health_score),
            "activity_rate": round(activity_rate * 100, 1),
            "infection_rate": round(infection_rate * 100, 1),
        }

    def reset(self) -> None:
        """Reset all counters to zero."""
        self._bees = 0
        self._pollen_bees = 0
        self._varroa_bees = 0
        self._wasps = 0
        self._total_bees = 0
