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

    # Use override=True to ensure .env file values take precedence over system env vars
    load_dotenv(override=True)
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
            if hasattr(st, "secrets") and key in st.secrets:
                return st.secrets[key]
        except:
            pass

    return default


# Demo mode: true only if running on localhost and .env sets DEMO_MODE=true
import socket

hostname = socket.gethostname()
local_ips = ["127.0.0.1", "localhost"]
is_localhost = any(host in get_secret("API_BASE_URL", "").lower() for host in local_ips)
DEMO_MODE = get_secret("DEMO_MODE", "false").lower() == "true" and is_localhost

# Supabase Configuration - always load for hybrid mode (question pools)
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = get_secret(
    "SUPABASE_SERVICE_KEY", ""
)  # Service role key for admin operations

# Stripe Configuration - always read from secrets
STRIPE_SECRET_KEY = get_secret("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = get_secret("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = get_secret("STRIPE_WEBHOOK_SECRET")

# HitPay Configuration (PayNow) - Feature flagged, disabled by default
ENABLE_HITPAY = get_secret("ENABLE_HITPAY", "false").lower() == "true"
HITPAY_API_KEY = get_secret("HITPAY_API_KEY", "") if ENABLE_HITPAY else ""
HITPAY_SALT = get_secret("HITPAY_SALT", "") if ENABLE_HITPAY else ""

# OpenRouter Configuration
OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY")

# Application Configuration
SECRET_KEY = get_secret("SECRET_KEY", "your-secret-key-change-this")
ENVIRONMENT = get_secret("ENVIRONMENT", "development")
import sys
def get_dynamic_api_base_url():
    # If running on localhost, try to detect the port Streamlit is running on
    # Otherwise, use the production URL from secrets or .env
    import socket
    import os
    # Try to get port from Streamlit environment
    port = os.environ.get("STREAMLIT_SERVER_PORT")
    if not port:
        # Try to get from sys.argv (e.g., --server.port 8501)
        for i, arg in enumerate(sys.argv):
            if arg in ("--server.port", "--port") and i + 1 < len(sys.argv):
                port = sys.argv[i + 1]
                break
    if not port:
        port = "8501"  # Default Streamlit port
    # If running on localhost, use detected port
    if "localhost" in socket.gethostname().lower() or os.environ.get("LOCAL_DEV", "false").lower() == "true":
        return f"http://localhost:{port}"
    # Otherwise, use the configured API_BASE_URL
    return get_secret("API_BASE_URL", "https://mockexamify.streamlit.app")

API_BASE_URL = get_dynamic_api_base_url()

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
        "SECRET_KEY",
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
