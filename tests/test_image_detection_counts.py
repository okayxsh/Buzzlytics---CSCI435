"""Tests that detections flow into analytics in tracker-off (image) mode.

R3 bug fix: single-image analysis previously showed zero counts because
analytics.update() received an empty tracks list when the tracker was
disabled. The fix makes process_frame pass detections when tracks is empty,
so image-mode counts now reflect what the detector actually found.
"""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from cv_pipeline.pipeline import CVPipeline
from cv_pipeline.detector import Detection


# ---------------------------------------------------------------------------
# Shared config / pipeline factory
# ---------------------------------------------------------------------------

def _make_config():
    return {
        "detector": {
            "model_path": "missing.pt",
            "conf_threshold": 0.25,
            "iou_threshold": 0.45,
            "imgsz": 640,
        },
        "tracker": {"track_buffer": 30, "match_thresh": 0.8},
        "analytics": {
            "varroa_penalty_per_pct": 2.5,
            "low_pollen_penalty": 5.0,
            "low_pollen_threshold": 1.0,
            "healthy_score": 70,
            "warning_score": 40,
        },
        "varroa_classifier": {"enabled": False},
        "visualize": {
            "colors": {
                "bee": [0, 200, 0],
                "pollen_bee": [0, 220, 255],
                "varroa_bee": [0, 0, 220],
            }
        },
        "video": {"frame_skip": 1},
        "motion": {
            "history": 500,
            "var_threshold": 16,
            "detect_shadows": True,
            "kernel_size": 3,
        },
        "preprocess": {
            "white_balance": True,
            "clahe_clip_limit": 2.0,
            "denoise_strength": 10,
        },
    }


def _make_pipe_no_tracker():
    """Build CVPipeline(use_tracker=False) with YOLO fully mocked."""
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        return CVPipeline(use_tracker=False, config=_make_config())


# ---------------------------------------------------------------------------
# Fake detections — 4 objects (2 bee, 1 pollen, 1 varroa)
# ---------------------------------------------------------------------------

FAKE_DETECTIONS = [
    Detection(bbox=[0.0, 0.0, 10.0, 10.0], confidence=0.9, class_id=0, class_name="bee"),
    Detection(bbox=[10.0, 0.0, 20.0, 10.0], confidence=0.85, class_id=0, class_name="bee"),
    Detection(bbox=[20.0, 0.0, 30.0, 10.0], confidence=0.8, class_id=1, class_name="pollen_bee"),
    Detection(bbox=[30.0, 0.0, 40.0, 10.0], confidence=0.75, class_id=2, class_name="varroa_bee"),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_detection_counts_flow_into_analytics(monkeypatch):
    """Analytics must reflect detector output on a single image frame.

    With use_tracker=False, process_frame should pass detections to
    analytics.update() so counts are non-zero.
    """
    pipe = _make_pipe_no_tracker()
    monkeypatch.setattr(pipe.detector, "detect", lambda frame: FAKE_DETECTIONS)

    dummy_frame = np.zeros((64, 64, 3), dtype=np.uint8)
    result = pipe.process_frame(dummy_frame)
    summary = result["summary"]

    assert summary["total_bees"] == 4, (
        f"Expected total_bees=4, got {summary['total_bees']}"
    )
    assert summary["active_bees"] == 3, (
        f"Expected active_bees=3 (2 bee + 1 pollen), got {summary['active_bees']}"
    )
    assert summary["pollen_bees"] == 1, (
        f"Expected pollen_bees=1, got {summary['pollen_bees']}"
    )
    assert summary["varroa_bees"] == 1, (
        f"Expected varroa_bees=1, got {summary['varroa_bees']}"
    )
    assert "wasps" not in summary


def test_zero_detections_gives_zero_counts(monkeypatch):
    """When the detector finds nothing, summary counts should all be zero."""
    pipe = _make_pipe_no_tracker()
    monkeypatch.setattr(pipe.detector, "detect", lambda frame: [])

    dummy_frame = np.zeros((64, 64, 3), dtype=np.uint8)
    result = pipe.process_frame(dummy_frame)
    summary = result["summary"]

    assert summary["total_bees"] == 0
    assert summary["active_bees"] == 0
    assert summary["pollen_bees"] == 0
    assert summary["varroa_bees"] == 0
    assert "wasps" not in summary


def test_result_dict_contains_detections_not_tracks(monkeypatch):
    """In tracker-off mode, result['detections'] should be populated and
    result['tracks'] should be empty."""
    pipe = _make_pipe_no_tracker()
    monkeypatch.setattr(pipe.detector, "detect", lambda frame: FAKE_DETECTIONS)

    dummy_frame = np.zeros((64, 64, 3), dtype=np.uint8)
    result = pipe.process_frame(dummy_frame)

    assert result["tracks"] == [], "tracks must be empty in detection-only mode"
    assert len(result["detections"]) == 4, (
        f"Expected 4 detections in result, got {len(result['detections'])}"
    )
