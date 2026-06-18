"""Tests for the config loader."""
from pathlib import Path

from cv_pipeline.config import load_config, get_default_config


def test_missing_file_returns_defaults():
    cfg = load_config("definitely_does_not_exist.yaml")
    assert cfg == get_default_config()


def test_defaults_have_unified_classes():
    cfg = get_default_config()
    colors = cfg["visualize"]["colors"]
    assert set(colors) == {"bee", "pollen_bee", "varroa_bee", "wasp"}
    assert colors["wasp"] == [0, 140, 255]


def test_file_overrides_merge_over_defaults(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("detector:\n  conf_threshold: 0.5\n")
    cfg = load_config(str(p))
    # overridden value
    assert cfg["detector"]["conf_threshold"] == 0.5
    # untouched default still present (deep merge, not replace)
    assert cfg["detector"]["iou_threshold"] == 0.45
    assert cfg["analytics"]["health_weights"]["wasp_penalty"] == 25
