"""
Configuration management for MockExamify
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if we're in demo mode
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

# Supabase Configuration
if DEMO_MODE:
    SUPABASE_URL = "demo"
    SUPABASE_KEY = "demo"
else:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Stripe Configuration
if DEMO_MODE:
    STRIPE_SECRET_KEY = "sk_test_demo"
    STRIPE_PUBLISHABLE_KEY = "pk_test_demo"
    STRIPE_WEBHOOK_SECRET = "whsec_demo"
else:
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Application Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

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