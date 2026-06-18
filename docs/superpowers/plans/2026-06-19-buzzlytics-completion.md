# Buzzlytics Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Buzzlytics so it detects 4 bee classes (bee/pollen_bee/varroa_bee/wasp) from real hive video, drives all thresholds from `config.yaml`, and ships with a trained model + report evidence.

**Architecture:** Existing FastAPI + Next.js + OpenCV/YOLOv8 scaffold. This plan (a) refactors the class taxonomy `active_bee/varroa_infected/dead_bee` → unified `bee/varroa_bee/wasp`, (b) externalizes thresholds into `config.yaml` read by a new `cv_pipeline/config.py`, (c) adds a Roboflow dataset-merge script, (d) provides a Colab training notebook, then (e) wires the trained weights in and benchmarks.

**Tech Stack:** Python 3.11, ultralytics 8.1.0, OpenCV, FastAPI, PyYAML, pytest (dev), Next.js/React, Roboflow API, Google Colab (T4).

## Global Constraints

- Python venv at `venv/` (Windows: `venv/Scripts/python.exe`). Run all Python via that interpreter.
- Unified classes, fixed order: `0=bee, 1=pollen_bee, 2=varroa_bee, 3=wasp`. Use these exact strings everywhere.
- No local GPU. Training runs on free Google Colab T4 only.
- All thresholds/colors/weights live in `config.yaml` — no magic-number literals in pipeline code.
- Wasp box color: BGR `(0, 140, 255)` (orange). Existing: bee green `(0,200,0)`, pollen yellow `(0,220,255)`, varroa red `(0,0,220)`.
- Performance target: ≥10 FPS on demo machine (criterion 6).
- Summary dict keys the frontend reads: `total_bees, active_bees, pollen_bees, varroa_bees, wasps, activity_rate, infection_rate, health_score, health_status`.
- ultralytics is pinned at 8.1.0 in `backend/requirements.txt`; do not bump it.

---

### Task 1: Test harness + `config.yaml` loader

**Files:**
- Create: `requirements-dev.txt`
- Create: `config.yaml`
- Create: `cv_pipeline/config.py`
- Create: `tests/__init__.py`, `tests/test_config.py`
- Create: `pytest.ini`

**Interfaces:**
- Produces: `cv_pipeline/config.py::load_config(path: str = "config.yaml") -> dict` — returns defaults deep-merged with file contents; never raises on missing file (logs a warning, returns defaults). Also `get_default_config() -> dict`.

- [ ] **Step 1: Add dev deps + pytest config**

Create `requirements-dev.txt`:
```
pytest==8.2.0
roboflow==1.1.28
```
Create `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
```
Install:
```bash
venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

- [ ] **Step 2: Write the failing test**

Create `tests/__init__.py` (empty). Create `tests/test_config.py`:
```python
"""Tests for the config loader."""
from pathlib import Path

from cv_pipeline.config import load_config, get_default_config


def test_missing_file_returns_defaults():
    cfg = load_config("definitely_does_not_exist.yaml")
    assert cfg == get_default_config()


def test_defaults_have_unified_classes():
    cfg = get_default_config()
    colors = cfg["visualize"]["colors"]
    assert set(colors) == {"bee", "pollen_bee", "varroa_bee", "wasp"}
    assert colors["wasp"] == [0, 140, 255]


def test_file_overrides_merge_over_defaults(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("detector:\n  conf_threshold: 0.5\n")
    cfg = load_config(str(p))
    # overridden value
    assert cfg["detector"]["conf_threshold"] == 0.5
    # untouched default still present (deep merge, not replace)
    assert cfg["detector"]["iou_threshold"] == 0.45
    assert cfg["analytics"]["health_weights"]["wasp_penalty"] == 25
```

- [ ] **Step 3: Run test, verify it fails**

Run: `venv/Scripts/python.exe -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cv_pipeline.config'`

- [ ] **Step 4: Write `cv_pipeline/config.py`**

```python
"""Configuration loader for the Buzzlytics CV pipeline.

Loads thresholds, colors, and weights from a YAML file, deep-merged
over built-in defaults so the application runs even if the file is
absent or partial. This is the single source of truth for tunable
values — pipeline modules read from here instead of hardcoding.
"""

from __future__ import annotations

import copy
import logging
import os
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

_DEFAULTS: Dict[str, Any] = {
    "detector": {
        "model_path": "cv_pipeline/weights/best.pt",
        "conf_threshold": 0.25,
        "iou_threshold": 0.45,
        "imgsz": 640,
    },
    "tracker": {"max_age": 30, "min_hits": 3, "iou_match": 0.3},
    "analytics": {
        "pollen_good_threshold": 0.1,
        "varroa_warn_threshold": 0.15,
        "wasp_threat_threshold": 0.05,
        "low_activity_threshold": 0.3,
        "health_weights": {
            "base": 70,
            "pollen_bonus": 10,
            "varroa_penalty": 20,
            "wasp_penalty": 25,
            "low_activity_penalty": 10,
        },
    },
    "visualize": {
        "colors": {
            "bee": [0, 200, 0],
            "pollen_bee": [0, 220, 255],
            "varroa_bee": [0, 0, 220],
            "wasp": [0, 140, 255],
        }
    },
    "video": {"frame_skip": 2},
}


def get_default_config() -> Dict[str, Any]:
    """Return a deep copy of the built-in default configuration."""
    return copy.deepcopy(_DEFAULTS)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``override`` into ``base`` and return ``base``."""
    for key, value in override.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from ``path`` merged over defaults.

    Args:
        path: Path to a YAML config file.

    Returns:
        Configuration dict. If the file is missing or empty, the
        built-in defaults are returned unchanged.
    """
    cfg = get_default_config()
    if not os.path.isfile(path):
        logger.warning("Config file '%s' not found; using defaults.", path)
        return cfg
    with open(path, "r", encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh) or {}
    if not isinstance(loaded, dict):
        logger.warning("Config file '%s' is not a mapping; using defaults.", path)
        return cfg
    return _deep_merge(cfg, loaded)
```

- [ ] **Step 5: Create `config.yaml` mirroring the defaults**

```yaml
# Buzzlytics configuration — single source of truth for tunable values.
detector:
  model_path: cv_pipeline/weights/best.pt
  conf_threshold: 0.25
  iou_threshold: 0.45
  imgsz: 640

tracker:
  max_age: 30
  min_hits: 3
  iou_match: 0.3

analytics:
  pollen_good_threshold: 0.1
  varroa_warn_threshold: 0.15
  wasp_threat_threshold: 0.05
  low_activity_threshold: 0.3
  health_weights:
    base: 70
    pollen_bonus: 10
    varroa_penalty: 20
    wasp_penalty: 25
    low_activity_penalty: 10

visualize:
  colors:
    bee: [0, 200, 0]
    pollen_bee: [0, 220, 255]
    varroa_bee: [0, 0, 220]
    wasp: [0, 140, 255]

video:
  frame_skip: 2
```

- [ ] **Step 6: Run tests, verify pass**

Run: `venv/Scripts/python.exe -m pytest tests/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add requirements-dev.txt pytest.ini config.yaml cv_pipeline/config.py tests/
git commit -m "Add config loader and config.yaml as single source of truth"
```

---

### Task 2: Analytics — unified classes + config-driven health

**Files:**
- Modify: `cv_pipeline/analytics.py`
- Create: `tests/test_analytics.py`

**Interfaces:**
- Consumes: `cv_pipeline/config.py::load_config`, `cv_pipeline/tracker.py::Track`.
- Produces: `AnalyticsEngine(config: dict | None = None)`. `update(tracks)` counts class names `bee/pollen_bee/varroa_bee/wasp`. `get_summary()` returns keys listed in Global Constraints (with `wasps`, no `dead_bees`/`varroa_infected`).

- [ ] **Step 1: Write failing tests**

Create `tests/test_analytics.py`:
```python
"""Tests for the analytics engine."""
from dataclasses import dataclass

from cv_pipeline.analytics import AnalyticsEngine


@dataclass
class FakeTrack:
    class_name: str
    track_id: int = 0
    bbox: list = None
    confidence: float = 0.9
    class_id: int = 0
    age: int = 1


def _tracks(names):
    return [FakeTrack(class_name=n, track_id=i) for i, n in enumerate(names)]


def test_counts_unified_classes():
    eng = AnalyticsEngine()
    eng.update(_tracks(["bee", "bee", "pollen_bee", "varroa_bee", "wasp"]))
    s = eng.get_summary()
    assert s["total_bees"] == 5
    assert s["active_bees"] == 2
    assert s["pollen_bees"] == 1
    assert s["varroa_bees"] == 1
    assert s["wasps"] == 1
    assert "dead_bees" not in s
    assert "varroa_infected" not in s


def test_wasp_presence_penalizes_health():
    eng = AnalyticsEngine()
    # 10 bees, no wasp -> healthy-ish baseline
    eng.update(_tracks(["bee"] * 10))
    base = eng.compute_health_score()
    # add wasps above 5% threshold -> penalty applied
    eng.update(_tracks(["bee"] * 8 + ["wasp"] * 2))
    with_wasp = eng.compute_health_score()
    assert with_wasp < base


def test_empty_returns_zero_score():
    eng = AnalyticsEngine()
    eng.update([])
    assert eng.compute_health_score() == 0.0
    assert eng.get_summary()["total_bees"] == 0
```

- [ ] **Step 2: Run, verify fail**

Run: `venv/Scripts/python.exe -m pytest tests/test_analytics.py -v`
Expected: FAIL (`wasps`/`KeyError` or assertion errors — old code uses dead_bee).

- [ ] **Step 3: Rewrite `cv_pipeline/analytics.py`**

Replace the entire file with:
```python
"""
Statistical analytics module for the Buzzlytics CV Pipeline.

Computes hive health metrics from detected/tracked bee populations:
a composite health score, activity rate, and varroa infection rate.
Thresholds and weights come from config.yaml.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .config import load_config
from .tracker import Track

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Computes hive health statistics from tracked bee detections.

    Counts the four unified classes (bee, pollen_bee, varroa_bee,
    wasp) per frame and derives a composite health score (0-100).

    Health score formula (weights/thresholds from config.yaml):
        base
        + pollen_bonus        if pollen_ratio > pollen_good_threshold
        - varroa_penalty      if varroa_ratio > varroa_warn_threshold
        - wasp_penalty        if wasp_ratio   > wasp_threat_threshold
        - low_activity_penalty if activity_rate < low_activity_threshold

    Health status: >70 Healthy, 40-70 Warning, <40 Critical.

    Args:
        config: Optional pre-loaded config dict. Loaded from
            config.yaml when omitted.
    """

    def __init__(self, config: Optional[Dict] = None) -> None:
        cfg = config if config is not None else load_config()
        a = cfg["analytics"]
        self._pollen_good = a["pollen_good_threshold"]
        self._varroa_warn = a["varroa_warn_threshold"]
        self._wasp_threat = a["wasp_threat_threshold"]
        self._low_activity = a["low_activity_threshold"]
        self._w = a["health_weights"]

        self._bees: int = 0
        self._pollen_bees: int = 0
        self._varroa_bees: int = 0
        self._wasps: int = 0
        self._total_bees: int = 0

    def update(self, tracks: List[Track]) -> None:
        """Replace current frame counts from a list of tracks."""
        bees = pollen = varroa = wasps = 0
        for track in tracks:
            name = track.class_name
            if name == "bee":
                bees += 1
            elif name == "pollen_bee":
                pollen += 1
            elif name == "varroa_bee":
                varroa += 1
            elif name == "wasp":
                wasps += 1

        self._bees = bees
        self._pollen_bees = pollen
        self._varroa_bees = varroa
        self._wasps = wasps
        self._total_bees = bees + pollen + varroa + wasps

    def compute_health_score(self) -> float:
        """Compute a composite hive health score in [0, 100]."""
        if self._total_bees == 0:
            return 0.0

        pollen_ratio = self._pollen_bees / self._total_bees
        varroa_ratio = self._varroa_bees / self._total_bees
        wasp_ratio = self._wasps / self._total_bees
        activity_rate = (self._bees + self._pollen_bees) / self._total_bees

        score: float = float(self._w["base"])
        if pollen_ratio > self._pollen_good:
            score += self._w["pollen_bonus"]
        if varroa_ratio > self._varroa_warn:
            score -= self._w["varroa_penalty"]
        if wasp_ratio > self._wasp_threat:
            score -= self._w["wasp_penalty"]
        if activity_rate < self._low_activity:
            score -= self._w["low_activity_penalty"]

        return max(0.0, min(100.0, score))

    def _compute_health_status(self, health_score: float) -> str:
        """Map a health score to Healthy/Warning/Critical."""
        if health_score > 70:
            return "Healthy"
        if health_score >= 40:
            return "Warning"
        return "Critical"

    def get_summary(self) -> Dict[str, object]:
        """Return current hive metrics as a summary dict."""
        health_score = self.compute_health_score()

        activity_rate = 0.0
        infection_rate = 0.0
        if self._total_bees > 0:
            activity_rate = (
                (self._bees + self._pollen_bees) / self._total_bees
            )
            infection_rate = self._varroa_bees / self._total_bees

        return {
            "total_bees": self._total_bees,
            "active_bees": self._bees,
            "pollen_bees": self._pollen_bees,
            "varroa_bees": self._varroa_bees,
            "wasps": self._wasps,
            "health_score": round(health_score, 1),
            "health_status": self._compute_health_status(health_score),
            "activity_rate": round(activity_rate * 100, 1),
            "infection_rate": round(infection_rate * 100, 1),
        }

    def reset(self) -> None:
        """Reset all counters to zero."""
        self._bees = 0
        self._pollen_bees = 0
        self._varroa_bees = 0
        self._wasps = 0
        self._total_bees = 0
```

- [ ] **Step 4: Run tests, verify pass**

Run: `venv/Scripts/python.exe -m pytest tests/test_analytics.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add cv_pipeline/analytics.py tests/test_analytics.py
git commit -m "Refactor analytics to unified classes + config-driven health"
```

---

### Task 3: Detector — unified class map + config wiring

**Files:**
- Modify: `cv_pipeline/detector.py` (lines 5, 21-27, 52, 65-69)
- Create: `tests/test_detector.py`

**Interfaces:**
- Consumes: `cv_pipeline/config.py`.
- Produces: `BEE_CLASS_NAMES == {0:"bee",1:"pollen_bee",2:"varroa_bee",3:"wasp"}`. `BeeDetector(model_path, conf_threshold, iou_threshold)` unchanged signature; `get_class_names()` returns the unified map.

- [ ] **Step 1: Write failing test**

Create `tests/test_detector.py`:
```python
"""Tests for detector class taxonomy (no model load required)."""
from cv_pipeline.detector import BEE_CLASS_NAMES


def test_unified_class_names():
    assert BEE_CLASS_NAMES == {
        0: "bee",
        1: "pollen_bee",
        2: "varroa_bee",
        3: "wasp",
    }
```

- [ ] **Step 2: Run, verify fail**

Run: `venv/Scripts/python.exe -m pytest tests/test_detector.py -v`
Expected: FAIL (current map has `active_bee`/`varroa_infected`/`dead_bee`).

- [ ] **Step 3: Edit `cv_pipeline/detector.py`**

Replace the `BEE_CLASS_NAMES` block (lines 21-27):
```python
BEE_CLASS_NAMES: Dict[int, str] = {
    0: "bee",
    1: "pollen_bee",
    2: "varroa_bee",
    3: "wasp",
}
```
Update docstrings: line 5 and line 52 change `active_bee, pollen_bee, varroa_infected, and dead_bee` → `bee, pollen_bee, varroa_bee, and wasp`.

- [ ] **Step 4: Run test, verify pass**

Run: `venv/Scripts/python.exe -m pytest tests/test_detector.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cv_pipeline/detector.py tests/test_detector.py
git commit -m "Rename detector classes to unified bee/pollen_bee/varroa_bee/wasp"
```

---

### Task 4: Visualizer — wasp color + summary panel keys

**Files:**
- Modify: `cv_pipeline/visualize.py` (lines 22-28 color map; lines 266-276 panel lines)
- Create: `tests/test_visualize.py`

**Interfaces:**
- Produces: `DEFAULT_COLOR_MAP` keyed `bee/pollen_bee/varroa_bee/wasp`; `Visualizer(color_map=None)` unchanged. Stats panel reads `varroa_bees` and `wasps`.

- [ ] **Step 1: Write failing test**

Create `tests/test_visualize.py`:
```python
"""Tests for visualizer color map."""
from cv_pipeline.visualize import DEFAULT_COLOR_MAP


def test_color_map_has_unified_classes():
    assert set(DEFAULT_COLOR_MAP) == {"bee", "pollen_bee", "varroa_bee", "wasp"}
    assert DEFAULT_COLOR_MAP["wasp"] == (0, 140, 255)
```

- [ ] **Step 2: Run, verify fail**

Run: `venv/Scripts/python.exe -m pytest tests/test_visualize.py -v`
Expected: FAIL (map has `active_bee`/`dead_bee`).

- [ ] **Step 3: Edit `cv_pipeline/visualize.py`**

Replace `DEFAULT_COLOR_MAP` (lines 22-28):
```python
DEFAULT_COLOR_MAP: Dict[str, Tuple[int, int, int]] = {
    "bee": (0, 200, 0),            # Green
    "pollen_bee": (0, 220, 255),   # Yellow (BGR)
    "varroa_bee": (0, 0, 220),     # Red
    "wasp": (0, 140, 255),         # Orange (BGR)
}
```
Replace the two panel lines (270-271):
```python
            f"Varroa: {summary.get('varroa_bees', 0)}",
            f"Wasps: {summary.get('wasps', 0)}",
```

- [ ] **Step 4: Run test, verify pass**

Run: `venv/Scripts/python.exe -m pytest tests/test_visualize.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cv_pipeline/visualize.py tests/test_visualize.py
git commit -m "Update visualizer colors and panel for wasp class"
```

---

### Task 5: Pipeline — thread config into sub-modules

**Files:**
- Modify: `cv_pipeline/pipeline.py` (lines 45-62)
- Create: `tests/test_pipeline_config.py`

**Interfaces:**
- Consumes: `load_config`, `BeeDetector`, `AnalyticsEngine`, `Visualizer`.
- Produces: `CVPipeline(model_path=None, conf_threshold=None, use_tracker=True, config=None)`. When `model_path`/`conf_threshold` are None, values come from config. Detector iou + visualizer colors + analytics thresholds all sourced from the same config.

- [ ] **Step 1: Write failing test**

Create `tests/test_pipeline_config.py`:
```python
"""Pipeline wires config values into sub-modules."""
from cv_pipeline.pipeline import CVPipeline


def test_pipeline_uses_config_conf_threshold():
    cfg = {
        "detector": {"model_path": "missing.pt", "conf_threshold": 0.31,
                     "iou_threshold": 0.4, "imgsz": 640},
        "tracker": {"max_age": 30, "min_hits": 3, "iou_match": 0.3},
        "analytics": {
            "pollen_good_threshold": 0.1, "varroa_warn_threshold": 0.15,
            "wasp_threat_threshold": 0.05, "low_activity_threshold": 0.3,
            "health_weights": {"base": 70, "pollen_bonus": 10,
                               "varroa_penalty": 20, "wasp_penalty": 25,
                               "low_activity_penalty": 10},
        },
        "visualize": {"colors": {"bee": [0, 200, 0], "pollen_bee": [0, 220, 255],
                                 "varroa_bee": [0, 0, 220], "wasp": [0, 140, 255]}},
        "video": {"frame_skip": 2},
    }
    pipe = CVPipeline(config=cfg)
    assert pipe.conf_threshold == 0.31
    assert pipe.detector.conf_threshold == 0.31
    assert pipe.visualizer.color_map["wasp"] == (0, 140, 255)
```

NOTE: `Visualizer` must expose the resolved map as `self.color_map` with tuple values. If it stores under another name, adapt the assertion to the real attribute (read `visualize.py` `__init__`).

- [ ] **Step 2: Run, verify fail**

Run: `venv/Scripts/python.exe -m pytest tests/test_pipeline_config.py -v`
Expected: FAIL (`CVPipeline` has no `config` kwarg).

- [ ] **Step 3: Edit `cv_pipeline/pipeline.py` `__init__`**

Replace lines 45-62 with:
```python
    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        use_tracker: bool = True,
        config: Optional[Dict] = None,
    ) -> None:
        from .config import load_config

        cfg = config if config is not None else load_config()
        det = cfg["detector"]

        self.model_path = model_path if model_path is not None else det["model_path"]
        self.conf_threshold = (
            conf_threshold if conf_threshold is not None else det["conf_threshold"]
        )
        self.use_tracker = use_tracker

        # Convert color lists from YAML into BGR tuples for OpenCV.
        color_map = {
            name: tuple(bgr)
            for name, bgr in cfg["visualize"]["colors"].items()
        }

        self.detector = BeeDetector(
            model_path=self.model_path,
            conf_threshold=self.conf_threshold,
            iou_threshold=det["iou_threshold"],
        )
        self.tracker = BeeTracker() if use_tracker else None
        self.analytics = AnalyticsEngine(config=cfg)
        self.visualizer = Visualizer(color_map=color_map)
```
Ensure `Dict` and `Optional` are imported at the top of `pipeline.py` (they are — `from typing import Dict, Generator, List, Optional`).

Confirm `Visualizer.__init__` stores the passed map as `self.color_map` (read lines 43-60 of `visualize.py`; if the attribute differs, either rename it to `color_map` or update the test assertion to match — pick the attribute the rest of `visualize.py` already uses for drawing).

- [ ] **Step 4: Run test, verify pass**

Run: `venv/Scripts/python.exe -m pytest tests/test_pipeline_config.py -v`
Expected: PASS.

- [ ] **Step 5: Run full suite + commit**

```bash
venv/Scripts/python.exe -m pytest -v
git add cv_pipeline/pipeline.py tests/test_pipeline_config.py
git commit -m "Thread config.yaml values through the CV pipeline"
```
Expected: all tests pass.

---

### Task 6: Frontend — dead-bee → wasp

**Files:**
- Modify: `frontend/components/StatsPanel.jsx` (lines 7 import, 74-89 metric)
- Modify: `frontend/components/HealthSummary.jsx` (lines 16, 23, 25, 43-55)

No JS test framework is configured; verify manually via the dev server. Keep changes minimal.

- [ ] **Step 1: Edit `StatsPanel.jsx`**

In the icon import (line 2-11), replace `Skull,` with `Bug,` already present — use `ShieldAlert` (already imported) for wasps. Replace the `dead_bees` metric object (lines 74-89) with:
```jsx
    {
      key: 'wasps',
      label: 'Wasps',
      icon: ShieldAlert,
      format: (v) => Math.round(v).toLocaleString(),
      getColor: (v, d) => {
        const ratio = d.total_bees ? (v / d.total_bees) * 100 : 0;
        return ratio > 5 ? 'critical' : ratio > 1 ? 'warning' : 'healthy';
      },
      getTrend: (v, d) => {
        const ratio = d.total_bees ? (v / d.total_bees) * 100 : 0;
        if (ratio > 5) return { dir: 'down', text: 'Threat' };
        if (ratio > 1) return { dir: 'neutral', text: 'Present' };
        return { dir: 'up', text: 'Clear' };
      },
    },
```
Remove `Skull,` from the import list (line 7) since it is no longer used.

- [ ] **Step 2: Edit `HealthSummary.jsx`**

Line 16 → wasp ratio:
```jsx
    const waspRatio = data.total_bees ? (data.wasps ?? 0) / data.total_bees * 100 : 0;
```
Lines 23 & 25 → replace `deadRatio` references:
```jsx
    if (score < 40 || infectionRate > 15 || waspRatio > 5) {
      currentStatus = 'critical';
    } else if (score < 70 || infectionRate > 5 || waspRatio > 1 || activityRate < 30) {
```
Lines 43-55 → wasp threat copy:
```jsx
    if (waspRatio > 5) {
      recs.push({
        type: 'critical',
        icon: AlertOctagon,
        text: 'Heavy wasp presence at entrance. Likely robbing/predation — reduce entrance size and inspect.',
      });
    } else if (waspRatio > 1) {
      recs.push({
        type: 'warning',
        icon: AlertTriangle,
        text: 'Wasps detected near the entrance. Monitor for robbing behaviour.',
      });
    }
```

- [ ] **Step 3: Manual verification**

```bash
cd frontend && npm run dev
```
Open the analysis page with mock/processed data; confirm the card reads "Wasps" (no "Dead Bees"), no React console errors, and the diagnostics log shows wasp messaging. Stop the server.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/StatsPanel.jsx frontend/components/HealthSummary.jsx
git commit -m "Replace dead-bee UI with wasp threat metric"
```

---

### Task 7: Dataset YAML + training scripts + README narrative

**Files:**
- Modify: `datasets/data/bee_dataset.yaml`
- Modify: `training/train.py` (line 5 docstring), `training/validate.py` (line 117 class list)
- Modify: `README.md` (4-class + health narrative)

- [ ] **Step 1: Rewrite `datasets/data/bee_dataset.yaml`**

```yaml
# Buzzlytics Bee Detection Dataset Configuration (YOLOv8)
path: ../datasets/data
train: train/images
val: valid/images
test: test/images

nc: 4
names:
  0: bee
  1: pollen_bee
  2: varroa_bee
  3: wasp
```

- [ ] **Step 2: Update training scripts**

`training/validate.py` line 117:
```python
    class_names = ["bee", "pollen_bee", "varroa_bee", "wasp"]
```
`training/train.py` line 5 docstring: replace `active_bee, pollen_bee, varroa_infected, and dead_bee.` with `bee, pollen_bee, varroa_bee, and wasp.`

- [ ] **Step 3: Update README narrative**

In `README.md` Features section, change the 4-class line to: `Detects bees, pollen-carrying bees, varroa-infected bees, and wasps (entrance pest/robbing threat)`. Remove dead-bee mentions; add one sentence that wasp presence at the entrance signals robbing/predation risk.

- [ ] **Step 4: Commit**

```bash
git add datasets/data/bee_dataset.yaml training/train.py training/validate.py README.md
git commit -m "Update dataset config, training scripts, and README to 4-class wasp taxonomy"
```

---

### Task 8: Dataset merge script (`prepare_dataset.py`)

**Files:**
- Create: `datasets/prepare_dataset.py`
- Create: `tests/test_prepare_dataset.py`

**Interfaces:**
- Produces: `remap_label_lines(lines: list[str], id_map: dict[int, int]) -> list[str]` — pure function rewriting the leading class id of each YOLO label line, dropping lines whose source id is not in `id_map`. `build_id_map(source_names: list[str], canonical: dict[str, int], aliases: dict[str, str]) -> dict[int, int]` — maps a dataset's own class order to unified ids via name/alias match.

- [ ] **Step 1: Write failing tests**

Create `tests/test_prepare_dataset.py`:
```python
"""Tests for dataset label remapping (pure functions)."""
from datasets.prepare_dataset import remap_label_lines, build_id_map

CANONICAL = {"bee": 0, "pollen_bee": 1, "varroa_bee": 2, "wasp": 3}
ALIASES = {
    "bees": "bee", "bee": "bee",
    "pollen": "pollen_bee", "pollenbearing": "pollen_bee", "pollen_bee": "pollen_bee",
    "varroa": "varroa_bee", "mite": "varroa_bee", "varroa_bee": "varroa_bee",
    "wasp": "wasp", "wasps": "wasp",
}


def test_build_id_map_by_alias():
    # source dataset order: ["bees", "pollen", "varroa"]
    src = ["bees", "pollen", "varroa"]
    id_map = build_id_map(src, CANONICAL, ALIASES)
    assert id_map == {0: 0, 1: 1, 2: 2}


def test_build_id_map_wasp_only():
    id_map = build_id_map(["wasp"], CANONICAL, ALIASES)
    assert id_map == {0: 3}


def test_remap_label_lines_rewrites_class_id():
    lines = ["0 0.5 0.5 0.2 0.2\n", "2 0.1 0.1 0.05 0.05\n"]
    out = remap_label_lines(lines, {0: 3})  # only class 0 -> 3, drop others
    assert out == ["3 0.5 0.5 0.2 0.2\n"]


def test_remap_preserves_coords():
    out = remap_label_lines(["1 0.25 0.75 0.1 0.1\n"], {1: 2})
    assert out == ["2 0.25 0.75 0.1 0.1\n"]
```

- [ ] **Step 2: Run, verify fail**

Run: `venv/Scripts/python.exe -m pytest tests/test_prepare_dataset.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Write `datasets/prepare_dataset.py`**

```python
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CANONICAL: Dict[str, int] = {"bee": 0, "pollen_bee": 1, "varroa_bee": 2, "wasp": 3}

# Map raw dataset class names (lowercased) to canonical names. Extend
# after inspecting the actual exported data.yaml of each dataset.
ALIASES: Dict[str, str] = {
    "bee": "bee", "bees": "bee", "honeybee": "bee", "worker": "bee",
    "pollen": "pollen_bee", "pollenbearing": "pollen_bee",
    "pollen_bee": "pollen_bee", "pollenbee": "pollen_bee",
    "varroa": "varroa_bee", "varroa_bee": "varroa_bee", "mite": "varroa_bee",
    "varroa_infected": "varroa_bee", "varroamite": "varroa_bee",
    "wasp": "wasp", "wasps": "wasp", "hornet": "wasp",
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


def download_datasets(api_key: str, raw_dir: Path) -> List[Path]:
    """Download Hofer bees + Audev wasps via Roboflow. Returns dataset roots."""
    from roboflow import Roboflow

    rf = Roboflow(api_key=api_key)
    roots: List[Path] = []
    # Hofer bees (bee/pollen/varroa)
    bees = (
        rf.workspace("andrew-hofer-1qh7e")
        .project("bees-ytrmp")
        .version(1)
        .download("yolov8", location=str(raw_dir / "hofer"))
    )
    roots.append(Path(bees.location))
    # Audev wasps
    wasps = (
        rf.workspace("audev")
        .project("wasps")
        .version(1)
        .download("yolov8", location=str(raw_dir / "wasps"))
    )
    roots.append(Path(wasps.location))
    return roots


def main() -> None:
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
```
Add `datasets/__init__.py` (empty) so the test import works:
```bash
touch datasets/__init__.py
```

- [ ] **Step 4: Run tests, verify pass**

Run: `venv/Scripts/python.exe -m pytest tests/test_prepare_dataset.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add datasets/prepare_dataset.py datasets/__init__.py tests/test_prepare_dataset.py
git commit -m "Add Roboflow dataset download + 4-class merge script"
```

---

### Task 9: Robustness — pipeline input validation

**Files:**
- Modify: `cv_pipeline/pipeline.py` (`process_video`, around line 164)
- Create: `tests/test_robustness.py`

**Interfaces:**
- Produces: `process_video` raises `FileNotFoundError` for a missing path and `ValueError` for an unopenable/corrupt file (already partially present — verify and harden). A new helper `validate_video_path(path: str) -> None`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_robustness.py`:
```python
"""Robustness: input validation for video processing."""
import pytest

from cv_pipeline.pipeline import CVPipeline


def test_missing_video_raises(tmp_path):
    pipe = CVPipeline(use_tracker=False)
    gen = pipe.process_video(str(tmp_path / "nope.mp4"))
    with pytest.raises(FileNotFoundError):
        next(gen)


def test_corrupt_video_raises(tmp_path):
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"not a real video")
    pipe = CVPipeline(use_tracker=False)
    gen = pipe.process_video(str(bad))
    with pytest.raises(ValueError):
        next(gen)
```
NOTE: `CVPipeline(use_tracker=False)` still constructs a `BeeDetector`, which loads `yolov8n.pt` (downloads on first run if absent). If offline, mark these with `@pytest.mark.skipif` on a network/env flag, or pre-place `yolov8n.pt`. Document whichever you choose in the test file.

- [ ] **Step 2: Run, verify current behaviour**

Run: `venv/Scripts/python.exe -m pytest tests/test_robustness.py -v`
Expected: missing-file test likely PASSES (guard at line 164 exists); corrupt-file test reveals whether `cv2.VideoCapture` failure is handled. Fix whatever fails.

- [ ] **Step 3: Harden `process_video`**

Ensure the opening of `process_video` reads:
```python
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            cap.release()
            raise ValueError(f"Could not open video (corrupt/unsupported): {video_path}")
```
(Adapt to the existing variable names; keep the rest of the method intact.)

- [ ] **Step 4: Run tests, verify pass**

Run: `venv/Scripts/python.exe -m pytest tests/test_robustness.py -v`
Expected: PASS (or documented skips when offline).

- [ ] **Step 5: Full suite + commit**

```bash
venv/Scripts/python.exe -m pytest -v
git add cv_pipeline/pipeline.py tests/test_robustness.py
git commit -m "Harden video input validation for corrupt/missing files"
```

---

## Operational Runbook (no TDD — external/manual steps)

These phases depend on Colab/GPU, the Roboflow key, and real footage. Execute after Tasks 1-9 land.

### R1 — Build the dataset (needs `ROBOFLOW_API_KEY`)

- [ ] Confirm the Roboflow version numbers: open each universe page (`andrew-hofer-1qh7e/bees-ytrmp`, `audev/wasps`), note the latest version, and set `.version(N)` in `download_datasets` accordingly.
- [ ] Run: `venv/Scripts/python.exe datasets/prepare_dataset.py --api-key YOUR_KEY`
- [ ] Inspect the logged `id_map` per dataset. If any class logged "Unmapped", add its raw name to `ALIASES` and re-run.
- [ ] Verify `datasets/data/{train,valid,test}/{images,labels}` are populated and a few label files start with ids 0-3.

### R2 — Train on Colab (T4)

- [ ] Create `training/colab_train.ipynb` with cells:
  1. `!pip install ultralytics==8.1.0`
  2. Upload the zipped `datasets/data` (or pull via Roboflow in-notebook) and unzip.
  3. Write/upload a `bee_dataset.yaml` with Colab-absolute `path:`.
  4. `from ultralytics import YOLO; YOLO("yolov8n.pt").train(data="bee_dataset.yaml", epochs=100, imgsz=640, batch=16)`
  5. After training: `model.val()` → record per-class mAP@50 / mAP@50-95, precision, recall (screenshot for report).
  6. Download `runs/detect/train/weights/best.pt`.
- [ ] Place `best.pt` at `cv_pipeline/weights/best.pt`. Add `cv_pipeline/weights/*.pt` to `.gitignore` (large binary); note its location in the README.

### R3 — Wire in + verify end-to-end (criterion 6 FPS)

- [ ] Confirm `config.yaml:detector.model_path` points to `cv_pipeline/weights/best.pt`.
- [ ] Start backend (`venv/Scripts/python.exe -m uvicorn backend.main:app --reload`) and frontend (`npm run dev`).
- [ ] Upload a real hive clip; confirm boxes/colors render for all 4 classes and the counters/health summary update.
- [ ] Benchmark FPS: time `pipe.process_video` over a clip; record machine-spec → FPS. If <10 FPS, raise `video.frame_skip` in `config.yaml` for live mode.

### R4 — Test set + report evidence

- [ ] Assemble 30-50 challenging clips/images (dawn, glare, overcast, blur, empty hive, odd angle); run them; log honest pass/fail in the report's failure-case section with images.
- [ ] Produce the report tables: per-class mAP, FPS, latency; architecture diagram (draw.io/excalidraw); IEEE/APA citations.
- [ ] Update the report intro + demo script to the wasp (not dead-bee) narrative so all materials are consistent.

---

## Self-Review

- **Spec coverage:** Phase 1 → Tasks 1-7; Phase 2 → Task 8 + R1; Phase 3 → R2; Phase 4 → Task 9 + R4; Phase 5 → R3; Phase 6 → R4. All spec sections mapped.
- **Placeholder scan:** No TBD/TODO; every code step shows full code. The two spots requiring inspection of existing internals (Visualizer attribute name in Task 5; existing `process_video` variable names in Task 9) are flagged with explicit instructions, not left vague.
- **Type consistency:** class strings `bee/pollen_bee/varroa_bee/wasp` and summary keys (`active_bees/pollen_bees/varroa_bees/wasps`) are identical across detector, analytics, visualize, frontend, and dataset yaml. Wasp BGR `(0,140,255)` consistent in config, visualize, and constraints.
