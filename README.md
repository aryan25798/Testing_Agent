# AI Testing Assistant Platform

An autonomous, multi-agent platform for intelligent software testing, test scenario design, Playwright automation execution, and quality analytics.

---

## 🚀 Quick Start on a New Machine (Clone & Run)

Follow these steps when cloning this repository onto another PC:

### 1. Clone the Repository
```bash
git clone https://github.com/aryan25798/Testing_Agent.git
cd Testing_Agent
```

---

### 🔑 2. Where to Place Your API Keys (3 Easy Ways)

You can configure your **Google Gemini** or **OpenAI** API keys using any of the following methods:

#### Method A: Direct in the Web UI (Recommended & Easiest)
1. Start the application backend and frontend (see Step 3 & 4 below).
2. Open your browser and navigate to **[http://localhost:4200/models](http://localhost:4200/models)** (or click **AI Model Settings** in the left sidebar).
3. Paste your Gemini API key (`AQ...` or `AIza...`) or OpenAI API key (`sk-...`).
4. Click **Verify & Save Key**.
5. The system will automatically validate the credentials, dynamically discover all live models available for your key, and enable independent per-agent model assignment.

#### Method B: In the `.env` Configuration File
1. In the project root directory, copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` in any text editor and insert your key:
   ```env
   GEMINI_API_KEY="your_actual_gemini_api_key_here"
   OPENAI_API_KEY="your_actual_openai_api_key_here"
   ```
3. When the backend starts up, it automatically loads these keys.

#### Method C: In Terminal / System Environment Variables
- **Windows (PowerShell)**:
  ```powershell
  $env:GEMINI_API_KEY="your_actual_gemini_api_key_here"
  $env:OPENAI_API_KEY="your_actual_openai_api_key_here"
  ```
- **macOS / Linux**:
  ```bash
  export GEMINI_API_KEY="your_actual_gemini_api_key_here"
  export OPENAI_API_KEY="your_actual_openai_api_key_here"
  ```

---

### 3. Setup & Start the Python Backend (FastAPI)

1. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers** (for headless/headed test execution):
   ```bash
   playwright install chromium
   ```

4. **Launch the FastAPI server**:
   ```bash
   python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
   ```
   *The backend is now live at `http://127.0.0.1:8000` (Swagger docs at `http://127.0.0.1:8000/docs`).*

---

### 4. Setup & Start the Angular Frontend

Open a new terminal window:

1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Start the Angular development server**:
   ```bash
   npx ng serve --port 4200
   ```
4. **Open your browser**:
   Navigate to **[http://localhost:4200](http://localhost:4200)** to access your AI Testing Assistant Dashboard!

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

### 5. Running the Application

The platform consists of a **FastAPI backend** and a modern **Angular frontend**:

1. **Start the FastAPI Backend**:
   ```powershell
   cd testing-agent-platform
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   - API Docs: `http://127.0.0.1:8000/docs`
   - Health Check: `http://127.0.0.1:8000/api/v1/health`
   - Dashboard API: `http://127.0.0.1:8000/api/v1/dashboard/overview`

2. **Start the Angular Frontend**:
   ```powershell
   cd testing-agent-platform\frontend
   npm start
   # Or: npx ng serve --port 4200 --host 127.0.0.1
   ```
   - Dashboard UI: `http://localhost:4200/`

3. **Database & Data Persistence**:
   - Location: `testing-agent-platform/testing_platform.db` (SQLite relational database)
   - Stores all projects, requirements, scenarios, test cases, Playwright automation scripts, execution history, and custom agents.

---

### 6. Project Directory Layout

```text
testing-agent-platform/
├── frontend/                # Modern Angular 19 Standalone Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/        # API services, models, and TypeScript interfaces
│   │   │   ├── layout/      # Deep navy sidebar, sticky search header
│   │   │   └── pages/       # Dashboard, Projects, Agents, Workflows, Cases, Reports, etc.
│   │   ├── styles.css       # Tailwind CSS & custom design tokens
│   │   └── index.html
│   ├── tailwind.config.js   # Custom design palette & typography
│   └── package.json
├── src/                     # Python 3.11+ FastAPI Backend
│   ├── agents/              # 6 specialized QA agents (Requirement, Scenario, Design, Automation, Execution, Reporting)
│   ├── api/                 # REST API routers (dashboard, projects, models, workflows, custom-agents, etc.)
│   ├── database/            # SQLAlchemy session and SQLite connection
│   ├── integrations/        # Jira, GitHub, and file upload parsers
│   ├── llm/                 # Model registry & dynamic provider router (Gemini & OpenAI)
│   ├── models/              # Relational database models (entities.py)
│   ├── workflows/           # LangGraph autonomous testing state machine
│   └── main.py              # FastAPI application entrypoint
├── testing_platform.db      # Persistent SQLite database
├── artifacts/               # Test execution logs and generated scripts
└── requirements.txt         # Backend Python dependencies
```

---

### 7. Production Isolation (Docker)

Local development relies on `.venv`. For staging and production environments, use containerized isolation (Docker) using multi-stage builds pinning the identical Python version (`>= 3.11`) and requirements to guarantee full reproducibility.
