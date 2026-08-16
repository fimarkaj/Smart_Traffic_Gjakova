# Smart Traffic AI

<p align="center">
  <strong>Enterprise-Grade Real-Time Intelligent Traffic Monitoring & Analytics System</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 18" /></a>
  <a href="https://vitejs.dev/"><img src="https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" /></a>
  <a href="https://docs.ultralytics.com/"><img src="https://img.shields.io/badge/YOLOv11-Ultralytics-111111?style=for-the-badge&logo=yolo&logoColor=white" alt="YOLOv11" /></a>
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" /></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge" alt="MIT License" /></a>
</p>

---
## Overview

**Smart Traffic AI** is a real-time computer vision and traffic intelligence platform designed for municipal monitoring, road network analysis, and incident alerting. Powered by **YOLOv11**, **ByteTrack**, and a reactive **FastAPI + React 18** architecture, it transforms standard RTSP/HLS surveillance feeds into actionable traffic metrics, spatial occupancy heatmaps, and automated congestion forecasts.

> [!IMPORTANT]
> **Default Dashboard Credentials:**
> - **Username:** `admin`
> - **Password:** `admin`
>
> In production deployments, change your credentials and update `auth.secret_key` in [`config.yaml`](file:///config.yaml).

> [!NOTE]
> **Model Auto-Fallback:**
> If custom weights are not placed in `models/best.pt`, the pipeline automatically falls back to official pre-trained `yolo11n.pt` weights so the application runs immediately after cloning.

> [!TIP]
> **Hardware Acceleration:**
> The inference pipeline dynamically detects and leverages **NVIDIA CUDA** GPUs (`cuda:0`) or **Apple Silicon** (`mps`). If no GPU is present, it executes smoothly on standard **CPU**.

---

## ✨ Key Features

- ⚡ **Real-Time Stream Processing**: Low-latency HLS/RTSP frame ingestion with resilient auto-reconnect and dropped-frame recovery.
- 🚗 **YOLOv11 Object Detection & Tracking**: High-accuracy vehicle detection combined with ByteTrack tracking for continuous multi-object assignment.
- 📐 **Interactive Multi-Zone Polygons (ROI)**: Define custom polygonal zones to quantify per-lane vehicle occupancy, density, and dwell times.
- ⏱️ **Directional Line-Crossing Telemetry**: Accurate entry/exit counters with spatial debouncing, centroid travel verification, and jitter elimination.
- 📹 **Automated Incident Clip Recording**: Circular ring buffer automatically captures 30s pre-event + 30s post-event MP4 video evidence when congestion spikes occur.
- 🔔 **Multi-Channel Alert Dispatcher**: Rule-based notification engine triggering Webhooks (Discord, Slack, MS Teams), Telegram Bots, and Email.
- 🔮 **Traffic Congestion Forecasting**: Machine-learning forecasting module evaluating historical flow to predict upcoming congestion bottlenecks.
- 🚦 **SUMO Simulation Ready**: Integrated export engine converting real-world traffic telemetry into Simulation of Urban MObility (SUMO) compatible state files.

---

## 🏗️ Architecture & Directory Layout

```
Smart_Traffic_Gjakova/
├── api/                     ← FastAPI application & REST/WebSocket routes
│   ├── routers/             ← Modular route handlers (analytics, live, auth, clips)
│   ├── services/            ← Background workers (alert engine, data retention)
│   ├── auth.py              ← JWT authentication & password hashing
│   ├── db.py                ← SQLite persistence & retention layer
│   ├── main.py              ← Backend entry point & service coordinator
│   ├── requirements.txt     ← API Python dependencies
│   └── Dockerfile           ← Container build recipe for API
├── detector/                ← Computer vision & inference subsystem
│   ├── capture.py           ← Stream ingestion with health monitoring
│   ├── detect.py            ← YOLOv11 tracker with dynamic hardware acceleration
│   ├── model_manager.py     ← Hot-swappable model manager with fallback logic
│   ├── line_counter.py      ← Directional line-crossing counting engine
│   ├── roi.py               ← Multi-polygon ROI occupancy calculator
│   ├── clip_recorder.py     ← Circular buffer incident video recorder
│   ├── shared_state.py      ← Thread-safe in-memory frame buffer
│   ├── predictor.py         ← Live ML congestion prediction loop
│   ├── requirements.txt     ← Detector Python dependencies
│   └── Dockerfile           ← CUDA-enabled container build recipe
├── frontend/                ← React 18 + Vite dashboard interface
│   ├── src/                 ← Pages, components, hooks, and Zustand store
│   ├── package.json         ← Frontend dependencies & scripts
│   ├── vite.config.js       ← Vite build config with WebSocket proxy
│   └── Dockerfile           ← Multi-stage production Nginx container
├── data/                    ← SQLite database, ROI geometries, incident clips
├── models/                  ← Model weights repository (.pt, .pkl)
├── config.yaml              ← Unified system configuration
├── sumo_csv_export.py       ← SUMO simulation CSV export utility
├── start.sh                 ← macOS / Linux one-click launcher
├── start.bat                ← Windows one-click launcher
└── docker-compose.yml       ← Full-stack multi-container orchestrator
```

---

## 🚀 Quick Start

### Option 1: macOS / Linux (Recommended)

```bash
# Make launcher executable and start
chmod +x start.sh
./start.sh
```

### Option 2: Windows One-Click

Double-click **`start.bat`** or run via command prompt:

```bat
start.bat
```

### Option 3: Docker Compose

```bash
docker compose up --build
```

---

## 🌐 Service Access Points

| Service | URL | Description | Default Auth |
|---|---|---|---|
| **Web Dashboard** | `http://localhost:5173` | React 18 Live UI & Analytics | `admin` / `admin` |
| **API Documentation** | `http://localhost:8000/docs` | Interactive Swagger / OpenAPI UI | Bearer JWT |
| **Health Check** | `http://localhost:8000/health` | API & Detector Liveness Status | Public |
| **WebSocket Stream** | `ws://localhost:8000/api/live/ws` | Live Annotated Frame & Stats Feed | Token Authenticated |

---

## ⚙️ Configuration Reference

All application parameters are centrally managed in [`config.yaml`](file:///config.yaml).

<details>
<summary><strong>🔍 Click to expand full <code>config.yaml</code> reference</strong></summary>

```yaml
stream:
  url: "https://gjirafa-video-live.gjirafa.net/gjvideo-slow/txu-9qc-kab-9fm/tracks-v1/mono.ts.m3u8"
  crop: [800, 600, 0, 250]   # width, height, x_offset, y_offset
  reconnect_delay: 2

model:
  path: "models/best.pt"
  confidence: 0.15
  iou: 0.45
  car_class_id: 0
  hot_swap_dir: "models"

roi:
  csv_path: "data/rois_polygons.csv"
  points_column: "cropped_points"
  offset_x: 0
  offset_y: 0

line_counter:
  lines_file: "data/counting_lines.json"
  grid_size: 40
  cooldown: 15.0

thresholds:
  green: 5
  yellow: 10

clips:
  output_dir: "data/clips"
  pre_event_seconds: 30
  post_event_seconds: 30
  trigger_occupancy: 10
  trigger_crossing_rate: 5

alerts:
  cooldown_seconds: 10
  channels:
    webhook:
      enabled: false
      url: ""

database:
  path: "data/traffic.db"
  retention_days: 30
  retention_run_hour: 3

api:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:5173"
    - "http://localhost:80"
    - "http://localhost"
```

</details>

---

## 🛠️ Manual Development Setup

<details>
<summary><strong>🔧 Click to expand step-by-step manual setup instructions</strong></summary>

### 1. Environment & Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- (Optional) NVIDIA GPU with CUDA 12+

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r api/requirements.txt -r detector/requirements.txt

# Start FastAPI backend
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# In a new terminal tab
cd frontend
npm install
npm run dev
```

</details>

---

## 📡 REST API Inventory

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/token` | Authenticate and obtain JWT bearer token |
| `GET` | `/api/auth/me` | Retrieve current authenticated user profile |
| `GET` | `/api/cameras/` | Query list of registered camera streams and live health |
| `GET` | `/api/analytics/counts` | Query historical per-zone vehicle counts |
| `GET` | `/api/analytics/totals` | Aggregate summary of total occupancy and crossings |
| `GET` | `/api/analytics/export/csv` | Stream CSV export of historical count data |
| `GET` | `/api/analytics/export/sumo` | Generate SUMO traffic simulation state CSV |
| `GET` | `/api/clips/` | List auto-recorded incident video clips |
| `GET` | `/api/clips/{filename}` | Stream / download incident MP4 clip |
| `GET` | `/api/config/lines` | Get line-crossing counter configuration |
| `PUT` | `/api/config/lines` | Update and hot-reload line definitions |
| `GET` | `/api/config/thresholds` | Fetch traffic congestion thresholds |
| `PUT` | `/api/config/thresholds` | Update traffic thresholds in real time |
| `GET` | `/api/model/status` | Current YOLO model status and swap history |
| `POST` | `/api/model/swap` | Hot-swap active YOLO weights without restarting |
| `GET` | `/api/forecast/live` | Real-time traffic congestion prediction |
| `GET` | `/api/alerts/` | Fetch configured alert rules |
| `POST` | `/api/alerts/` | Create a new automated alert rule |

---

## 📄 License

This project is licensed under the [MIT License](file:///LICENSE).
