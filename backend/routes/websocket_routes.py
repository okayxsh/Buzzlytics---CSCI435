"""WebSocket routes for live webcam streaming in Buzzlytics API.

Provides a WebSocket endpoint that accepts base64-encoded JPEG frames from
a client's webcam, processes each frame through the computer vision pipeline,
and returns the annotated frame along with a summary of detected analytics.
Supports multiple concurrent connections via a ConnectionManager.
"""

import base64
import json
import sys
from pathlib import Path
from typing import Dict, Set

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Add the parent directory to sys.path so cv_pipeline can be imported
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cv_pipeline import CVPipeline

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages active WebSocket connections for webcam streaming.

    Tracks connected clients and their associated CV pipeline instances,
    enabling multiple concurrent webcam sessions.
    """

    def __init__(self) -> None:
        """Initialize the connection manager with empty stores."""
        # Map of websocket -> CVPipeline instance
        self.active_connections: Dict[WebSocket, CVPipeline] = {}
        # Set of all connected websockets for broadcasting / counting
        self._connection_ids: Set[int] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Creates a new CVPipeline instance for this connection so each
        client has independent processing state.

        Args:
            websocket: The incoming WebSocket connection.
        """
        await websocket.accept()
        pipeline = CVPipeline()
        self.active_connections[websocket] = pipeline
        self._connection_ids.add(id(websocket))
        print(
            f"[WebSocket] Client connected. "
            f"Total active connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection and clean up its pipeline.

        Args:
            websocket: The WebSocket connection to disconnect.
        """
        self.active_connections.pop(websocket, None)
        self._connection_ids.discard(id(websocket))
        print(
            f"[WebSocket] Client disconnected. "
            f"Total active connections: {len(self.active_connections)}"
        )

    def get_pipeline(self, websocket: WebSocket) -> CVPipeline:
        """Retrieve the CVPipeline instance associated with a connection.

        Args:
            websocket: The WebSocket connection.

        Returns:
            The CVPipeline instance for this connection.

        Raises:
            KeyError: If the websocket is not in active connections.
        """
        return self.active_connections[websocket]

    @property
    def connection_count(self) -> int:
        """Return the number of currently active connections."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


def _decode_base64_frame(b64_string: str) -> np.ndarray:
    """Decode a base64-encoded JPEG string into a numpy array (BGR image).

    Handles the common case where the base64 string includes a data URI
    prefix (e.g., 'data:image/jpeg;base64,...') by stripping it before
    decoding.

    Args:
        b64_string: Base64-encoded JPEG image string, optionally with
            a data URI prefix.

    Returns:
        A numpy array representing the decoded BGR image.

    Raises:
        ValueError: If the base64 string cannot be decoded into a valid image.
    """
    # Strip data URI prefix if present
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Failed to decode image from bytes")
        return frame
    except Exception as exc:
        raise ValueError(f"Invalid base64 image data: {exc}")


def _encode_frame_to_base64(frame: np.ndarray) -> str:
    """Encode a numpy array (BGR image) into a base64-encoded JPEG string.

    Args:
        frame: A numpy array representing a BGR image.

    Returns:
        A base64-encoded string of the JPEG-encoded image.

    Raises:
        ValueError: If the frame cannot be encoded.
    """
    success, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        raise ValueError("Failed to encode frame to JPEG")

    b64_string = base64.b64encode(encoded.tobytes()).decode("utf-8")
    return b64_string


@router.websocket("/ws/webcam")
async def websocket_webcam(websocket: WebSocket) -> None:
    """WebSocket endpoint for live webcam streaming.

    On connect:
        - Accepts the connection and initializes a CVPipeline instance.
    On receive:
        - Expects a base64-encoded JPEG frame as a text message.
        - Decodes the frame, runs it through process_frame(), encodes the
          annotated frame back to base64 JPEG, and sends a JSON response
          with the annotated frame and summary analytics.
    On disconnect:
        - Cleans up the pipeline and removes the connection.

    Error handling:
        - Sends JSON error messages back to the client when decoding or
          processing fails, but keeps the connection alive for transient
          errors. Fatal errors result in connection closure.
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive the message from the client
            raw_data = await websocket.receive_text()

            try:
                # Parse JSON payload: {"frame": "<base64_data>"}
                payload = json.loads(raw_data)
                b64_frame = payload.get("frame", payload.get("data", ""))
                if not b64_frame:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No frame data in payload",
                    })
                    continue

                # Decode the incoming frame
                frame = _decode_base64_frame(b64_frame)
            except json.JSONDecodeError as exc:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid JSON payload: {exc}",
                })
                continue
            except ValueError as exc:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Frame decode error: {exc}",
                })
                continue

            try:
                # Process the frame through the CV pipeline
                pipeline = manager.get_pipeline(websocket)
                result = pipeline.process_frame(frame)

                # Extract annotated frame and summary
                if isinstance(result, dict):
                    annotated_frame = result.get("annotated_frame", frame)
                    summary = result.get("summary", {})
                elif isinstance(result, tuple) and len(result) == 2:
                    annotated_frame, summary = result
                else:
                    # Fallback: return the original frame with empty summary
                    annotated_frame = frame
                    summary = {}

                # Encode the annotated frame back to base64
                encoded_frame = _encode_frame_to_base64(annotated_frame)

                # Send the annotated frame and summary back to the client
                # Frontend expects: { annotated_frame, stats }
                await websocket.send_json({
                    "type": "frame",
                    "annotated_frame": encoded_frame,
                    "stats": summary,
                })

            except ValueError as exc:
                # Encoding error - send error but keep connection alive
                await websocket.send_json({
                    "type": "error",
                    "message": f"Frame encoding error: {exc}",
                })
            except Exception as exc:
                # Pipeline processing error - send error but keep connection alive
                await websocket.send_json({
                    "type": "error",
                    "message": f"Processing error: {exc}",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        # Unexpected error - clean up the connection
        print(f"[WebSocket] Unexpected error: {exc}")
        manager.disconnect(websocket)
