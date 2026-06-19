"""MOG2 background-subtraction motion detection with morphological cleanup.

Provides entrance-activity measurement for the Buzzlytics pipeline:
- cv2.BackgroundSubtractorMOG2 models the static hive background and
  flags moving bees as foreground (vision technique: change detection).
- Morphological opening then closing cleans the binary mask, removing
  speckle and merging fragmented blobs (vision technique: morphology).
The foreground fraction is a proxy for entrance traffic over time.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass
class MotionResult:
    mask: NDArray[np.uint8]
    activity_ratio: float
    blob_count: int


class MotionDetector:
    """MOG2 + morphology entrance-activity detector."""

    def __init__(self, history: int = 500, var_threshold: float = 16.0,
                 detect_shadows: bool = True, kernel_size: int = 3) -> None:
        self._bg = cv2.createBackgroundSubtractorMOG2(
            history=history, varThreshold=var_threshold,
            detectShadows=detect_shadows,
        )
        self._kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
        )

    def process(self, frame: NDArray[np.uint8]) -> MotionResult:
        if frame is None or getattr(frame, "size", 0) == 0:
            raise ValueError("Cannot process an empty frame")
        fg = self._bg.apply(frame)
        # MOG2 marks shadows as 127; keep only hard foreground (255).
        _, binary = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, self._kernel)
        cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, self._kernel)
        activity = float(np.count_nonzero(cleaned)) / cleaned.size
        n_labels, _ = cv2.connectedComponents(cleaned)
        return MotionResult(mask=cleaned, activity_ratio=activity,
                            blob_count=max(0, n_labels - 1))
