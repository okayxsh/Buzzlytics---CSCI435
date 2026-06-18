"""Tests for visualizer color map."""
from cv_pipeline.visualize import DEFAULT_COLOR_MAP


def test_color_map_has_unified_classes():
    assert set(DEFAULT_COLOR_MAP) == {"bee", "pollen_bee", "varroa_bee", "wasp"}
    assert DEFAULT_COLOR_MAP["wasp"] == (0, 140, 255)
