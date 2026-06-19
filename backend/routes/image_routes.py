"""Image upload and processing route for Buzzlytics API.

Provides a single POST endpoint that accepts an uploaded image file,
runs it through the CV pipeline's process_frame(), and returns a JSON
response containing the analytics summary, motion metrics, and a
base64-encoded annotated JPEG — mirroring the encoding used in the
WebSocket route.
"""

import base64
import sys
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

# Add the parent directory to sys.path so cv_pipeline can be imported
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cv_pipeline import CVPipeline

router = APIRouter(prefix="/api/image", tags=["image"])


def _decode_upload_to_frame(data: bytes) -> np.ndarray:
    """Decode raw image bytes into a BGR numpy array.

    Args:
        data: Raw bytes of the uploaded image file.

    Returns:
        BGR numpy array (HxWxC).

    Raises:
        ValueError: If the bytes cannot be decoded into a valid image.
    """
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Uploaded file could not be decoded as an image")
    return frame


def _encode_frame_to_base64(frame: np.ndarray) -> str:
    """Encode a BGR numpy array into a base64-encoded JPEG string.

    Mirrors the encoding used by websocket_routes._encode_frame_to_base64.

    Args:
        frame: BGR numpy array.

    Returns:
        Base64-encoded JPEG string.

    Raises:
        ValueError: If the frame cannot be JPEG-encoded.
    """
    success, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        raise ValueError("Failed to encode annotated frame to JPEG")
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


@router.post("")
async def process_image(
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Process a single uploaded image through the CV pipeline.

    Accepts a multipart image file upload (JPEG, PNG, etc.), decodes it,
    runs it through CVPipeline.process_frame(), and returns:
        - summary: analytics summary dict (bee counts, health score, …)
        - motion: activity_ratio and blob_count from the motion detector
        - annotated_image: base64-encoded JPEG of the annotated frame

    Args:
        file: The uploaded image file (field name: ``file``).

    Returns:
        JSON dict with ``summary``, ``motion``, and ``annotated_image``.

    Raises:
        HTTPException 400: If the uploaded bytes cannot be decoded as an
            image or if frame encoding fails.
    """
    # Read uploaded bytes
    try:
        contents = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read uploaded file: {exc}")

    # Decode to OpenCV frame
    try:
        frame = _decode_upload_to_frame(contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Run through CV pipeline (lazy — one pipeline per request is fine for
    # a stateless image endpoint)
    try:
        pipeline = CVPipeline()
        result = pipeline.process_frame(frame)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {exc}")

    # Extract components from the result dict
    annotated_frame = result.get("annotated_frame", frame)
    summary = result.get("summary", {})
    motion = result.get("motion", {"activity_ratio": 0.0, "blob_count": 0})

    # Encode annotated frame to base64 JPEG (mirrors websocket_routes encoding)
    try:
        annotated_b64 = _encode_frame_to_base64(annotated_frame)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "summary": summary,
        "motion": motion,
        "annotated_image": annotated_b64,
    }
