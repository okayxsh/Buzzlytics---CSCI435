import numpy as np
from unittest.mock import patch, MagicMock
from cv_pipeline.pipeline import CVPipeline


def _pipe(config=None):
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        return CVPipeline(use_tracker=False, config=config)


def test_process_frame_includes_motion():
    pipe = _pipe()
    # stub detector to avoid the mocked-YOLO inference returning junk
    pipe.detector.detect = lambda f: []
    out = pipe.process_frame(np.zeros((64, 64, 3), dtype=np.uint8))
    assert "motion" in out
    assert "activity_ratio" in out["motion"] and "blob_count" in out["motion"]


def test_pipeline_reads_preprocess_config_keys():
    """CVPipeline must store clahe_clip_limit and denoise_strength from config."""
    from cv_pipeline.config import load_config

    cfg = load_config()
    # Override preprocess keys with sentinel values
    cfg["preprocess"]["clahe_clip_limit"] = 7.5
    cfg["preprocess"]["denoise_strength"] = 42

    pipe = _pipe(config=cfg)

    assert pipe._clahe_clip == 7.5, (
        f"Expected _clahe_clip=7.5, got {pipe._clahe_clip}"
    )
    assert pipe._denoise_strength == 42, (
        f"Expected _denoise_strength=42, got {pipe._denoise_strength}"
    )
