# Buzzlytics: Computer Vision Hive Health Dashboard

Buzzlytics is a computer-vision hive health prototype that converts uploaded hive entrance videos, still frames, and close-up bee crops into annotated analysis results. It combines bee detection, pollen-return estimation, tracking, motion analysis, and Varroa crop inspection in a local FastAPI + Next.js application.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Vision Capabilities](#vision-capabilities)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Model Training](#model-training)
- [API Endpoints](#api-endpoints)
- [User Story](#user-story)

---

## Features

- **Video Upload Processing**: Upload pre-recorded hive videos for batch analysis with annotated output and health reports
- **WebSocket Frame Endpoint**: Backend support for live frame processing via `/ws/webcam` for future webcam UI work
- **Two-Stage Bee Analysis**: A YOLOv8 detector boxes every bee as bee/pollen-carrying; a separate close-up Varroa model classifies crops or, when detector weights are installed, detects mite boxes directly
- **Multi-Object Tracking**: ByteTrack-based persistent identity tracking across video frames
- **Health Score Engine**: Algorithmic hive health scoring (0-100) with clinical status classification
- **Analytics Dashboard**: Metrics panel with counts, pollen return rate, activity rate, health score, and trend indicators

---

## Architecture

```
+-------------------+       HTTP/WS        +-------------------+       Python        +-------------------+
|                   |  <===============>   |                   |  <===============>  |                   |
|    Frontend       |                      |     Backend       |                     |    CV Pipeline    |
|    (Next.js)      |                      |    (FastAPI)      |                     |  (OpenCV/YOLO)    |
|                   |                      |                   |                     |                   |
| - Video Upload    |   POST /upload       | - Route Handling  |  process_frame()    | - CLAHE Enhance   |
| - Webcam Stream   |   WS  /ws/webcam     | - File Management |  process_video()    | - YOLOv8 Detect   |
| - Stats Panel     |   GET /status        | - WebSocket Mgmt  |                     | - ByteTrack       |
| - Health View     |   GET /result        | - Background Task |                     | - Analytics       |
|                   |                      |                   |                     | - Visualize       |
+-------------------+                      +-------------------+                     +-------------------+
```

### Data Flow

**Video Upload Flow:**
1. Frontend sends video file via `POST /api/video/upload`
2. Backend saves file and enqueues background processing
3. CV Pipeline processes each frame: Preprocess -> Detect -> Track -> Analyze -> Visualize
4. Annotated video is saved to results directory
5. Frontend polls `GET /api/video/status/{id}` until complete
6. Annotated video and analytics summary are displayed

**Backend Live Frame Flow (prototype endpoint):**
1. A client sends base64-encoded camera frames via WebSocket
2. Backend decodes each frame and runs the CV pipeline
3. Annotated frame and analytics are sent back via WebSocket
4. The current shipped frontend focuses on uploaded video, uploaded image, and Varroa crop workflows

---

## Vision Capabilities

The app integrates the following four computer vision capabilities:

| # | Capability | Implementation | Module |
|---|-----------|---------------|--------|
| 1 | **Object Detection** | YOLO detects bees and pollen-carrying bees | `cv_pipeline/detector.py` |
| 2 | **Object Tracking** | Tracker assigns persistent IDs and counts bees over time | `cv_pipeline/tracker.py` |
| 3 | **Video Processing / Moving Object Detection** | Frame-by-frame video analysis with optional motion mask/background modelling | `cv_pipeline/pipeline.py`, `cv_pipeline/motion.py` |
| 4 | **Object Recognition / Classification** | Varroa classifier/detector identifies healthy vs infected bee crops | `cv_pipeline/varroa_classifier.py`, `cv_pipeline/varroa_detector.py` |

**Two-stage taxonomy:**
- Stage 1 — detector (boxes every bee): `bee` (0), `pollen_bee` (1)
- Stage 2 — per-bee classifier on each detected bee crop: `healthy` / `varroa`
- A bee classified `varroa` is relabeled `varroa_bee` at runtime, which analytics/visualize count and color.

Why two stages: the varroa mite is tiny and only annotated as single-bee classification crops
(VarroaDataset), not boxed bees-in-scene — so forcing it into detection ruins per-bee localization.
This detect-then-classify design follows IntelliBeeHive / BeeAlarmed.

To upgrade close-up Varroa from classification to true mite detection:

```bash
python training/make_varroa_detection_dataset.py --source <varroa-folder-with-gt_one.csv> --out datasets/varroa_det
python training/train_varroa_detector.py --data datasets/varroa_det/varroa_mite.yaml --epochs 80 --imgsz 960
```

Then copy `training/runs/varroa_mite_detector/weights/best.pt` to
`cv_pipeline/weights/varroa_det.pt`. The `/api/varroa` route will use detector
mode automatically when that file exists; otherwise it falls back to classifier mode.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Lucide Icons, Recharts |
| Backend | Python 3.10+, FastAPI, Uvicorn, WebSockets |
| CV Pipeline | OpenCV, Ultralytics YOLOv8, NumPy |
| Model Training | Ultralytics, PyTorch |

---

## Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher
- **npm** 9 or higher
- **Webcam** (optional, only if building against the backend WebSocket frame endpoint)
- **CUDA-capable GPU** (recommended for real-time performance, but CPU works)

---

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>/buzzlytics.git
cd buzzlytics
```

### 2. Set Up the Python Backend

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

### 3. Set Up the Frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Model weights (already included)

The trained Buzzlytics models ship with the repo, so it runs out of the box:

- `cv_pipeline/weights/best.pt` — stage-1 detector (`bee`, `pollen_bee`)
- `cv_pipeline/weights/varroa_cls.pt` — stage-2 varroa classifier (`healthy`, `varroa`)
- `cv_pipeline/weights/varroa_det.pt` — close-up Varroa mite detector (`mite`)

No download or training needed. (To retrain, see [Model Training](#model-training) and drop the new
weights at those same paths.) If `best.pt` is ever missing, the app falls back to a generic YOLOv8
nano model — it will run but won't detect bees meaningfully.

---

## Running the Application

You need to run both the backend and frontend simultaneously.

### Terminal 1: Start the Backend

```bash
# From the project root directory
# Make sure your virtual environment is activated
source venv/bin/activate

# Start the FastAPI server FROM THE PROJECT ROOT (not from backend/).
# config.yaml and the model weights are resolved relative to the working
# directory, so the server must be launched from the repo root.
python backend/main.py
```

The backend will be available at `http://localhost:8000` (API docs at `http://localhost:8000/docs`).

### Terminal 2: Start the Frontend

```bash
# From the project root directory
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Quick Start (Both at Once)

On macOS/Linux (run both from the project root):

```bash
# Start backend in background (from repo root — paths are root-relative)
python backend/main.py &
# Start frontend
cd frontend && npm run dev
```

---

## Project Structure

```
buzzlytics/
├── frontend/                     # React / Next.js UI Core
│   ├── pages/
│   │   ├── index.jsx             # Main static file processing layout
│   │   └── webcam.jsx            # Low-latency live webcam streaming canvas
│   ├── components/
│   │   ├── UploadVideo.jsx       # Drag-and-drop asynchronous file ingestion
│   │   ├── VideoPlayer.jsx       # Bounding box & tracking vector overlay renderer
│   │   ├── StatsPanel.jsx        # Quantitative geometric metrics dashboard grid
│   │   └── HealthSummary.jsx     # Clinical text-based algorithmic diagnosis widget
│   ├── services/
│   │   └── api.js                # Network abstraction layer (Axios/Fetch/WebSockets)
│   ├── styles/
│   │   └── globals.css           # Dark-themed dashboard CSS
│   ├── public/                   # Static client assets
│   ├── next.config.js            # Next.js config with API proxy
│   └── package.json              # Client dependencies
│
├── backend/                      # Python FastAPI Application Layer
│   ├── main.py                   # Server initialization, middleware, and entry point
│   ├── routes/
│   │   ├── video_routes.py       # Asynchronous HTTP POST multipart video handlers
│   │   └── websocket_routes.py   # Persistent duplex live frame streaming pipelines
│   ├── uploads/                  # Volatile local cache for incoming raw video clips
│   ├── results/                  # Local cache for compiled processed visual files
│   └── requirements.txt          # Python microservice dependencies
│
├── cv_pipeline/                  # Core Computer Vision Processing Module
│   ├── pipeline.py               # Central orchestration script execution pipeline
│   ├── preprocess.py             # Shadow balancing & illumination fixes (CLAHE)
│   ├── detector.py               # Stage-1 2-class YOLOv8 detector (bee, pollen_bee)
│   ├── tracker.py                # Multi-object temporal identity tracker (ByteTrack)
│   ├── analytics.py              # Statistical aggregation, tracking lines, and thresholds
│   └── visualize.py              # Frame matrix annotation and box overlay engine
│
├── datasets/                     # Unified model training and validation matrices
│   ├── data/
│   │   └── bee_dataset.yaml      # YOLO dataset configuration
│   ├── images/
│   │   ├── train/                # Training images (add your data here)
│   │   └── val/                  # Validation images (add your data here)
│   └── labels/
│       ├── train/                # Training labels in YOLO format
│       └── val/                  # Validation labels in YOLO format
│
├── training/                     # Standalone model training and verification scripts
│   ├── train.py                  # YOLOv8 fine-tuning script
│   └── validate.py               # Model validation and metrics reporting
│
├── README.md                     # This file
└── .gitignore                    # Weights, datasets, and cache masking definitions
```

---

## Model Training

### Preparing the Dataset

The builder produces **two** datasets from two public sources (no API key needed):

- **Detection** (stage 1) from **VnPollenBee** ([HUST ComVis](https://comvis-hust.github.io/datasets/pollenbee.html)) —
  LabelMe polygons → `datasets/data/{train,valid,test}`. `nonpollenbee` → `bee`, `pollenbee` → `pollen_bee`.
- **Varroa classification** (fallback health check) from **VarroaDataset** ([TU Wien, Zenodo 4085044](https://zenodo.org/records/4085044), CC-BY-4.0) —
  single-bee crops sorted into `datasets/varroa_cls/{train,val,test}/{healthy,varroa}/`.
- **Varroa mite detection** (close-up crop detector) from VarroaDataset coordinate labels —
  YOLO mite boxes under `datasets/varroa_det/{train,valid,test}`.

```bash
python datasets/prepare_dataset.py        # downloads ~1.5 GB into datasets/raw/
```

The detection config is written to `datasets/data/bee_dataset.yaml`. The end-to-end path is two Colab
notebooks: run `training/build_dataset_colab.ipynb` once (builds both zips into your Drive), then
`training/colab_train.ipynb` (trains **both** the detector and the varroa classifier).
Drop `best.pt` → `cv_pipeline/weights/best.pt`, `varroa_cls.pt` → `cv_pipeline/weights/varroa_cls.pt`,
and the close-up mite detector weights → `cv_pipeline/weights/varroa_det.pt`.

### Label Format (YOLO)

Each `.txt` label file should contain one line per object:

```
class_id x_center y_center width height
```

All values are normalized to [0, 1]. Detection class IDs:
- `0` = bee
- `1` = pollen_bee

Varroa is not a label in the entrance-frame bee detector. Close-up mite detection is handled by
the separate `varroa_det.pt` model, while the crop classifier remains available as a fallback
`healthy`/`varroa` health check.

### Training

```bash
# From the training directory
cd training
python train.py --data ../datasets/data/bee_dataset.yaml --epochs 100 --batch 16
```

**Recommended training parameters:**
- Start with `yolov8n.pt` (nano) for quick iteration
- Use `yolov8s.pt` (small) for better accuracy once the dataset is large enough
- Minimum 500 images per class for reasonable results
- Aim for 2000+ total annotated instances

### Validation

```bash
python validate.py --weights runs/bee_detector/weights/best.pt
```

### Using the Trained Model

```bash
# Copy best weights for inference
cp training/runs/bee_detector/weights/best.pt cv_pipeline/custom_bee_model.pt
```

When starting the backend, the pipeline will automatically detect and use `custom_bee_model.pt` if it exists.

---

## API Endpoints

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check endpoint |
| `POST` | `/api/video/upload` | Upload a video file for processing |
| `GET` | `/api/video/status/{video_id}` | Check processing status |
| `GET` | `/api/video/result/{video_id}` | Stream the annotated video |
| `GET` | `/api/video/results` | List all processed videos |
| `DELETE` | `/api/video/result/{video_id}` | Delete a processed video |
| `POST` | `/api/varroa` | Analyze a close-up bee crop with the Varroa classifier or YOLO mite detector |

### WebSocket Endpoint

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/webcam` | Live webcam frame streaming |

**WebSocket Protocol:**

Send (client to server):
```json
{
  "frame": "<base64_encoded_jpeg>"
}
```

Receive (server to client):
```json
{
  "type": "frame",
  "annotated_frame": "<base64_encoded_jpeg>",
  "stats": {
    "total_bees": 12,
    "active_bees": 8,
    "pollen_bees": 2,
    "varroa_bees": 1,
    "wasps": 1,
    "health_score": 65,
    "health_status": "Warning",
    "activity_rate": 0.67,
    "infection_rate": 0.08
  }
}
```

---

## User Story

**As a beekeeper**, I want to analyze hive entrance footage and close-up bee crops so that I can turn visual inspection into repeatable evidence about activity, pollen return, and Varroa risk.

**Scenario 1 - Video Upload Analysis:**
I upload a video of my hive entrance recorded during the morning foraging period. The system processes the video and shows me:
- An annotated video with bounding boxes around each detected bee and pollen-carrying bee
- A count of detected bees and pollen-carrying bees, plus motion/activity trends
- A health score of 75/100 with a "Healthy" classification
- A recommendation noting good foraging activity based on the pollen-carrying ratio

**Scenario 2 - Close-up Varroa Crop Inspection:**
I upload a close-up crop of a bee. The system processes the crop and:
- Predicts whether the crop shows Varroa evidence
- Displays detector confidence and any mite boxes found
- Shows reference mite count when dataset annotations are available
- Falls back to crop-level healthy/Varroa classification if detector weights are unavailable

**Value Delivered:**
- Provides quantitative health data instead of subjective visual assessment
- Supports Varroa screening through a dedicated close-up crop workflow
- Tracks foraging activity trends over time to identify declining hive productivity
