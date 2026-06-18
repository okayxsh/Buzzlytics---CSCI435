"""Tests for detector class taxonomy (no model load required)."""
from cv_pipeline.detector import BEE_CLASS_NAMES


def test_unified_class_names():
    assert BEE_CLASS_NAMES == {
        0: "bee",
        1: "pollen_bee",
        2: "varroa_bee",
        3: "wasp",
    }
