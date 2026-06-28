"""YOLO-based close-up Varroa mite detector.

This is separate from the entrance bee/pollen detector. It expects close-up
single-bee images and predicts mite boxes directly when trained detection
weights are available.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass
class MiteDetection:
    bbox: List[float]
    confidence: float
    class_id: int
    class_name: str


class VarroaMiteDetector:
    """Detect mite boxes in close-up bee crop images."""

    def __init__(
        self,
        model_path: str = "cv_pipeline/weights/varroa_det.pt",
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.45,
        imgsz: int = 960,
    ) -> None:
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        self._model = None

        try:
            from ultralytics import YOLO  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("ultralytics not installed; VarroaMiteDetector is disabled.")
            return

        if os.path.isfile(model_path):
            logger.info("Loading varroa mite detector from: %s", model_path)
            self._model = YOLO(model_path)
        else:
            logger.info(
                "Varroa detector weights not found at '%s'; falling back to classifier.",
                model_path,
            )

    @property
    def available(self) -> bool:
        return self._model is not None

    def detect(self, frame: NDArray[np.uint8]) -> List[MiteDetection]:
        if self._model is None or frame is None or frame.size == 0:
            return []
        if frame.ndim != 3:
            return []

        results = self._model(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            verbose=False,
        )

        detections: List[MiteDetection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            names: Dict[int, str] = getattr(result, "names", {}) or {}
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                name = names.get(cls_id, "mite") if hasattr(names, "get") else "mite"
                detections.append(
                    MiteDetection(
                        bbox=[x1, y1, x2, y2],
                        confidence=conf,
                        class_id=cls_id,
                        class_name=str(name),
                    )
                )
        return detections
