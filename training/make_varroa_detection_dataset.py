"""Build a YOLO detection dataset for close-up Varroa mite boxes.

Input is a VarroaDataset-style directory containing bee crop images and a
``gt_one.csv`` or ``gt.csv`` file. Each CSV row is expected to look like:

    image_path mite_count [x1 y1 x2 y2 ...]

Rows with ``mite_count == 0`` are written as background images with empty label
files. Rows with boxes are written as class 0 (``mite``).

Usage:
    python training/make_varroa_detection_dataset.py \
        --source C:/Users/aaron/Downloads/test_varroa/test \
        --out datasets/varroa_det
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import cv2
import yaml

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _safe_stem(text: str) -> str:
    flat = text.replace("\\", "/").replace("/", "__")
    flat = "".join(c if (c.isalnum() or c in "._-") else "_" for c in flat)
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"{flat[:90]}_{digest}"


def _split_for(name: str) -> str:
    lower = name.lower().replace("\\", "/")
    if "/test/" in lower or lower.startswith("test/"):
        return "test"
    if "/val/" in lower or "/valid/" in lower or lower.startswith(("val/", "valid/")):
        return "valid"
    if "/train/" in lower or lower.startswith("train/"):
        return "train"
    bucket = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16) % 10
    if bucket < 7:
        return "train"
    if bucket < 9:
        return "valid"
    return "test"


def _find_csv(source: Path) -> Path:
    for name in ("gt_one.csv", "gt.csv"):
        direct = source / name
        if direct.is_file():
            return direct
    matches = list(source.glob("**/gt_one.csv")) or list(source.glob("**/gt.csv"))
    if not matches:
        raise FileNotFoundError(f"No gt_one.csv or gt.csv found under {source}")
    return matches[0]


def _index_images(source: Path) -> Tuple[Dict[str, Path], Dict[str, Path]]:
    by_rel: Dict[str, Path] = {}
    by_base: Dict[str, Path] = {}
    for path in source.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMG_EXTS:
            rel = str(path.relative_to(source)).replace("\\", "/")
            by_rel[rel] = path
            by_base.setdefault(path.name, path)
    return by_rel, by_base


def _resolve_image(raw: str, source: Path, by_rel: Dict[str, Path], by_base: Dict[str, Path]) -> Optional[Path]:
    norm = raw.replace("\\", "/")
    candidates = [
        by_rel.get(norm),
        by_rel.get(norm.lstrip("./")),
        by_base.get(Path(norm).name),
    ]
    direct = source / norm
    if direct.is_file():
        candidates.append(direct)
    return next((path for path in candidates if path is not None and path.is_file()), None)


def _boxes_to_yolo(coords: List[float], img_w: int, img_h: int) -> List[str]:
    lines: List[str] = []
    for idx in range(0, len(coords), 4):
        if idx + 3 >= len(coords):
            continue
        x1, y1, x2, y2 = coords[idx : idx + 4]
        x1 = max(0.0, min(float(img_w), x1))
        x2 = max(0.0, min(float(img_w), x2))
        y1 = max(0.0, min(float(img_h), y1))
        y2 = max(0.0, min(float(img_h), y2))
        if x2 <= x1 or y2 <= y1:
            continue
        cx = ((x1 + x2) / 2.0) / img_w
        cy = ((y1 + y2) / 2.0) / img_h
        bw = (x2 - x1) / img_w
        bh = (y2 - y1) / img_h
        lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
    return lines


def _ensure_dirs(out: Path) -> None:
    for split in ("train", "valid", "test"):
        (out / split / "images").mkdir(parents=True, exist_ok=True)
        (out / split / "labels").mkdir(parents=True, exist_ok=True)


def build_dataset(source: Path, out: Path, split_override: Optional[str] = None) -> int:
    source = source.resolve()
    out = out.resolve()
    _ensure_dirs(out)
    csv_path = _find_csv(source)
    by_rel, by_base = _index_images(source)

    written = 0
    for line in csv_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        raw_image = parts[0]
        image_path = _resolve_image(raw_image, source, by_rel, by_base)
        if image_path is None:
            continue

        image = cv2.imread(str(image_path))
        if image is None:
            continue
        img_h, img_w = image.shape[:2]
        mite_count = int(float(parts[1]))
        coords = [float(value) for value in parts[2:]]
        label_lines = _boxes_to_yolo(coords, img_w, img_h) if mite_count > 0 else []

        split = split_override or _split_for(raw_image)
        stem = _safe_stem(raw_image)
        dest_img = out / split / "images" / f"{stem}{image_path.suffix.lower()}"
        dest_lbl = out / split / "labels" / f"{stem}.txt"
        shutil.copy2(image_path, dest_img)
        dest_lbl.write_text("".join(label_lines), encoding="utf-8")
        written += 1

    data_yaml = {
        "path": str(out),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": 1,
        "names": {0: "mite"},
    }
    (out / "varroa_mite.yaml").write_text(yaml.safe_dump(data_yaml, sort_keys=False), encoding="utf-8")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build YOLO Varroa mite detection data")
    parser.add_argument("--source", required=True, help="Folder containing gt_one.csv/gt.csv and images")
    parser.add_argument("--out", default="datasets/varroa_det", help="Output YOLO dataset folder")
    parser.add_argument(
        "--split",
        choices=["train", "valid", "test"],
        default=None,
        help="Force all rows from this source into one split",
    )
    args = parser.parse_args()

    count = build_dataset(Path(args.source), Path(args.out), split_override=args.split)
    print(f"Wrote {count} images to {Path(args.out).resolve()}")
    print(f"Data YAML: {(Path(args.out) / 'varroa_mite.yaml').resolve()}")


if __name__ == "__main__":
    main()
