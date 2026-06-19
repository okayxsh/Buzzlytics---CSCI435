import numpy as np
from unittest.mock import patch, MagicMock
from cv_pipeline.pipeline import CVPipeline


def _pipe():
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        return CVPipeline(use_tracker=False)


def test_process_frame_includes_motion():
    pipe = _pipe()
    # stub detector to avoid the mocked-YOLO inference returning junk
    pipe.detector.detect = lambda f: []
    out = pipe.process_frame(np.zeros((64, 64, 3), dtype=np.uint8))
    assert "motion" in out
    assert "activity_ratio" in out["motion"] and "blob_count" in out["motion"]
