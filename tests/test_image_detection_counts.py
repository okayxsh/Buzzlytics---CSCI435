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
            "pollen_good_threshold": 0.1,
            "varroa_warn_threshold": 0.15,
            "wasp_threat_threshold": 0.05,
            "low_activity_threshold": 0.3,
            "health_weights": {
                "base": 70,
                "pollen_bonus": 10,
                "varroa_penalty": 20,
                "wasp_penalty": 25,
                "low_activity_penalty": 10,
            },
        },
        "visualize": {
            "colors": {
                "bee": [0, 200, 0],
                "pollen_bee": [0, 220, 255],
                "varroa_bee": [0, 0, 220],
                "wasp": [0, 140, 255],
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
# Fake detections — 5 objects across all 4 classes
# ---------------------------------------------------------------------------

FAKE_DETECTIONS = [
    Detection(bbox=[0.0, 0.0, 10.0, 10.0], confidence=0.9, class_id=0, class_name="bee"),
    Detection(bbox=[10.0, 0.0, 20.0, 10.0], confidence=0.85, class_id=0, class_name="bee"),
    Detection(bbox=[20.0, 0.0, 30.0, 10.0], confidence=0.8, class_id=1, class_name="pollen_bee"),
    Detection(bbox=[30.0, 0.0, 40.0, 10.0], confidence=0.75, class_id=2, class_name="varroa_bee"),
    Detection(bbox=[40.0, 0.0, 50.0, 10.0], confidence=0.7, class_id=3, class_name="wasp"),
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

    assert summary["total_bees"] == 5, (
        f"Expected total_bees=5, got {summary['total_bees']}"
    )
    assert summary["active_bees"] == 2, (
        f"Expected active_bees=2 (two plain bees), got {summary['active_bees']}"
    )
    assert summary["pollen_bees"] == 1, (
        f"Expected pollen_bees=1, got {summary['pollen_bees']}"
    )
    assert summary["varroa_bees"] == 1, (
        f"Expected varroa_bees=1, got {summary['varroa_bees']}"
    )
    assert summary["wasps"] == 1, (
        f"Expected wasps=1, got {summary['wasps']}"
    )


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
    assert summary["wasps"] == 0


def test_result_dict_contains_detections_not_tracks(monkeypatch):
    """In tracker-off mode, result['detections'] should be populated and
    result['tracks'] should be empty."""
    pipe = _make_pipe_no_tracker()
    monkeypatch.setattr(pipe.detector, "detect", lambda frame: FAKE_DETECTIONS)

    dummy_frame = np.zeros((64, 64, 3), dtype=np.uint8)
    result = pipe.process_frame(dummy_frame)

    assert result["tracks"] == [], "tracks must be empty in detection-only mode"
    assert len(result["detections"]) == 5, (
        f"Expected 5 detections in result, got {len(result['detections'])}"
    )
