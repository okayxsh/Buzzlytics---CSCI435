"""Tests for visualizer color map."""
from cv_pipeline.visualize import DEFAULT_COLOR_MAP


def test_color_map_has_detection_classes():
    assert set(DEFAULT_COLOR_MAP) == {"bee", "pollen_bee", "varroa_bee"}
    assert DEFAULT_COLOR_MAP["varroa_bee"] == (0, 0, 220)
