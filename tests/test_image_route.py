"""Tests for POST /api/image image-processing endpoint."""
import base64
import io
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient


def _make_png_bytes(height: int = 64, width: int = 64) -> bytes:
    """Return raw PNG bytes for a small solid-colour image."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :] = (80, 120, 160)  # BGR fill
    success, buf = cv2.imencode(".png", arr)
    assert success, "cv2.imencode failed during test setup"
    return buf.tobytes()


@pytest.fixture()
def client():
    """Return a TestClient with YOLO patched out so no weights are needed."""
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        # Import app *inside* the patch so CVPipeline (and BeeDetector)
        # never attempt to load real YOLO weights.
        from backend.main import app
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_image_endpoint_returns_200(client):
    """POST a valid PNG and expect HTTP 200."""
    png_bytes = _make_png_bytes()
    response = client.post(
        "/api/image",
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 200


def test_image_endpoint_response_has_required_keys(client):
    """Response JSON must contain summary, motion, and annotated_image."""
    png_bytes = _make_png_bytes()
    response = client.post(
        "/api/image",
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "summary" in body, "Missing 'summary' key"
    assert "motion" in body, "Missing 'motion' key"
    assert "annotated_image" in body, "Missing 'annotated_image' key"


def test_image_endpoint_motion_has_sub_keys(client):
    """motion dict must have activity_ratio and blob_count."""
    png_bytes = _make_png_bytes()
    response = client.post(
        "/api/image",
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 200
    motion = response.json()["motion"]
    assert "activity_ratio" in motion
    assert "blob_count" in motion


def test_image_endpoint_annotated_image_is_valid_base64_jpeg(client):
    """annotated_image must decode as valid base64 and produce a JPEG buffer."""
    png_bytes = _make_png_bytes()
    response = client.post(
        "/api/image",
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 200
    b64 = response.json()["annotated_image"]
    # Must be valid base64
    raw = base64.b64decode(b64)
    assert len(raw) > 0
    # Must decode to a valid image via OpenCV
    nparr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    assert img is not None, "annotated_image base64 does not decode to a valid image"


# ---------------------------------------------------------------------------
# Error-handling tests
# ---------------------------------------------------------------------------

def test_image_endpoint_no_file_returns_422(client):
    """POST with no file attached should return 422 (validation error)."""
    response = client.post("/api/image")
    assert response.status_code == 422


def test_image_endpoint_invalid_image_returns_400(client):
    """POST with non-image bytes should return 400, not 500."""
    garbage = b"this is not an image"
    response = client.post(
        "/api/image",
        files={"file": ("bad.png", io.BytesIO(garbage), "image/png")},
    )
    assert response.status_code == 400
