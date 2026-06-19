import numpy as np
from cv_pipeline.motion import MotionDetector


def test_motion_detects_change_between_frames():
    det = MotionDetector(history=5, var_threshold=16, detect_shadows=False)
    static = np.zeros((64, 64, 3), dtype=np.uint8)
    for _ in range(5):           # warm up background model on static frames
        r0 = det.process(static)
    moved = static.copy()
    moved[20:40, 20:40] = 255    # a bright block appears
    r1 = det.process(moved)
    assert r1.activity_ratio > r0.activity_ratio
    assert r1.mask.shape == (64, 64) and r1.mask.dtype == np.uint8
    assert set(np.unique(r1.mask)).issubset({0, 255})
    assert r1.blob_count >= 1


def test_morphology_removes_salt_noise():
    det = MotionDetector(history=5, var_threshold=16, detect_shadows=False, kernel_size=5)
    base = np.zeros((64, 64, 3), dtype=np.uint8)
    for _ in range(5):
        det.process(base)
    noisy = base.copy()
    rng = np.random.default_rng(0)
    # sprinkle isolated single-pixel speckle
    ys = rng.integers(0, 64, 30); xs = rng.integers(0, 64, 30)
    noisy[ys, xs] = 255
    r = det.process(noisy)
    # open() should erase most isolated speckle -> very low activity
    assert r.activity_ratio < 0.05
