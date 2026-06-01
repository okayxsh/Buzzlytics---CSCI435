"""
ByteTrack-based multi-object tracker for the Buzzlytics CV Pipeline.

Tracks detected bees across video frames, assigning persistent IDs
and maintaining trajectory histories for activity analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from numpy.typing import NDArray

from .detector import Detection, BEE_CLASS_NAMES

logger = logging.getLogger(__name__)


@dataclass
class Track:
    """Represents a tracked object across frames.

    Attributes:
        track_id: Unique persistent identifier for this track.
        bbox: Bounding box as [x1, y1, x2, y2] in pixel coordinates.
        confidence: Detection confidence score in [0, 1].
        class_id: Integer class identifier.
        class_name: Human-readable class name.
        age: Number of frames this track has been alive.
    """

    track_id: int
    bbox: List[float]
    confidence: float
    class_id: int
    class_name: str
    age: int


class BeeTracker:
    """ByteTrack-based multi-object tracker for bee monitoring.

    Uses the ultralytics YOLO tracking interface with ByteTrack to
    maintain persistent track IDs across frames. Keeps a history of
    center positions for each track to support trajectory visualization.

    Args:
        tracker_type: Tracker configuration file name. Defaults to
            "bytetrack.yaml".
        max_age: Maximum number of frames a track can survive without
            a matching detection before being deleted.
        min_hits: Minimum number of matching detections before a track
            is considered confirmed.
        iou_threshold: IoU threshold for track-detection association.
    """

    def __init__(
        self,
        tracker_type: str = "bytetrack.yaml",
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3,
    ) -> None:
        self.tracker_type = tracker_type
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self._model = None
        self._track_histories: Dict[int, List[Tuple[float, float]]] = {}
        self._track_ages: Dict[int, int] = {}

        try:
            from ultralytics import YOLO  # type: ignore[import-untyped]
        except ImportError:
            logger.warning(
                "ultralytics is not installed. BeeTracker will not "
                "be functional. Install with: pip install ultralytics"
            )
            self._model = None
            return

    def _ensure_model(self, model_path: str = "yolov8n.pt") -> None:
        """Lazily initialize the YOLO model for tracking.

        The model is loaded on first use so that the tracker can be
        constructed without an immediate dependency on model weights.

        Args:
            model_path: Path to YOLOv8 weights file.
        """
        if self._model is not None:
            return

        try:
            from ultralytics import YOLO  # type: ignore[import-untyped]

            import os

            if os.path.isfile(model_path):
                self._model = YOLO(model_path)
            else:
                self._model = YOLO("yolov8n.pt")

            logger.info("Tracker model loaded from: %s", model_path)
        except ImportError:
            logger.error(
                "ultralytics is not installed. Cannot initialize tracker."
            )
            self._model = None

    def update(
        self,
        detections: List[Detection],
        frame: NDArray[np.uint8],
        model_path: str = "yolov8n.pt",
    ) -> List[Track]:
        """Update tracks with new detections and the current frame.

        Uses the ultralytics model.track() approach to run detection
        and tracking jointly on the frame. Existing detection results
        are used to augment the tracked output with class information.

        Args:
            detections: List of Detection objects from the current frame.
            frame: Current BGR video frame.
            model_path: Path to YOLOv8 weights for the tracker model.

        Returns:
            List of Track objects with persistent IDs and trajectory
            information.

        Raises:
            ValueError: If the frame is empty.
            RuntimeError: If the tracker model cannot be loaded.
        """
        if not isinstance(frame, np.ndarray):
            raise TypeError(
                f"Expected numpy array, got {type(frame).__name__}"
            )

        if frame.size == 0:
            raise ValueError("Cannot track on an empty frame")

        self._ensure_model(model_path)

        if self._model is None:
            raise RuntimeError(
                "Tracker model is not loaded. Ensure ultralytics is "
                "installed and the model path is valid."
            )

        tracks: List[Track] = []

        # Use ultralytics tracking with ByteTrack
        results = self._model.track(
            frame,
            persist=True,
            tracker=self.tracker_type,
            conf=0.25,
            iou=self.iou_threshold,
            verbose=False,
        )

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                # Get track ID; skip if not assigned
                if box.id is None:
                    continue

                track_id = int(box.id[0].cpu().numpy())
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())

                # Map class name
                if class_id in BEE_CLASS_NAMES:
                    class_name = BEE_CLASS_NAMES[class_id]
                elif (
                    hasattr(result, "names")
                    and class_id in result.names
                ):
                    class_name = result.names[class_id]
                else:
                    class_name = f"class_{class_id}"

                # Compute center point for trajectory
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0

                # Update track history
                if track_id not in self._track_histories:
                    self._track_histories[track_id] = []
                self._track_histories[track_id].append((cx, cy))

                # Update track age
                self._track_ages[track_id] = (
                    self._track_ages.get(track_id, 0) + 1
                )

                track = Track(
                    track_id=track_id,
                    bbox=[x1, y1, x2, y2],
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    age=self._track_ages[track_id],
                )
                tracks.append(track)

        return tracks

    def get_track_histories(
        self,
    ) -> Dict[int, List[Tuple[float, float]]]:
        """Return trajectory histories for all active tracks.

        Returns:
            Dictionary mapping track IDs to lists of (cx, cy) center
            point tuples representing the trajectory of each tracked
            object across frames.
        """
        return dict(self._track_histories)

    def reset(self) -> None:
        """Reset all tracker state including track histories and ages."""
        self._track_histories.clear()
        self._track_ages.clear()

        # Reset the model tracking state by reloading
        if self._model is not None:
            self._model = None
