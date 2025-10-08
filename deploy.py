"""
Deployment scripts and utilities for MockExamify
"""
import os
import subprocess
import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'streamlit',
        'fastapi',
        'uvicorn',
        'supabase',
        'stripe',
        'httpx',
        'pydantic',
        'weasyprint',
        'python-dotenv',
        'reportlab',
        'bcrypt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed!")
    return True

def check_environment():
    """Check if environment variables are set"""
    print("\n🔧 Checking environment configuration...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"❌ {var}")
        else:
            print(f"✅ {var}")
    
    optional_vars = [
        'OPENROUTER_API_KEY',
        'STRIPE_WEBHOOK_SECRET'
    ]
    
    for var in optional_vars:
        if not os.getenv(var):
            print(f"⚠️  {var} (optional)")
        else:
            print(f"✅ {var}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with these variables.")
        return False
    
    print("✅ Environment configuration complete!")
    return True

def start_backend():
    """Start the FastAPI backend server"""
    print("\n🚀 Starting FastAPI backend...")
    try:
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", "api:app", 
            "--reload", "--port", "8000", "--host", "0.0.0.0"
        ])
        print("✅ Backend server starting on http://localhost:8000")
        return True
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False

def start_frontend():
    """Start the Streamlit frontend"""
    print("\n🚀 Starting Streamlit frontend...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501"
        ])
        return True
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return False

def deploy_check():
    """Run deployment readiness check"""
    print("🚀 MockExamify Deployment Check")
    print("=" * 40)
    
    checks = [
        check_dependencies,
        check_environment
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! Ready for deployment.")
        
        choice = input("\nWould you like to start the application? (y/n): ")
        if choice.lower() == 'y':
            print("\n📋 Starting application...")
            print("1. Starting backend server...")
            start_backend()
            
            print("2. Waiting for backend to initialize...")
            import time
            time.sleep(3)
            
            print("3. Starting frontend...")
            start_frontend()
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")

if __name__ == "__main__":
    deploy_check()