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
from .motion import MotionDetector
from .preprocess import preprocess_frame
from .tracker import BeeTracker, Track
from .visualize import Visualizer

logger = logging.getLogger(__name__)


class CVPipeline:
    """Full computer vision pipeline for beehive health monitoring.

    Orchestrates the complete processing chain:
        preprocess -> detect/track -> analyze -> visualize

    Can process individual frames for real-time streaming or entire
    video files with progress reporting.

    Args:
        model_path: Path to YOLOv8 weights file. If None, taken from
            config. If the file does not exist, the pretrained nano
            model is used as fallback.
        conf_threshold: Minimum confidence threshold for detections.
            If None, taken from config.
        use_tracker: Whether to enable multi-object tracking. When
            enabled, model.track() is the sole inference path (no
            separate detector.detect() call). When disabled, only
            detector.detect() is used.
        config: Optional pre-loaded config dict. If None, load_config()
            is called to read config.yaml (merged over defaults).
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        use_tracker: bool = True,
        config: Optional[Dict] = None,
    ) -> None:
        from .config import load_config

        cfg = config if config is not None else load_config()
        det = cfg["detector"]

        self.model_path = model_path if model_path is not None else det["model_path"]
        self.conf_threshold = (
            conf_threshold if conf_threshold is not None else det["conf_threshold"]
        )
        self.use_tracker = use_tracker

        # Convert color lists from YAML into BGR tuples for OpenCV.
        color_map = {
            name: tuple(bgr)
            for name, bgr in cfg["visualize"]["colors"].items()
        }

        imgsz = det.get("imgsz", 640)

        self.detector = BeeDetector(
            model_path=self.model_path,
            conf_threshold=self.conf_threshold,
            iou_threshold=det["iou_threshold"],
            imgsz=imgsz,
        )

        if use_tracker:
            trk = cfg["tracker"]
            self.tracker: Optional[BeeTracker] = BeeTracker(
                conf_threshold=self.conf_threshold,
                iou_threshold=det["iou_threshold"],
                imgsz=imgsz,
                track_buffer=trk.get("track_buffer", 30),
                match_thresh=trk.get("match_thresh", 0.8),
            )
        else:
            self.tracker = None

        self.analytics = AnalyticsEngine(config=cfg)
        self.visualizer = Visualizer(color_map=color_map)
        self.motion = MotionDetector(**cfg["motion"])
        pp = cfg["preprocess"]
        self._white_balance = pp["white_balance"]
        self._clahe_clip = pp["clahe_clip_limit"]
        self._denoise_strength = pp["denoise_strength"]

        # frame_skip: process every Nth frame; <=1 means every frame
        self._frame_skip: int = max(1, int(cfg.get("video", {}).get("frame_skip", 1)))

    def process_frame(
        self,
        frame: NDArray[np.uint8],
    ) -> Dict[str, object]:
        """Process a single frame through the full pipeline.

        Executes the complete chain: preprocess -> detect OR track ->
        analyze -> visualize.

        When the tracker is enabled, model.track() is the SOLE inference
        path — detector.detect() is NOT called, eliminating the previous
        double-inference bug.

        Args:
            frame: Input BGR frame (HxWxC numpy array).

        Returns:
            Dictionary with the following keys:
                - annotated_frame: BGR frame with all overlays drawn.
                - tracks: List of Track objects (empty if tracker is
                    disabled).
                - detections: List of Detection objects from the
                    current frame (empty when tracker is active).
                - summary: Analytics summary dictionary.
                - motion: Dict with activity_ratio and blob_count.

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
        processed = preprocess_frame(
            frame,
            white_balance=self._white_balance,
            clip_limit=self._clahe_clip,
            denoise_strength=self._denoise_strength,
        )

        # Step 1b: Motion detection
        motion_result = self.motion.process(processed)

        # Step 2: Single inference path — either track OR detect, never both
        detections: List[Detection] = []
        tracks: List[Track] = []
        track_histories: Optional[Dict[int, List]] = None

        if self.tracker is not None:
            # Tracker is the sole inference path (model.track() inside)
            tracks = self.tracker.update(processed, self.model_path)
            track_histories = self.tracker.get_track_histories()
            # detections stays empty — analytics/visualize use tracks
        else:
            # Detection-only path
            detections = self.detector.detect(processed)

        # Step 3: Analyze
        self.analytics.update(tracks if tracks else [])
        summary = self.analytics.get_summary()

        # Step 4: Visualize
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
            "motion": {
                "activity_ratio": motion_result.activity_ratio,
                "blob_count": motion_result.blob_count,
            },
        }

    def process_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
    ) -> Generator[Dict[str, object], None, Dict[str, object]]:
        """Process an entire video file through the pipeline.

        Processes each frame sequentially and yields progress
        information after each frame. Frames at indices where
        ``idx % frame_skip != 0`` are skipped: the previous annotated
        frame and summary are reused for the output video and progress
        yields. ``frame_skip <= 1`` means every frame is processed.

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
                - timeline: Per-frame activity list.

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
            cap.release()
            raise ValueError(
                f"Could not open video (corrupt/unsupported): {video_path}"
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
        timeline: List[Dict[str, object]] = []
        frame_number = 0
        final_summary: Dict[str, object] = {}

        # Seed with a blank result so skipped frames before first
        # processed frame have something to reuse
        last_result: Optional[Dict[str, object]] = None

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # frame_skip: only process every Nth frame
                if self._frame_skip > 1 and frame_number % self._frame_skip != 0:
                    # Reuse the previous frame's result
                    if last_result is not None:
                        result = last_result
                    else:
                        # Edge case: haven't processed even one frame yet;
                        # force process this frame to seed last_result
                        result = self.process_frame(frame)
                        last_result = result
                else:
                    result = self.process_frame(frame)
                    last_result = result

                # Record bee count
                total_bees = result["summary"].get("total_bees", 0)
                bee_counts.append(int(total_bees))

                # Accumulate activity timeline
                timeline.append({
                    "frame": frame_number,
                    "activity_ratio": result["motion"]["activity_ratio"],
                    "total_bees": int(total_bees),
                })

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
            "timeline": timeline,
        }

    def reset(self) -> None:
        """Reset all pipeline state including tracker and analytics."""
        if self.tracker is not None:
            self.tracker.reset()
        self.analytics.reset()
        logger.info("CV Pipeline state reset.")
