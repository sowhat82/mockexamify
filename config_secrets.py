"""
Secrets management for MockExamify deployment
This file shows how to access secrets in different environments
"""

import os
import streamlit as st

def get_secret(key: str, default: str = None) -> str:
    """
    Get secret from environment variables or Streamlit secrets
    Priority: Environment variables > Streamlit secrets > default
    """
    # First try environment variables (for local development)
    value = os.getenv(key)
    if value:
        return value
    
    # Then try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    
    # Return default if provided
    if default:
        return default
    
    # Raise error if no value found
    raise ValueError(f"Secret '{key}' not found in environment or Streamlit secrets")

# Example usage:
# SUPABASE_URL = get_secret("SUPABASE_URL")
# STRIPE_SECRET_KEY = get_secret("STRIPE_SECRET_KEY")