"""
MockExamify Test Configuration
Pytest fixtures and test setup for comprehensive testing
"""

import asyncio
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

# Import our modules
import config
from auth_utils import AuthUtils
from db import DatabaseManager
from models import Attempt, Mock, QuestionSchema, User


class TestConfig:
    """Test-specific configuration"""

    TEST_DATABASE_URL = "sqlite:///test_mockexamify.db"
    TEST_API_BASE_URL = "http://localhost:8501"
    TEST_DEMO_MODE = True
    TEST_ENVIRONMENT = "testing"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_streamlit_state():
    """Mock Streamlit session state for all tests"""
    with patch.dict("streamlit.session_state", {}, clear=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.page = "login"
        st.session_state.token = None
        yield st.session_state


@pytest.fixture
def test_config():
    """Provide test configuration"""
    return TestConfig()


@pytest.fixture
def mock_auth_utils():
    """Mock AuthUtils for testing"""
    auth = MagicMock(spec=AuthUtils)
    auth.is_authenticated.return_value = False
    auth.get_current_user.return_value = None
    auth.is_admin.return_value = False
    auth.sign_in = AsyncMock(return_value=(False, None, "Invalid credentials"))
    auth.sign_up = AsyncMock(return_value=(False, None, "Registration failed"))
    auth.logout = MagicMock()
    return auth


@pytest.fixture
def mock_authenticated_auth():
    """Mock authenticated AuthUtils"""
    auth = MagicMock(spec=AuthUtils)
    auth.is_authenticated.return_value = True
    auth.get_current_user.return_value = {
        "id": "test-user-1",
        "email": "test@example.com",
        "role": "user",
        "credits_balance": 10,
    }
    auth.is_admin.return_value = False
    return auth


@pytest.fixture
def mock_admin_auth():
    """Mock admin AuthUtils"""
    auth = MagicMock(spec=AuthUtils)
    auth.is_authenticated.return_value = True
    auth.get_current_user.return_value = {
        "id": "admin-1",
        "email": "admin@mockexamify.com",
        "role": "admin",
        "credits_balance": 0,  # Admins don't need credits
    }
    auth.is_admin.return_value = True
    return auth


@pytest.fixture
def mock_db():
    """Mock database manager"""
    db = Mock(spec=DatabaseManager)

    # Mock demo data
    demo_user = User(
        id="test-user-1",
        email="test@example.com",
        password_hash="hashed_password",
        credits_balance=10,
        role="user",
        created_at="2024-01-01T00:00:00Z",
    )

    demo_mock = Mock(
        id=1,
        title="Test Category Mock",
        description="Test exam category",
        category="Test Category",
        time_limit=60,
        price=5.0,
        total_questions=10,
        difficulty_level="Medium",
        question_types=["Multiple Choice"],
        created_by="admin",
    )

    # Setup async mock methods
    db.get_user_by_email = AsyncMock(return_value=demo_user)
    db.get_user_by_id = AsyncMock(return_value=demo_user)
    db.authenticate_user = AsyncMock(return_value=demo_user)
    db.create_user = AsyncMock(return_value=demo_user)
    db.get_exam_categories = AsyncMock(return_value=[demo_mock])
    db.get_questions_by_category = AsyncMock(return_value=[])
    db.get_papers_by_category = AsyncMock(return_value=[])
    db.create_attempt = AsyncMock(return_value=None)
    db.add_credits = AsyncMock(return_value=True)

    return db


@pytest.fixture
def test_user_data():
    """Standard test user data"""
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "id": "test-user-1",
        "role": "user",
        "credits_balance": 10,
    }


@pytest.fixture
def test_admin_data():
    """Standard test admin data"""
    return {
        "email": "admin@mockexamify.com",
        "password": "admin123",
        "id": "admin-1",
        "role": "admin",
        "credits_balance": 0,  # Admins don't need credits
    }


@pytest.fixture
def sample_questions():
    """Sample question data for testing"""
    return [
        {
            "id": 1,
            "question": "What is the capital of France?",
            "choices": ["London", "Berlin", "Paris", "Madrid"],
            "correct_index": 2,
            "explanation": "Paris is the capital and largest city of France.",
            "category": "Geography",
            "difficulty": "easy",
        },
        {
            "id": 2,
            "question": "Which programming language is used for this app?",
            "choices": ["Java", "Python", "C++", "JavaScript"],
            "correct_index": 1,
            "explanation": "Python is used with Streamlit framework.",
            "category": "Programming",
            "difficulty": "medium",
        },
    ]


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for database testing"""
    client = Mock()

    # Mock table operations
    table_mock = Mock()
    table_mock.select.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.delete.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.execute.return_value = Mock(data=[], error=None)

    client.table.return_value = table_mock
    return client


@pytest.fixture
def app_test():
    """Streamlit app testing fixture"""
    return AppTest.from_file("streamlit_app.py")


class TestHelpers:
    """Helper functions for tests"""

    @staticmethod
    def mock_streamlit_components():
        """Mock common Streamlit components"""
        with patch("streamlit.title") as mock_title, patch(
            "streamlit.header"
        ) as mock_header, patch("streamlit.subheader") as mock_subheader, patch(
            "streamlit.text"
        ) as mock_text, patch(
            "streamlit.markdown"
        ) as mock_markdown, patch(
            "streamlit.error"
        ) as mock_error, patch(
            "streamlit.success"
        ) as mock_success, patch(
            "streamlit.info"
        ) as mock_info, patch(
            "streamlit.warning"
        ) as mock_warning:

            yield {
                "title": mock_title,
                "header": mock_header,
                "subheader": mock_subheader,
                "text": mock_text,
                "markdown": mock_markdown,
                "error": mock_error,
                "success": mock_success,
                "info": mock_info,
                "warning": mock_warning,
            }

    @staticmethod
    def create_mock_response(data=None, error=None):
        """Create mock API response"""
        response = Mock()
        response.data = data or []
        response.error = error
        return response

    @staticmethod
    def assert_no_errors_displayed(mock_components):
        """Assert no error messages were displayed"""
        mock_components["error"].assert_not_called()

    @staticmethod
    def assert_success_message(mock_components, message=None):
        """Assert success message was displayed"""
        mock_components["success"].assert_called()
        if message:
            args = mock_components["success"].call_args[0]
            assert message in args[0]


@pytest.fixture
def test_helpers():
    """Provide test helper functions"""
    return TestHelpers()


# Test markers
pytest_markers = [
    "unit: Unit tests for individual functions/methods",
    "integration: Integration tests for component interaction",
    "regression: Regression tests for critical functionality",
    "auth: Authentication and authorization tests",
    "db: Database operation tests",
    "ui: User interface tests",
    "admin: Admin functionality tests",
    "slow: Tests that take longer to run",
]


# Register custom markers
def pytest_configure(config):
    """Register custom pytest markers"""
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test"""
    yield
    # Cleanup any temporary files, reset global state, etc.
    pass
