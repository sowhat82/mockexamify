#!/bin/bash
# Concurrent server runner for bash (Linux/macOS/Codespaces)
# Runs Flask API (port 5000) and Streamlit UI (port 8501)

set -e

echo -e "\033[0;36m=== MockExamify Development Servers ===\033[0m"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "\033[0;31mERROR: Virtual environment not found. Run setup.sh first\033[0m"
    exit 1
fi

# Activate venv
echo -e "\033[0;33mActivating virtual environment...\033[0m"
source venv/bin/activate

# Port configuration
FLASK_PORT=5000
STREAMLIT_PORT=8501

# Check if ports are in use
if lsof -Pi :$FLASK_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "\033[0;33mWARNING: Port $FLASK_PORT already in use (Flask may already be running)\033[0m"
fi

if lsof -Pi :$STREAMLIT_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "\033[0;33mWARNING: Port $STREAMLIT_PORT already in use (Streamlit may already be running)\033[0m"
fi

# Process tracking
FLASK_PID=""
STREAMLIT_PID=""

# Cleanup function
cleanup() {
    echo -e "\n\n\033[0;33mShutting down servers...\033[0m"

    # Kill our spawned processes
    [ -n "$FLASK_PID" ] && kill $FLASK_PID 2>/dev/null && echo "Stopped Flask (PID $FLASK_PID)"
    [ -n "$STREAMLIT_PID" ] && kill $STREAMLIT_PID 2>/dev/null && echo "Stopped Streamlit (PID $STREAMLIT_PID)"

    # Fallback: kill any processes on our ports
    FLASK_PROC=$(lsof -ti:$FLASK_PORT 2>/dev/null)
    STREAMLIT_PROC=$(lsof -ti:$STREAMLIT_PORT 2>/dev/null)

    [ -n "$FLASK_PROC" ] && kill $FLASK_PROC 2>/dev/null && echo "Killed process on port $FLASK_PORT"
    [ -n "$STREAMLIT_PROC" ] && kill $STREAMLIT_PROC 2>/dev/null && echo "Killed process on port $STREAMLIT_PORT"

    echo -e "\033[0;32mCleanup complete\033[0m"
    exit 0
}

# Register cleanup on Ctrl+C
trap cleanup SIGINT SIGTERM

# Start FastAPI in background
echo -e "\n\033[0;33m[1/2] Starting FastAPI on port $FLASK_PORT...\033[0m"
python -m uvicorn api:app --host 0.0.0.0 --port $FLASK_PORT &
FLASK_PID=$!
echo -e "\033[0;32m✓ FastAPI started (PID: $FLASK_PID)\033[0m"

sleep 2

# Start Streamlit in background
echo -e "\n\033[0;33m[2/2] Starting Streamlit on port $STREAMLIT_PORT...\033[0m"
python -m streamlit run streamlit_app.py --server.port $STREAMLIT_PORT --server.headless true &
STREAMLIT_PID=$!
echo -e "\033[0;32m✓ Streamlit started (PID: $STREAMLIT_PID)\033[0m"

echo -e "\n\033[0;32m=== Servers Running ===\033[0m"
echo -e "\033[0;36mFlask API:      http://localhost:$FLASK_PORT\033[0m"
echo -e "\033[0;36mStreamlit UI:   http://localhost:$STREAMLIT_PORT\033[0m"
echo -e "\n\033[0;33mPress Ctrl+C to stop all servers\033[0m"

# Wait for both processes
wait $FLASK_PID $STREAMLIT_PID
