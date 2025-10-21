#!/usr/bin/env pwsh
# Concurrent server runner for Windows PowerShell
# Runs Flask API (port 5000) and Streamlit UI (port 8501)

$ErrorActionPreference = "Stop"

Write-Host "=== MockExamify Development Servers ===" -ForegroundColor Cyan

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "ERROR: Virtual environment not found. Run setup.ps1 first" -ForegroundColor Red
    exit 1
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Check if ports are already in use
$flask_port = 5000
$streamlit_port = 8501

$flask_in_use = Get-NetTCPConnection -LocalPort $flask_port -State Listen -ErrorAction SilentlyContinue
$streamlit_in_use = Get-NetTCPConnection -LocalPort $streamlit_port -State Listen -ErrorAction SilentlyContinue

if ($flask_in_use) {
    Write-Host "WARNING: Port $flask_port already in use (Flask may already be running)" -ForegroundColor Yellow
}

if ($streamlit_in_use) {
    Write-Host "WARNING: Port $streamlit_port already in use (Streamlit may already be running)" -ForegroundColor Yellow
}

# Job tracking
$jobs = @()

# Cleanup function
function Cleanup {
    Write-Host "`n`nShutting down servers..." -ForegroundColor Yellow

    # Stop all background jobs
    $jobs | ForEach-Object {
        if ($_.State -eq "Running") {
            Stop-Job -Job $_
            Remove-Job -Job $_
        }
    }

    # Kill processes on our ports (fallback)
    $processes = Get-NetTCPConnection -LocalPort $flask_port, $streamlit_port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

    foreach ($proc_id in $processes) {
        try {
            Stop-Process -Id $proc_id -Force -ErrorAction SilentlyContinue
            Write-Host "Killed process $proc_id" -ForegroundColor Gray
        } catch {}
    }

    Write-Host "Cleanup complete" -ForegroundColor Green
    exit 0
}

# Register cleanup on Ctrl+C
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }

try {
    Write-Host "`n[1/2] Starting Flask API on port $flask_port..." -ForegroundColor Yellow
    $flask_job = Start-Job -ScriptBlock {
        & ".\venv\Scripts\python.exe" -m flask --app api run --port 5000
    }
    $jobs += $flask_job
    Write-Host "✓ Flask started (Job ID: $($flask_job.Id))" -ForegroundColor Green

    Start-Sleep -Seconds 2

    Write-Host "`n[2/2] Starting Streamlit on port $streamlit_port..." -ForegroundColor Yellow
    $streamlit_job = Start-Job -ScriptBlock {
        & ".\venv\Scripts\python.exe" -m streamlit run streamlit_app.py --server.port 8501 --server.headless true
    }
    $jobs += $streamlit_job
    Write-Host "✓ Streamlit started (Job ID: $($streamlit_job.Id))" -ForegroundColor Green

    Write-Host "`n=== Servers Running ===" -ForegroundColor Green
    Write-Host "Flask API:      http://localhost:$flask_port" -ForegroundColor Cyan
    Write-Host "Streamlit UI:   http://localhost:$streamlit_port" -ForegroundColor Cyan
    Write-Host "`nPress Ctrl+C to stop all servers" -ForegroundColor Yellow

    # Monitor jobs and stream output
    while ($true) {
        foreach ($job in $jobs) {
            $output = Receive-Job -Job $job -ErrorAction SilentlyContinue
            if ($output) {
                Write-Host $output
            }

            if ($job.State -eq "Failed" -or $job.State -eq "Stopped") {
                Write-Host "ERROR: $($job.Name) job failed" -ForegroundColor Red
                Cleanup
            }
        }
        Start-Sleep -Milliseconds 500
    }

} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Cleanup
}
