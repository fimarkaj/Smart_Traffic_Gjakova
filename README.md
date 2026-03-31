# Smart Traffic AI

Real-time traffic monitoring system using YOLOv11. Detects and counts vehicles from a live HLS stream, displays results on a React dashboard with live charts, clip recording, alerts, and analytics.

## Architecture

```
smart-traffic-ai/
├── api/          ← FastAPI backend (Python)
├── detector/     ← YOLO detection pipeline (Python)
├── frontend/     ← React + Vite dashboard
├── data/         ← SQLite DB, ROI CSV, clips (auto-created)
├── models/       ← Place your .pt model files here
├── config.yaml   ← All settings live here
└── start.bat     ← Windows one-click launcher
```

## Quick Start (Windows)

```bat
1. Clone the repo
2. Edit start.bat — set CONDA_ENV and CONDA_ACTIVATE to match your setup
3. Place your best.pt in models/
4. Run start.bat
```

Opens at **http://localhost:5173** — Login: `admin` / `admin`

## Manual Setup

### Prerequisites
- Python 3.9+ (Anaconda/Miniconda recommended)
- Node.js 18+
- NVIDIA GPU (optional, CPU works)

### Backend

```bash
# Create conda env (or use venv)
conda create -n smarttraffic python=3.10
conda activate smarttraffic

# Install API deps
cd api
pip install -r requirements.txt

# Install detector deps
cd ../detector
pip install -r requirements.txt

# Run API (starts detector automatically)
cd ../api
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Docker (Linux/Mac)

```bash
docker compose up --build
```

Frontend: http://localhost  
API docs: http://localhost:8000/docs

## Configuration

All settings are in **`config.yaml`**:

| Section | Key | Description |
|---|---|---|
| `stream.url` | HLS/RTSP URL | Live stream to monitor |
| `model.path` | `models/best.pt` | YOLO model — place here |
| `roi.csv_path` | `data/rois_polygons.csv` | ROI zone polygons |
| `line_counter.lines_file` | `data/counting_lines.json` | Counting line definitions |
| `auth.users` | admin/admin | Change password in production |
| `alerts.channels.webhook.url` | — | Discord/Slack webhook URL |
| `database.path` | `data/traffic.db` | SQLite database |

All paths are relative to the project root and work on Windows, Linux, and Mac.

## Required Files (not in repo)

| File | Where to get it |
|---|---|
| `models/best.pt` | Your trained YOLOv11 model |
| `data/rois_polygons.csv` | Already included — edit for your camera |
| `data/counting_lines.json` | Already included as empty — configure in UI |
| `models/traffic_congestion_model.pkl` | Optional — forecast model |

## API Docs

Available at http://localhost:8000/docs when the backend is running.
