"""
Configuration management for MockExamify
"""
import os
from dotenv import load_dotenv

# Try to import streamlit for secrets access
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, skip loading .env file
    pass

def get_secret(key: str, default: str = "") -> str:
    """Get secret from environment variables or Streamlit secrets"""
    # First try environment variables
    value = os.getenv(key)
    if value:
        return value
    
    # Then try Streamlit secrets if available
    if HAS_STREAMLIT:
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except:
            pass
    
    return default

# Check if we're in demo mode
DEMO_MODE = get_secret('DEMO_MODE', 'false').lower() == 'true'

# Override demo mode if no secrets are available (force production mode on Streamlit Cloud)
if not HAS_STREAMLIT or not hasattr(st, 'secrets'):
    DEMO_MODE = False

# Supabase Configuration
if DEMO_MODE:
    SUPABASE_URL = "demo"
    SUPABASE_KEY = "demo"
else:
    SUPABASE_URL = get_secret("SUPABASE_URL")
    SUPABASE_KEY = get_secret("SUPABASE_KEY")

# Stripe Configuration
if DEMO_MODE:
    STRIPE_SECRET_KEY = "sk_test_demo"
    STRIPE_PUBLISHABLE_KEY = "pk_test_demo"
    STRIPE_WEBHOOK_SECRET = "whsec_demo"
else:
    STRIPE_SECRET_KEY = get_secret("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = get_secret("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = get_secret("STRIPE_WEBHOOK_SECRET")

# OpenRouter Configuration
OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY")

# Application Configuration
SECRET_KEY = get_secret("SECRET_KEY", "your-secret-key-change-this")
ENVIRONMENT = get_secret("ENVIRONMENT", "development")
API_BASE_URL = get_secret("API_BASE_URL", "http://localhost:8000")

# Admin credentials
ADMIN_EMAIL = get_secret("ADMIN_EMAIL", "admin@mockexamify.com")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "admin123")

# Email Configuration
SMTP_HOST = get_secret("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(get_secret("SMTP_PORT", "587"))
SMTP_USER = get_secret("SMTP_USER")
SMTP_PASSWORD = get_secret("SMTP_PASSWORD")

# Credit Pack Configurations
CREDIT_PACKS = {
    "starter": {"credits": 5, "price": 999, "name": "Starter Pack"},  # $9.99
    "standard": {"credits": 15, "price": 2499, "name": "Standard Pack"},  # $24.99
    "premium": {"credits": 30, "price": 4499, "name": "Premium Pack"},  # $44.99
}

# OpenRouter Model Configuration
OPENROUTER_MODEL = "anthropic/claude-3-haiku"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# PDF Configuration
PDF_TEMPLATE_DIR = "templates"
PDF_OUTPUT_DIR = "temp_pdfs"

# Ensure required directories exist
os.makedirs(PDF_TEMPLATE_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

def validate_config():
    """Validate that all required configuration is present"""
    if DEMO_MODE:
        return True
        
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not globals().get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True

# Fallback configuration for Streamlit Cloud
try:
    validate_config()
except Exception as e:
    # If validation fails on Streamlit Cloud, enable demo mode
    if HAS_STREAMLIT:
        DEMO_MODE = True
        SUPABASE_URL = "demo"
        SUPABASE_KEY = "demo"
        STRIPE_SECRET_KEY = "demo"
        STRIPE_PUBLISHABLE_KEY = "demo"
        OPENROUTER_API_KEY = "demo"
        SECRET_KEY = "demo-secret-key"
        API_BASE_URL = "http://localhost:8000"