"""Tests for single-inference path and frame_skip behaviour."""
import numpy as np
from unittest.mock import patch, MagicMock
from cv_pipeline.pipeline import CVPipeline


def _pipe(**kw):
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        return CVPipeline(**kw)


def test_tracker_runs_single_inference_per_frame(monkeypatch):
    # With the tracker enabled, the detector's standalone detect() must NOT
    # be called (no double inference). Track is the single inference path.
    pipe = _pipe(use_tracker=True)
    detect_calls = {"n": 0}
    pipe.detector.detect = lambda f: (detect_calls.__setitem__("n", detect_calls["n"] + 1) or [])
    track_calls = {"n": 0}
    pipe.tracker.update = lambda frame, model_path=None: (track_calls.__setitem__("n", track_calls["n"] + 1) or [])
    pipe.process_frame(np.zeros((64, 64, 3), dtype=np.uint8))
    assert detect_calls["n"] == 0      # detector NOT called when tracking
    assert track_calls["n"] == 1       # tracker called once


def test_detector_used_when_tracker_disabled():
    pipe = _pipe(use_tracker=False)
    calls = {"n": 0}
    pipe.detector.detect = lambda f: (calls.__setitem__("n", calls["n"] + 1) or [])
    pipe.process_frame(np.zeros((64, 64, 3), dtype=np.uint8))
    assert calls["n"] == 1


def test_frame_skip_processes_subset(tmp_path):
    # frame_skip=3 -> only ~1/3 of frames get a fresh process_frame; the rest
    # reuse the last result. We assert process_frame is called fewer times
    # than total frames. (Construct a tiny synthetic video.)
    import cv2
    vid = str(tmp_path / "v.mp4")
    w = cv2.VideoWriter(vid, cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 64))
    for _ in range(9):
        w.write(np.zeros((64, 64, 3), dtype=np.uint8))
    w.release()
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        pipe = CVPipeline(use_tracker=False, config=_skip_config(3))
    pipe.detector.detect = lambda f: []
    calls = {"n": 0}
    real = pipe.process_frame
    pipe.process_frame = lambda f: (calls.__setitem__("n", calls["n"] + 1) or real(f))
    list(pipe.process_video(vid))
    assert calls["n"] < 9 and calls["n"] >= 3   # skipped some frames


def _skip_config(skip):
    from cv_pipeline.config import get_default_config
    c = get_default_config()
    c["video"]["frame_skip"] = skip
    c["video"]["process_fps"] = 0  # test the fixed frame_skip path directly
    return c
