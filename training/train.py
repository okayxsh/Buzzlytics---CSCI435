"""
Buzzlytics Model Training Script

Fine-tunes a YOLOv8 model on a custom bee detection dataset with three classes:
bee, pollen_bee, and varroa_bee.

Usage:
    python train.py --data ../datasets/data/bee_dataset.yaml --epochs 100 --batch 16

The script downloads the pretrained YOLOv8 nano model as a starting point and
fine-tunes it on the bee dataset. The best weights are saved to the runs/
directory and can be copied to the cv_pipeline directory for inference.
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure the project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for training configuration."""
    parser = argparse.ArgumentParser(
        description="Fine-tune YOLOv8 on the Buzzlytics bee detection dataset"
    )
    parser.add_argument(
        "--data",
        type=str,
        default=str(PROJECT_ROOT / "datasets" / "data" / "bee_dataset.yaml"),
        help="Path to the YOLO dataset configuration YAML file",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Pretrained model weights to start fine-tuning from (default: yolov8n.pt)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs (default: 100)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size for training (default: 16)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size for training (default: 640)",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=20,
        help="Early stopping patience in epochs (default: 20)",
    )
    parser.add_argument(
        "--lr0",
        type=float,
        default=0.01,
        help="Initial learning rate (default: 0.01)",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=str(PROJECT_ROOT / "training" / "runs"),
        help="Directory to save training runs",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="bee_detector",
        help="Name of the training run",
    )
    return parser.parse_args()


def main() -> None:
    """Main training entry point."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print(
            "Error: ultralytics is not installed. "
            "Install it with: pip install ultralytics"
        )
        sys.exit(1)

    args = parse_args()

    # Validate dataset config
    if not os.path.isfile(args.data):
        print(f"Error: Dataset config not found at '{args.data}'")
        print(
            "Please create a YOLO-format dataset with the following structure:\n"
            "  datasets/\n"
            "    images/\n"
            "      train/   (training images)\n"
            "      val/     (validation images)\n"
            "    labels/\n"
            "      train/   (training labels in YOLO format)\n"
            "      val/     (validation labels in YOLO format)\n"
            "    data/\n"
            "      bee_dataset.yaml  (dataset config)"
        )
        sys.exit(1)

    print(f"[Training] Loading pretrained model: {args.model}")
    model = YOLO(args.model)

    print(f"[Training] Dataset config: {args.data}")
    print(f"[Training] Epochs: {args.epochs}")
    print(f"[Training] Batch size: {args.batch}")
    print(f"[Training] Image size: {args.imgsz}")
    print(f"[Training] Output: {args.project}/{args.name}")
    print("-" * 50)

    # Start training
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        patience=args.patience,
        lr0=args.lr0,
        project=args.project,
        name=args.name,
        exist_ok=True,
        verbose=True,
        # Augmentation settings for small object detection (bees)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
    )

    print("-" * 50)
    print("[Training] Training completed!")
    print(f"[Training] Results saved to: {args.project}/{args.name}")

    # Find the best weights
    best_weights = Path(args.project) / args.name / "weights" / "best.pt"
    if best_weights.exists():
        print(f"[Training] Best weights: {best_weights}")
        print(
            f"[Training] Copy the best weights to the project root for inference:\n"
            f"  cp {best_weights} ../cv_pipeline/custom_bee_model.pt"
        )
    else:
        print("[Training] Warning: best.pt not found. Check training logs.")


if __name__ == "__main__":
    main()
