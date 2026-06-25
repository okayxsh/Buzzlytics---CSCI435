# Buzzlytics: Computer Vision Hive Health Dashboard

Buzzlytics is an analytical, automated monitoring platform that converts video feeds of a beehive entrance into real-time colony health diagnostics. By eliminating manual hive inspections and visual counts, the platform delivers precise, automated quantitative tracking parameters for beekeepers to prevent colony collapse.

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
- **Live Webcam Streaming**: Real-time bee monitoring via WebSocket-based frame streaming with instant annotations
- **Two-Stage Bee Analysis**: A YOLOv8 detector boxes every bee as bee/pollen-carrying; a second classifier marks each detected bee as varroa-infected or healthy
- **Multi-Object Tracking**: ByteTrack-based persistent identity tracking across video frames
- **Health Score Engine**: Algorithmic hive health scoring (0-100) with clinical status classification
- **Real-Time Analytics Dashboard**: Live metrics panel with counts, rates, and trend indicators

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

**Live Webcam Flow:**
1. Frontend captures webcam frames at ~10 FPS
2. Each frame is base64-encoded and sent via WebSocket
3. Backend decodes frame and runs CV Pipeline
4. Annotated frame and analytics are sent back via WebSocket
5. Frontend renders annotated frame on canvas and updates dashboard

---

## Vision Capabilities

The system integrates the following four computer vision capabilities:

| # | Capability | Implementation | Module |
|---|-----------|---------------|--------|
| 1 | **Image Enhancement** | CLAHE (Contrast Limited Adaptive Histogram Equalization) in LAB color space + Non-Local Means denoising | `cv_pipeline/preprocess.py` |
| 2 | **Object Detection** | Fine-tuned YOLOv8 with 3 bee classes | `cv_pipeline/detector.py` |
| 3 | **Object Tracking** | ByteTrack multi-object tracker via ultralytics | `cv_pipeline/tracker.py` |
| 4 | **Video Processing** | Full video pipeline with frame-by-frame processing, moving object tracking, and health analytics | `cv_pipeline/pipeline.py` |

**Two-stage taxonomy:**
- Stage 1 — detector (boxes every bee): `bee` (0), `pollen_bee` (1)
- Stage 2 — per-bee classifier on each detected bee crop: `healthy` / `varroa`
- A bee classified `varroa` is relabeled `varroa_bee` at runtime, which analytics/visualize count and color.

Why two stages: the varroa mite is tiny and only annotated as single-bee classification crops
(VarroaDataset), not boxed bees-in-scene — so forcing it into detection ruins per-bee localization.
This detect-then-classify design follows IntelliBeeHive / BeeAlarmed.

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
- **Webcam** (for live streaming feature)
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

### 4. (Optional) Download a Custom Trained Model

If you have trained a custom bee detection model (see [Model Training](#model-training)), copy the weights:

```bash
cp training/runs/bee_detector/weights/best.pt cv_pipeline/custom_bee_model.pt
```

If no custom model is found, the system automatically uses the pretrained YOLOv8 nano model, which will be downloaded on first run.

---

## Running the Application

You need to run both the backend and frontend simultaneously.

### Terminal 1: Start the Backend

```bash
# From the project root directory
# Make sure your virtual environment is activated
source venv/bin/activate

# Start the FastAPI server
cd backend
python main.py
```

The backend will be available at `http://localhost:8000`. You can verify it is running by visiting `http://localhost:8000/api/health`.

### Terminal 2: Start the Frontend

```bash
# From the project root directory
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Quick Start (Both at Once)

On macOS/Linux:

```bash
# Start backend in background
cd backend && python main.py &
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
- **Varroa classification** (stage 2) from **VarroaDataset** ([TU Wien, Zenodo 4085044](https://zenodo.org/records/4085044), CC-BY-4.0) —
  single-bee crops sorted into `datasets/varroa_cls/{train,val,test}/{healthy,varroa}/`.

```bash
python datasets/prepare_dataset.py        # downloads ~1.5 GB into datasets/raw/
```

The detection config is written to `datasets/data/bee_dataset.yaml`. The end-to-end path is two Colab
notebooks: run `training/build_dataset_colab.ipynb` once (builds both zips into your Drive), then
`training/colab_train.ipynb` (trains **both** the detector and the varroa classifier).
Drop `best.pt` → `cv_pipeline/weights/best.pt` and `varroa_cls.pt` → `cv_pipeline/weights/varroa_cls.pt`.

### Label Format (YOLO)

Each `.txt` label file should contain one line per object:

```
class_id x_center y_center width height
```

All values are normalized to [0, 1]. Detection class IDs:
- `0` = bee
- `1` = pollen_bee

(Varroa is not a detection label — the stage-2 classifier sorts crops into `healthy`/`varroa` folders.)

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

**As a beekeeper**, I want to monitor the health of my beehives remotely using video feeds so that I can detect problems early and prevent colony collapse without frequent manual inspections.

**Scenario 1 - Video Upload Analysis:**
I upload a video of my hive entrance recorded during the morning foraging period. The system processes the video and shows me:
- An annotated video with bounding boxes around each detected bee, color-coded by health status
- A count of healthy bees, pollen-carrying bees, varroa-infected bees, and wasps
- A health score of 75/100 with a "Healthy" classification
- A recommendation noting good foraging activity based on the pollen-carrying ratio

**Scenario 2 - Live Webcam Monitoring:**
I connect my webcam pointed at the hive entrance. The system processes frames in real-time and:
- Displays a live annotated video feed with bounding boxes and tracking trails
- Continuously updates bee counts and health metrics
- Alerts me when the varroa infection rate exceeds 15%, suggesting immediate mite treatment
- Shows an activity rate below 30%, warning of potential queen issues

**Value Delivered:**
- Eliminates the need for daily physical hive inspections
- Provides quantitative health data instead of subjective visual assessment
- Enables early detection of varroa mite infestations before they cause colony collapse
- Tracks foraging activity trends over time to identify declining hive productivity
