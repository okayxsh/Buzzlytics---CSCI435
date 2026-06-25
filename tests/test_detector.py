"""Tests for detector class taxonomy (no model load required)."""
from cv_pipeline.detector import BEE_CLASS_NAMES


def test_unified_class_names():
    # Stage-1 detector is 2-class; varroa_bee is assigned by the stage-2
    # classifier at runtime, not detected directly.
    assert BEE_CLASS_NAMES == {
        0: "bee",
        1: "pollen_bee",
    }
