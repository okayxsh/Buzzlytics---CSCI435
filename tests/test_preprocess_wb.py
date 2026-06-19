import numpy as np
from cv_pipeline.preprocess import apply_white_balance


def test_white_balance_neutralizes_color_cast():
    # Blue-cast image: B channel high, R low. Gray-world should rebalance
    # channel means toward each other.
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    frame[:, :, 0] = 200  # B
    frame[:, :, 1] = 120  # G
    frame[:, :, 2] = 40   # R
    out = apply_white_balance(frame)
    means = out.reshape(-1, 3).mean(axis=0)
    assert out.shape == frame.shape and out.dtype == np.uint8
    # channel means closer together than before (spread shrinks)
    assert means.max() - means.min() < (200 - 40)


def test_white_balance_gray_image_unchanged():
    frame = np.full((16, 16, 3), 128, dtype=np.uint8)
    out = apply_white_balance(frame)
    assert abs(int(out.mean()) - 128) <= 2
