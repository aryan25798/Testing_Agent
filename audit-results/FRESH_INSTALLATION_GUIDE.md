# FRESH MACHINE INSTALLATION & SETUP GUIDE

**Target System:** Independent Engineer Workstation (Windows, macOS, or Linux)  
**Auditor Roles:** DevOps Engineer, Full-Stack Developer, Open-Source Maintainer  
**Repository:** `https://github.com/aryan25798/Testing-Agent`  

This guide provides tested, step-by-step instructions for an independent engineer to clone this repository on a completely fresh machine, install dependencies, configure environment variables, and launch the platform.

---

## 1. PREREQUISITES

Ensure the following tools are installed on your workstation before starting:

| Tool | Minimum Version | Installation Check Command | Download / Install URL |
|---|---|---|---|
| **Git** | 2.30+ | `git --version` | [git-scm.com](https://git-scm.com/) |
| **Python** | 3.11+ | `python --version` (or `python3`) | [python.org](https://www.python.org/) |
| **Node.js** | 20+ (LTS) | `node --version` | [nodejs.org](https://nodejs.org/) |
| **npm** | 10+ | `npm --version` | Bundled with Node.js |

---

## 2. INSTALLATION ON WINDOWS (POWERSHELL)

### Step 1: Clone Repository
```powershell
git clone https://github.com/aryan25798/Testing-Agent.git
cd Testing-Agent/testing-agent-platform
```

### Step 2: Set Up Python Virtual Environment & Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install production requirements
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in your text editor and supply your keys:
```ini
# Application Core
APP_NAME="Testing Agent Platform"
APP_VERSION="1.0.0"
ENVIRONMENT="development"
SECRET_KEY="generate_a_random_32_character_string_here"

# LLM Providers (Provide at least one)
GEMINI_API_KEY="your-google-gemini-api-key"
OPENAI_API_KEY="your-openai-api-key"

# Database
DATABASE_URL="sqlite:///./data/testing_platform.db"

# MCP Integrations (Optional, can also configure in UI)
GITHUB_PERSONAL_ACCESS_TOKEN=""
ATLASSIAN_HOST_URL=""
ATLASSIAN_USER_EMAIL=""
ATLASSIAN_API_TOKEN=""
```

### Step 4: Set Up Angular Frontend Dependencies
Open a **new** PowerShell terminal:
```powershell
cd Testing-Agent/testing-agent-platform/frontend
npm install
```

---

## 3. INSTALLATION ON LINUX / MACOS (BASH / ZSH)

### Step 1: Clone Repository
```bash
git clone https://github.com/aryan25798/Testing-Agent.git
cd Testing-Agent/testing-agent-platform
```

### Step 2: Set Up Python Virtual Environment & Dependencies
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install production requirements
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browser binaries and OS dependencies
playwright install --with-deps chromium
```

### Step 3: Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and supply GEMINI_API_KEY or OPENAI_API_KEY
nano .env
```

### Step 4: Set Up Angular Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 4. RUNNING THE APPLICATION

You will run the backend and frontend in two separate terminal windows.

### Terminal 1: Start FastAPI Backend
```bash
# Windows
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# Linux / macOS
source .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend will be live at: `http://127.0.0.1:8000`
* Interactive API Documentation (Swagger): `http://127.0.0.1:8000/docs`
* Health Endpoint: `http://127.0.0.1:8000/api/v1/health`

### Terminal 2: Start Angular Frontend
```bash
cd frontend
npm start
```
* Frontend will be live at: `http://localhost:4200`

---

## 5. FIRST RUN VERIFICATION & TESTING WORKFLOW

1. **Open Browser:** Navigate to `http://localhost:4200`.
2. **Verify Health:** The dashboard top-bar status indicator should display `System Healthy` with a green pulse.
3. **Configure Models:**
   * Go to **Model Settings** in the sidebar.
   * Verify your active model (e.g., `gemini-1.5-pro` or `gpt-4o`).
   * Click **Test Connection** to confirm API key validity.
4. **Create a Test Project:**
   * Go to **Projects** -> **Create Project**.
   * Enter a project name (e.g., `Demo WebApp`).
   * Enter target repository URL (e.g., `https://github.com/aryan25798/TrainMate`).
   * Enter target application URL (e.g., `https://train-mate-blond.vercel.app`).
   * Click **Save Project**.
5. **Run Autonomous Workflow:**
   * Open the project details or navigate to **Workflows**.
   * Select the project and click **Execute Full Workflow**.
   * Watch the 6 agents run sequentially in LangGraph:
     * Requirements Analyst -> Test Scenarios -> Test Cases -> Automation Scripts -> Test Execution -> Quality Advisor.
6. **Inspect Test Execution & Reports:**
   * Navigate to **Executions** to view live browser test logs.
   * Navigate to **Reports** to download the generated PDF Quality Report.

---

## 6. TROUBLESHOOTING COMMON SETUP ISSUES

### Issue 1: `ModuleNotFoundError: No module named 'playwright'`
* **Cause:** Virtual environment not activated or dependencies not installed.
* **Fix:** Ensure your terminal prompt shows `(.venv)` and run `pip install -r requirements.txt`.

### Issue 2: `playwright._impl._errors.Error: Executable doesn't exist at ...`
* **Cause:** Browser binaries have not been downloaded yet.
* **Fix:** Run `playwright install chromium` inside your virtual environment.

### Issue 3: `Port 8000 is already in use`
* **Cause:** A previous instance of uvicorn is still running.
* **Fix (Windows):** `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force`
* **Fix (Linux/macOS):** `kill -9 $(lsof -t -i:8000)`

### Issue 4: `CORS Error in Browser Console`
* **Cause:** Frontend accessed via an alternate domain not listed in `CORS_ORIGINS`.
* **Fix:** Access the frontend strictly via `http://localhost:4200`. Check `CORS_ORIGINS` in `.env` if using a custom host.
