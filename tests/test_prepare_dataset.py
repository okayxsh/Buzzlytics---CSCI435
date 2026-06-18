"""Tests for dataset label remapping (pure functions)."""
from datasets.prepare_dataset import remap_label_lines, build_id_map

CANONICAL = {"bee": 0, "pollen_bee": 1, "varroa_bee": 2, "wasp": 3}
ALIASES = {
    "bees": "bee", "bee": "bee",
    "pollen": "pollen_bee", "pollenbearing": "pollen_bee", "pollen_bee": "pollen_bee",
    "varroa": "varroa_bee", "mite": "varroa_bee", "varroa_bee": "varroa_bee",
    "wasp": "wasp", "wasps": "wasp",
}


def test_build_id_map_by_alias():
    # source dataset order: ["bees", "pollen", "varroa"]
    src = ["bees", "pollen", "varroa"]
    id_map = build_id_map(src, CANONICAL, ALIASES)
    assert id_map == {0: 0, 1: 1, 2: 2}


def test_build_id_map_wasp_only():
    id_map = build_id_map(["wasp"], CANONICAL, ALIASES)
    assert id_map == {0: 3}


def test_remap_label_lines_rewrites_class_id():
    lines = ["0 0.5 0.5 0.2 0.2\n", "2 0.1 0.1 0.05 0.05\n"]
    out = remap_label_lines(lines, {0: 3})  # only class 0 -> 3, drop others
    assert out == ["3 0.5 0.5 0.2 0.2\n"]


def test_remap_preserves_coords():
    out = remap_label_lines(["1 0.25 0.75 0.1 0.1\n"], {1: 2})
    assert out == ["2 0.25 0.75 0.1 0.1\n"]
