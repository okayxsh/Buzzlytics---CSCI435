"""
Image enhancement module for the Buzzlytics CV Pipeline.

Provides CLAHE-based shadow/illumination correction and denoising
capabilities optimized for beehive monitoring footage.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np
from numpy.typing import NDArray


def apply_clahe(
    frame: NDArray[np.uint8],
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
) -> NDArray[np.uint8]:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to a frame.

    Converts the frame to LAB color space, applies CLAHE to the L channel,
    and converts back to BGR. This corrects for uneven illumination and
    shadow areas common in beehive monitoring footage.

    Args:
        frame: Input BGR frame (HxWxC numpy array).
        clip_limit: Threshold for contrast limiting. Higher values give more
            contrast enhancement. Defaults to 2.0.
        tile_grid_size: Size of the grid for histogram equalization.
            Defaults to (8, 8).

    Returns:
        CLAHE-enhanced BGR frame of the same shape and dtype as input.

    Raises:
        ValueError: If the frame is empty or has an unexpected shape.
        TypeError: If the frame is not a numpy array.
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(
            f"Expected numpy array, got {type(frame).__name__}"
        )

    if frame.size == 0:
        raise ValueError("Cannot apply CLAHE to an empty frame")

    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(
            f"Expected 3-channel BGR frame, got shape {frame.shape}"
        )

    # Convert to LAB color space
    lab: NDArray[np.uint8] = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    # Split channels and apply CLAHE to L channel only
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=clip_limit, tileGridSize=tile_grid_size
    )
    l_enhanced: NDArray[np.uint8] = clahe.apply(l_channel)

    # Merge back and convert to BGR
    lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
    enhanced: NDArray[np.uint8] = cv2.cvtColor(
        lab_enhanced, cv2.COLOR_LAB2BGR
    )

    return enhanced


def denoise(
    frame: NDArray[np.uint8],
    strength: int = 10,
) -> NDArray[np.uint8]:
    """Apply fast Non-Local Means denoising to a frame.

    Reduces sensor noise and compression artifacts while preserving
    edges and fine details important for bee detection.

    Args:
        frame: Input BGR frame (HxWxC numpy array).
        strength: Denoising strength. Higher values remove more noise
            but may blur fine details. Recommended range 3-15.
            Defaults to 10.

    Returns:
        Denoised BGR frame of the same shape and dtype as input.

    Raises:
        ValueError: If the frame is empty.
        TypeError: If the frame is not a numpy array.
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(
            f"Expected numpy array, got {type(frame).__name__}"
        )

    if frame.size == 0:
        raise ValueError("Cannot denoise an empty frame")

    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(
            f"Expected 3-channel BGR frame, got shape {frame.shape}"
        )

    # fastNlMeansDenoisingColored parameters:
    # h: luminance denoising strength
    # hColor: chroma denoising strength (typically smaller)
    # templateWindowSize: odd, recommended 7
    # searchWindowSize: odd, recommended 21
    result: NDArray[np.uint8] = cv2.fastNlMeansDenoisingColored(
        src=frame,
        dst=None,
        h=strength,
        hColor=strength,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    return result


def preprocess_frame(
    frame: NDArray[np.uint8],
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
    denoise_strength: int = 10,
) -> NDArray[np.uint8]:
    """Full preprocessing pipeline for a beehive monitoring frame.

    Applies denoising first to remove sensor noise, then CLAHE to
    correct for uneven illumination. This order prevents noise
    amplification that can occur if CLAHE is applied to noisy data.

    Args:
        frame: Input BGR frame (HxWxC numpy array).
        clip_limit: CLAHE clip limit. Defaults to 2.0.
        tile_grid_size: CLAHE grid size. Defaults to (8, 8).
        denoise_strength: Denoising strength. Defaults to 10.

    Returns:
        Preprocessed BGR frame of the same shape and dtype as input.

    Raises:
        ValueError: If the frame is empty or has wrong shape.
        TypeError: If the frame is not a numpy array.
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(
            f"Expected numpy array, got {type(frame).__name__}"
        )

    if frame.size == 0:
        raise ValueError("Cannot preprocess an empty frame")

    # Step 1: Denoise to remove sensor noise
    denoised: NDArray[np.uint8] = denoise(
        frame, strength=denoise_strength
    )

    # Step 2: Apply CLAHE for illumination correction
    enhanced: NDArray[np.uint8] = apply_clahe(
        denoised, clip_limit=clip_limit, tile_grid_size=tile_grid_size
    )

    return enhanced
