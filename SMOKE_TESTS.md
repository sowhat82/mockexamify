# Smoke Test Commands

Quick validation commands to ensure your environment is set up correctly.

## Prerequisites
Make sure you've run the setup script:
```powershell
# Windows
.\setup.ps1

# Linux/macOS/Codespaces
bash setup.sh
```

## Python Import Tests

### Windows PowerShell
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Test core imports
python -c "import streamlit; print('Streamlit:', streamlit.__version__)"
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import supabase; print('Supabase: OK')"
python -c "import stripe; print('Stripe: OK')"

# Test custom modules
python -c "import db; print('Database module: OK')"
python -c "import auth_utils; print('Auth module: OK')"
python -c "import openrouter_utils; print('OpenRouter module: OK')"
python -c "import config; print('Config module: OK')"

# All in one
python -c "import streamlit, flask, supabase, stripe, db, auth_utils, openrouter_utils, config; print('✓ All imports successful')"
```

### Bash (Linux/macOS/Codespaces)
```bash
# Activate venv
source venv/bin/activate

# Test core imports
python -c "import streamlit; print('Streamlit:', streamlit.__version__)"
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import supabase; print('Supabase: OK')"
python -c "import stripe; print('Stripe: OK')"

# Test custom modules
python -c "import db; print('Database module: OK')"
python -c "import auth_utils; print('Auth module: OK')"
python -c "import openrouter_utils; print('OpenRouter module: OK')"
python -c "import config; print('Config module: OK')"

# All in one
python -c "import streamlit, flask, supabase, stripe, db, auth_utils, openrouter_utils, config; print('✓ All imports successful')"
```

## Configuration Validation

### Check Secrets File (Windows)
```powershell
# Check if secrets file exists
Test-Path .\.streamlit\secrets.toml

# View secrets structure (DON'T commit output!)
Get-Content .\.streamlit\secrets.toml
```

### Check Secrets File (Bash)
```bash
# Check if secrets file exists
test -f .streamlit/secrets.toml && echo "✓ Secrets file exists" || echo "✗ Secrets file missing"

# View secrets structure (DON'T commit output!)
cat .streamlit/secrets.toml
```

## Port Availability Tests

### Windows PowerShell
```powershell
# Check if Flask port (5000) is available
$flask_port = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
if ($flask_port) {
    Write-Host "⚠ Port 5000 is in use"
} else {
    Write-Host "✓ Port 5000 is available"
}

# Check if Streamlit port (8501) is available
$streamlit_port = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
if ($streamlit_port) {
    Write-Host "⚠ Port 8501 is in use"
} else {
    Write-Host "✓ Port 8501 is available"
}
```

### Bash
```bash
# Check if Flask port (5000) is available
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠ Port 5000 is in use"
else
    echo "✓ Port 5000 is available"
fi

# Check if Streamlit port (8501) is available
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠ Port 8501 is in use"
else
    echo "✓ Port 8501 is available"
fi
```

## Database Connection Test

### Windows PowerShell
```powershell
# Test Supabase connection
python -c "from db import DatabaseManager; db = DatabaseManager(); print('✓ Database connection successful')"
```

### Bash
```bash
# Test Supabase connection
python -c "from db import DatabaseManager; db = DatabaseManager(); print('✓ Database connection successful')"
```

## API Health Check

### After Starting Servers
```powershell
# Windows - Check Flask health
Invoke-WebRequest -Uri http://localhost:5000/health -UseBasicParsing | Select-Object -ExpandProperty StatusCode

# Windows - Check Streamlit
Invoke-WebRequest -Uri http://localhost:8501/healthz -UseBasicParsing | Select-Object -ExpandProperty StatusCode
```

```bash
# Bash - Check Flask health
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health

# Bash - Check Streamlit
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/healthz
```

## Quick Validation Script

### Windows (save as smoke-test.ps1)
```powershell
#!/usr/bin/env pwsh
.\venv\Scripts\Activate.ps1
python -c "import streamlit, flask, supabase, stripe, db, auth_utils; print('✓ All imports successful')" && Write-Host "✓ Environment OK" -ForegroundColor Green || Write-Host "✗ Environment failed" -ForegroundColor Red
```

### Bash (save as smoke-test.sh)
```bash
#!/bin/bash
source venv/bin/activate
python -c "import streamlit, flask, supabase, stripe, db, auth_utils; print('✓ All imports successful')" && echo -e "\033[0;32m✓ Environment OK\033[0m" || echo -e "\033[0;31m✗ Environment failed\033[0m"
```

## Expected Output

✅ **Success looks like:**
```
Streamlit: 1.30.0
Flask: 3.0.0
Supabase: OK
Stripe: OK
Database module: OK
Auth module: OK
OpenRouter module: OK
Config module: OK
✓ All imports successful
```

❌ **Failure looks like:**
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution:** Run setup script again: `.\setup.ps1` or `bash setup.sh`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Run `.\setup.ps1` or `bash setup.sh` |
| Port in use | Stop existing server or use `.\stop_server.ps1` |
| Database connection fails | Check `.streamlit/secrets.toml` configuration |
| Secrets file missing | Copy from `.env.example` and configure |
| Python version error | Install Python 3.10+ |
