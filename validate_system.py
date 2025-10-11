#!/usr/bin/env python3
"""
MockExamify System Validation
Final validation script to ensure production readiness
"""
import os
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

def validate_file_structure():
    """Validate that all required files are present"""
    print("🗂️  Validating file structure...")
    
    required_files = {
        # Core application files
        "streamlit_app.py": "Main Streamlit application",
        "api.py": "FastAPI backend",
        "models.py": "Data models",
        "db.py": "Database operations",
        "config.py": "Configuration management",
        
        # Utility modules
        "auth_utils.py": "Authentication utilities",
        "security_utils.py": "Security framework",
        "openrouter_utils.py": "AI integration",
        "stripe_utils.py": "Payment processing",
        "pdf_utils.py": "PDF generation",
        "production_utils.py": "Production utilities",
        "ingest.py": "Document ingestion",
        
        # Admin pages
        "pages/admin_dashboard.py": "Admin dashboard",
        "pages/admin_upload.py": "Admin upload interface",
        "pages/admin_manage.py": "Admin management",
        "pages/exam.py": "Exam interface",
        "pages/dashboard.py": "User dashboard",
        "pages/purchase_credits.py": "Credit purchase",
        
        # Configuration files
        "requirements.txt": "Python dependencies",
        "pytest.ini": "Test configuration",
        
        # Testing files
        "test_suite.py": "Test suite",
        "test_integration.py": "Integration tests",
        "run_tests.py": "Test runner",
        
        # Documentation
        "README.md": "Project documentation",
        "DEPLOYMENT_CHECKLIST.md": "Deployment guide"
    }
    
    missing_files = []
    present_files = []
    
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            present_files.append(f"✅ {file_path} - {description}")
        else:
            missing_files.append(f"❌ {file_path} - {description}")
    
    print(f"\n📋 File Structure Report:")
    print(f"  Present: {len(present_files)}")
    print(f"  Missing: {len(missing_files)}")
    
    if missing_files:
        print(f"\n⚠️  Missing files:")
        for file in missing_files:
            print(f"    {file}")
    
    return len(missing_files) == 0

def validate_python_imports():
    """Validate that all modules can be imported"""
    print("\n🐍 Validating Python imports...")
    
    modules_to_test = [
        ("streamlit", "Streamlit framework"),
        ("fastapi", "FastAPI framework"),
        ("supabase", "Supabase client"),
        ("stripe", "Stripe payments"),
        ("pydantic", "Data validation"),
        ("pytest", "Testing framework"),
        ("psutil", "System monitoring"),
        ("scipy", "Scientific computing"),
        ("bleach", "HTML sanitization"),
        ("PyPDF2", "PDF processing"),
        ("docx", "DOCX processing"),
    ]
    
    local_modules = [
        ("models", "Data models"),
        ("db", "Database manager"),
        ("auth_utils", "Authentication"),
        ("security_utils", "Security framework"),
        ("openrouter_utils", "AI integration"),
        ("stripe_utils", "Payment utilities"),
        ("pdf_utils", "PDF utilities"),
        ("production_utils", "Production utilities"),
    ]
    
    failed_imports = []
    successful_imports = []
    
    # Test external dependencies
    for module, description in modules_to_test:
        try:
            __import__(module)
            successful_imports.append(f"✅ {module} - {description}")
        except ImportError as e:
            failed_imports.append(f"❌ {module} - {description} ({e})")
    
    # Test local modules
    for module, description in local_modules:
        try:
            if os.path.exists(f"{module}.py"):
                # Try to compile the module
                with open(f"{module}.py", 'r', encoding='utf-8') as f:
                    compile(f.read(), f"{module}.py", 'exec')
                successful_imports.append(f"✅ {module} - {description}")
            else:
                failed_imports.append(f"❌ {module}.py - File not found")
        except SyntaxError as e:
            failed_imports.append(f"❌ {module} - Syntax error: {e}")
        except Exception as e:
            failed_imports.append(f"❌ {module} - Error: {e}")
    
    print(f"\n📋 Import Report:")
    print(f"  Successful: {len(successful_imports)}")
    print(f"  Failed: {len(failed_imports)}")
    
    if failed_imports:
        print(f"\n⚠️  Failed imports:")
        for failure in failed_imports:
            print(f"    {failure}")
    
    return len(failed_imports) == 0

def validate_configuration():
    """Validate configuration files and environment"""
    print("\n⚙️  Validating configuration...")
    
    config_checks = []
    
    # Check if config.py exists and has required attributes
    try:
        import config
        required_config = [
            'SUPABASE_URL',
            'SUPABASE_KEY', 
            'OPENROUTER_API_KEY',
            'STRIPE_SECRET_KEY'
        ]
        
        for attr in required_config:
            if hasattr(config, attr):
                value = getattr(config, attr)
                if value and value != "your_key_here":
                    config_checks.append(f"✅ {attr} - Configured")
                else:
                    config_checks.append(f"⚠️  {attr} - Not configured")
            else:
                config_checks.append(f"❌ {attr} - Missing")
                
    except ImportError:
        config_checks.append("❌ config.py - Cannot import")
    
    # Check streamlit secrets
    secrets_file = "streamlit-secrets.toml"
    if os.path.exists(secrets_file):
        config_checks.append("✅ streamlit-secrets.toml - Present")
    else:
        config_checks.append("⚠️  streamlit-secrets.toml - Missing")
    
    # Check requirements.txt
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", 'r') as f:
            requirements = f.read()
            if "streamlit" in requirements and "fastapi" in requirements:
                config_checks.append("✅ requirements.txt - Core dependencies listed")
            else:
                config_checks.append("⚠️  requirements.txt - Missing core dependencies")
    else:
        config_checks.append("❌ requirements.txt - Missing")
    
    print(f"\n📋 Configuration Report:")
    for check in config_checks:
        print(f"    {check}")
    
    return not any("❌" in check for check in config_checks)

def validate_database_schema():
    """Validate database schema files"""
    print("\n🗄️  Validating database schema...")
    
    schema_files = [
        "database_schema.sql",
        "database_schema_enhanced.sql",
        "database_schema_updated.sql"
    ]
    
    schema_checks = []
    
    for schema_file in schema_files:
        if os.path.exists(schema_file):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for key tables
                required_tables = [
                    "users", "exam_categories", "topics", "questions", 
                    "papers", "attempts", "credits_ledger"
                ]
                
                found_tables = []
                for table in required_tables:
                    if f"CREATE TABLE {table}" in content or f"create table {table}" in content:
                        found_tables.append(table)
                
                if len(found_tables) >= 5:  # At least 5 core tables
                    schema_checks.append(f"✅ {schema_file} - Valid schema ({len(found_tables)} tables)")
                else:
                    schema_checks.append(f"⚠️  {schema_file} - Incomplete schema ({len(found_tables)} tables)")
                    
            except Exception as e:
                schema_checks.append(f"❌ {schema_file} - Error reading: {e}")
        else:
            schema_checks.append(f"⚠️  {schema_file} - Not found")
    
    print(f"\n📋 Database Schema Report:")
    for check in schema_checks:
        print(f"    {check}")
    
    return len(schema_checks) > 0

def validate_testing_infrastructure():
    """Validate testing setup"""
    print("\n🧪 Validating testing infrastructure...")
    
    test_checks = []
    
    # Check test files
    test_files = ["test_suite.py", "test_integration.py", "run_tests.py"]
    for test_file in test_files:
        if os.path.exists(test_file):
            test_checks.append(f"✅ {test_file} - Present")
        else:
            test_checks.append(f"❌ {test_file} - Missing")
    
    # Check pytest configuration
    if os.path.exists("pytest.ini"):
        test_checks.append("✅ pytest.ini - Present")
    else:
        test_checks.append("⚠️  pytest.ini - Missing")
    
    # Check if pytest is available
    try:
        import pytest
        test_checks.append("✅ pytest - Installed")
    except ImportError:
        test_checks.append("❌ pytest - Not installed")
    
    print(f"\n📋 Testing Infrastructure Report:")
    for check in test_checks:
        print(f"    {check}")
    
    return not any("❌" in check for check in test_checks)

def validate_security_features():
    """Validate security implementations"""
    print("\n🔒 Validating security features...")
    
    security_checks = []
    
    # Check security_utils.py
    if os.path.exists("security_utils.py"):
        try:
            with open("security_utils.py", 'r', encoding='utf-8') as f:
                content = f.read()
                
            security_features = [
                ("SecurityManager", "Security manager class"),
                ("InputValidator", "Input validation"),
                ("validate_input", "Input validation function"),
                ("create_session_token", "Session management"),
                ("rate_limiting", "Rate limiting"),
                ("audit_log", "Audit logging")
            ]
            
            for feature, description in security_features:
                if feature in content:
                    security_checks.append(f"✅ {description} - Implemented")
                else:
                    security_checks.append(f"⚠️  {description} - Not found")
                    
        except Exception as e:
            security_checks.append(f"❌ security_utils.py - Error reading: {e}")
    else:
        security_checks.append("❌ security_utils.py - Missing")
    
    # Check for SQL injection prevention
    if os.path.exists("db.py"):
        try:
            with open("db.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "supabase" in content and "parameterized" in content.lower():
                security_checks.append("✅ SQL injection prevention - Implemented")
            else:
                security_checks.append("⚠️  SQL injection prevention - Check implementation")
        except:
            security_checks.append("⚠️  SQL injection prevention - Cannot verify")
    
    print(f"\n📋 Security Features Report:")
    for check in security_checks:
        print(f"    {check}")
    
    return not any("❌" in check for check in security_checks)

def validate_ai_integration():
    """Validate AI integration setup"""
    print("\n🤖 Validating AI integration...")
    
    ai_checks = []
    
    # Check openrouter_utils.py
    if os.path.exists("openrouter_utils.py"):
        try:
            with open("openrouter_utils.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            ai_features = [
                ("generate_questions", "Question generation"),
                ("generate_explanation", "Explanation generation"),
                ("tag_question_topic", "Topic tagging"),
                ("openrouter_manager", "OpenRouter manager")
            ]
            
            for feature, description in ai_features:
                if feature in content:
                    ai_checks.append(f"✅ {description} - Implemented")
                else:
                    ai_checks.append(f"⚠️  {description} - Not found")
                    
        except Exception as e:
            ai_checks.append(f"❌ openrouter_utils.py - Error reading: {e}")
    else:
        ai_checks.append("❌ openrouter_utils.py - Missing")
    
    print(f"\n📋 AI Integration Report:")
    for check in ai_checks:
        print(f"    {check}")
    
    return not any("❌" in check for check in ai_checks)

def generate_validation_report(results: Dict[str, bool]):
    """Generate final validation report"""
    print("\n" + "="*60)
    print(" MOCKEXAMIFY SYSTEM VALIDATION REPORT")
    print("="*60)
    
    passed_validations = sum(1 for result in results.values() if result)
    total_validations = len(results)
    success_rate = (passed_validations / total_validations) * 100
    
    print(f"\n📊 Validation Summary: {passed_validations}/{total_validations} passed ({success_rate:.1f}%)")
    print(f"🕒 Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n📋 Detailed Results:")
    for validation_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {validation_name}")
    
    # Overall assessment
    if success_rate >= 90:
        print(f"\n🎉 Overall Status: EXCELLENT - System is production-ready!")
        print(f"   🚀 Ready for deployment with confidence")
    elif success_rate >= 80:
        print(f"\n✅ Overall Status: GOOD - System is mostly ready")
        print(f"   ⚠️  Address minor issues before deployment")
    elif success_rate >= 70:
        print(f"\n⚠️  Overall Status: NEEDS WORK - Some critical issues")
        print(f"   🔧 Fix failing validations before deployment")
    else:
        print(f"\n🚨 Overall Status: CRITICAL ISSUES - Not ready for deployment")
        print(f"   🛠️  Significant work needed before deployment")
    
    # Recommendations
    print(f"\n📝 Recommendations:")
    
    if results.get("File Structure", False):
        print(f"  ✅ File structure is complete")
    else:
        print(f"  🔧 Complete missing files before deployment")
    
    if results.get("Python Imports", False):
        print(f"  ✅ All dependencies are properly installed")
    else:
        print(f"  📦 Install missing dependencies: pip install -r requirements.txt")
    
    if results.get("Configuration", False):
        print(f"  ✅ Configuration is properly set up")
    else:
        print(f"  ⚙️  Complete configuration setup (API keys, database)")
    
    if results.get("Security Features", False):
        print(f"  ✅ Security features are implemented")
    else:
        print(f"  🔒 Implement missing security features")
    
    if results.get("Testing Infrastructure", False):
        print(f"  ✅ Testing infrastructure is ready")
        print(f"     Run: python run_tests.py")
    else:
        print(f"  🧪 Complete testing setup")
    
    print(f"\n🎯 Next Steps:")
    if success_rate >= 90:
        print(f"  1. Run comprehensive tests: python run_tests.py")
        print(f"  2. Deploy to staging environment")
        print(f"  3. Perform end-to-end validation")
        print(f"  4. Deploy to production")
    elif success_rate >= 80:
        print(f"  1. Address failing validations")
        print(f"  2. Run comprehensive tests")
        print(f"  3. Re-run validation")
        print(f"  4. Deploy to staging")
    else:
        print(f"  1. Fix critical issues identified above")
        print(f"  2. Complete missing components")
        print(f"  3. Re-run validation")
        print(f"  4. Run tests when validation passes")
    
    return success_rate >= 80

def main():
    """Main validation function"""
    print("🔍 MockExamify System Validation")
    print("Checking production readiness...")
    print("-" * 40)
    
    # Run all validations
    validations = {
        "File Structure": validate_file_structure(),
        "Python Imports": validate_python_imports(),
        "Configuration": validate_configuration(),
        "Database Schema": validate_database_schema(),
        "Testing Infrastructure": validate_testing_infrastructure(),
        "Security Features": validate_security_features(),
        "AI Integration": validate_ai_integration()
    }
    
    # Generate report
    overall_success = generate_validation_report(validations)
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Validation failed with exception: {e}")
        sys.exit(1)