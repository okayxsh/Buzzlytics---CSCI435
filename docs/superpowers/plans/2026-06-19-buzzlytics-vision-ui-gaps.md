# Buzzlytics Vision + UI Gaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Close the gaps between the built system and the assignment brief: add the missing vision techniques (white balance, MOG2 change detection, morphological ops) so Criterion 1 (15 marks) genuinely shows 5 techniques, and assemble the dashboard UI (timeline chart, counters, health summary, input tabs, image upload) for Criterion 3 (10 marks).

**Architecture:** Existing OpenCV/YOLOv8 pipeline + FastAPI + Next.js. Add `apply_white_balance` to `preprocess.py`; a new `cv_pipeline/motion.py` (MOG2 + morphology producing an activity signal); thread motion into `pipeline.py` and accumulate a per-frame activity timeline; add a `/api/image` backend route; build `ActivityTimeline.jsx` and `UploadImage.jsx`, and assemble `analysis.jsx` with Image/Video/Webcam tabs rendering StatsPanel + HealthSummary + timeline.

**Tech Stack:** Python 3.11, OpenCV, ultralytics 8.4.71, FastAPI, pytest, Next.js/React, recharts 2.12.

## Global Constraints

- Unified classes: `bee/pollen_bee/varroa_bee/wasp` (ids 0-3). Wasp box color BGR `(0,140,255)`.
- All tunables live in `config.yaml` (single source of truth via `cv_pipeline/config.py`); no magic numbers in pipeline logic.
- Vision techniques must be genuinely used, not bolted on: white balance feeds detection robustness; MOG2 activity feeds the entrance-activity timeline; morphology cleans the MOG2 mask and separates touching blobs.
- Python venv: `venv/Scripts/python.exe`. Tests: `venv/Scripts/python.exe -m pytest`.
- Summary keys unchanged: `total_bees, active_bees, pollen_bees, varroa_bees, wasps, health_score, health_status, activity_rate, infection_rate`.
- Performance target ≥10 FPS (criterion 6) — motion step must stay cheap (mask ops at processing resolution).

---

### Task 1: White balance in preprocessing

**Files:**
- Modify: `cv_pipeline/preprocess.py`
- Modify: `cv_pipeline/config.py` (add `preprocess` defaults), `config.yaml`
- Test: `tests/test_preprocess_wb.py`

**Interfaces:**
- Produces: `apply_white_balance(frame: NDArray[uint8]) -> NDArray[uint8]` (gray-world). `preprocess_frame(..., white_balance: bool = True)` applies WB before CLAHE.

- [ ] **Step 1: Write failing test** — `tests/test_preprocess_wb.py`:
```python
import numpy as np
from cv_pipeline.preprocess import apply_white_balance


def test_white_balance_neutralizes_color_cast():
    # Blue-cast image: B channel high, R low. Gray-world should rebalance
    # channel means toward each other.
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    frame[:, :, 0] = 200  # B
    frame[:, :, 1] = 120  # G
    frame[:, :, 2] = 40   # R
    out = apply_white_balance(frame)
    means = out.reshape(-1, 3).mean(axis=0)
    assert out.shape == frame.shape and out.dtype == np.uint8
    # channel means closer together than before (spread shrinks)
    assert means.max() - means.min() < (200 - 40)


def test_white_balance_gray_image_unchanged():
    frame = np.full((16, 16, 3), 128, dtype=np.uint8)
    out = apply_white_balance(frame)
    assert abs(int(out.mean()) - 128) <= 2
```

- [ ] **Step 2: Run, verify fail** — `venv/Scripts/python.exe -m pytest tests/test_preprocess_wb.py -v` → ImportError.

- [ ] **Step 3: Implement** `apply_white_balance` in `preprocess.py`:
```python
def apply_white_balance(frame: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Gray-world white balance: scale each BGR channel so their means match.

    Corrects colour casts from dawn/dusk/overcast hive footage before
    detection. Returns a BGR uint8 frame of the same shape.
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(f"Expected numpy array, got {type(frame).__name__}")
    if frame.size == 0:
        raise ValueError("Cannot white-balance an empty frame")
    result = frame.astype(np.float32)
    means = result.reshape(-1, 3).mean(axis=0)
    gray = float(means.mean())
    for c in range(3):
        if means[c] > 1e-6:
            result[:, :, c] *= gray / means[c]
    return np.clip(result, 0, 255).astype(np.uint8)
```
Add a `white_balance: bool = True` param to `preprocess_frame`; apply it as Step 0 (before denoise/CLAHE) when true. Read default from `config.yaml:preprocess.white_balance` at the pipeline call site (do not import config inside preprocess — keep preprocess pure; the pipeline passes the flag).

- [ ] **Step 4: Config** — add to `_DEFAULTS` and `config.yaml`:
```yaml
preprocess:
  white_balance: true
  clahe_clip_limit: 2.0
  denoise_strength: 10
```

- [ ] **Step 5: Run tests green; commit**
```bash
venv/Scripts/python.exe -m pytest tests/test_preprocess_wb.py -v
git add cv_pipeline/preprocess.py cv_pipeline/config.py config.yaml tests/test_preprocess_wb.py
git commit -m "Add gray-world white balance to preprocessing (vision technique 1)"
```

---

### Task 2: MOG2 motion + morphology module

**Files:**
- Create: `cv_pipeline/motion.py`
- Modify: `cv_pipeline/config.py`, `config.yaml` (add `motion` section)
- Test: `tests/test_motion.py`

**Interfaces:**
- Produces: `MotionDetector(history=500, var_threshold=16, detect_shadows=True, kernel_size=3)`. Method `process(frame) -> MotionResult` with fields `mask: NDArray[uint8]` (cleaned binary 0/255), `activity_ratio: float` (foreground fraction 0-1), `blob_count: int`. Uses `cv2.createBackgroundSubtractorMOG2` (technique 4) + `cv2.morphologyEx` open→close with an elliptical `getStructuringElement` (technique 5).

- [ ] **Step 1: Write failing test** — `tests/test_motion.py`:
```python
import numpy as np
from cv_pipeline.motion import MotionDetector


def test_motion_detects_change_between_frames():
    det = MotionDetector(history=5, var_threshold=16, detect_shadows=False)
    static = np.zeros((64, 64, 3), dtype=np.uint8)
    for _ in range(5):           # warm up background model on static frames
        r0 = det.process(static)
    moved = static.copy()
    moved[20:40, 20:40] = 255    # a bright block appears
    r1 = det.process(moved)
    assert r1.activity_ratio > r0.activity_ratio
    assert r1.mask.shape == (64, 64) and r1.mask.dtype == np.uint8
    assert set(np.unique(r1.mask)).issubset({0, 255})
    assert r1.blob_count >= 1


def test_morphology_removes_salt_noise():
    det = MotionDetector(history=5, var_threshold=16, detect_shadows=False, kernel_size=5)
    base = np.zeros((64, 64, 3), dtype=np.uint8)
    for _ in range(5):
        det.process(base)
    noisy = base.copy()
    rng = np.random.default_rng(0)
    # sprinkle isolated single-pixel speckle
    ys = rng.integers(0, 64, 30); xs = rng.integers(0, 64, 30)
    noisy[ys, xs] = 255
    r = det.process(noisy)
    # open() should erase most isolated speckle -> very low activity
    assert r.activity_ratio < 0.05
```

- [ ] **Step 2: Run, verify fail** — ImportError.

- [ ] **Step 3: Implement** `cv_pipeline/motion.py`:
```python
"""MOG2 background-subtraction motion detection with morphological cleanup.

Provides entrance-activity measurement for the Buzzlytics pipeline:
- cv2.BackgroundSubtractorMOG2 models the static hive background and
  flags moving bees as foreground (vision technique: change detection).
- Morphological opening then closing cleans the binary mask, removing
  speckle and merging fragmented blobs (vision technique: morphology).
The foreground fraction is a proxy for entrance traffic over time.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass
class MotionResult:
    mask: NDArray[np.uint8]
    activity_ratio: float
    blob_count: int


class MotionDetector:
    """MOG2 + morphology entrance-activity detector."""

    def __init__(self, history: int = 500, var_threshold: float = 16.0,
                 detect_shadows: bool = True, kernel_size: int = 3) -> None:
        self._bg = cv2.createBackgroundSubtractorMOG2(
            history=history, varThreshold=var_threshold,
            detectShadows=detect_shadows,
        )
        self._kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
        )

    def process(self, frame: NDArray[np.uint8]) -> MotionResult:
        if frame is None or getattr(frame, "size", 0) == 0:
            raise ValueError("Cannot process an empty frame")
        fg = self._bg.apply(frame)
        # MOG2 marks shadows as 127; keep only hard foreground (255).
        _, binary = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, self._kernel)
        cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, self._kernel)
        activity = float(np.count_nonzero(cleaned)) / cleaned.size
        n_labels, _ = cv2.connectedComponents(cleaned)
        return MotionResult(mask=cleaned, activity_ratio=activity,
                            blob_count=max(0, n_labels - 1))
```

- [ ] **Step 4: Config** — add to `_DEFAULTS` + `config.yaml`:
```yaml
motion:
  history: 500
  var_threshold: 16
  detect_shadows: true
  kernel_size: 3
```

- [ ] **Step 5: Tests green; commit**
```bash
venv/Scripts/python.exe -m pytest tests/test_motion.py -v
git add cv_pipeline/motion.py cv_pipeline/config.py config.yaml tests/test_motion.py
git commit -m "Add MOG2 change detection + morphological cleanup (vision techniques 4-5)"
```

---

### Task 3: Thread motion + white balance into the pipeline; accumulate activity timeline

**Files:**
- Modify: `cv_pipeline/pipeline.py`
- Test: `tests/test_pipeline_motion.py`

**Interfaces:**
- Consumes: `MotionDetector`, `apply_white_balance` (via preprocess flag), config.
- Produces: `CVPipeline` builds a `MotionDetector` from config and a white-balance flag. `process_frame` return dict gains `motion: {activity_ratio, blob_count}`. `process_video` accumulates `timeline: list[{frame, activity_ratio, total_bees}]` in its final results dict.

- [ ] **Step 1: Write failing test** — `tests/test_pipeline_motion.py` (mock YOLO as in test_pipeline_config.py):
```python
import numpy as np
from unittest.mock import patch, MagicMock
from cv_pipeline.pipeline import CVPipeline


def _pipe():
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        return CVPipeline(use_tracker=False)


def test_process_frame_includes_motion():
    pipe = _pipe()
    # stub detector to avoid the mocked-YOLO inference returning junk
    pipe.detector.detect = lambda f: []
    out = pipe.process_frame(np.zeros((64, 64, 3), dtype=np.uint8))
    assert "motion" in out
    assert "activity_ratio" in out["motion"] and "blob_count" in out["motion"]
```

- [ ] **Step 2: Run, verify fail** — KeyError 'motion'.

- [ ] **Step 3: Implement** — in `CVPipeline.__init__` read `cfg["motion"]` and build `self.motion = MotionDetector(**cfg["motion"])`; read `self._white_balance = cfg["preprocess"]["white_balance"]`. In `process_frame`: call `preprocess_frame(frame, white_balance=self._white_balance, ...)`, run `motion_result = self.motion.process(processed)`, add `"motion": {"activity_ratio": motion_result.activity_ratio, "blob_count": motion_result.blob_count}` to the returned dict. In `process_video`: append `{"frame": idx, "activity_ratio": motion_result.activity_ratio, "total_bees": summary["total_bees"]}` to a `timeline` list each frame; include `timeline` in the final results dict. Keep `preprocess` defaults available in config (Task 1/2 added them).

- [ ] **Step 4: Run full suite green; commit**
```bash
venv/Scripts/python.exe -m pytest -v
git add cv_pipeline/pipeline.py tests/test_pipeline_motion.py
git commit -m "Wire white balance + MOG2 motion into pipeline; accumulate activity timeline"
```

---

### Task 4: Backend — expose timeline + image endpoint

**Files:**
- Modify: `backend/routes/video_routes.py` (include `timeline` in the result payload)
- Create: `backend/routes/image_routes.py` (POST `/api/image` — process one image)
- Modify: `backend/main.py` (register image router)
- Test: `tests/test_image_route.py` (FastAPI TestClient, YOLO mocked)

**Interfaces:**
- Produces: `POST /api/image` accepts an uploaded image file, runs `CVPipeline.process_frame`, returns JSON `{summary, motion}` + a base64 annotated image (mirror the websocket route's encoding). Video result JSON includes `timeline`.

- [ ] **Step 1: Write failing test** — `tests/test_image_route.py`: use `fastapi.testclient.TestClient`, patch YOLO, POST a small PNG (encode a numpy array with cv2.imencode), assert 200 and `summary`/`annotated_image` keys. (If TestClient construction triggers heavy imports, mark with the same YOLO patch used elsewhere.)

- [ ] **Step 2: Run, verify fail.**

- [ ] **Step 3: Implement** the image route mirroring `websocket_routes.py` frame handling (decode upload → `process_frame` → encode annotated frame to base64 JPEG → return with summary + motion). Register it in `main.py` like the other routers. Add `timeline` to the video result dict returned by `video_routes` (read it from the pipeline's final results).

- [ ] **Step 4: Run suite green; commit**
```bash
venv/Scripts/python.exe -m pytest tests/test_image_route.py -v
git add backend/ tests/test_image_route.py
git commit -m "Add image-processing endpoint and expose activity timeline in video results"
```

---

### Task 5: Frontend — ActivityTimeline + UploadImage components

**Files:**
- Create: `frontend/components/ActivityTimeline.jsx` (recharts AreaChart of activity over frames)
- Create: `frontend/components/UploadImage.jsx` (image picker → POST /api/image → show annotated image + summary)
- Modify: `frontend/services/api.js` (add `imageApi.process(file)` and timeline access)

**Interfaces:**
- Produces: `<ActivityTimeline data={timeline} />` renders a responsive recharts AreaChart (x=frame, y=activity_ratio or total_bees). `<UploadImage onResult={...} />`.

- [ ] **Step 1: Implement `ActivityTimeline.jsx`** using `recharts` (`ResponsiveContainer`, `AreaChart`, `XAxis`, `YAxis`, `Tooltip`, `Area`). Guard empty/null data with a placeholder. Match the existing dark theme classes used in StatsPanel.

- [ ] **Step 2: Implement `UploadImage.jsx`** — file input (accept="image/*"), POST via `imageApi.process`, render returned annotated image + a compact summary. Mirror `UploadVideo.jsx` structure/props (`onUploadStart/Complete/Error`).

- [ ] **Step 3: Add `imageApi` to `services/api.js`** — `process(file)` posts multipart to `/api/image`; export a `getTimeline`/result helper if needed.

- [ ] **Step 4: Verify build compiles** — `cd frontend && npm run build` (compile step must pass). Commit.
```bash
git add frontend/components/ActivityTimeline.jsx frontend/components/UploadImage.jsx frontend/services/api.js
git commit -m "Add activity timeline chart and image-upload components"
```

---

### Task 6: Assemble the analysis dashboard (tabs + panels + timeline)

**Files:**
- Modify: `frontend/pages/analysis.jsx`

**Interfaces:**
- Consumes: `UploadImage`, `UploadVideo`, `VideoPlayer`, `StatsPanel`, `HealthSummary`, `ActivityTimeline`, webcam link/component.

- [ ] **Step 1: Implement** — add an input-mode tab bar (Image / Video / Webcam). Render `UploadImage` or `UploadVideo` per tab (Webcam tab links to/embeds the existing webcam page). On a completed analysis, render `StatsPanel` (counters) + `HealthSummary` (verdict) + `ActivityTimeline` (entrance traffic) using the result summary + timeline. Keep the existing dark theme and layout idiom. Pull the summary/timeline from the API result already fetched by the page.

- [ ] **Step 2: Verify build compiles** — `cd frontend && npm run build` (compile step must pass; the page-data collection step may still fail on the pre-existing WIP `/analysis` issue — note it). Confirm the page renders StatsPanel + HealthSummary + ActivityTimeline + tabs with no React errors in the compile output.

- [ ] **Step 3: Commit**
```bash
git add frontend/pages/analysis.jsx
git commit -m "Assemble analysis dashboard: input tabs, counters, health summary, activity timeline"
```

---

## Self-Review

- **Spec coverage:** Criterion-1 techniques — white balance (T1), MOG2 (T2 technique 4), morphology (T2 technique 5), plus existing CLAHE/detection/tracking = 5+ genuinely-used techniques. Criterion-3 UI — timeline (T5), counters + health summary assembled (T6), Image/Video/Webcam tabs (T6), image upload (T4/T5). All mapped.
- **Placeholder scan:** every code step contains full code or a precise mirror-this instruction.
- **Type consistency:** `MotionResult` fields (`mask/activity_ratio/blob_count`) used identically in motion.py, pipeline, and tests. Summary keys unchanged. Config sections (`preprocess`, `motion`) added once and read in pipeline.
- **Genuine use:** motion activity → timeline (not bolted on); morphology → mask cleanup; white balance → robustness under varying light.
