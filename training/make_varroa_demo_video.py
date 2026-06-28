"""Create a labeled VarroaDataset demo video from bee crop images.

The VarroaDataset stores close-up bee crops under a folder named "videos".
This script turns those still images plus gt_one.csv annotations into a short
MP4 that is easier to show during a presentation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


def parse_rows(csv_path: Path) -> Iterable[tuple[Path, int, list[float]]]:
    for line in csv_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        image_path = Path(parts[0])
        mite_count = int(parts[1])
        coords = [float(value) for value in parts[2:]]
        yield image_path, mite_count, coords


def draw_sample(
    image: np.ndarray,
    mite_count: int,
    coords: list[float],
    source_name: str,
) -> np.ndarray:
    canvas = cv2.resize(image, (320, 560), interpolation=cv2.INTER_CUBIC)
    scale_x = 320 / image.shape[1]
    scale_y = 560 / image.shape[0]

    for idx in range(0, len(coords), 4):
        if idx + 3 >= len(coords):
            break
        x1, y1, x2, y2 = coords[idx : idx + 4]
        pt1 = (int(round(x1 * scale_x)), int(round(y1 * scale_y)))
        pt2 = (int(round(x2 * scale_x)), int(round(y2 * scale_y)))
        cv2.rectangle(canvas, pt1, pt2, (0, 0, 255), 3)

    label = "VARROA" if mite_count > 0 else "HEALTHY"
    color = (0, 0, 255) if mite_count > 0 else (0, 180, 0)
    cv2.rectangle(canvas, (0, 0), (320, 58), (20, 20, 20), -1)
    cv2.putText(
        canvas,
        f"{label}  mites:{mite_count}",
        (12, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        source_name[:28],
        (12, 548),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (230, 230, 230),
        1,
        cv2.LINE_AA,
    )
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--split-dir",
        type=Path,
        required=True,
        help="Path like C:/.../test_varroa/test containing gt_one.csv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("varroa_demo.mp4"),
        help="Output MP4 path.",
    )
    parser.add_argument("--fps", type=float, default=2.0)
    parser.add_argument("--max-samples", type=int, default=80)
    parser.add_argument(
        "--positives-first",
        action="store_true",
        help="Show infected examples before healthy examples.",
    )
    args = parser.parse_args()

    csv_path = args.split_dir / "gt_one.csv"
    rows = list(parse_rows(csv_path))
    if args.positives_first:
        rows.sort(key=lambda row: row[1] <= 0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(args.output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        args.fps,
        (320, 560),
    )

    written = 0
    for rel_path, mite_count, coords in rows:
        if written >= args.max_samples:
            break
        image_path = args.split_dir / rel_path
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        frame = draw_sample(image, mite_count, coords, image_path.name)
        writer.write(frame)
        written += 1

    writer.release()
    print(f"Wrote {written} frames to {args.output}")


if __name__ == "__main__":
    main()
