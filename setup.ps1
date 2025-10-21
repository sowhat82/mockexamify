#!/usr/bin/env pwsh
# Setup script for Windows PowerShell
# Idempotent - safe to run multiple times

$ErrorActionPreference = "Stop"

Write-Host "=== MockExamify Setup (Windows) ===" -ForegroundColor Cyan

# 1. Check Python version
Write-Host "`n[1/5] Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]

        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "ERROR: Python 3.10 or newer required. Found: $pythonVersion" -ForegroundColor Red
            Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "✓ Found $pythonVersion" -ForegroundColor Green
    } else {
        throw "Could not parse Python version"
    }
} catch {
    Write-Host "ERROR: Python not found or not in PATH" -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# 2. Create virtual environment if needed
Write-Host "`n[2/5] Setting up virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# 3. Activate virtual environment
Write-Host "`n[3/5] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "ERROR: Activation script not found" -ForegroundColor Red
    exit 1
}

# 4. Upgrade pip
Write-Host "`n[4/5] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pip upgraded" -ForegroundColor Green
} else {
    Write-Host "WARNING: pip upgrade failed (non-critical)" -ForegroundColor Yellow
}

# 5. Install requirements
Write-Host "`n[5/5] Installing requirements..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install requirements" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Requirements installed" -ForegroundColor Green
} else {
    Write-Host "WARNING: requirements.txt not found" -ForegroundColor Yellow
}

# Print installed versions
Write-Host "`n=== Installed Versions ===" -ForegroundColor Cyan
try {
    $streamlitVersion = python -c "import streamlit; print(streamlit.__version__)" 2>$null
    Write-Host "Streamlit: $streamlitVersion" -ForegroundColor Green
} catch {
    Write-Host "Streamlit: Not installed" -ForegroundColor Red
}

try {
    $flaskVersion = python -c "import flask; print(flask.__version__)" 2>$null
    Write-Host "Flask: $flaskVersion" -ForegroundColor Green
} catch {
    Write-Host "Flask: Not installed" -ForegroundColor Red
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "To activate venv manually: .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "To run servers: .\run_all.ps1" -ForegroundColor Cyan
