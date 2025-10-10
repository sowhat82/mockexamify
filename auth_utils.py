"""
Authentication utilities for MockExamify
Handles sign-in, sign-up, and logout with proper error handling
"""
import streamlit as st
import httpx
import json
import asyncio
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AuthUtils:
    """Authentication utility class"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
    
    async def sign_in(self, email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Sign in user with email and password
        Returns: (success, user_data, error_message)
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/auth/login",
                    json={"email": email, "password": password},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return True, data, None
                elif response.status_code == 401:
                    return False, None, "Invalid email or password"
                elif response.status_code == 404:
                    return False, None, "User not found"
                else:
                    return False, None, f"Login failed: {response.status_code}"
                    
        except httpx.TimeoutException:
            return False, None, "Request timed out. Please try again."
        except httpx.ConnectError:
            return False, None, "Unable to connect to server. Please check your connection."
        except Exception as e:
            logger.error(f"Sign in error: {e}")
            return False, None, f"An unexpected error occurred: {str(e)}"
    
    async def sign_up(self, email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Sign up new user
        Returns: (success, user_data, error_message)
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/auth/register",
                    json={"email": email, "password": password},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return True, data, None
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("detail", "Registration failed")
                    except:
                        error_msg = "Registration failed"
                    return False, None, error_msg
                elif response.status_code == 409:
                    return False, None, "An account with this email already exists"
                else:
                    return False, None, f"Registration failed: {response.status_code}"
                    
        except httpx.TimeoutException:
            return False, None, "Request timed out. Please try again."
        except httpx.ConnectError:
            return False, None, "Unable to connect to server. Please check your connection."
        except Exception as e:
            logger.error(f"Sign up error: {e}")
            return False, None, f"An unexpected error occurred: {str(e)}"
    
    def logout(self):
        """Clear authentication state"""
        if "authenticated" in st.session_state:
            del st.session_state.authenticated
        if "user_token" in st.session_state:
            del st.session_state.user_token
        if "current_user" in st.session_state:
            del st.session_state.current_user
        if "last_email" in st.session_state:
            del st.session_state.last_email
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return st.session_state.get("authenticated", False)
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current user data"""
        if self.is_authenticated():
            return st.session_state.get("current_user")
        return None
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        user = self.get_current_user()
        if user:
            return user.get("role") == "admin"
        return False

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    import re
    
    if not email:
        return False, "Email is required"
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Please enter a valid email address"
    
    return True, ""

def validate_password(password: str, confirm_password: str = None) -> Tuple[bool, str]:
    """Validate password strength and confirmation"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match"
    
    # Check for at least one letter and one number
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, ""

def run_async(coro):
    """Helper to run async functions in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)