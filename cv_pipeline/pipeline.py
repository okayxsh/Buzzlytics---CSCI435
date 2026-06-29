"""
Central orchestration module for the Buzzlytics CV Pipeline.

Coordinates preprocessing, detection, tracking, analytics, and
visualization into a unified processing pipeline for both single
frames and full video files.
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict, deque
from typing import Dict, Generator, List, Optional

import cv2
import imageio.v2 as imageio
import numpy as np
from numpy.typing import NDArray

from .analytics import AnalyticsEngine
from .detector import BeeDetector, Detection
from .motion import MotionDetector
from .preprocess import preprocess_frame
from .tracker import BeeTracker, Track
from .varroa_classifier import VarroaClassifier
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
        self._pollen_min_conf = float(det.get("pollen_min_conf", 0.55))

        # Convert color lists from YAML into BGR tuples for OpenCV.
        color_map = {
            name: tuple(bgr)
            for name, bgr in cfg["visualize"]["colors"].items()
        }

        imgsz = det.get("imgsz", 640)
        self._min_box_width = float(det.get("min_box_width", 0))
        self._min_box_height = float(det.get("min_box_height", 0))
        self._min_box_area_pct = float(det.get("min_box_area_pct", 0.0))
        self._max_box_aspect_ratio = float(det.get("max_box_aspect_ratio", 0.0))

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
                track_high_thresh=trk.get("track_high_thresh", self.conf_threshold),
                track_low_thresh=trk.get("track_low_thresh", 0.1),
                new_track_thresh=trk.get("new_track_thresh", self.conf_threshold),
            )
        else:
            self.tracker = None

        self.analytics = AnalyticsEngine(config=cfg)
        viz = cfg.get("visualize", {})
        self.visualizer = Visualizer(
            color_map=color_map,
            draw_trails=bool(viz.get("draw_trails", True)),
            max_trail_length=int(viz.get("max_trail_length", 60)),
        )
        self.motion = MotionDetector(**cfg["motion"])

        # Stage-2 varroa classifier (per-bee healthy/varroa). Inert if the
        # weights are missing — detection still works.
        vc = cfg.get("varroa_classifier", {})
        self.varroa_classifier: Optional[VarroaClassifier] = (
            VarroaClassifier(
                model_path=vc.get(
                    "model_path", "cv_pipeline/weights/varroa_cls.pt"
                ),
                conf_threshold=vc.get("conf_threshold", 0.5),
            )
            if vc.get("enabled", True)
            else None
        )
        self._varroa_min_crop_size = int(vc.get("min_crop_size", 2))
        self._varroa_min_track_hits = max(1, int(vc.get("min_track_hits", 1)))
        self._varroa_vote_window = max(
            self._varroa_min_track_hits, int(vc.get("vote_window", 1))
        )
        self._varroa_votes = defaultdict(
            lambda: deque(maxlen=self._varroa_vote_window)
        )
        pp = cfg["preprocess"]
        self._white_balance = pp["white_balance"]
        self._clahe_clip = pp["clahe_clip_limit"]
        self._denoise_strength = pp["denoise_strength"]

        # frame_skip: process every Nth frame; <=1 means every frame
        vid_cfg = cfg.get("video", {})
        self._frame_skip: int = max(1, int(vid_cfg.get("frame_skip", 1)))
        # Cap how much of an uploaded video gets processed (seconds). 0/None
        # means no cap. Keeps CPU processing time bounded on long uploads.
        self._max_seconds: float = float(vid_cfg.get("max_seconds", 10) or 0)

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

        # Step 1: Preprocess — used ONLY for motion detection. The detector
        # was fine-tuned on raw images, so feeding it CLAHE/white-balanced
        # frames hurts recall (~30% fewer detections in testing). Detection
        # and tracking therefore run on the RAW frame.
        processed = preprocess_frame(
            frame,
            white_balance=self._white_balance,
            clip_limit=self._clahe_clip,
            denoise_strength=self._denoise_strength,
        )

        # Step 1b: Motion detection (on the stabilised/preprocessed frame)
        motion_result = self.motion.process(processed)

        # Step 2: Single inference path — either track OR detect, never both.
        # Run on the RAW frame to match the model's training distribution.
        detections: List[Detection] = []
        tracks: List[Track] = []
        track_histories: Optional[Dict[int, List]] = None

        if self.tracker is not None:
            # Tracker is the sole inference path (model.track() inside)
            tracks = self.tracker.update(frame, self.model_path)
            tracks = self._filter_objects(tracks, frame.shape[:2])
            track_histories = self.tracker.get_track_histories()
            # detections stays empty — analytics/visualize use tracks
        else:
            # Detection-only path
            detections = self.detector.detect(frame)
            detections = self._filter_objects(detections, frame.shape[:2])

        # Step 2b: demote low-confidence pollen_bee -> bee. Pollen is the
        # minority/hard class and over-fires on out-of-domain bees; requiring
        # higher confidence removes most false-positive pollen labels.
        self._gate_pollen(tracks if tracks else detections)

        # Step 2c: per-bee varroa classification (stage 2). Crop each detected
        # bee from the ORIGINAL frame and upgrade its label to "varroa_bee"
        # when the classifier flags infection. Operates in-place on the
        # tracks/detections so analytics + visualize pick it up unchanged.
        if self.varroa_classifier is not None and self.varroa_classifier.available:
            objs = tracks if tracks else detections
            self._classify_varroa(frame, objs)

        # Step 3: Analyze
        # When the tracker is off (image mode), tracks is [] but detections
        # holds the raw detector output — pass those instead so analytics
        # produces non-zero counts for single-frame analysis.
        self.analytics.update(tracks if tracks else detections)
        summary = self.analytics.get_summary()

        # Step 4: Visualize on the RAW frame (not the CLAHE-preprocessed one)
        # so the output video keeps natural colour and skipped frames don't
        # flicker in brightness.
        annotated = self.visualizer.annotate_frame(
            frame=frame,
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

    def _gate_pollen(self, objs: List) -> None:
        """Demote pollen_bee detections below the pollen confidence floor to bee.

        Mutates ``class_name``/``class_id`` in place. Objects must have
        ``confidence``, ``class_name`` and ``class_id`` attributes.
        """
        for obj in objs:
            if (
                obj.class_name == "pollen_bee"
                and obj.confidence < self._pollen_min_conf
            ):
                obj.class_name = "bee"
                obj.class_id = 0

    def _classify_varroa(self, frame: NDArray[np.uint8], objs: List) -> None:
        """Upgrade detected bees to 'varroa_bee' via the stage-2 classifier.

        Crops each bee/pollen_bee box from the original frame, classifies it,
        and mutates ``class_name`` in place when varroa is detected.

        Args:
            frame: Original BGR frame (box coords are in this frame's space).
            objs: List of Track or Detection objects (have bbox + class_name).
        """
        h, w = frame.shape[:2]
        for obj in objs:
            if obj.class_name not in ("bee", "pollen_bee"):
                continue
            x1, y1, x2, y2 = (int(round(v)) for v in obj.bbox)
            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w))
            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h))
            if (
                x2 - x1 < self._varroa_min_crop_size
                or y2 - y1 < self._varroa_min_crop_size
            ):
                continue
            is_varroa = self.varroa_classifier.is_varroa(frame[y1:y2, x1:x2])
            track_id = getattr(obj, "track_id", None)
            if track_id is not None:
                votes = self._varroa_votes[int(track_id)]
                votes.append(is_varroa)
                is_varroa = sum(votes) >= self._varroa_min_track_hits
            if is_varroa:
                obj.class_name = "varroa_bee"

    def _filter_objects(self, objs: List, frame_hw: tuple[int, int]) -> List:
        """Drop implausible boxes that are common on wood grain clutter."""
        if not objs:
            return objs

        frame_h, frame_w = frame_hw
        min_area = self._min_box_area_pct * float(frame_w * frame_h)
        out = []
        for obj in objs:
            x1, y1, x2, y2 = [float(v) for v in obj.bbox]
            bw = max(0.0, x2 - x1)
            bh = max(0.0, y2 - y1)
            if bw < self._min_box_width or bh < self._min_box_height:
                continue
            if min_area > 0 and bw * bh < min_area:
                continue
            if self._max_box_aspect_ratio > 0 and bw > 0 and bh > 0:
                aspect = max(bw / bh, bh / bw)
                if aspect > self._max_box_aspect_ratio:
                    continue
            out.append(obj)
        return out

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

        # Cap processing to the first ``max_seconds`` of footage (0 = no cap).
        max_frames = int(fps * self._max_seconds) if self._max_seconds else 0
        if max_frames and (total_frames <= 0 or max_frames < total_frames):
            total_frames = max_frames

        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Set up video writer if output path is specified
        writer = None
        if output_path is not None:
            writer = imageio.get_writer(
                output_path, fps=fps, codec="libx264", macro_block_size=8,
                output_params=["-preset", "ultrafast"],  # faster CPU encode
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
                if max_frames and frame_number >= max_frames:
                    break  # reached the max_seconds cap
                ret, frame = cap.read()
                if not ret:
                    break

                # frame_skip: only run inference on every Nth frame, BUT still
                # emit every frame so the output video stays smooth. On skipped
                # frames we redraw the last-known boxes onto the *current* frame
                # (cheap, no inference) instead of repeating the old frame —
                # otherwise motion freezes for N frames and looks choppy.
                if (
                    self._frame_skip > 1
                    and frame_number % self._frame_skip != 0
                    and last_result is not None
                ):
                    annotated = self.visualizer.annotate_frame(
                        frame=frame,
                        tracks=last_result["tracks"] or None,
                        detections=last_result["detections"] or None,
                        summary=last_result["summary"],
                    )
                    result = {**last_result, "annotated_frame": annotated}
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

                # Write annotated frame to output video (imageio expects RGB)
                if writer is not None:
                    writer.append_data(cv2.cvtColor(result["annotated_frame"], cv2.COLOR_BGR2RGB))

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
                writer.close()

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
        self._varroa_votes.clear()
        self.analytics.reset()
        logger.info("CV Pipeline state reset.")
