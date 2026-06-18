# Buzzlytics — Completion Design

**Date:** 2026-06-19
**Project:** Buzzlytics (CSCI435) — CV beehive health dashboard
**Status:** Scaffold ~80% built. This spec covers the remaining work to a working, mark-earning system.

---

## 1. Context

The codebase already contains a working architecture:

- **CV pipeline** (`cv_pipeline/`): detector (YOLOv8), tracker (ByteTrack-style), analytics, preprocess (CLAHE), visualize.
- **Backend** (`backend/`): FastAPI with video-upload route and WebSocket webcam route.
- **Frontend** (`frontend/`): Next.js pages (index/analysis/webcam) + components (UploadVideo, VideoPlayer, StatsPanel, HealthSummary).
- **Training** (`training/`): `train.py`, `validate.py`.
- Docker, README, git (1 commit).

**What is missing and blocks a working demo:**

1. No dataset — only `datasets/data/bee_dataset.yaml`; zero images/labels.
2. No trained weights — detector falls back to COCO `yolov8n` and detects people/cars, not bees.
3. No `config.yaml` — thresholds are magic numbers in code (loses criterion-5 marks).
4. Class taxonomy conflict — code uses `dead_bee`; spec/model section uses `wasp`.

## 2. Decisions (locked)

- **Classes (4):** `bee`, `pollen_bee`, `varroa_bee`, `wasp`. Indices `0,1,2,3`.
  - This **drops dead-bee detection**. The product/health narrative shifts from "dead-bee count = disease" to "wasp at entrance = robbing/pest threat." Report intro, README, and demo script must be updated to match so the story is internally consistent.
- **Compute:** no local GPU. Training runs on free Google Colab (T4). Dataset prep and all code run locally.
- **Datasets:** Andrew Hofer `bees-ytrmp` (bee/pollen/varroa) + Audev `wasps` (wasp), both from Roboflow Universe.
- **Model:** fine-tune `yolov8n` (nano) @ 640 — justified by the 10-FPS requirement (criterion 6) favoring a single-stage nano detector.

## 3. Phased plan

Critical path to a working demo: **Phase 1 → 2 → 3 → 5**. Phases 4 and 6 are marks-polish.

### Phase 1 — Class refactor + `config.yaml` (local, no GPU)

Rename `dead_bee` → `wasp` and the legacy `active_bee` label stays as the generic `bee` concept where it appears, with consistent naming. Touch points (verified by grep):

| File | Change |
|------|--------|
| `cv_pipeline/detector.py` | `BEE_CLASS_NAMES[3] = "wasp"`; docstrings (lines 5, 52). |
| `cv_pipeline/analytics.py` | replace `_dead_bees`/`dead`/`dead_ratio` with `_wasps`/`wasp`/`wasp_ratio`; rewrite health formula (see below); `get_summary` key `dead_bees`→`wasps`; docstring line 29, 141. |
| `cv_pipeline/visualize.py` | color map `dead_bee`→`wasp` (keep a distinct color, e.g. orange/purple, not gray); stats label line 271 `Dead`→`Wasps`. |
| `frontend/components/StatsPanel.jsx` | key `dead_bees`→`wasps`, label `Dead Bees`→`Wasps`. |
| `frontend/components/HealthSummary.jsx` | `deadRatio`→`waspRatio`; threat copy (lines 47, 53) → wasp/robbing language; thresholds reviewed. |
| `datasets/data/bee_dataset.yaml` | `3: dead_bee`→`3: wasp` (full rewrite in Phase 2). |
| `training/train.py`, `training/validate.py` | class-name lists/docstrings → `["bee","pollen_bee","varroa_bee","wasp"]`. |
| `README.md` | 4-class description + health narrative. |

**New health formula** (in analytics, sourced from `config.yaml`):
```
base = 70
+10 if pollen_ratio > pollen_good_threshold     (good foraging)
-20 if varroa_ratio > varroa_warn_threshold     (mite infestation)
-25 if wasp_ratio   > wasp_threat_threshold      (pest / robbing threat)
-10 if activity_rate < low_activity_threshold    (weak colony)
status: >70 Healthy, 40-70 Warning, <40 Critical
```

**`config.yaml`** (new, project root) — single source of truth for thresholds. Sections:
```yaml
detector:   { model_path, conf_threshold, iou_threshold, imgsz }
tracker:    { max_age, min_hits, iou_match }
analytics:  { pollen_good_threshold, varroa_warn_threshold,
              wasp_threat_threshold, low_activity_threshold,
              health_weights: {...} }
visualize:  { colors: { bee, pollen_bee, varroa_bee, wasp } }
video:      { frame_skip }
```
Loader: `cv_pipeline/config.py` reads YAML once, exposes a typed config object. Detector/analytics/visualize/pipeline read from it instead of hardcoded literals. Sensible defaults if file missing (so app never hard-crashes).

### Phase 2 — Data pipeline (local; needs Roboflow API key)

`datasets/prepare_dataset.py`:
1. Download both datasets via Roboflow API (YOLOv8 export format) into `datasets/raw/hofer/` and `datasets/raw/wasps/`.
2. **Inspect** each exported `data.yaml` — class names AND order differ per dataset; do NOT assume. Print the discovered mapping.
3. Build a remap table to unified ids `bee=0, pollen_bee=1, varroa_bee=2, wasp=3`. (Hofer's bee/pollen/varroa names may differ, e.g. `bees`, `pollenbearing`, `varroa`; map by inspection.)
4. Rewrite each label file's leading class id; copy images+labels into merged `datasets/data/{train,valid,test}/{images,labels}/`.
5. Emit unified `datasets/data/bee_dataset.yaml` (`nc: 4`, names, split paths).

Risks noted in report: varroa is a tiny object (small-object detection is hard → lower mAP expected for class 2); wasp images come from a different visual context than hive entrances (domain gap) — acceptable for a distinct class, documented as a limitation.

### Phase 3 — Training (Colab T4)

`training/colab_train.ipynb`:
- Install `ultralytics`; mount/upload the merged dataset (zip or Roboflow pull).
- Fine-tune `yolov8n.pt` @ imgsz 640, ~100 epochs, standard augmentations (mosaic, hsv, flip).
- Record per-class mAP@50 and mAP@50-95, precision, recall.
- Export `best.pt` → committed/placed at `cv_pipeline/weights/best.pt` (gitignore the large file or use LFS; document where it lives).
- `config.yaml:detector.model_path` points to it; detector loads it, falls back to `yolov8n` with a clear log warning if absent.

### Phase 4 — Robustness (criterion 2)

- Input validation (check what already exists in routes/pipeline first): empty file, corrupt/undecodable video, zero detections, very low resolution, wrong file type. Return clear API errors, never 500-crash.
- Assemble 30–50 challenging test clips/images (dawn, glare, overcast, blur, empty hive, odd angle). Document results incl. honest failures in the report.

### Phase 5 — Wire model in + verify

- Place `best.pt`, run a real hive video end-to-end through the pipeline.
- Confirm boxes/labels/colors correct for all 4 classes.
- Benchmark FPS on the demo machine; record machine-spec→FPS table (criterion 6, must hit ≥10 FPS — use frame-skip in live mode if needed).

### Phase 6 — Report evidence

- mAP-per-class table, FPS/latency table, failure-case images, architecture diagram (draw.io/excalidraw), consistent IEEE/APA citations.

## 4. Out of scope (YAGNI)

- Auth, user accounts, database persistence (in-memory store is fine for the demo).
- Cloud deployment — local + Docker is enough.
- 5th class / dead-bee detection (explicitly dropped).

## 5. Success criteria

- App processes a real hive video and draws correct colored boxes for bee/pollen_bee/varroa_bee/wasp.
- Live counters + health summary reflect real detections.
- ≥10 FPS measured on demo machine.
- `config.yaml` drives all thresholds; no magic numbers.
- Training produced per-class mAP numbers for the report.
- README/report/demo narrative consistent with the 4-class (wasp, not dead-bee) story.
