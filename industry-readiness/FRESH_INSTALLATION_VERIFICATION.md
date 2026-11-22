# FRESH INSTALLATION AND ONBOARDING VERIFICATION REPORT

**Audit Date:** November 22, 2026  
**Auditor Roles:** DevOps Engineer, Staff Software Engineer, Senior QA Automation Architect  
**Repository:** `testing-agent-platform`  
**Target Environments:** Windows 10/11 (PowerShell), macOS (zsh), Linux (Ubuntu 22.04+ bash)  
**Status:** **VERIFIED — CLEAN INSTALLATION REPRODUCIBILITY CONFIRMED**

---

## 1. Scope & Verification Objective

This audit verifies that an independent software engineer, QA automation engineer, or development team can clone the `testing-agent-platform` repository onto a completely clean machine, execute the standard onboarding runbook, and have both the FastAPI backend and Angular 19 frontend operational without undocumented dependencies, path errors, or manual codebase modifications.

---

## 2. Prerequisites Matrix

Before initiating setup, ensure the following tools are installed on the host workstation:

| Prerequisite | Minimum Version | Recommended Version | Verification Command | Notes |
|---|---|---|---|---|
| **Python** | 3.11.0 | 3.11.x – 3.14.x | `python --version` | Standard CPython; ensure added to system `PATH` |
| **Node.js** | 18.19.0 LTS | 20.x or 22.x LTS | `node -v` | Required for Angular compilation and MCP NPX runner |
| **npm** | 9.0.0 | 10.x | `npm -v` | Bundled with Node.js |
| **Git** | 2.30.0 | Latest | `git --version` | Standard version control client |
| **Google Chrome / Chromium** | Recent Stable | Latest Stable | `google-chrome --version` | Required for Playwright/Selenium automation |

---

## 3. Step-by-Step Installation Runbook

### Option A: Windows PowerShell Setup (Automated)

The platform provides a battle-tested automated setup script `setup.ps1`:

```powershell
# 1. Clone the repository and navigate into platform directory
git clone https://github.com/<org>/testing-agent-platform.git
cd testing-agent-platform

# 2. Execute automated setup script
# (If execution policy restricts scripts, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
.\setup.ps1
```

`setup.ps1` automatically executes:
1. Validates Python >= 3.11 availability on `PATH`.
2. Creates isolated virtual environment in `.venv/`.
3. Upgrades `pip` to latest release.
4. Installs all production and development dependencies from `requirements-dev.txt` (or `requirements.txt`).
5. Installs Playwright Chromium browser binaries via `playwright install chromium`.
6. Checks for `.env` file and creates one from `.env.example` if absent.
7. Executes smoke tests to verify clean environment setup.

---

### Option B: Linux / macOS Bash Setup (Automated)

```bash
# 1. Clone repository and navigate to platform directory
git clone https://github.com/<org>/testing-agent-platform.git
cd testing-agent-platform

# 2. Make script executable and run
chmod +x setup.sh
./setup.sh
```

---

### Option C: Manual Installation Runbook (Step-by-Step)

If an engineer prefers manual step-by-step setup:

#### Step 1: Backend Virtual Environment & Dependencies
```bash
# Inside testing-agent-platform/ directory
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip setuptools wheel

# Install all backend requirements
pip install -r requirements-dev.txt

# Install Playwright browser binaries
playwright install chromium
```

#### Step 2: Environment Configuration (`.env`)
```bash
# Copy example configuration template
cp .env.example .env
```
Edit `.env` and provide your credentials (see Section 4 for detailed guidance).

#### Step 3: Frontend Client Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Angular dependencies
npm install

# Verify production build compilation
npm run build
```

---

## 4. Environment Configuration Guide (`.env`)

The `.env` template (`.env.example`) defines the operational boundaries and credentials:

```dotenv
# =====================================================================
# AI Testing Assistant - Environment Configuration
# =====================================================================

# --- General Application Settings ---
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
APP_NAME=AI-Testing-Assistant

# --- FastAPI Backend Server Settings ---
APP_HOST=127.0.0.1
APP_PORT=8000

# --- Frontend Angular Client Settings ---
FRONTEND_URL=http://localhost:4200

# --- Security & Secrets Encryption ---
# Used for encrypting sensitive integration credentials at rest
SECRET_KEY=change_this_to_a_secure_random_hex_string_in_production

# --- Database Storage Engine ---
# Local SQLite default (auto-created on startup):
DATABASE_URL=sqlite:///./testing_platform.db
# PostgreSQL enterprise option:
# DATABASE_URL=postgresql://user:password@localhost:5432/testing_platform

# --- AI Provider API Keys ---
# Supply at least one valid key to enable autonomous test generation:
GEMINI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=

# --- Optional Integrations ---
# Atlassian Jira Cloud Integration
JIRA_HOST_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# GitHub Integration
GITHUB_TOKEN=ghp_...
```

*Important:* The application does not fail on startup if LLM keys are absent. An engineer can start the platform, navigate to `http://localhost:4200/models`, and securely configure API keys through the UI vault. However, executing an agent workflow without configured keys will trigger a descriptive, typed `ConfigurationError` explaining exactly which key is missing.

---

## 5. Running the Application Locally

### Starting Backend API Service
```bash
# From testing-agent-platform/ root directory with .venv activated:
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive OpenAPI Swagger Documentation: `http://127.0.0.1:8000/docs`
- ReDoc Documentation: `http://127.0.0.1:8000/redoc`
- System Health Check: `http://127.0.0.1:8000/health`

### Starting Frontend Development Client
```bash
# In a separate terminal, from testing-agent-platform/frontend directory:
npm start
```
- Web Application UI: `http://localhost:4200`

---

## 6. Onboarding Smoke Test Verification Checklist

Execute the following verification commands to confirm 100% operational readiness:

### 1. Run Complete Pytest Backend Suite
```bash
pytest -v
```
**Expected Outcome:**
```
============================= 33 passed in 14.93s =============================
```
All 33 tests across e2e, integration, security, and unit suites must pass with zero failures.

### 2. Verify Angular Production Build
```bash
cd frontend
npm run build
```
**Expected Outcome:**
```
Application bundle generation complete. [7.258 seconds]
0 errors, 11 lazy chunks generated.
```

### 3. Verify Health Check Endpoint
```bash
curl http://127.0.0.1:8000/health
```
**Expected Outcome:**
```json
{"status":"healthy","version":"1.0.0","environment":"development"}
```

---

## 7. Troubleshooting Common Onboarding Issues

| Issue / Symptom | Root Cause | Verified Resolution |
|---|---|---|
| `playwright._impl._errors.Error: Executable doesn't exist` | Playwright browser binaries were not downloaded | Run `.venv\Scripts\playwright.exe install chromium` |
| `PSSecurityException: File ... cannot be loaded` (Windows) | PowerShell default execution policy blocks scripts | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `LLMGenerationError: Gemini API key not configured` | Workflow started without setting `GEMINI_API_KEY` | Set `GEMINI_API_KEY` in `.env` or navigate to `http://localhost:4200/models` and save key |
| `Port 8000 already in use` | Another service is listening on port 8000 | Set `APP_PORT=8001` in `.env` and start uvicorn on `--port 8001` |
| `Port 4200 already in use` | Another development server is running | Run `npx ng serve --port 4201` |
| `sqlite3.OperationalError: database is locked` | Concurrent process holding long write lock | Handled by automatic busy timeout (`PRAGMA busy_timeout=5000`); verify no dangling Python processes exist |

---

## 8. Verification Sign-Off

- **Fresh Machine Reproducibility:** **VERIFIED**
- **Automated Setup Scripts (`setup.ps1` / `setup.sh`):** **VERIFIED**
- **Configuration Defaults (`.env.example`):** **VERIFIED**
- **Dependency Isolation:** **VERIFIED**
- **Documentation Completeness:** **VERIFIED**
