# setup.ps1 - Automated Local Environment Setup Script for Windows PowerShell
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Testing Agent Platform - Environment Setup (Windows)       " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verify Python availability
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Write-Error "Python was not found on PATH. Please install Python 3.11 or higher."
    exit 1
}

$pythonVersionOutput = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$major, $minor = $pythonVersionOutput.Split('.') | ForEach-Object { [int]$_ }
Write-Host "Found Python version: $pythonVersionOutput" -ForegroundColor Green

if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
    Write-Error "Python 3.11 or higher is required. Found Python $pythonVersionOutput."
    exit 1
}

# 2. Virtual Environment Creation
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment in .venv..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "Existing virtual environment detected at .venv." -ForegroundColor Green
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment Python interpreter not found at $venvPython."
    exit 1
}

# 3. Upgrade pip
Write-Host "Upgrading pip inside virtual environment..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip

# 4. Install Dependencies
$reqDev = Join-Path $PSScriptRoot "requirements-dev.txt"
if (Test-Path $reqDev) {
    Write-Host "Installing dependencies from requirements-dev.txt..." -ForegroundColor Yellow
    & $venvPython -m pip install -r $reqDev
} else {
    $req = Join-Path $PSScriptRoot "requirements.txt"
    Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    & $venvPython -m pip install -r $req
}

# 5. Environment Variables (.env)
$envFile = Join-Path $PSScriptRoot ".env"
$envExample = Join-Path $PSScriptRoot ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item -Path $envExample -Destination $envFile
        Write-Host ".env created. Please customize it if needed." -ForegroundColor Green
    } else {
        Write-Warning ".env.example not found. Please create .env manually."
    }
} else {
    Write-Host ".env already exists." -ForegroundColor Green
}

# 6. Run Environment Verification
$checkScript = Join-Path $PSScriptRoot "scripts\check_environment.py"
Write-Host "Running environment verification..." -ForegroundColor Yellow
& $venvPython $checkScript

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nEnvironment setup is complete and verified!" -ForegroundColor Green
    Write-Host "To activate this environment in PowerShell run:" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
} else {
    Write-Error "Environment verification failed. Please check the logs above."
}
