"""
Statistical analytics module for the Buzzlytics CV Pipeline.

Computes hive health metrics from detected/tracked bee populations:
a composite health score, activity rate, and varroa infection rate.

Classes counted: bee, pollen_bee, varroa_bee (wasp was dropped).

Health score (0-100), continuous and interpretable:

    score = 100
          - varroa_penalty_per_pct * infection_rate(%)   # disease is dominant
          - low_pollen_penalty       if pollen_rate(%) < low_pollen_threshold

so a clean colony scores ~100 and degrades smoothly as the varroa
infection rate climbs (e.g. 10% infection -> 75, 20% -> 50, 40% -> 0).
Thresholds/weights come from config.yaml ("analytics").
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from .config import load_config
from .tracker import Track

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Computes hive health statistics from tracked bee detections.

    A bee classified by stage 2 as infected carries the class name
    ``varroa_bee``; ``bee`` and ``pollen_bee`` are the healthy/active bees.

    Args:
        config: Optional pre-loaded config dict. Loaded from config.yaml
            when omitted.
    """

    def __init__(self, config: Optional[Dict] = None) -> None:
        cfg = config if config is not None else load_config()
        a = cfg.get("analytics", {})
        self._varroa_penalty_per_pct = float(a.get("varroa_penalty_per_pct", 2.5))
        self._low_pollen_penalty = float(a.get("low_pollen_penalty", 5.0))
        self._low_pollen_threshold = float(a.get("low_pollen_threshold", 1.0))
        self._healthy_score = float(a.get("healthy_score", 70))
        self._warning_score = float(a.get("warning_score", 40))

        self._bees: int = 0
        self._pollen_bees: int = 0
        self._varroa_bees: int = 0
        self._total_bees: int = 0

    def update(self, tracks: List[Track]) -> None:
        """Replace current-frame counts from a list of tracks/detections."""
        bees = pollen = varroa = 0
        for track in tracks:
            name = track.class_name
            if name == "bee":
                bees += 1
            elif name == "pollen_bee":
                pollen += 1
            elif name == "varroa_bee":
                varroa += 1

        self._bees = bees
        self._pollen_bees = pollen
        self._varroa_bees = varroa
        self._total_bees = bees + pollen + varroa

    def _rates(self) -> Tuple[float, float, float]:
        """Return (activity_rate, pollen_rate, infection_rate) as percentages.

        activity_rate = share of bees that are healthy/active (bee + pollen);
        pollen_rate   = share carrying pollen (foraging);
        infection_rate = share flagged varroa.
        """
        if self._total_bees == 0:
            return 0.0, 0.0, 0.0
        active = self._bees + self._pollen_bees
        return (
            active / self._total_bees * 100.0,
            self._pollen_bees / self._total_bees * 100.0,
            self._varroa_bees / self._total_bees * 100.0,
        )

    def compute_health_score(self) -> float:
        """Compute a continuous hive health score in [0, 100]."""
        if self._total_bees == 0:
            return 0.0
        _, pollen_rate, infection_rate = self._rates()
        score = 100.0 - self._varroa_penalty_per_pct * infection_rate
        if pollen_rate < self._low_pollen_threshold:
            score -= self._low_pollen_penalty
        return max(0.0, min(100.0, score))

    def _compute_health_status(self, health_score: float) -> str:
        """Map a health score to Healthy/Warning/Critical."""
        if health_score >= self._healthy_score:
            return "Healthy"
        if health_score >= self._warning_score:
            return "Warning"
        return "Critical"

    def get_summary(self) -> Dict[str, object]:
        """Return current hive metrics as a summary dict."""
        health_score = self.compute_health_score()
        activity_rate, _, infection_rate = self._rates()
        return {
            "total_bees": self._total_bees,
            "active_bees": self._bees + self._pollen_bees,
            "pollen_bees": self._pollen_bees,
            "varroa_bees": self._varroa_bees,
            "health_score": round(health_score, 1),
            "health_status": self._compute_health_status(health_score),
            "activity_rate": round(activity_rate, 1),
            "infection_rate": round(infection_rate, 1),
        }

    def reset(self) -> None:
        """Reset all counters to zero."""
        self._bees = 0
        self._pollen_bees = 0
        self._varroa_bees = 0
        self._total_bees = 0
