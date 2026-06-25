"""
Buzzlytics Model Validation Script

Evaluates a trained YOLOv8 model on the validation set and reports
metrics including mAP, precision, recall, and per-class performance.

Usage:
    python validate.py --weights ../training/runs/bee_detector/weights/best.pt
    python validate.py --weights ../training/runs/bee_detector/weights/best.pt --data ../datasets/data/bee_dataset.yaml
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for validation configuration."""
    parser = argparse.ArgumentParser(
        description="Validate a trained YOLOv8 bee detection model"
    )
    parser.add_argument(
        "--weights",
        type=str,
        required=True,
        help="Path to the trained model weights file (e.g., best.pt)",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=str(PROJECT_ROOT / "datasets" / "data" / "bee_dataset.yaml"),
        help="Path to the YOLO dataset configuration YAML file",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size for validation (default: 16)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size for validation (default: 640)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for detections (default: 0.25)",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.45,
        help="IoU threshold for NMS (default: 0.45)",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="val",
        help="Dataset split to validate on: val or test (default: val)",
    )
    return parser.parse_args()


def main() -> None:
    """Main validation entry point."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print(
            "Error: ultralytics is not installed. "
            "Install it with: pip install ultralytics"
        )
        sys.exit(1)

    args = parse_args()

    # Validate weights file exists
    if not Path(args.weights).exists():
        print(f"Error: Weights file not found at '{args.weights}'")
        sys.exit(1)

    print(f"[Validate] Loading model: {args.weights}")
    model = YOLO(args.weights)

    print(f"[Validate] Dataset config: {args.data}")
    print(f"[Validate] Split: {args.split}")
    print(f"[Validate] Batch size: {args.batch}")
    print(f"[Validate] Image size: {args.imgsz}")
    print("-" * 50)

    # Run validation
    metrics = model.val(
        data=args.data,
        batch=args.batch,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        split=args.split,
        verbose=True,
    )

    print("-" * 50)
    print("[Validate] Validation Results:")
    print(f"  mAP50:    {metrics.box.map50:.4f}")
    print(f"  mAP50-95: {metrics.box.map:.4f}")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall:    {metrics.box.mr:.4f}")

    # Per-class metrics
    class_names = ["bee", "pollen_bee"]
    if hasattr(metrics.box, "maps") and metrics.box.maps is not None:
        print("\n  Per-class mAP50-95:")
        for i, name in enumerate(class_names):
            if i < len(metrics.box.maps):
                print(f"    {name}: {metrics.box.maps[i]:.4f}")


if __name__ == "__main__":
    main()
