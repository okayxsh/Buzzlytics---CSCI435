"""Train a YOLO detector for Varroa mite boxes on close-up bee crops.

Usage:
    python training/train_varroa_detector.py \
        --data datasets/varroa_det/varroa_mite.yaml \
        --epochs 80 --imgsz 960

After training, copy:
    training/runs/varroa_mite_detector/weights/best.pt
to:
    cv_pipeline/weights/varroa_det.pt
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train close-up Varroa mite YOLO detector")
    parser.add_argument(
        "--data",
        default=str(PROJECT_ROOT / "datasets" / "varroa_det" / "varroa_mite.yaml"),
        help="Path to Varroa mite YOLO data yaml",
    )
    parser.add_argument("--model", default="yolov8n.pt", help="Starting YOLO weights")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument(
        "--project",
        default=str(PROJECT_ROOT / "training" / "runs"),
        help="Training output directory",
    )
    parser.add_argument("--name", default="varroa_mite_detector")
    return parser.parse_args()


def main() -> None:
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics is not installed. Install it with: pip install ultralytics")
        sys.exit(1)

    args = parse_args()
    if not os.path.isfile(args.data):
        print(f"Error: dataset yaml not found: {args.data}")
        print("Build it first with training/make_varroa_detection_dataset.py")
        sys.exit(1)

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        patience=args.patience,
        project=args.project,
        name=args.name,
        exist_ok=True,
        verbose=True,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.35,
        degrees=5.0,
        translate=0.08,
        scale=0.4,
        fliplr=0.5,
        mosaic=0.5,
        mixup=0.0,
        close_mosaic=10,
    )

    best = Path(args.project) / args.name / "weights" / "best.pt"
    print(f"Best weights: {best}")
    print("Copy to: cv_pipeline/weights/varroa_det.pt")


if __name__ == "__main__":
    main()
