# Testing Agent Platform

An autonomous, multi-agent platform for intelligent software testing, test generation, test execution, and quality analytics.

---

## Phase 0: Environment Isolation & Setup Guide

This project strictly requires an isolated Python virtual environment (`.venv`) for all development and execution tasks. Dependencies must never be installed directly into the global/system Python environment.

---

### 1. Prerequisites

- **Python**: Version `3.11` or higher (verified with Python 3.14).
- **Git**: Installed and available on your system path.
- **Shell**: PowerShell (Windows) or Bash / Zsh (Linux / macOS).

Verify your system Python and Git versions before starting:

```powershell
python --version
git --version
```

If Python is not installed or version < 3.11:
- **Windows**: Download the latest installer from [python.org](https://www.python.org/downloads/) or run `winget install Python.Python.3.12`. Ensure *"Add python.exe to PATH"* is checked.
- **macOS**: Use Homebrew: `brew install python@3.12`.
- **Linux**: Use your package manager (e.g. `sudo apt update && sudo apt install python3.12 python3.12-venv python3-pip`).

---

### 2. Quick Setup (Automated)

Run the platform setup script for your operating system:

#### Windows (PowerShell)
```powershell
.\setup.ps1
```

#### Linux / macOS / Git Bash
```bash
chmod +x setup.sh
./setup.sh
```

The script will automatically:
1. Verify Python >= 3.11 is present.
2. Create the `.venv` virtual environment (if it does not exist).
3. Upgrade `pip` inside `.venv`.
4. Install all dependencies from `requirements-dev.txt`.
5. Create `.env` from `.env.example` (if missing).
6. Run `scripts/check_environment.py` to verify full isolation and configuration.

---

### 3. Manual Step-by-Step Setup

If you prefer configuring the environment manually, follow these steps:

#### Step 3.1: Navigate to the Project Directory
```powershell
cd testing-agent-platform
```

#### Step 3.2: Create the Virtual Environment
Create a dedicated virtual environment named `.venv`:

- **Windows**:
  ```powershell
  python -m venv .venv
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv .venv
  ```

#### Step 3.3: Activate the Virtual Environment
Activate `.venv` before running any commands:

- **Windows PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(Note: If script execution is restricted in PowerShell, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once).*

- **Windows Command Prompt (cmd)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```

Verify that the active interpreter points to `.venv`:
```powershell
# Windows
(Get-Command python).Source

# Linux / macOS
which python
```

#### Step 3.4: Upgrade pip
```bash
python -m pip install --upgrade pip
```

#### Step 3.5: Install Dependencies
Always use `python -m pip` to ensure packages install into `.venv`:

- **Production Dependencies**:
  ```bash
  python -m pip install -r requirements.txt
  ```
- **Development & Testing Dependencies**:
  ```bash
  python -m pip install -r requirements-dev.txt
  ```

#### Step 3.6: Configure Environment Variables
Copy the template `.env.example` to `.env`:

- **Windows PowerShell**:
  ```powershell
  Copy-Item .env.example .env
  ```
- **Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

Update `.env` with your local settings and credentials.

> [!WARNING]
> Never commit `.env` or sensitive credentials to Git. `.env` and `.venv/` are explicitly excluded via `.gitignore`.

---

### 4. Verification

Run the automated verification script to validate interpreter isolation, dependency resolution, `.env` loading, and directory structure:

```bash
python scripts/check_environment.py
```

Expected output:
```text
============================================================
Testing Agent Platform - Environment Verification
============================================================
Project Root: ...\testing-agent-platform

--- 1. Virtual Environment Check ---
Interpreter: ...\testing-agent-platform\.venv\Scripts\python.exe
Prefix:      ...\testing-agent-platform\.venv
Base Prefix: C:\Program Files\Python314
[PASS] Running inside dedicated project virtual environment (.venv).

--- 2. Python Version Check ---
Python Version: 3.14.2
[PASS] Python version 3.14.2 meets requirement (>=3.11).

--- 3. pip Tooling Check ---
pip version: pip 26.3 from ...\.venv\Lib\site-packages\pip (python 3.14)
[PASS] pip is accessible and functional inside virtual environment.

--- 4. Dependency Installation Check ---
  - fastapi: 0.165.0 [INSTALLED]
  - uvicorn: 0.54.0 [INSTALLED]
  - pydantic: 2.14.4 [INSTALLED]
  - streamlit: 1.67.0 [INSTALLED]
  - python-dotenv: 1.2.4 [INSTALLED]
  - httpx: 0.28.1 [INSTALLED]
  - pytest: 9.2.0 [INSTALLED]
[PASS] All required core packages are installed.

--- 5. Environment Variables (.env) Check ---
  - ENVIRONMENT=development
  - APP_HOST=127.0.0.1
  - APP_PORT=8000
[PASS] .env file loaded successfully and contains expected variables.

--- 6. Project Files & Directory Structure Check ---
  - [FOUND] requirements.txt
  - [FOUND] requirements-dev.txt
  - [FOUND] .gitignore
  - [FOUND] .env
  - [FOUND] .env.example
  - [FOUND] scripts/check_environment.py
[PASS] All essential project files and directories exist.

--- 7. .gitignore Safety Check ---
[PASS] .gitignore properly excludes .venv and .env.

============================================================
Verification Summary
============================================================
ALL CHECKS PASSED: Environment is clean, isolated, and ready for development.
```

---

### 5. Mandatory Development Rules

1. **Active Interpreter Enforcement**:
   - Every Python command must use `.venv`.
   - Never run `pip install` globally or without `.venv` activated.
2. **FastAPI Application**:
   - Must run within `.venv`:
     ```bash
     uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
     ```
3. **Streamlit Dashboard**:
   - Must run within `.venv`:
     ```bash
     streamlit run ui/app.py --server.port 8501
     ```
4. **Test Execution**:
   - All tests must run using `pytest` inside `.venv`:
     ```bash
     pytest
     ```
5. **Agents & Background Workers**:
   - All background workers and agent runtimes must execute within the verified `.venv` environment or an isolated container runtime.

---

### 6. Project Directory Layout

```text
testing-agent-platform/
├── .env                     # Local environment secrets (ignored by git)
├── .env.example             # Template environment variables
├── .gitignore               # Excludes .venv, .env, caches, logs, databases
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development and testing dependencies
├── setup.ps1                # Automated setup script (Windows)
├── setup.sh                 # Automated setup script (Linux / macOS)
├── README.md                # Environment setup & development documentation
└── scripts/
    └── check_environment.py # Verification and diagnostics script
```

---

### 7. Production Isolation (Docker)

Local development relies on `.venv`. For staging and production environments, use containerized isolation (Docker) using multi-stage builds pinning the identical Python version (`>= 3.11`) and requirements to guarantee full reproducibility.
