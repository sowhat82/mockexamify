#!/bin/bash
# Setup script for bash (Linux/macOS/Codespaces)
# Idempotent - safe to run multiple times

set -e

echo -e "\033[0;36m=== MockExamify Setup (bash) ===\033[0m"

# 1. Check Python version
echo -e "\n\033[0;33m[1/5] Checking Python version...\033[0m"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "\033[0;31mERROR: Python not found\033[0m"
    echo -e "\033[0;33mInstall Python 3.10+ from your package manager\033[0m"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+')
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo -e "\033[0;31mERROR: Python 3.10+ required. Found: Python $PYTHON_VERSION\033[0m"
    exit 1
fi

echo -e "\033[0;32m✓ Found Python $PYTHON_VERSION\033[0m"

# 2. Create virtual environment if needed
echo -e "\n\033[0;33m[2/5] Setting up virtual environment...\033[0m"
if [ -d "venv" ]; then
    echo -e "\033[0;32m✓ Virtual environment already exists\033[0m"
else
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo -e "\033[0;32m✓ Virtual environment created\033[0m"
fi

# 3. Activate virtual environment
echo -e "\n\033[0;33m[3/5] Activating virtual environment...\033[0m"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "\033[0;32m✓ Virtual environment activated\033[0m"
else
    echo -e "\033[0;31mERROR: Activation script not found\033[0m"
    exit 1
fi

# 4. Upgrade pip
echo -e "\n\033[0;33m[4/5] Upgrading pip...\033[0m"
if python -m pip install --upgrade pip --quiet; then
    echo -e "\033[0;32m✓ pip upgraded\033[0m"
else
    echo -e "\033[0;33mWARNING: pip upgrade failed (non-critical)\033[0m"
fi

# 5. Install requirements
echo -e "\n\033[0;33m[5/5] Installing requirements...\033[0m"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "\033[0;32m✓ Requirements installed\033[0m"
else
    echo -e "\033[0;33mWARNING: requirements.txt not found\033[0m"
fi

# Print installed versions
echo -e "\n\033[0;36m=== Installed Versions ===\033[0m"
STREAMLIT_VERSION=$(python -c "import streamlit; print(streamlit.__version__)" 2>/dev/null || echo "Not installed")
FLASK_VERSION=$(python -c "import flask; print(flask.__version__)" 2>/dev/null || echo "Not installed")

if [ "$STREAMLIT_VERSION" != "Not installed" ]; then
    echo -e "\033[0;32mStreamlit: $STREAMLIT_VERSION\033[0m"
else
    echo -e "\033[0;31mStreamlit: Not installed\033[0m"
fi

if [ "$FLASK_VERSION" != "Not installed" ]; then
    echo -e "\033[0;32mFlask: $FLASK_VERSION\033[0m"
else
    echo -e "\033[0;31mFlask: Not installed\033[0m"
fi

echo -e "\n\033[0;32m=== Setup Complete ===\033[0m"
echo -e "\033[0;36mTo activate venv manually: source venv/bin/activate\033[0m"
echo -e "\033[0;36mTo run servers: ./run_all.sh\033[0m"
