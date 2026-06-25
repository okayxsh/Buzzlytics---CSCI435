"""Tests for the analytics engine."""
from dataclasses import dataclass

from cv_pipeline.analytics import AnalyticsEngine


@dataclass
class FakeTrack:
    class_name: str
    track_id: int = 0
    bbox: list = None
    confidence: float = 0.9
    class_id: int = 0
    age: int = 1


def _tracks(names):
    return [FakeTrack(class_name=n, track_id=i) for i, n in enumerate(names)]


def test_counts_classes():
    eng = AnalyticsEngine()
    eng.update(_tracks(["bee", "bee", "pollen_bee", "varroa_bee"]))
    s = eng.get_summary()
    assert s["total_bees"] == 4
    assert s["active_bees"] == 3  # 2 bee + 1 pollen (healthy/active)
    assert s["pollen_bees"] == 1
    assert s["varroa_bees"] == 1
    assert "wasps" not in s  # wasp class dropped
    assert s["infection_rate"] == 25.0  # 1/4


def test_varroa_lowers_health():
    eng = AnalyticsEngine()
    eng.update(_tracks(["bee"] * 10))
    base = eng.compute_health_score()
    eng.update(_tracks(["bee"] * 7 + ["varroa_bee"] * 3))  # 30% infection
    infected = eng.compute_health_score()
    assert infected < base


def test_health_score_is_continuous_and_responsive():
    eng = AnalyticsEngine()
    # clean colony with foraging -> near 100
    eng.update(_tracks(["bee"] * 9 + ["pollen_bee"]))
    assert eng.compute_health_score() >= 95
    # 20% infection -> ~50 (100 - 2.5*20)
    eng.update(_tracks(["bee"] * 8 + ["varroa_bee"] * 2))
    assert 45 <= eng.compute_health_score() <= 55


def test_empty_returns_zero_score():
    eng = AnalyticsEngine()
    eng.update([])
    assert eng.compute_health_score() == 0.0
    assert eng.get_summary()["total_bees"] == 0
