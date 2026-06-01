"""
Statistical analytics module for the Buzzlytics CV Pipeline.

Computes hive health metrics based on detected and tracked bee
populations, including health scores and activity/infection rates.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from .tracker import Track

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Computes hive health statistics from tracked bee detections.

    Maintains running counters for each bee class and derives health
    metrics including a composite health score (0-100), activity rate,
    and infection rate.

    Health score formula:
        base = 70
        +10 if pollen_ratio > 0.1  (good foraging activity)
        -20 if varroa_ratio > 0.15 (significant mite infestation)
        -30 if dead_ratio > 0.1    (high mortality)
        -10 if activity_rate < 0.3 (low activity level)

    Health status thresholds:
        >70  = Healthy
        40-70 = Warning
        <40  = Critical
    """

    def __init__(self) -> None:
        """Initialize the analytics engine with zeroed counters."""
        self._active_bees: int = 0
        self._pollen_bees: int = 0
        self._varroa_infected: int = 0
        self._dead_bees: int = 0
        self._total_bees: int = 0

    def update(self, tracks: List[Track]) -> None:
        """Update internal counters with a new set of tracks.

        Each call replaces the current frame-level counts (does not
        accumulate across frames), so the summary always reflects the
        most recent observation.

        Args:
            tracks: List of Track objects from the current frame.
        """
        active = 0
        pollen = 0
        varroa = 0
        dead = 0

        for track in tracks:
            name = track.class_name
            if name == "active_bee":
                active += 1
            elif name == "pollen_bee":
                pollen += 1
            elif name == "varroa_infected":
                varroa += 1
            elif name == "dead_bee":
                dead += 1

        self._active_bees = active
        self._pollen_bees = pollen
        self._varroa_infected = varroa
        self._dead_bees = dead
        self._total_bees = active + pollen + varroa + dead

    def compute_health_score(self) -> float:
        """Compute a composite hive health score from 0 to 100.

        Applies the health score formula based on the ratios of
        different bee classes in the current observation.

        Returns:
            Health score clamped to [0, 100].
        """
        if self._total_bees == 0:
            return 0.0

        pollen_ratio = self._pollen_bees / self._total_bees
        varroa_ratio = self._varroa_infected / self._total_bees
        dead_ratio = self._dead_bees / self._total_bees
        activity_rate = (
            (self._active_bees + self._pollen_bees) / self._total_bees
        )

        score: float = 70.0

        # Positive signal: good foraging activity
        if pollen_ratio > 0.1:
            score += 10.0

        # Negative signals
        if varroa_ratio > 0.15:
            score -= 20.0

        if dead_ratio > 0.1:
            score -= 30.0

        if activity_rate < 0.3:
            score -= 10.0

        # Clamp to valid range
        return max(0.0, min(100.0, score))

    def _compute_health_status(self, health_score: float) -> str:
        """Determine health status label from the health score.

        Args:
            health_score: Computed health score in [0, 100].

        Returns:
            One of "Healthy", "Warning", or "Critical".
        """
        if health_score > 70:
            return "Healthy"
        elif health_score >= 40:
            return "Warning"
        else:
            return "Critical"

    def get_summary(self) -> Dict[str, object]:
        """Return a summary dictionary of current hive health metrics.

        Returns:
            Dictionary with the following keys:
                - total_bees: Total number of detected bees.
                - active_bees: Count of active bees.
                - pollen_bees: Count of pollen-carrying bees.
                - varroa_infected: Count of varroa-infected bees.
                - dead_bees: Count of dead bees.
                - health_score: Composite health score (0-100).
                - health_status: "Healthy", "Warning", or "Critical".
                - activity_rate: Ratio of active + pollen bees to total.
                - infection_rate: Ratio of varroa-infected bees to total.
        """
        health_score = self.compute_health_score()

        activity_rate: float = 0.0
        infection_rate: float = 0.0

        if self._total_bees > 0:
            activity_rate = (
                (self._active_bees + self._pollen_bees)
                / self._total_bees
            )
            infection_rate = self._varroa_infected / self._total_bees

        return {
            "total_bees": self._total_bees,
            "active_bees": self._active_bees,
            "pollen_bees": self._pollen_bees,
            "varroa_bees": self._varroa_infected,
            "varroa_infected": self._varroa_infected,
            "dead_bees": self._dead_bees,
            "health_score": round(health_score, 1),
            "health_status": self._compute_health_status(health_score),
            "activity_rate": round(activity_rate * 100, 1),
            "infection_rate": round(infection_rate * 100, 1),
        }

    def reset(self) -> None:
        """Reset all counters to zero."""
        self._active_bees = 0
        self._pollen_bees = 0
        self._varroa_infected = 0
        self._dead_bees = 0
        self._total_bees = 0
