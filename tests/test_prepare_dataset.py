"""Tests for dataset label remapping + new source converters (pure funcs)."""
from datasets.prepare_dataset import (
    remap_label_lines,
    build_id_map,
    points_to_yolo_box,
    labelme_shapes_to_yolo,
    varroa_flag_to_class,
    whole_image_label,
    parse_varroa_gt_line,
    sample_varroa_rows,
    split_for,
)

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


# --- VnPollenBee LabelMe -> YOLO -------------------------------------------- #
def test_points_to_yolo_box_envelope():
    # rectangle drawn as a 4-pt polygon on a 100x100 image
    box = points_to_yolo_box([[10, 20], [40, 20], [40, 60], [10, 60]], 100, 100)
    assert box == (0.25, 0.4, 0.3, 0.4)


def test_points_to_yolo_box_degenerate_returns_none():
    assert points_to_yolo_box([[10, 10], [10, 10]], 100, 100) is None
    assert points_to_yolo_box([[0, 0], [5, 5]], 0, 0) is None


def test_labelme_shapes_maps_pollen_and_drops_unknown():
    shapes = [
        {"label": "nonpollenbee", "points": [[0, 0], [50, 100]]},
        {"label": "pollenbee", "points": [[100, 100], [200, 300]]},
        {"label": "queen", "points": [[0, 0], [10, 10]]},  # unknown -> dropped
    ]
    out = labelme_shapes_to_yolo(shapes, 1920, 1080)
    assert len(out) == 2
    assert out[0].startswith("0 ")  # nonpollenbee -> bee
    assert out[1].startswith("1 ")  # pollenbee -> pollen_bee


# --- VarroaDataset gt.csv -> whole-crop box --------------------------------- #
def test_varroa_flag_to_class():
    assert varroa_flag_to_class(1) == 2  # infected -> varroa_bee
    assert varroa_flag_to_class(3) == 2  # infected (quality-code 3) -> varroa_bee
    assert varroa_flag_to_class(0) == 0  # healthy -> bee


def test_whole_image_label():
    assert whole_image_label(2) == "2 0.5 0.5 1.0 1.0\n"


def test_parse_varroa_gt_line_infected_with_mite_boxes():
    line = "test/videos/x/foo.png 1 84 143 109 172 54 142 82 172"
    assert parse_varroa_gt_line(line) == ("test/videos/x/foo.png", 2)


def test_parse_varroa_gt_line_healthy():
    assert parse_varroa_gt_line("train/videos/y/bar.png 0") == (
        "train/videos/y/bar.png",
        0,
    )


def test_parse_varroa_gt_line_blank():
    assert parse_varroa_gt_line("   ") is None


# --- split assignment ------------------------------------------------------- #
def test_split_honours_explicit_hint():
    assert split_for("anything", "test/videos/x.png") == "test"
    assert split_for("anything", "train/videos/x.png") == "train"


def test_split_is_deterministic_and_valid():
    s1 = split_for("vpb_image_001")
    s2 = split_for("vpb_image_001")
    assert s1 == s2
    assert s1 in {"train", "valid", "test"}


# --- varroa subsampling ----------------------------------------------------- #
def _varroa_rows():
    # 24 healthy (bee=0), 6 infected (varroa=2)  -> ratio 4:1
    return [(f"h/{i}.png", 0) for i in range(24)] + [(f"v/{i}.png", 2) for i in range(6)]


def test_sample_varroa_none_returns_all():
    rows = _varroa_rows()
    assert sample_varroa_rows(rows, None) is rows
    assert len(sample_varroa_rows(rows, 999)) == len(rows)


def test_sample_varroa_caps_and_preserves_ratio():
    rows = _varroa_rows()  # 30 total, 4:1
    kept = sample_varroa_rows(rows, 10)
    assert len(kept) <= 10
    healthy = sum(1 for _, c in kept if c == 0)
    infected = sum(1 for _, c in kept if c == 2)
    # ~8 healthy : ~2 infected
    assert healthy == 8 and infected == 2


def test_sample_varroa_is_deterministic():
    rows = _varroa_rows()
    assert sample_varroa_rows(rows, 10) == sample_varroa_rows(rows, 10)
