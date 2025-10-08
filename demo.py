"""
MockExamify Demo Launcher
Starts the application in demo mode with mock data
"""
import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def start_demo_api():
    """Start the FastAPI backend in demo mode"""
    print("🚀 Starting MockExamify Backend (Demo Mode)...")
    
    # Set demo environment variables
    os.environ["DEMO_MODE"] = "true"
    os.environ["SUPABASE_URL"] = "demo"
    os.environ["SUPABASE_KEY"] = "demo"
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_demo"
    os.environ["SECRET_KEY"] = "demo_secret_key_for_testing_only"
    
    try:
        # Start FastAPI server
        cmd = [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped")

def start_demo_streamlit():
    """Start the Streamlit frontend in demo mode"""
    print("🎨 Starting MockExamify Frontend (Demo Mode)...")
    
    # Set demo environment variables
    os.environ["DEMO_MODE"] = "true"
    os.environ["SUPABASE_URL"] = "demo"
    os.environ["SUPABASE_KEY"] = "demo"
    os.environ["STRIPE_PUBLISHABLE_KEY"] = "pk_test_demo"
    os.environ["SECRET_KEY"] = "demo_secret_key_for_testing_only"
    
    try:
        # Start Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port", "8501"]
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped")

def main():
    print("🎯 MockExamify Demo Mode")
    print("=" * 50)
    print("This will start the application with demo data.")
    print("No external services required!")
    print()
    print("Access the app at: http://localhost:8501")
    print("API docs at: http://localhost:8000/docs")
    print()
    print("Demo accounts:")
    print("- Admin: admin@demo.com / admin123")
    print("- User: user@demo.com / user123")
    print()
    print("Press Ctrl+C to stop both services")
    print("=" * 50)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_demo_api, daemon=True)
    backend_thread.start()
    
    # Give backend time to start
    time.sleep(3)
    
    # Start frontend (blocking)
    start_demo_streamlit()

if __name__ == "__main__":
    main()