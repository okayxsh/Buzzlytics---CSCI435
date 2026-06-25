"""
Frame annotation and overlay engine for the Buzzlytics CV Pipeline.

Draws bounding boxes, track trails, stats panels, and health
indicators on video frames for real-time monitoring visualization.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from numpy.typing import NDArray

from .detector import Detection
from .tracker import Track

logger = logging.getLogger(__name__)

# Default color map: BGR format for OpenCV drawing
DEFAULT_COLOR_MAP: Dict[str, Tuple[int, int, int]] = {
    "bee": (0, 200, 0),            # Green
    "pollen_bee": (0, 220, 255),   # Yellow (BGR)
    "varroa_bee": (0, 0, 220),     # Red
}


class Visualizer:
    """Draws detection and tracking overlays on video frames.

    Provides methods for rendering bounding boxes, class labels,
    confidence scores, track IDs, trajectory trails, statistical
    overlay panels, and health status indicators.

    Args:
        color_map: Optional custom mapping from class names to BGR
            color tuples. Defaults to the standard Buzzlytics palette.
    """

    def __init__(
        self,
        color_map: Optional[Dict[str, Tuple[int, int, int]]] = None,
    ) -> None:
        self.color_map: Dict[str, Tuple[int, int, int]] = (
            dict(DEFAULT_COLOR_MAP)
            if color_map is None
            else dict(color_map)
        )

        # Font settings
        self._font = cv2.FONT_HERSHEY_SIMPLEX
        self._font_scale = 0.5
        self._font_thickness = 1
        self._box_thickness = 2
        self._trail_thickness = 1
        self._max_trail_length = 60

    def _get_color(self, class_name: str) -> Tuple[int, int, int]:
        """Get the BGR color for a class name.

        Falls back to white if the class is not in the color map.

        Args:
            class_name: Name of the detection/tracking class.

        Returns:
            BGR color tuple.
        """
        return self.color_map.get(class_name, (255, 255, 255))

    def draw_detections(
        self,
        frame: NDArray[np.uint8],
        detections: List[Detection],
    ) -> NDArray[np.uint8]:
        """Draw bounding boxes with class labels and confidence scores.

        Args:
            frame: BGR frame to annotate (modified in place and returned).
            detections: List of Detection objects to render.

        Returns:
            Annotated BGR frame.
        """
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det.bbox]
            color = self._get_color(det.class_name)

            # Draw bounding box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                self._box_thickness,
            )

            # Draw label with class name and confidence
            label = f"{det.class_name} {det.confidence:.2f}"
            (text_w, text_h), baseline = cv2.getTextSize(
                label, self._font, self._font_scale, self._font_thickness
            )

            # Label background
            cv2.rectangle(
                frame,
                (x1, y1 - text_h - baseline - 4),
                (x1 + text_w, y1),
                color,
                -1,
            )

            # Label text (dark for visibility on colored bg)
            cv2.putText(
                frame,
                label,
                (x1, y1 - baseline - 2),
                self._font,
                self._font_scale,
                (0, 0, 0),
                self._font_thickness,
                cv2.LINE_AA,
            )

        return frame

    def draw_tracks(
        self,
        frame: NDArray[np.uint8],
        tracks: List[Track],
        track_histories: Optional[
            Dict[int, List[Tuple[float, float]]]
        ] = None,
    ) -> NDArray[np.uint8]:
        """Draw bounding boxes with track IDs and trailing trajectory lines.

        Args:
            frame: BGR frame to annotate (modified in place and returned).
            tracks: List of Track objects to render.
            track_histories: Optional dict mapping track IDs to lists of
                (cx, cy) center points for drawing motion trails.

        Returns:
            Annotated BGR frame.
        """
        for track in tracks:
            x1, y1, x2, y2 = [int(v) for v in track.bbox]
            color = self._get_color(track.class_name)

            # Draw bounding box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                self._box_thickness,
            )

            # Draw track ID label
            label = f"ID:{track.track_id} {track.class_name}"
            (text_w, text_h), baseline = cv2.getTextSize(
                label, self._font, self._font_scale, self._font_thickness
            )

            # Label background
            cv2.rectangle(
                frame,
                (x1, y1 - text_h - baseline - 4),
                (x1 + text_w, y1),
                color,
                -1,
            )

            # Label text
            cv2.putText(
                frame,
                label,
                (x1, y1 - baseline - 2),
                self._font,
                self._font_scale,
                (0, 0, 0),
                self._font_thickness,
                cv2.LINE_AA,
            )

        # Draw trajectory trails
        if track_histories is not None:
            for track_id, points in track_histories.items():
                if len(points) < 2:
                    continue

                # Limit trail length
                trail = points[-self._max_trail_length :]
                # Determine color from track class if available
                trail_color = (200, 200, 200)  # Default light gray
                for track in tracks:
                    if track.track_id == track_id:
                        trail_color = self._get_color(track.class_name)
                        break

                # Draw trail as connected line segments with fading
                for i in range(1, len(trail)):
                    pt1 = (int(trail[i - 1][0]), int(trail[i - 1][1]))
                    pt2 = (int(trail[i][0]), int(trail[i][1]))

                    # Fade: older segments are dimmer
                    alpha = i / len(trail)
                    faded_color = tuple(
                        int(c * alpha) for c in trail_color
                    )

                    cv2.line(
                        frame,
                        pt1,
                        pt2,
                        faded_color,
                        self._trail_thickness,
                        cv2.LINE_AA,
                    )

        return frame

    def draw_stats_overlay(
        self,
        frame: NDArray[np.uint8],
        summary: Dict[str, object],
    ) -> NDArray[np.uint8]:
        """Draw a semi-transparent stats panel in the top-left corner.

        Shows bee counts, health score, and rates from the analytics
        summary.

        Args:
            frame: BGR frame to annotate (modified in place and returned).
            summary: Summary dictionary from AnalyticsEngine.get_summary().

        Returns:
            Annotated BGR frame.
        """
        h, w = frame.shape[:2]

        # Panel dimensions
        panel_w = 220
        line_height = 22
        num_lines = 9
        panel_h = num_lines * line_height + 16

        # Create overlay for transparency
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (10, 10),
            (10 + panel_w, 10 + panel_h),
            (30, 30, 30),
            -1,
        )

        # Apply semi-transparent overlay
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Text lines
        lines = [
            f"Total Bees: {summary.get('total_bees', 0)}",
            f"Active: {summary.get('active_bees', 0)}",
            f"Pollen: {summary.get('pollen_bees', 0)}",
            f"Varroa: {summary.get('varroa_bees', 0)}",
            f"Health Score: {summary.get('health_score', 0)}",
            f"Status: {summary.get('health_status', 'N/A')}",
            f"Activity: {summary.get('activity_rate', 0):.1f}%",
            f"Infection: {summary.get('infection_rate', 0):.1f}%",
        ]

        y_offset = 10 + line_height
        for line in lines:
            cv2.putText(
                frame,
                line,
                (20, y_offset),
                self._font,
                self._font_scale,
                (255, 255, 255),
                self._font_thickness,
                cv2.LINE_AA,
            )
            y_offset += line_height

        return frame

    def draw_health_indicator(
        self,
        frame: NDArray[np.uint8],
        health_status: str,
    ) -> NDArray[np.uint8]:
        """Draw a colored health status indicator circle.

        Green for Healthy, Yellow for Warning, Red for Critical.

        Args:
            frame: BGR frame to annotate (modified in place and returned).
            health_status: One of "Healthy", "Warning", "Critical".

        Returns:
            Annotated BGR frame.
        """
        h, w = frame.shape[:2]

        # Position: top-right corner
        center = (w - 40, 40)
        radius = 18

        status_colors: Dict[str, Tuple[int, int, int]] = {
            "Healthy": (0, 200, 0),
            "Warning": (0, 220, 255),
            "Critical": (0, 0, 220),
        }

        color = status_colors.get(health_status, (160, 160, 160))

        # Draw filled circle with border
        cv2.circle(frame, center, radius, color, -1, cv2.LINE_AA)
        cv2.circle(frame, center, radius, (255, 255, 255), 2, cv2.LINE_AA)

        # Draw status text next to indicator
        cv2.putText(
            frame,
            health_status,
            (center[0] - radius - len(health_status) * 9, center[1] + 5),
            self._font,
            self._font_scale,
            (255, 255, 255),
            self._font_thickness,
            cv2.LINE_AA,
        )

        return frame

    def annotate_frame(
        self,
        frame: NDArray[np.uint8],
        tracks: Optional[List[Track]] = None,
        detections: Optional[List[Detection]] = None,
        track_histories: Optional[
            Dict[int, List[Tuple[float, float]]]
        ] = None,
        summary: Optional[Dict[str, object]] = None,
    ) -> NDArray[np.uint8]:
        """Master annotation method that applies all overlays.

        Draws detections, tracks, trails, stats panel, and health
        indicator on the frame. Each overlay is optional and will be
        skipped if the corresponding argument is None.

        Args:
            frame: BGR frame to annotate.
            tracks: Optional list of Track objects to draw.
            detections: Optional list of Detection objects to draw.
            track_histories: Optional trajectory histories for trails.
            summary: Optional analytics summary for the stats panel.

        Returns:
            Fully annotated BGR frame.
        """
        # Draw detections first (lower layer)
        if detections is not None:
            frame = self.draw_detections(frame, detections)

        # Draw tracks on top (with trails)
        if tracks is not None:
            frame = self.draw_tracks(frame, tracks, track_histories)

        # Stats text panel intentionally NOT drawn on the frame — the dashboard
        # UI already shows these metrics, and the overlay just clutters the video.
        if summary is not None:
            # Keep the small corner health indicator dot only.
            health_status = summary.get("health_status")
            if health_status is not None:
                frame = self.draw_health_indicator(frame, str(health_status))

        return frame
