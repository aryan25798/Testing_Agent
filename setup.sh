#!/usr/bin/env bash
# setup.sh - Automated Local Environment Setup Script for Linux / macOS / Git Bash
set -euo pipefail

echo "============================================================"
echo " Testing Agent Platform - Environment Setup (Linux/macOS)   "
echo "============================================================"

# 1. Determine Python executable (python3 or python)
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[ERROR] Python was not found. Please install Python 3.11 or higher." >&2
    exit 1
fi

PY_VERSION=$($PY_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Found Python version: $PY_VERSION"

# 2. Check Python version >= 3.11
$PY_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" || {
    echo "[ERROR] Python 3.11 or higher is required. Found Python $PY_VERSION." >&2
    exit 1
}

# 3. Create Virtual Environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at .venv..."
    $PY_CMD -m venv "$VENV_DIR"
    echo "Virtual environment created."
else
    echo "Existing virtual environment found at .venv."
fi

VENV_PY="$VENV_DIR/bin/python"
if [ ! -f "$VENV_PY" ]; then
    # Fallback check for Windows Git Bash path
    if [ -f "$VENV_DIR/Scripts/python.exe" ]; then
        VENV_PY="$VENV_DIR/Scripts/python.exe"
    else
        echo "[ERROR] Python interpreter not found in .venv." >&2
        exit 1
    fi
fi

# 4. Upgrade pip
echo "Upgrading pip..."
"$VENV_PY" -m pip install --upgrade pip

# 5. Install Dependencies
if [ -f "$SCRIPT_DIR/requirements-dev.txt" ]; then
    echo "Installing dependencies from requirements-dev.txt..."
    "$VENV_PY" -m pip install -r "$SCRIPT_DIR/requirements-dev.txt"
else
    echo "Installing dependencies from requirements.txt..."
    "$VENV_PY" -m pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# 6. Configure .env
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo ".env created."
    fi
else
    echo ".env already exists."
fi

# 7. Verify Environment
echo "Running environment verification..."
"$VENV_PY" "$SCRIPT_DIR/scripts/check_environment.py"

echo ""
echo "Setup complete! To activate the environment run:"
echo "  source .venv/bin/activate"
