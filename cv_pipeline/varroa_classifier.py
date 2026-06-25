"""
Stage-2 varroa classifier for the Buzzlytics CV pipeline.

The detector (stage 1) only boxes bees as ``bee`` / ``pollen_bee``. This
classifier runs on each detected bee crop and decides ``healthy`` vs
``varroa`` — because the varroa mite is tiny and only annotated as single-bee
classification crops (VarroaDataset), not as boxed bees in a scene. This is
the standard detect-then-classify design (cf. IntelliBeeHive / BeeAlarmed).

A YOLOv8 *classification* model (``yolov8n-cls``) is expected at the configured
weights path. If the weights are missing or ultralytics is unavailable, the
classifier is inert (``available == False``) and the pipeline simply never
upgrades a bee to varroa — detection still works.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

VARROA_LABEL = "varroa"


class VarroaClassifier:
    """Classify a single-bee crop as healthy vs varroa.

    Args:
        model_path: Path to a YOLOv8-cls weights file (``varroa_cls.pt``).
        conf_threshold: Minimum top-1 confidence to call a crop ``varroa``.
    """

    def __init__(
        self,
        model_path: str = "cv_pipeline/weights/varroa_cls.pt",
        conf_threshold: float = 0.5,
    ) -> None:
        self.conf_threshold = conf_threshold
        self._model = None

        try:
            from ultralytics import YOLO  # type: ignore[import-untyped]
        except ImportError:
            logger.warning(
                "ultralytics not installed; VarroaClassifier is disabled."
            )
            return

        if os.path.isfile(model_path):
            logger.info("Loading varroa classifier from: %s", model_path)
            self._model = YOLO(model_path)
        else:
            logger.info(
                "Varroa classifier weights not found at '%s'; varroa "
                "classification disabled (detection still works).",
                model_path,
            )

    @property
    def available(self) -> bool:
        """True when a classifier model is loaded and usable."""
        return self._model is not None

    def is_varroa(self, crop: NDArray[np.uint8]) -> bool:
        """Return True if the bee crop is classified as varroa-infected.

        Args:
            crop: BGR image of a single detected bee (any size; the model
                resizes internally). Empty/None crops return False.
        """
        if self._model is None or crop is None or crop.size == 0:
            return False
        if crop.ndim != 3 or min(crop.shape[:2]) < 2:
            return False

        results = self._model(crop, verbose=False)
        if not results:
            return False
        probs = getattr(results[0], "probs", None)
        if probs is None:
            return False

        top1 = int(probs.top1)
        conf = float(probs.top1conf)
        names = results[0].names
        name = names.get(top1) if hasattr(names, "get") else names[top1]
        return name == VARROA_LABEL and conf >= self.conf_threshold
