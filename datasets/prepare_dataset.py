"""
Download and merge Roboflow bee + wasp datasets into one unified
4-class YOLOv8 dataset for Buzzlytics.

Unified classes: 0=bee, 1=pollen_bee, 2=varroa_bee, 3=wasp.

The two source datasets use their own class names and ordering, so
this script inspects each exported data.yaml, maps source ids to the
unified ids by name/alias, rewrites every label file, and copies
images+labels into datasets/data/{train,valid,test}.

Usage:
    set ROBOFLOW_API_KEY=...   (or pass --api-key)
    python datasets/prepare_dataset.py --api-key YOUR_KEY
"""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path
from typing import Dict, List

import yaml

logger = logging.getLogger(__name__)

CANONICAL: Dict[str, int] = {"bee": 0, "pollen_bee": 1, "varroa_bee": 2, "wasp": 3}

# Map raw dataset class names (lowercased) to canonical names. Extend
# after inspecting the actual exported data.yaml of each dataset.
ALIASES: Dict[str, str] = {
    "bee": "bee", "bees": "bee", "honeybee": "bee", "worker": "bee",
    "pollen": "pollen_bee", "pollenbearing": "pollen_bee",
    "pollen_bee": "pollen_bee", "pollenbee": "pollen_bee",
    "varroa": "varroa_bee", "varroa_bee": "varroa_bee",
    "varroa_infected": "varroa_bee",
    # NOTE: hofer's standalone "mite", "queen", "queen_cell" classes are
    # intentionally NOT mapped -> dropped. We only keep bee/pollen/varroa.
    # Wasp class is sourced from the Vespa orientalis (Oriental hornet)
    # dataset, a real honeybee-hive predator, since Audev's export is broken.
    "wasp": "wasp", "wasps": "wasp", "hornet": "wasp",
    "vespa_orientalis": "wasp", "vespaorientalis": "wasp", "vespa": "wasp",
}


def build_id_map(
    source_names: List[str],
    canonical: Dict[str, int],
    aliases: Dict[str, str],
) -> Dict[int, int]:
    """Map a dataset's class indices to unified class ids.

    Args:
        source_names: Class names in the dataset's own order.
        canonical: Unified name -> unified id.
        aliases: Raw (lowercased) name -> canonical name.

    Returns:
        Mapping of source index -> unified id. Source classes that
        cannot be mapped are omitted (their labels get dropped).
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
    """Rewrite the leading class id of each YOLO label line.

    Lines whose source class id is not in ``id_map`` are dropped.

    Args:
        lines: Raw label-file lines (``"<cls> cx cy w h"``).
        id_map: source class id -> unified class id.

    Returns:
        Remapped, filtered lines (trailing newline preserved).
    """
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


def _read_names(data_yaml: Path) -> List[str]:
    """Read class names (ordered) from a YOLO data.yaml."""
    with open(data_yaml, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    names = doc["names"]
    if isinstance(names, dict):
        return [names[k] for k in sorted(names)]
    return list(names)


def _merge_split(
    src_root: Path, split: str, id_map: Dict[int, int], dst_root: Path, prefix: str
) -> int:
    """Copy and remap one split (train/valid/test). Returns image count."""
    src_img = src_root / split / "images"
    src_lbl = src_root / split / "labels"
    if not src_img.is_dir():
        return 0
    dst_img = dst_root / split / "images"
    dst_lbl = dst_root / split / "labels"
    dst_img.mkdir(parents=True, exist_ok=True)
    dst_lbl.mkdir(parents=True, exist_ok=True)

    count = 0
    for img in src_img.iterdir():
        if not img.is_file():
            continue
        new_name = f"{prefix}_{img.name}"
        shutil.copy2(img, dst_img / new_name)
        lbl = src_lbl / (img.stem + ".txt")
        if lbl.is_file():
            lines = lbl.read_text(encoding="utf-8").splitlines(keepends=True)
            remapped = remap_label_lines(lines, id_map)
            (dst_lbl / f"{prefix}_{img.stem}.txt").write_text(
                "".join(remapped), encoding="utf-8"
            )
        count += 1
    return count


def _download_roboflow(
    api_key: str, ws: str, proj: str, version: int, location: Path
) -> Path:
    """Download a Roboflow YOLOv8 export via the REST export link.

    The roboflow SDK's ``version.download`` builds a regional-bucket URL
    that 404s for some Universe projects. The public REST endpoint returns
    a working signed ``export.link`` instead, which we fetch and unzip.

    Args:
        api_key: Roboflow private API key.
        ws: Workspace slug.
        proj: Project slug.
        version: Dataset version number.
        location: Destination directory (created if missing).

    Returns:
        The destination path containing the extracted dataset.

    Raises:
        RuntimeError: If no export link is available after retries.
    """
    import io
    import json
    import time
    import urllib.request
    import zipfile

    location.mkdir(parents=True, exist_ok=True)
    api = (
        f"https://api.roboflow.com/{ws}/{proj}/{version}/yolov8"
        f"?api_key={api_key}"
    )
    link = None
    for attempt in range(5):
        with urllib.request.urlopen(api, timeout=60) as resp:
            payload = json.load(resp)
        link = payload.get("export", {}).get("link")
        if link:
            break
        logger.info("export not ready for %s/%s (attempt %d); waiting...", ws, proj, attempt + 1)
        time.sleep(10)
    if not link:
        raise RuntimeError(f"No export link for {ws}/{proj} v{version}")

    req = urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()
    target = location.resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        # Guard against Zip Slip: reject any member that escapes ``location``.
        for member in zf.namelist():
            dest = (target / member).resolve()
            if target != dest and target not in dest.parents:
                raise RuntimeError(f"Zip entry escapes target directory: {member}")
        zf.extractall(str(target))
    return location


def download_datasets(api_key: str, raw_dir: Path) -> List[Path]:
    """Download bee + wasp datasets via Roboflow REST. Returns dataset roots.

    Sources:
        - andrew-hofer-1qh7e/bees-ytrmp v5: bee/pollen/varroa (+ unused classes).
        - tfg-g55nk/vespa-orientalis v3: Oriental hornet, mapped to the wasp
          class (a real honeybee-hive predator). Substitutes Audev/wasps,
          whose Roboflow export is broken server-side.
    """
    roots: List[Path] = []

    # (workspace, project, version, local sub-dir).
    sources = [
        ("andrew-hofer-1qh7e", "bees-ytrmp", 5, "hofer"),
        ("tfg-g55nk", "vespa-orientalis", 3, "wasps"),
    ]
    for ws, proj_id, vnum, sub in sources:
        location = raw_dir / sub
        if (location / "data.yaml").is_file():
            logger.info("%s already downloaded at %s; skipping.", sub, location)
            roots.append(location)
            continue
        logger.info("downloading %s (%s/%s v%d)...", sub, ws, proj_id, vnum)
        roots.append(_download_roboflow(api_key, ws, proj_id, vnum, location))
    return roots


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Build the unified bee+wasp dataset")
    parser.add_argument("--api-key", default=None, help="Roboflow API key")
    parser.add_argument("--raw-dir", default="datasets/raw")
    parser.add_argument("--out-dir", default="datasets/data")
    args = parser.parse_args()

    import os
    api_key = args.api_key or os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        raise SystemExit("Provide --api-key or set ROBOFLOW_API_KEY")

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    roots = download_datasets(api_key, raw_dir)
    for root, prefix in zip(roots, ("hofer", "wasps")):
        names = _read_names(root / "data.yaml")
        id_map = build_id_map(names, CANONICAL, ALIASES)
        logger.info("%s classes %s -> id_map %s", prefix, names, id_map)
        total = 0
        for split in ("train", "valid", "test"):
            total += _merge_split(root, split, id_map, out_dir, prefix)
        logger.info("%s: merged %d images", prefix, total)

    logger.info("Done. Unified dataset at %s", out_dir)


if __name__ == "__main__":
    main()
