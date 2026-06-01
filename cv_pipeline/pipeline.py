"""
Central orchestration module for the Buzzlytics CV Pipeline.

Coordinates preprocessing, detection, tracking, analytics, and
visualization into a unified processing pipeline for both single
frames and full video files.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Generator, List, Optional

import cv2
import numpy as np
from numpy.typing import NDArray

from .analytics import AnalyticsEngine
from .detector import BeeDetector, Detection
from .preprocess import preprocess_frame
from .tracker import BeeTracker, Track
from .visualize import Visualizer

logger = logging.getLogger(__name__)


class CVPipeline:
    """Full computer vision pipeline for beehive health monitoring.

    Orchestrates the complete processing chain:
        preprocess -> detect -> track -> analyze -> visualize

    Can process individual frames for real-time streaming or entire
    video files with progress reporting.

    Args:
        model_path: Path to YOLOv8 weights file. If the file does not
            exist, the pretrained nano model is used as fallback.
        conf_threshold: Minimum confidence threshold for detections.
        use_tracker: Whether to enable multi-object tracking. When
            disabled, only detection results are used.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf_threshold: float = 0.25,
        use_tracker: bool = True,
    ) -> None:
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.use_tracker = use_tracker

        # Initialize sub-modules
        self.detector = BeeDetector(
            model_path=model_path,
            conf_threshold=conf_threshold,
        )
        self.tracker = BeeTracker() if use_tracker else None
        self.analytics = AnalyticsEngine()
        self.visualizer = Visualizer()

    def process_frame(
        self,
        frame: NDArray[np.uint8],
    ) -> Dict[str, object]:
        """Process a single frame through the full pipeline.

        Executes the complete chain: preprocess -> detect -> track ->
        analyze -> visualize.

        Args:
            frame: Input BGR frame (HxWxC numpy array).

        Returns:
            Dictionary with the following keys:
                - annotated_frame: BGR frame with all overlays drawn.
                - tracks: List of Track objects (empty if tracker is
                    disabled).
                - detections: List of Detection objects from the
                    current frame.
                - summary: Analytics summary dictionary.

        Raises:
            ValueError: If the frame is empty or invalid.
            TypeError: If the frame is not a numpy array.
        """
        if not isinstance(frame, np.ndarray):
            raise TypeError(
                f"Expected numpy array, got {type(frame).__name__}"
            )

        if frame.size == 0:
            raise ValueError("Cannot process an empty frame")

        # Step 1: Preprocess
        processed = preprocess_frame(frame)

        # Step 2: Detect
        detections: List[Detection] = self.detector.detect(processed)

        # Step 3: Track
        tracks: List[Track] = []
        track_histories: Optional[Dict[int, List]] = None

        if self.tracker is not None:
            tracks = self.tracker.update(detections, processed, self.model_path)
            track_histories = self.tracker.get_track_histories()

        # Step 4: Analyze
        self.analytics.update(tracks if tracks else [])
        summary = self.analytics.get_summary()

        # Step 5: Visualize
        annotated = self.visualizer.annotate_frame(
            frame=processed,
            tracks=tracks if tracks else None,
            detections=detections if detections else None,
            track_histories=track_histories,
            summary=summary,
        )

        return {
            "annotated_frame": annotated,
            "tracks": tracks,
            "detections": detections,
            "summary": summary,
        }

    def process_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
    ) -> Generator[Dict[str, object], None, Dict[str, object]]:
        """Process an entire video file through the pipeline.

        Processes each frame sequentially and yields progress
        information after each frame. The generator returns a final
        results dictionary when exhausted.

        Args:
            video_path: Path to the input video file.
            output_path: Optional path for the annotated output video.
                If None, no output video is written.

        Yields:
            Dictionary with progress information:
                - frame_number: Current frame index (0-based).
                - total_frames: Total number of frames in the video.
                - progress: Progress fraction in [0, 1].

        Returns:
            Final results dictionary with:
                - total_frames: Total number of frames processed.
                - avg_bees: Average bee count across all frames.
                - final_summary: Analytics summary from the last frame.
                - output_path: Path to the output video (or None).

        Raises:
            FileNotFoundError: If the video file does not exist.
            ValueError: If the video cannot be opened.
        """
        if not os.path.isfile(video_path):
            raise FileNotFoundError(
                f"Video file not found: {video_path}"
            )

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(
                f"Cannot open video file: {video_path}"
            )

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0

        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Set up video writer if output path is specified
        writer: Optional[cv2.VideoWriter] = None
        if output_path is not None:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(
                output_path, fourcc, fps, (frame_w, frame_h)
            )

        bee_counts: List[int] = []
        frame_number = 0
        final_summary: Dict[str, object] = {}

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Process the frame
                result = self.process_frame(frame)

                # Record bee count
                total_bees = result["summary"].get("total_bees", 0)
                bee_counts.append(int(total_bees))

                final_summary = result["summary"]

                # Write annotated frame to output video
                if writer is not None:
                    writer.write(result["annotated_frame"])

                frame_number += 1

                # Yield progress
                progress = frame_number / total_frames if total_frames > 0 else 1.0
                yield {
                    "frame_number": frame_number - 1,
                    "total_frames": total_frames,
                    "progress": progress,
                }
        finally:
            cap.release()
            if writer is not None:
                writer.release()

        # Compute average bees
        avg_bees = 0.0
        if bee_counts:
            avg_bees = sum(bee_counts) / len(bee_counts)

        return {
            "total_frames": frame_number,
            "avg_bees": round(avg_bees, 2),
            "final_summary": final_summary,
            "output_path": output_path,
        }

    def reset(self) -> None:
        """Reset all pipeline state including tracker and analytics."""
        if self.tracker is not None:
            self.tracker.reset()
        self.analytics.reset()
        logger.info("CV Pipeline state reset.")
