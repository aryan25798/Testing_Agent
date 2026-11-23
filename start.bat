@echo off
setlocal enabledelayedexpansion

title AI Testing Agent Platform - Launcher
echo ===============================================================================
echo            AI TESTING AGENT PLATFORM - ENTERPRISE LAUNCHER
echo ===============================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python 3.10+ is required but not found in PATH.
        echo Please install Python 3.10 or newer from https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    set "PY_CMD=py -3"
) else (
    set "PY_CMD=python"
)

:: 2. Check and setup Virtual Environment (.venv)
if not exist ".venv\Scripts\activate.bat" (
    echo [SETUP] Creating isolated Python virtual environment in .venv...
    %PY_CMD% -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SETUP] Virtual environment created successfully.
)

call .venv\Scripts\activate.bat

:: 3. Verify / Install Dependencies
if not exist ".venv\installed.flag" (
    echo [SETUP] First-time setup detected. Installing Python dependencies...
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Dependency installation encountered an issue.
        pause
        exit /b 1
    )
    echo [SETUP] Installing Playwright Chromium browser binary...
    playwright install chromium
    echo Installed on %DATE% %TIME% > ".venv\installed.flag"
    echo [SETUP] Dependencies initialized successfully.
)

:: 4. Verify Frontend Static Distribution
if not exist "frontend\dist\frontend\browser\index.html" (
    echo [WARN] Compiled frontend distribution not found.
    where npm >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        echo [SETUP] Building Angular frontend static bundle...
        pushd frontend
        call npm install --silent
        call npm run build -- --configuration production
        popd
    ) else (
        echo [WARN] Node.js/npm not found to build frontend. Running in API-only mode.
    )
)

:: 5. Launch FastAPI Single-Port Server and Open Browser
echo.
echo [START] Starting Unified Testing Platform at http://localhost:8000
echo [INFO]  Press Ctrl+C to safely shut down the platform.
echo ===============================================================================
echo.

:: Launch browser in parallel after 2 seconds
start "" powershell -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8000'"

:: Start Uvicorn Server
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000

pause
