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


def test_counts_unified_classes():
    eng = AnalyticsEngine()
    eng.update(_tracks(["bee", "bee", "pollen_bee", "varroa_bee", "wasp"]))
    s = eng.get_summary()
    assert s["total_bees"] == 5
    assert s["active_bees"] == 2
    assert s["pollen_bees"] == 1
    assert s["varroa_bees"] == 1
    assert s["wasps"] == 1
    assert "dead_bees" not in s
    assert "varroa_infected" not in s


def test_wasp_presence_penalizes_health():
    eng = AnalyticsEngine()
    # 10 bees, no wasp -> healthy-ish baseline
    eng.update(_tracks(["bee"] * 10))
    base = eng.compute_health_score()
    # add wasps above 5% threshold -> penalty applied
    eng.update(_tracks(["bee"] * 8 + ["wasp"] * 2))
    with_wasp = eng.compute_health_score()
    assert with_wasp < base


def test_empty_returns_zero_score():
    eng = AnalyticsEngine()
    eng.update([])
    assert eng.compute_health_score() == 0.0
    assert eng.get_summary()["total_bees"] == 0
