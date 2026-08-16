#!/usr/bin/env bash
set -e

# ==============================================================================
# Smart Traffic AI — Launch Script (macOS / Linux)
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="${ROOT_DIR}/api"
DETECTOR_DIR="${ROOT_DIR}/detector"
FRONTEND_DIR="${ROOT_DIR}/frontend"

echo ""
echo "=========================================="
echo "  SmartTraffic AI — Starting System"
echo "=========================================="
echo ""

# 1. Check Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 is required but not found in PATH."
    exit 1
fi
echo "[OK] Using Python: $(${PYTHON_CMD} --version)"

# 2. Check Node
if ! command -v node >/dev/null 2>&1; then
    echo "[ERROR] Node.js is required for frontend development. Install from https://nodejs.org/"
    exit 1
fi
echo "[OK] Using Node: $(node --version)"

# 3. Create required runtime directories
mkdir -p "${ROOT_DIR}/data" "${ROOT_DIR}/data/clips" "${ROOT_DIR}/models"
echo "[OK] Runtime directories verified."

# 4. Check YOLO weights
if [ ! -f "${ROOT_DIR}/models/best.pt" ]; then
    echo "[INFO] Custom model weights models/best.pt not found."
    echo "       The detector will run with standard YOLOv11 fallback."
fi

# 5. Frontend dependencies
if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
    echo "[SETUP] Installing frontend dependencies..."
    (cd "${FRONTEND_DIR}" && npm install)
fi

# Clean exit handler
cleanup() {
    echo ""
    echo "[STOP] Shutting down Smart Traffic AI services..."
    if [ -n "${API_PID:-}" ] && kill -0 "${API_PID}" 2>/dev/null; then
        kill "${API_PID}" 2>/dev/null || true
    fi
    if [ -n "${FRONTEND_PID:-}" ] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
        kill "${FRONTEND_PID}" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "[STOP] All processes terminated."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 6. Start Backend (FastAPI + Background Detector Thread)
echo "[START] Launching Backend API on port 8000..."
export PYTHONPATH="${ROOT_DIR}:${API_DIR}:${DETECTOR_DIR}:${PYTHONPATH:-}"
(
    cd "${API_DIR}"
    ${PYTHON_CMD} -m uvicorn main:app --host 0.0.0.0 --port 8000
) &
API_PID=$!

# Wait for API to start
sleep 2

# 7. Start Frontend Dev Server
echo "[START] Launching Frontend on port 5173..."
(
    cd "${FRONTEND_DIR}"
    npm run dev
) &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  Dashboard : http://localhost:5173"
echo "  API Docs  : http://localhost:8000/docs"
echo "  Health    : http://localhost:8000/health"
echo "  Login     : admin / admin"
echo "=========================================="
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for background jobs
wait
