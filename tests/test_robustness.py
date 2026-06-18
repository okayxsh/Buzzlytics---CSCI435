"""Robustness: input validation for video processing."""
import pytest
from unittest.mock import patch, MagicMock

from cv_pipeline.pipeline import CVPipeline


def _make_pipe():
    """Construct a CVPipeline with YOLO mocked out (no weights needed)."""
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        return CVPipeline(use_tracker=False)


def test_missing_video_raises(tmp_path):
    pipe = _make_pipe()
    gen = pipe.process_video(str(tmp_path / "nope.mp4"))
    with pytest.raises(FileNotFoundError):
        next(gen)


def test_corrupt_video_raises(tmp_path):
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"not a real video")
    pipe = _make_pipe()
    gen = pipe.process_video(str(bad))
    with pytest.raises(ValueError):
        next(gen)
