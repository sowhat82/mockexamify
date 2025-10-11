#!/usr/bin/env python3
"""
MockExamify Test Runner
Runs comprehensive tests for the application
"""
import os
import sys
import subprocess
import time
from datetime import datetime

def print_banner(text):
    """Print a banner with text"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_section(text):
    """Print a section header"""
    print(f"\n🔍 {text}")
    print("-" * 40)

def run_command(command, description, timeout=60):
    """Run a command and capture output"""
    print(f"Running: {description}")
    print(f"Command: {command}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} - Completed in {duration:.2f}s")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - Failed in {duration:.2f}s")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"💥 {description} - Exception: {e}")
        return False

def check_python_version():
    """Check Python version"""
    print_section("Python Environment Check")
    
    version_info = sys.version_info
    python_version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    print(f"Python Version: {python_version}")
    
    if version_info >= (3, 8):
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print_section("Dependency Check")
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "fastapi",
        "streamlit",
        "supabase",
        "stripe",
        "httpx",
        "pydantic",
        "psutil",
        "scipy",
        "bleach",
        "PyPDF2",
        "python-docx"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def run_syntax_check():
    """Check Python syntax of all files"""
    print_section("Syntax Check")
    
    python_files = [
        "streamlit_app.py",
        "api.py", 
        "models.py",
        "db.py",
        "auth_utils.py",
        "security_utils.py",
        "openrouter_utils.py",
        "stripe_utils.py",
        "pdf_utils.py",
        "production_utils.py",
        "ingest.py",
        "test_suite.py",
        "test_integration.py"
    ]
    
    all_passed = True
    
    for file in python_files:
        if os.path.exists(file):
            success = run_command(
                f"python -m py_compile {file}",
                f"Syntax check: {file}",
                timeout=10
            )
            if not success:
                all_passed = False
        else:
            print(f"⚠️  File not found: {file}")
    
    return all_passed

def run_unit_tests():
    """Run unit tests"""
    print_section("Unit Tests")
    
    if not os.path.exists("test_suite.py"):
        print("❌ test_suite.py not found")
        return False
    
    return run_command(
        "python -m pytest test_suite.py -v --tb=short --timeout=60",
        "Unit Tests",
        timeout=120
    )

def run_integration_tests():
    """Run integration tests"""
    print_section("Integration Tests")
    
    if not os.path.exists("test_integration.py"):
        print("❌ test_integration.py not found")
        return False
    
    return run_command(
        "python test_integration.py",
        "Integration Tests",
        timeout=180
    )

def run_security_tests():
    """Run security-focused tests"""
    print_section("Security Tests")
    
    success = run_command(
        "python -c \"from test_suite import run_security_tests; run_security_tests()\"",
        "Security Tests",
        timeout=60
    )
    
    return success

def run_performance_tests():
    """Run performance tests"""
    print_section("Performance Tests")
    
    success = run_command(
        "python -c \"from test_suite import run_performance_tests; run_performance_tests()\"",
        "Performance Tests",
        timeout=120
    )
    
    return success

def run_api_health_check():
    """Check if the API is responsive"""
    print_section("API Health Check")
    
    # Try to import and test API
    success = run_command(
        "python -c \"from api import app; from fastapi.testclient import TestClient; client = TestClient(app); response = client.get('/api/health'); print(f'Health check: {response.status_code}'); assert response.status_code == 200\"",
        "API Health Check",
        timeout=30
    )
    
    return success

def run_database_connectivity():
    """Test database connectivity"""
    print_section("Database Connectivity")
    
    success = run_command(
        "python -c \"from db import db; import asyncio; result = asyncio.run(db.health_check()); print(f'Database health: {result}'); assert result.get('database', {}).get('connected', False)\"",
        "Database Connectivity",
        timeout=30
    )
    
    return success

def generate_test_report(results):
    """Generate a test report"""
    print_banner("TEST REPORT SUMMARY")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
    print(f"🕒 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📋 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if success_rate >= 80:
        print("\n🎉 Overall Status: GOOD - Ready for deployment!")
    elif success_rate >= 60:
        print("\n⚠️  Overall Status: NEEDS ATTENTION - Some tests failed")
    else:
        print("\n🚨 Overall Status: CRITICAL ISSUES - Multiple test failures")
    
    return success_rate >= 80

def main():
    """Main test runner"""
    print_banner("MockExamify Comprehensive Test Suite")
    print(f"🚀 Starting test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Store test results
    results = {}
    
    # Pre-flight checks
    results["Python Version"] = check_python_version()
    results["Dependencies"] = check_dependencies()
    
    if not results["Dependencies"]:
        print("\n🛑 Cannot proceed without required dependencies")
        return False
    
    # Code quality checks
    results["Syntax Check"] = run_syntax_check()
    
    # Core functionality tests
    results["API Health"] = run_api_health_check()
    results["Database Connectivity"] = run_database_connectivity()
    
    # Test suites
    results["Unit Tests"] = run_unit_tests()
    results["Integration Tests"] = run_integration_tests()
    results["Security Tests"] = run_security_tests()
    results["Performance Tests"] = run_performance_tests()
    
    # Generate final report
    overall_success = generate_test_report(results)
    
    if overall_success:
        print("\n🎯 All critical tests passed! MockExamify is ready.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test runner failed with exception: {e}")
        sys.exit(1)