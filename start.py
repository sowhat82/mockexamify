"""
Web launcher for MockExamify - Simple development server
Runs both FastAPI backend and Streamlit frontend
"""
import subprocess
import sys
import time
import threading
import webbrowser
from pathlib import Path

def run_backend():
    """Run FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Backend server error: {e}")

def run_frontend():
    """Run Streamlit frontend"""
    print("🚀 Starting Streamlit frontend...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Frontend server error: {e}")

def check_requirements():
    """Check if all requirements are installed"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Try importing key packages
        import streamlit
        import fastapi
        import uvicorn
        print("✅ Core packages installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path(".env.example")
        if env_example.exists():
            print("⚠️  .env file not found. Creating from template...")
            try:
                env_file.write_text(env_example.read_text())
                print("✅ .env file created from template")
                print("⚠️  Please update .env with your actual credentials")
                return True
            except Exception as e:
                print(f"❌ Error creating .env file: {e}")
                return False
        else:
            print("❌ .env file not found and no template available")
            return False
    
    print("✅ .env file found")
    return True

def open_browser_after_delay():
    """Open browser after servers start"""
    time.sleep(5)  # Wait for servers to start
    print("🌐 Opening browser...")
    webbrowser.open("http://localhost:8501")

def main():
    """Main launcher function"""
    print("🎯 MockExamify Development Server")
    print("=" * 40)
    
    # Pre-flight checks
    if not check_requirements():
        return
    
    if not check_env_file():
        return
    
    print("\n🚀 Starting servers...")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    # Open browser after delay (disabled to prevent redundant tabs)
    # browser_thread = threading.Thread(target=open_browser_after_delay, daemon=True)
    # browser_thread.start()
    
    print("\n📊 Server Status:")
    print("- Backend API: http://localhost:8000")
    print("- Frontend App: http://localhost:8501")
    print("- API Docs: http://localhost:8000/docs")
    print("\n⚠️  Keep this terminal open to keep servers running")
    print("Press Ctrl+C to stop servers\n")
    
    # Run frontend in main thread (blocks until stopped)
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        print("✅ MockExamify stopped successfully")

if __name__ == "__main__":
    main()