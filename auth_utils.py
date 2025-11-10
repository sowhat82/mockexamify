"""
Authentication utilities for MockExamify
Handles sign-in, sign-up, and logout with proper error handling
"""

import asyncio
import json
import logging
import re
from typing import Dict, Optional, Tuple

import httpx
import streamlit as st

logger = logging.getLogger(__name__)


class AuthUtils:
    """Authentication utility class"""

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    async def sign_in(
        self, email: str, password: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Sign in user with email and password
        Returns: (success, user_data, error_message)
        """
        # ALWAYS use direct database - never use API for Streamlit Cloud
        try:
            from db import db

            logger.info(f"Sign in attempt for {email} using direct database")

            user = await db.authenticate_user(email, password)
            if user:
                logger.info(f"User {email} authenticated successfully")
                user_data = {
                    "token": f"db_token_{user.id}",
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "credits_balance": user.credits_balance,
                }
                return True, user_data, None
            else:
                logger.info(f"Authentication failed for {email}")
                return False, None, "Invalid email or password"

        except Exception as e:
            logger.error(f"Sign in error for {email}: {type(e).__name__}: {str(e)}", exc_info=True)
            return False, None, f"Login error: {str(e)}"

    async def sign_up(
        self, email: str, password: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Sign up new user
        Returns: (success, user_data, error_message)
        """
        # ALWAYS use direct database - never use API for Streamlit Cloud
        try:
            from db import db

            logger.info(f"Sign up attempt for {email} using direct database")

            # Check if user already exists
            existing_user = await db.get_user_by_email(email)
            if existing_user:
                logger.info(f"User {email} already exists")
                return False, None, "An account with this email already exists"

            # Create new user
            logger.info(f"Creating new user {email}")
            user = await db.create_user(email, password)
            if user:
                logger.info(f"User {email} created successfully")
                user_data = {
                    "token": f"db_token_{user.id}",
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "credits_balance": user.credits_balance,
                }
                return True, user_data, None
            else:
                logger.error(f"Failed to create user {email}")
                return False, None, "Failed to create account. Please try again."

        except Exception as e:
            logger.error(f"Sign up error for {email}: {type(e).__name__}: {str(e)}", exc_info=True)
            return False, None, f"Registration error: {str(e)}"

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
            user = st.session_state.get("current_user")
            # In demo mode, always refresh from DEMO_USERS to get latest UUID
            import config

            if config.DEMO_MODE and user and user.get("email") == "student@test.com":
                from db import DEMO_USERS

                demo_user = DEMO_USERS.get("student@test.com")
                if demo_user:
                    user = demo_user.copy()
                    st.session_state["current_user"] = user
            return user
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

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
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


def verify_admin_access() -> bool:
    """Verify if current user has admin access"""
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        return False

    current_user = st.session_state.get("current_user", {})
    return current_user.get("role") == "admin"


def require_admin_access():
    """Decorator/function to require admin access"""
    if not verify_admin_access():
        st.error("🚫 Admin access required")
        st.info("Please login with an admin account to access this page.")
        return False
    return True
