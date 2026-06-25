"""
Build TWO-STAGE data for Buzzlytics from two public research datasets.

Stage 1 — DETECTION (boxes every bee): classes 0=bee, 1=pollen_bee.
Stage 2 — CLASSIFICATION (per-bee varroa): labels healthy / varroa.

Why two stages: VarroaDataset is single-bee CROPS (classification), not
boxed bees-in-scene. Forcing it into detection as whole-image boxes ruins
per-bee localisation and poisons the bee class. So varroa is a per-bee
attribute decided by a classifier on each detected bee crop, the way
IntelliBeeHive / BeeAlarmed do it.

Sources
-------
1. VnPollenBee (HUST ComVis) — real hive-entrance DETECTION set.
   LabelMe JSON (polygons) with embedded base64 ``imageData``.
   labels: ``nonpollenbee`` -> bee (0), ``pollenbee`` -> pollen_bee (1).
   https://comvis-hust.github.io/datasets/pollenbee.html  (Google-Drive folder)

2. VarroaDataset (TU Wien, Zenodo 4085044) — varroa CLASSIFICATION set.
   160x280 single-bee crops + ``gt.csv`` (``<path> <flag> [mite boxes]``).
   flag 0 = healthy, non-zero = infected. Crops are sorted into a YOLOv8
   classification ImageFolder: ``{split}/{healthy|varroa}/``.
   https://zenodo.org/records/4085044

Output:
    datasets/data/{train,valid,test}/{images,labels}   (detection, 2-class)
    datasets/varroa_cls/{train,val,test}/{healthy,varroa}/   (classification)

Usage
-----
    python datasets/prepare_dataset.py \
        --vnpollenbee-url "https://drive.google.com/drive/folders/1fdEcu7CNmEkVAamu9wh_Ppw_-uW3VNY1"

Both sources are public — no API key required.  ``gdown`` is needed for the
Google-Drive folder; it is installed on demand if missing.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import logging
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# DETECTION class ids (stage 1). Only bee + pollen_bee get bounding boxes,
# from VnPollenBee. Varroa is NOT a detection class — it is decided per-bee
# by the stage-2 classifier (see VARROA_CLASSES), because VarroaDataset is a
# classification set (single-bee crops), not boxed bees-in-scene.
CANONICAL: Dict[str, int] = {"bee": 0, "pollen_bee": 1}

# CLASSIFICATION labels (stage 2) for the varroa crop classifier.
VARROA_CLASSES = ("healthy", "varroa")

# Zenodo VarroaDataset file URLs (CC-BY-4.0). Two endpoints exist and Zenodo
# 403s one or the other depending on the caller's IP/rate, so we try both.
ZENODO_FILES = ("train.zip", "val.zip", "test.zip", "gt.csv")


def _zenodo_urls(name: str) -> List[str]:
    """Return both Zenodo download endpoints for a file (fallback order)."""
    return [
        f"https://zenodo.org/records/4085044/files/{name}?download=1",
        f"https://zenodo.org/api/records/4085044/files/{name}/content",
    ]

# Default VnPollenBee Google-Drive folder (from the project page).
VNPB_DRIVE_URL = (
    "https://drive.google.com/drive/folders/"
    "1fdEcu7CNmEkVAamu9wh_Ppw_-uW3VNY1"
)


# --------------------------------------------------------------------------- #
# Legacy pure helpers — kept for back-compat with existing tests. They are no
# longer used by the new pipeline (the old Roboflow merge is gone) but remain
# importable and correct for generic YOLO id remapping.
# --------------------------------------------------------------------------- #
def build_id_map(
    source_names: List[str],
    canonical: Dict[str, int],
    aliases: Dict[str, str],
) -> Dict[int, int]:
    """Map a dataset's class indices to unified class ids.

    Source classes that cannot be mapped are omitted (labels dropped).
    """
    id_map: Dict[int, int] = {}
    for src_idx, raw in enumerate(source_names):
        key = raw.strip().lower().replace(" ", "").replace("-", "")
        canon = aliases.get(key)
        if canon is None and raw.strip().lower() in canonical:
            canon = raw.strip().lower()
        if canon is not None:
            id_map[src_idx] = canonical[canon]
        else:
            logger.warning("Unmapped source class '%s' (idx %d) — dropping.", raw, src_idx)
    return id_map


def remap_label_lines(lines: List[str], id_map: Dict[int, int]) -> List[str]:
    """Rewrite the leading class id of each YOLO label line; drop unmapped."""
    out: List[str] = []
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        src_id = int(float(parts[0]))
        if src_id not in id_map:
            continue
        parts[0] = str(id_map[src_id])
        out.append(" ".join(parts) + "\n")
    return out


# --------------------------------------------------------------------------- #
# New pure converters (unit-tested).
# --------------------------------------------------------------------------- #
def _norm_label(raw: str) -> str:
    """Normalise a raw class label for alias lookup."""
    return raw.strip().lower().replace(" ", "").replace("-", "").replace("_", "")


# Normalised LabelMe label -> canonical name (VnPollenBee).
VNPB_ALIASES: Dict[str, str] = {
    "nonpollenbee": "bee",
    "nonpollenbees": "bee",
    "bee": "bee",
    "bees": "bee",
    "pollenbee": "pollen_bee",
    "pollenbees": "pollen_bee",
    "pollen": "pollen_bee",
    "pollenbearing": "pollen_bee",
}


def points_to_yolo_box(
    points: List[List[float]], img_w: int, img_h: int
) -> Optional[Tuple[float, float, float, float]]:
    """Convert LabelMe polygon/rectangle points to a normalised YOLO box.

    The bbox is the axis-aligned min/max envelope of the points, so this
    works for both ``rectangle`` (2 pts) and ``polygon`` (n pts) shapes.

    Args:
        points: ``[[x, y], ...]`` in pixel coordinates.
        img_w: Image width in pixels.
        img_h: Image height in pixels.

    Returns:
        ``(cx, cy, w, h)`` normalised to [0, 1], or ``None`` if the box is
        empty/degenerate or the image dims are invalid.
    """
    if not points or img_w <= 0 or img_h <= 0:
        return None
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    x1, x2 = max(0.0, min(xs)), min(float(img_w), max(xs))
    y1, y2 = max(0.0, min(ys)), min(float(img_h), max(ys))
    if x2 <= x1 or y2 <= y1:
        return None
    cx = ((x1 + x2) / 2.0) / img_w
    cy = ((y1 + y2) / 2.0) / img_h
    w = (x2 - x1) / img_w
    h = (y2 - y1) / img_h
    return cx, cy, w, h


def labelme_shapes_to_yolo(
    shapes: List[Dict],
    img_w: int,
    img_h: int,
    aliases: Dict[str, str] = VNPB_ALIASES,
    canonical: Dict[str, int] = CANONICAL,
) -> List[str]:
    """Convert LabelMe ``shapes`` to YOLO label lines (drops unknown labels)."""
    out: List[str] = []
    for shape in shapes:
        canon = aliases.get(_norm_label(shape.get("label", "")))
        if canon is None or canon not in canonical:
            continue
        box = points_to_yolo_box(shape.get("points", []), img_w, img_h)
        if box is None:
            continue
        cx, cy, w, h = box
        out.append(f"{canonical[canon]} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
    return out


def varroa_flag_to_label(flag: int) -> str:
    """Map a VarroaDataset gt flag to a classification label.

    The gt.csv first field is 0 for healthy and NON-ZERO (observed 1 or 3,
    an annotation-quality code) for varroa-infected — verified against the
    dataset's published 9562 healthy / 3947 infected counts.
    """
    return "varroa" if int(flag) != 0 else "healthy"


def sample_varroa_rows(
    rows: List[Tuple[str, int]], limit: Optional[int]
) -> List[Tuple[str, int]]:
    """Deterministically subsample varroa rows, preserving class balance.

    Groups by class, orders each group by a stable hash of the path, then
    takes a per-class quota proportional to the original class sizes so the
    infected:healthy ratio is preserved. ``limit=None`` or ``>= len(rows)``
    returns all rows.

    Args:
        rows: ``[(crop_path, class_id), ...]``.
        limit: Max total rows to keep, or ``None`` for all.

    Returns:
        The sampled subset (order grouped by class).
    """
    if limit is None or limit >= len(rows) or limit <= 0:
        return rows
    groups: Dict[int, List[Tuple[str, int]]] = {}
    for row in rows:
        groups.setdefault(row[1], []).append(row)
    total = len(rows)
    out: List[Tuple[str, int]] = []
    for cls, items in groups.items():
        items.sort(key=lambda r: hashlib.md5(r[0].encode("utf-8")).hexdigest())
        quota = max(1, round(limit * len(items) / total))
        out.extend(items[:quota])
    return out


def parse_varroa_gt_line(line: str) -> Optional[Tuple[str, str]]:
    """Parse one ``gt.csv`` line into ``(crop_path, label)``.

    Line form: ``<path> <flag> [mite boxes...]``. ``label`` is
    "healthy"/"varroa". Returns ``None`` for blanks.
    """
    parts = line.split()
    if not parts:
        return None
    path = parts[0]
    flag = int(parts[1]) if len(parts) > 1 and parts[1].lstrip("-").isdigit() else 0
    return path, varroa_flag_to_label(flag)


def split_for(name: str, hint: str = "") -> str:
    """Pick a deterministic split for an item lacking an explicit one.

    Honours an explicit ``hint`` path containing train/val/valid/test; else
    hashes ``name`` into a stable ~70/20/10 train/valid/test split.
    """
    h = hint.lower()
    if "test" in h:
        return "test"
    if "valid" in h or "/val/" in h or h.endswith("val") or "val_" in h:
        return "valid"
    if "train" in h:
        return "train"
    bucket = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16) % 10
    if bucket < 7:
        return "train"
    if bucket < 9:
        return "valid"
    return "test"


# --------------------------------------------------------------------------- #
# Download + extraction helpers (network; not unit-tested).
# --------------------------------------------------------------------------- #
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _download(urls, dest: Path, retries: int = 5) -> None:
    """Stream the first working URL to ``dest`` (skips if already downloaded).

    ``urls`` may be a single URL or a list of fallbacks. Each is retried with
    exponential backoff on 403/429/5xx (Zenodo rate-limits programmatic
    access from shared IPs like Colab's).
    """
    import time

    if dest.is_file() and dest.stat().st_size > 0:
        logger.info("exists, skip download: %s", dest.name)
        return
    if isinstance(urls, str):
        urls = [urls]

    last_err: Optional[Exception] = None
    for attempt in range(retries):
        url = urls[min(attempt, len(urls) - 1)]  # cycle through fallbacks
        try:
            logger.info("downloading %s -> %s (attempt %d)", url, dest.name, attempt + 1)
            req = urllib.request.Request(url, headers=_BROWSER_HEADERS)
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(req, timeout=600) as resp, open(tmp, "wb") as fh:
                shutil.copyfileobj(resp, fh)
            tmp.replace(dest)
            return
        except Exception as exc:  # noqa: BLE001 - retry on any transient failure
            last_err = exc
            wait = 3 * (2 ** attempt)
            logger.warning("download failed (%s); retrying in %ds", exc, wait)
            time.sleep(wait)
    raise RuntimeError(f"failed to download {dest.name} after {retries} tries: {last_err}")


def _safe_extract(zip_path: Path, dest: Path) -> None:
    """Extract a zip, guarding against Zip-Slip path escapes."""
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            target = (root / member).resolve()
            if root != target and root not in target.parents:
                raise RuntimeError(f"Zip entry escapes target dir: {member}")
        zf.extractall(str(root))


def _ensure_dirs(out_dir: Path) -> None:
    for split in ("train", "valid", "test"):
        (out_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (out_dir / split / "labels").mkdir(parents=True, exist_ok=True)


def _write_pair(
    out_dir: Path, split: str, stem: str, img_bytes: bytes, ext: str, label_lines: List[str]
) -> None:
    """Write one image+label pair into the split (empty label allowed)."""
    (out_dir / split / "images" / f"{stem}{ext}").write_bytes(img_bytes)
    (out_dir / split / "labels" / f"{stem}.txt").write_text(
        "".join(label_lines), encoding="utf-8"
    )


# --------------------------------------------------------------------------- #
# Source 1: VnPollenBee (Google-Drive LabelMe JSON folder).
# --------------------------------------------------------------------------- #
def prepare_vnpollenbee(
    drive_url: str,
    raw_dir: Path,
    out_dir: Path,
    local_dir: Optional[str] = None,
) -> int:
    """Convert VnPollenBee LabelMe JSONs to YOLO. Returns #images.

    If ``local_dir`` is given (a folder of already-downloaded ``*.json``),
    it is used directly — this is the reliable path, since the source Drive
    folder has >50 files per subfolder and gdown's scraper cannot traverse
    it (Google caps folder listings at 50). The Colab notebook downloads the
    JSONs via the real Drive API and passes them here.

    Without ``local_dir`` it falls back to ``gdown.download_folder`` (only
    works for small folders — kept for convenience/local use).
    """
    if local_dir:
        vpb_dir = Path(local_dir)
        if not vpb_dir.is_dir():
            raise FileNotFoundError(f"--vnpollenbee-dir not found: {vpb_dir}")
        logger.info("using pre-downloaded VnPollenBee dir: %s", vpb_dir)
    else:
        try:
            import gdown  # type: ignore
        except ImportError:  # pragma: no cover - convenience install
            import subprocess
            import sys

            logger.info("installing gdown ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "gdown"])
            import gdown  # type: ignore

        vpb_dir = raw_dir / "vnpollenbee"
        vpb_dir.mkdir(parents=True, exist_ok=True)
        logger.info("downloading VnPollenBee Drive folder (LabelMe JSON) ...")
        # NOTE: gdown raises FolderContentsMaximumLimitError on folders with
        # >50 files. For the real dataset use --vnpollenbee-dir instead.
        gdown.download_folder(
            url=drive_url,
            output=str(vpb_dir),
            quiet=False,
            use_cookies=False,
            remaining_ok=True,
        )

    count = 0
    skipped = 0
    for js in sorted(vpb_dir.rglob("*.json")):
        try:
            doc = json.loads(js.read_text(encoding="utf-8"))
            img_w = int(doc.get("imageWidth") or 0)
            img_h = int(doc.get("imageHeight") or 0)
            shapes = doc.get("shapes", [])
            if not img_w or not img_h or not shapes:
                skipped += 1
                continue

            # Image: prefer embedded base64, else a sibling file by imagePath.
            img_bytes: Optional[bytes] = None
            ext = ".jpg"
            data = doc.get("imageData")
            if data:
                try:
                    img_bytes = base64.b64decode(data)
                except Exception:  # noqa: BLE001
                    img_bytes = None
            if img_bytes is None:
                ip = doc.get("imagePath")
                if ip:
                    cand = (js.parent / ip).resolve()
                    if cand.is_file():
                        img_bytes = cand.read_bytes()
                        ext = cand.suffix or ".jpg"
            if img_bytes is None:
                skipped += 1
                continue

            labels = labelme_shapes_to_yolo(shapes, img_w, img_h)
            rel = str(js.relative_to(vpb_dir))
            stem = "vpb_" + _safe_stem(js.stem)
            split = split_for(stem, hint=rel)
            _write_pair(out_dir, split, stem, img_bytes, ext, labels)
            count += 1
        except Exception as exc:  # noqa: BLE001 - never let one bad file abort the build
            logger.warning("skipping %s: %s", js.name, exc)
            skipped += 1
    logger.info("VnPollenBee: wrote %d images (skipped %d)", count, skipped)
    return count


# --------------------------------------------------------------------------- #
# Source 2: VarroaDataset (Zenodo crops + gt.csv).
# --------------------------------------------------------------------------- #
def prepare_varroa(
    raw_dir: Path, cls_out_dir: Path, limit: Optional[int] = None
) -> int:
    """Download VarroaDataset crops into a YOLOv8 classification ImageFolder.

    Stage-2 classifier data. Each single-bee crop is copied to
    ``cls_out_dir/{split}/{healthy|varroa}/`` (NO bounding boxes — these are
    classification crops, not boxed bees). Split comes from the gt.csv path
    prefix (train/val/test). Returns #crops written.

    ``limit`` caps crops kept (class-stratified, deterministic); ``None`` = all.
    """
    varroa_dir = raw_dir / "varroa"
    varroa_dir.mkdir(parents=True, exist_ok=True)

    for fname in ZENODO_FILES:
        _download(_zenodo_urls(fname), varroa_dir / fname)
    for zname in ("train.zip", "val.zip", "test.zip"):
        marker = varroa_dir / (zname[:-4] + "_extracted")
        if marker.exists():
            continue
        _safe_extract(varroa_dir / zname, varroa_dir)
        marker.write_text("ok", encoding="utf-8")

    # Index every extracted image by relative path AND basename, so we can
    # resolve gt.csv paths regardless of how the zips nested their folders.
    by_rel: Dict[str, Path] = {}
    by_base: Dict[str, Path] = {}
    for p in varroa_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg"):
            rel = str(p.relative_to(varroa_dir)).replace("\\", "/")
            by_rel[rel] = p
            by_base.setdefault(p.name, p)

    # Pass 1: collect resolvable (path, label) rows.
    rows: List[Tuple[str, str]] = []
    for line in (varroa_dir / "gt.csv").read_text(encoding="utf-8").splitlines():
        parsed = parse_varroa_gt_line(line)
        if parsed is None:
            continue
        rel_norm = parsed[0].replace("\\", "/")
        if by_rel.get(rel_norm) or by_base.get(Path(rel_norm).name):
            rows.append((rel_norm, parsed[1]))

    # Pass 2: optional subsample, then write into ImageFolder structure.
    kept = sample_varroa_rows(rows, limit)
    logger.info("VarroaDataset: keeping %d of %d resolvable crops", len(kept), len(rows))
    count = 0
    for rel_norm, label in kept:
        img = by_rel.get(rel_norm) or by_base.get(Path(rel_norm).name)
        # YOLOv8-cls wants train/ and val/ ; map the dataset's "test" -> test too.
        split = split_for(rel_norm, hint=rel_norm)
        split = "val" if split == "valid" else split
        dest_dir = cls_out_dir / split / label
        dest_dir.mkdir(parents=True, exist_ok=True)
        stem = _safe_stem(rel_norm)
        (dest_dir / f"{stem}{img.suffix or '.png'}").write_bytes(img.read_bytes())
        count += 1
    logger.info("VarroaDataset (cls): wrote %d crops to %s", count, cls_out_dir)
    return count


def _safe_stem(text: str) -> str:
    """Flatten a path/stem into a collision-resistant filesystem-safe stem."""
    flat = text.replace("\\", "/").replace("/", "__")
    flat = "".join(c if (c.isalnum() or c in "._-") else "_" for c in flat)
    # Append a short hash to avoid collisions after sanitising.
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"{flat[:80]}_{digest}"


def write_data_yaml(out_dir: Path) -> Path:
    """Write the YOLO detection data.yaml (2-class: bee, pollen_bee)."""
    cfg = {
        "path": str(out_dir.resolve()),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": len(CANONICAL),
        "names": {v: k for k, v in sorted(CANONICAL.items(), key=lambda kv: kv[1])},
    }
    dest = out_dir / "bee_dataset.yaml"
    with open(dest, "w", encoding="utf-8") as fh:
        yaml.safe_dump(cfg, fh, sort_keys=False)
    return dest


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Build two-stage data: detection (VnPollenBee, bee/pollen) "
        "+ varroa classification crops (VarroaDataset)"
    )
    parser.add_argument("--raw-dir", default="datasets/raw")
    parser.add_argument(
        "--out-dir", default="datasets/data",
        help="Detection dataset out dir (bee + pollen_bee boxes).",
    )
    parser.add_argument(
        "--varroa-cls-dir", default="datasets/varroa_cls",
        help="Varroa CLASSIFICATION ImageFolder out dir (healthy/varroa crops).",
    )
    parser.add_argument("--vnpollenbee-url", default=VNPB_DRIVE_URL)
    parser.add_argument(
        "--vnpollenbee-dir",
        default=None,
        help="Folder of pre-downloaded VnPollenBee *.json (skips gdown). "
        "Use this on Colab — the Drive folder has >50 files/subfolder.",
    )
    parser.add_argument(
        "--skip-varroa", action="store_true", help="Skip the Zenodo varroa set"
    )
    parser.add_argument(
        "--varroa-limit",
        type=int,
        default=None,
        help="Cap varroa crops kept (class-stratified). Default: all 13.5k.",
    )
    parser.add_argument(
        "--skip-vnpollenbee", action="store_true", help="Skip the VnPollenBee set"
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    cls_dir = Path(args.varroa_cls_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    _ensure_dirs(out_dir)

    n_det = 0
    if not args.skip_vnpollenbee:
        n_det = prepare_vnpollenbee(
            args.vnpollenbee_url, raw_dir, out_dir, local_dir=args.vnpollenbee_dir
        )
    n_cls = 0
    if not args.skip_varroa:
        n_cls = prepare_varroa(raw_dir, cls_dir, limit=args.varroa_limit)

    yaml_path = write_data_yaml(out_dir)
    logger.info(
        "Done. Detection: %d images -> %s (%s). Varroa-cls: %d crops -> %s",
        n_det, out_dir, yaml_path, n_cls, cls_dir,
    )


if __name__ == "__main__":
    main()
