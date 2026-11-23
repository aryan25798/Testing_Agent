#!/usr/bin/env bash
# ==============================================================================
#            AI TESTING AGENT PLATFORM - ENTERPRISE LAUNCHER (macOS/Linux)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==============================================================================="
echo "           AI TESTING AGENT PLATFORM - ENTERPRISE LAUNCHER"
echo "==============================================================================="
echo ""

# 1. Check Python installation
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3.10+ is required but not found in PATH."
    echo "Please install Python 3.10 or newer from your package manager or python.org."
    exit 1
fi

# 2. Check and setup Virtual Environment (.venv)
if [ ! -d ".venv" ]; then
    echo "[SETUP] Creating isolated Python virtual environment in .venv..."
    $PY_CMD -m venv .venv
    echo "[SETUP] Virtual environment created successfully."
fi

# shellcheck source=/dev/null
source .venv/bin/activate

# 3. Verify / Install Dependencies
if [ ! -f ".venv/installed.flag" ]; then
    echo "[SETUP] First-time setup detected. Installing Python dependencies..."
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
    echo "[SETUP] Installing Playwright Chromium browser binary..."
    playwright install chromium
    date > ".venv/installed.flag"
    echo "[SETUP] Dependencies initialized successfully."
fi

# 4. Verify Frontend Static Distribution
if [ ! -f "frontend/dist/frontend/browser/index.html" ]; then
    echo "[WARN] Compiled frontend distribution not found."
    if command -v npm &>/dev/null; then
        echo "[SETUP] Building Angular frontend static bundle..."
        (cd frontend && npm install --silent && npm run build -- --configuration production)
    else
        echo "[WARN] Node.js/npm not found to build frontend. Running in API-only mode."
    fi
fi

# 5. Launch FastAPI Server & Open Browser
echo ""
echo "[START] Starting Unified Testing Platform at http://localhost:8000"
echo "[INFO]  Press Ctrl+C to safely shut down the platform."
echo "==============================================================================="
echo ""

# Background browser opener
(
    sleep 2
    if command -v xdg-open &>/dev/null; then
        xdg-open "http://localhost:8000" &>/dev/null || true
    elif command -v open &>/dev/null; then
        open "http://localhost:8000" &>/dev/null || true
    fi
) &

# Run server
exec python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
