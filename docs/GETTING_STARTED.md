# Getting Started with AI Testing Assistant

Welcome! This guide is designed for beginners and first-time users of Agentic AI. You do not need any coding or testing background to get started.

---

## 1. Prerequisites

- Python 3.11 or higher
- Git installed on your computer

---

## 2. Quick Setup (1-Click)

On Windows (PowerShell):
```powershell
cd testing-agent-platform
.\setup.ps1
```

On Linux or macOS:
```bash
cd testing-agent-platform
chmod +x setup.sh
./setup.sh
```

---

## 3. Starting the Applications

### 1. Launch the FastAPI Backend
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Launch the Angular Frontend
In another terminal:
```powershell
cd frontend
npm start
```
The visual dashboard will open at: [http://localhost:4200](http://localhost:4200)

---

## 4. Running Your First Test in 3 Minutes

1. In the left sidebar, click **"Start Testing (Wizard)"**.
2. **Step 1**: Choose a project name (e.g. *Online Shopping*).
3. **Step 2**: Paste any simple feature description (e.g. *Users can add items to cart and pay with card*).
4. Click **Next** through the steps.
5. Watch the 6 AI agents analyze requirements, generate test scenarios, create step-by-step test cases, write automation code, execute tests in a sandbox, and compile your report.
6. Download your PDF or CSV report!
