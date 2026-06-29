"""Varroa crop detection/classification endpoint."""

from __future__ import annotations

import base64
import re
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cv_pipeline.config import load_config
from cv_pipeline.varroa_classifier import VarroaClassifier
from cv_pipeline.varroa_detector import MiteDetection, VarroaMiteDetector

router = APIRouter(prefix="/api/varroa", tags=["varroa"])


def _decode_upload_to_frame(data: bytes) -> np.ndarray:
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Uploaded file could not be decoded as an image")
    return frame


def _encode_frame_to_base64(frame: np.ndarray) -> str:
    success, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not success:
        raise ValueError("Failed to encode annotated frame to JPEG")
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


@lru_cache(maxsize=1)
def _get_classifier() -> VarroaClassifier:
    cfg = load_config()
    vc = cfg.get("varroa_classifier", {})
    return VarroaClassifier(
        model_path=vc.get("model_path", "cv_pipeline/weights/varroa_cls.pt"),
        conf_threshold=vc.get("conf_threshold", 0.85),
    )


@lru_cache(maxsize=1)
def _get_detector() -> VarroaMiteDetector:
    cfg = load_config()
    vd = cfg.get("varroa_detector", {})
    if not vd.get("enabled", True):
        return VarroaMiteDetector(model_path="")
    return VarroaMiteDetector(
        model_path=vd.get("model_path", "cv_pipeline/weights/varroa_det.pt"),
        conf_threshold=vd.get("conf_threshold", 0.35),
        iou_threshold=vd.get("iou_threshold", 0.45),
        imgsz=vd.get("imgsz", 960),
    )


def _candidate_csv_paths() -> List[Path]:
    roots = os.environ.get("VARROA_DATA_ROOTS")
    candidates: List[Path] = []
    if roots:
        for root in roots.split(os.pathsep):
            candidates.extend(Path(root).glob("**/gt_one.csv"))

    home = Path.home()
    candidates.extend(
        [
            home / "Downloads" / "test_varroa" / "test" / "gt_one.csv",
            home / "Downloads" / "val_varroa" / "val" / "gt_one.csv",
            home / "Downloads" / "train_varroa" / "train" / "gt_one.csv",
        ]
    )
    return [path for path in candidates if path.is_file()]


@lru_cache(maxsize=1)
def _load_varroa_ground_truth() -> Dict[str, Dict[str, object]]:
    lookup: Dict[str, Dict[str, object]] = {}
    for csv_path in _candidate_csv_paths():
        for line in csv_path.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            filename = Path(parts[0]).name
            mite_count = int(parts[1])
            coords = [float(value) for value in parts[2:]]
            boxes = [
                coords[idx : idx + 4]
                for idx in range(0, len(coords), 4)
                if idx + 3 < len(coords)
            ]
            record = {
                "mite_count": mite_count,
                "boxes": boxes,
                "source": str(csv_path),
            }
            lookup[filename] = record
            lookup[Path(filename).stem] = record

            bee_match = re.search(r"bee_id_\d+-\d+-\d+", filename)
            if bee_match:
                lookup[bee_match.group(0)] = record
    return lookup


def _find_ground_truth(filename: str) -> Optional[Dict[str, object]]:
    lookup = _load_varroa_ground_truth()
    clean_name = Path(filename or "").name
    candidates = [clean_name, Path(clean_name).stem]

    bee_match = re.search(r"bee_id_\d+-\d+-\d+", clean_name)
    if bee_match:
        candidates.append(bee_match.group(0))

    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def _draw_varroa_annotation(
    frame: np.ndarray,
    prediction: Dict[str, object],
    ground_truth: Optional[Dict[str, object]],
    focus_box: Optional[List[int]] = None,
    detections: Optional[List[MiteDetection]] = None,
) -> np.ndarray:
    annotated = frame.copy()
    h, w = annotated.shape[:2]

    if detections:
        for det in detections:
            x1, y1, x2, y2 = [int(round(float(value))) for value in det.bbox]
            x1 = max(0, min(w - 1, x1))
            x2 = max(0, min(w - 1, x2))
            y1 = max(0, min(h - 1, y1))
            y2 = max(0, min(h - 1, y2))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
            label = f"mite {det.confidence:.2f}"
            label_y = max(16, y1 - 5)
            cv2.rectangle(
                annotated,
                (x1, label_y - 16),
                (min(w - 1, x1 + 82), label_y + 3),
                (0, 0, 255),
                -1,
            )
            cv2.putText(
                annotated,
                label,
                (x1 + 3, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
    elif ground_truth:
        for box in ground_truth.get("boxes", []):
            x1, y1, x2, y2 = [int(round(float(value))) for value in box]
            x1 = max(0, min(w - 1, x1))
            x2 = max(0, min(w - 1, x2))
            y1 = max(0, min(h - 1, y1))
            y2 = max(0, min(h - 1, y2))
            cv2.rectangle(
                annotated,
                (x1, y1),
                (x2, y2),
                (0, 255, 255),
                7,
            )
            cv2.rectangle(
                annotated,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                3,
            )
            label_y = max(16, y1 - 5)
            cv2.rectangle(
                annotated,
                (x1, label_y - 16),
                (min(w - 1, x1 + 48), label_y + 3),
                (0, 255, 255),
                -1,
            )
            cv2.putText(
                annotated,
                "mite",
                (x1 + 3, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )
    elif focus_box:
        x1, y1, x2, y2 = focus_box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 255), 7)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
        label_y = max(16, y1 - 5)
        cv2.rectangle(
            annotated,
            (x1, label_y - 16),
            (min(w - 1, x1 + 88), label_y + 3),
            (0, 255, 255),
            -1,
        )
        cv2.putText(
            annotated,
            "model focus",
            (x1 + 3, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

    label = str(prediction.get("label", "unknown")).upper()
    conf = float(prediction.get("confidence", 0.0))
    is_varroa = bool(prediction.get("is_varroa", False))
    color = (0, 0, 220) if is_varroa else (0, 180, 0)
    text = f"{label} {conf:.2f}"
    if ground_truth:
        text += f" | GT mites:{ground_truth.get('mite_count', 0)}"

    cv2.rectangle(annotated, (0, 0), (w, 42), (25, 25, 25), -1)
    cv2.putText(
        annotated,
        text,
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        color,
        2,
        cv2.LINE_AA,
    )
    return annotated


def _varroa_score(prediction: Dict[str, object]) -> float:
    scores = prediction.get("scores", {})
    if isinstance(scores, dict):
        return float(scores.get("varroa", 0.0))
    return float(prediction.get("confidence", 0.0)) if prediction.get("label") == "varroa" else 0.0


def _estimate_focus_box(
    classifier: VarroaClassifier,
    frame: np.ndarray,
    prediction: Dict[str, object],
) -> Optional[List[int]]:
    if not prediction.get("is_varroa"):
        return None

    base_score = _varroa_score(prediction)
    if base_score <= 0:
        return None

    h, w = frame.shape[:2]
    patch_w = max(24, w // 4)
    patch_h = max(32, h // 6)
    step_x = max(12, patch_w // 2)
    step_y = max(16, patch_h // 2)
    fill = tuple(int(v) for v in frame.reshape(-1, 3).mean(axis=0))

    best_drop = 0.0
    best_box: Optional[List[int]] = None
    for y1 in range(42, max(43, h - patch_h + 1), step_y):
        for x1 in range(0, max(1, w - patch_w + 1), step_x):
            x2 = min(w, x1 + patch_w)
            y2 = min(h, y1 + patch_h)
            occluded = frame.copy()
            occluded[y1:y2, x1:x2] = fill
            score = _varroa_score(classifier.classify(occluded))
            drop = base_score - score
            if drop > best_drop:
                best_drop = drop
                best_box = [x1, y1, x2, y2]

    return best_box if best_drop >= 0.05 else None


@router.post("")
async def process_varroa_crop(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        contents = await file.read()
        frame = _decode_upload_to_frame(contents)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    detector = _get_detector()
    classifier = _get_classifier()
    ground_truth = _find_ground_truth(file.filename or "")

    detections: List[MiteDetection] = []
    if detector.available:
        detections = detector.detect(frame)
        max_conf = max((det.confidence for det in detections), default=0.0)
        prediction = {
            "label": "varroa" if detections else "healthy",
            "confidence": max_conf,
            "scores": {"varroa": max_conf, "healthy": 1.0 - max_conf},
            "is_varroa": bool(detections),
            "threshold": detector.conf_threshold,
            "method": "detector",
        }
        focus_box = None
    else:
        if not classifier.available:
            raise HTTPException(
                status_code=500,
                detail="Varroa detector/classifier weights are unavailable",
            )
        prediction = classifier.classify(frame)
        prediction["method"] = "classifier"
        focus_box = None if ground_truth else _estimate_focus_box(classifier, frame, prediction)

    annotated = _draw_varroa_annotation(
        frame,
        prediction,
        ground_truth,
        focus_box,
        detections=detections,
    )

    try:
        annotated_b64 = _encode_frame_to_base64(annotated)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "prediction": prediction,
        "detections": [
            {
                "bbox": det.bbox,
                "confidence": det.confidence,
                "class_id": det.class_id,
                "class_name": det.class_name,
            }
            for det in detections
        ],
        "ground_truth": ground_truth,
        "focus_box": focus_box,
        "annotated_image": annotated_b64,
    }

