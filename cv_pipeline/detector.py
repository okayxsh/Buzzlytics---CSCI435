"""
YOLOv8-based object detector for the Buzzlytics CV Pipeline.

Detects four bee-related classes in beehive monitoring footage:
bee, pollen_bee, varroa_bee, and wasp.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

# Class ID to class name mapping for the bee detection model
BEE_CLASS_NAMES: Dict[int, str] = {
    0: "bee",
    1: "pollen_bee",
    2: "varroa_bee",
    3: "wasp",
}


@dataclass
class Detection:
    """Represents a single object detection result.

    Attributes:
        bbox: Bounding box as [x1, y1, x2, y2] in pixel coordinates.
        confidence: Detection confidence score in [0, 1].
        class_id: Integer class identifier.
        class_name: Human-readable class name.
    """

    bbox: List[float]
    confidence: float
    class_id: int
    class_name: str


class BeeDetector:
    """YOLOv8-based detector for bee-related objects.

    Loads a YOLOv8 model and runs inference on video frames to detect
    four classes of interest in beehive monitoring: bee,
    pollen_bee, varroa_bee, and wasp.

    If a custom model file exists at the specified path, it will be
    loaded. Otherwise, the pretrained YOLOv8 nano model is used as a
    fallback (which detects generic 80 COCO classes until fine-tuned).

    Args:
        model_path: Path to a custom YOLOv8 weights file. If the file
            does not exist, falls back to the pretrained nano model.
        conf_threshold: Minimum confidence threshold for detections.
        iou_threshold: IoU threshold for Non-Maximum Suppression.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ) -> None:
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.class_names: Dict[int, str] = dict(BEE_CLASS_NAMES)
        self._model = None

        try:
            from ultralytics import YOLO  # type: ignore[import-untyped]
        except ImportError:
            logger.warning(
                "ultralytics is not installed. BeeDetector will not "
                "be functional. Install with: pip install ultralytics"
            )
            self._model = None
            return

        # Load custom model if it exists; otherwise use pretrained nano
        if os.path.isfile(model_path):
            logger.info("Loading custom model from: %s", model_path)
            self._model = YOLO(model_path)
        else:
            logger.info(
                "Custom model not found at '%s'. Falling back to "
                "pretrained YOLOv8n model.",
                model_path,
            )
            self._model = YOLO("yolov8n.pt")

    def detect(self, frame: NDArray[np.uint8]) -> List[Detection]:
        """Run object detection on a single frame.

        Args:
            frame: Input BGR frame (HxWxC numpy array).

        Returns:
            List of Detection objects, each containing bounding box,
            confidence, class ID, and class name.

        Raises:
            ValueError: If the frame is empty or has wrong dimensions.
            RuntimeError: If the model is not loaded (ultralytics missing).
        """
        if not isinstance(frame, np.ndarray):
            raise TypeError(
                f"Expected numpy array, got {type(frame).__name__}"
            )

        if frame.size == 0:
            raise ValueError("Cannot detect on an empty frame")

        if self._model is None:
            raise RuntimeError(
                "Model is not loaded. Ensure ultralytics is installed "
                "and the model path is valid."
            )

        # Run YOLOv8 inference
        results = self._model(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False,
        )

        detections: List[Detection] = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())

                # Map class ID to name; use class_names for custom model,
                # or fall back to the model's own names dictionary
                if class_id in self.class_names:
                    class_name = self.class_names[class_id]
                elif (
                    hasattr(result, "names")
                    and class_id in result.names
                ):
                    class_name = result.names[class_id]
                else:
                    class_name = f"class_{class_id}"

                detection = Detection(
                    bbox=[x1, y1, x2, y2],
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                )
                detections.append(detection)

        return detections

    def get_class_names(self) -> Dict[int, str]:
        """Return the mapping of class IDs to class names.

        Returns:
            Dictionary mapping integer class IDs to string class names.
        """
        return dict(self.class_names)
