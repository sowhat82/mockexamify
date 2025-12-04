"""
Database operations and Supabase integration for WantAMock
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import bcrypt

import config
from models import AttemptResponse, Mock, QuestionSchema, Ticket, User
from openrouter_utils import generate_explanation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client only if not in demo mode
if config.DEMO_MODE:
    logger.info("Running in demo mode - database mocked")
else:
    logger.info("Running in production mode - connecting to Supabase")

# Demo data for testing
# Persistent storage file for demo tickets
DEMO_TICKETS_FILE = ".demo_tickets.json"


def load_demo_tickets():
    """Load demo tickets from persistent storage"""
    try:
        with open(DEMO_TICKETS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_demo_tickets():
    """Save demo tickets to persistent storage"""
    try:
        with open(DEMO_TICKETS_FILE, "w") as f:
            json.dump(DEMO_TICKETS, f, indent=2)
        logger.info(f"Saved {len(DEMO_TICKETS)} demo tickets to {DEMO_TICKETS_FILE}")
    except Exception as e:
        logger.error(f"Error saving demo tickets: {e}")


# Load existing demo tickets on startup
DEMO_TICKETS = load_demo_tickets()
logger.info(f"Loaded {len(DEMO_TICKETS)} demo tickets from persistent storage")

DEMO_USERS = {
    "admin@mockexamify.com": {
        "id": "admin-demo-id",
        "email": "admin@mockexamify.com",
        "password_hash": bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        ),
        "credits_balance": 100,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    "admin@wantamock.com": {
        "id": "demo-admin-001",
        "email": "admin@wantamock.com",
        "password_hash": bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        ),
        "credits_balance": 100,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    "admin@demo.com": {
        "id": "demo-admin-002",
        "email": "admin@demo.com",
        "password_hash": bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        ),
        "credits_balance": 100,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    "user@demo.com": {
        "id": "demo-user-001",
        "email": "user@demo.com",
        "password_hash": bcrypt.hashpw("user123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        "credits_balance": 5,
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    "student@test.com": {
        "id": "student-demo-id",
        "email": "student@test.com",
        "password_hash": bcrypt.hashpw("password".encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        ),
        "credits_balance": 33,
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
}

DEMO_MOCKS = {
    "demo-mock-001": {
        "id": "demo-mock-001",
        "title": "Python Fundamentals Quiz",
        "description": "Test your basic Python knowledge",
        "questions": [
            {
                "question": "What is the output of print(2 ** 3)?",
                "choices": ["6", "8", "9", "16"],
                "correct_index": 1,
                "explanation_template": "2 ** 3 means 2 to the power of 3, which equals 8.",
            },
            {
                "question": "Which keyword is used to define a function in Python?",
                "choices": ["function", "def", "define", "func"],
                "correct_index": 1,
                "explanation_template": "The 'def' keyword is used to define functions in Python.",
            },
            {
                "question": "What data type is the result of: type([])?",
                "choices": ["dict", "list", "tuple", "set"],
                "correct_index": 1,
                "explanation_template": "[] creates an empty list, so type([]) returns <class 'list'>.",
            },
        ],
        "price_credits": 1,
        "explanation_enabled": True,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
}

DEMO_ATTEMPTS = []


class DatabaseManager:
    """Handles all database operations"""

    def __init__(self):
        self.demo_mode = config.DEMO_MODE
        # Always initialize Supabase client for question pools, even in demo mode
        if not self.demo_mode or (config.SUPABASE_URL and config.SUPABASE_URL != "demo"):
            from supabase import Client, create_client

            self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

            # Create admin client with service role key for bypassing RLS on admin operations
            if config.SUPABASE_SERVICE_KEY:
                self.admin_client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
                logger.info("Admin client initialized with service role key")
            else:
                self.admin_client = self.client  # Fall back to regular client
                logger.warning("No service role key found - admin operations may fail due to RLS")
        else:
            self.client = None
            self.admin_client = None

    # Demo mode methods
    async def _demo_authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Demo mode user authentication"""
        if email in DEMO_USERS:
            user_data = DEMO_USERS[email]
            if bcrypt.checkpw(password.encode("utf-8"), user_data["password_hash"].encode("utf-8")):
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    credits_balance=user_data["credits_balance"],
                    role=user_data["role"],
                    created_at=user_data["created_at"],
                )
        return None

    async def _demo_create_user(
        self, email: str, password: str, role: str = "user"
    ) -> Optional[User]:
        """Demo mode user creation"""
        if email in DEMO_USERS:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Create demo user
        user_id = f"demo-user-{len(DEMO_USERS) + 1:03d}"
        user_data = {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "credits_balance": 0,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        DEMO_USERS[email] = user_data

        return User(
            id=user_data["id"],
            email=user_data["email"],
            credits_balance=user_data["credits_balance"],
            role=user_data["role"],
            created_at=user_data["created_at"],
        )

    async def initialize_tables(self):
        """Initialize database tables if they don't exist"""
        if self.demo_mode:
            logger.info("Demo mode - skipping table initialization")
            return

        try:
            # Check if tables exist by trying to query them
            result = self.client.table("users").select("id").limit(1).execute()
            logger.info("Database tables already exist")
        except Exception as e:
            logger.info(f"Creating database tables: {e}")
            # Tables will be created via Supabase dashboard or SQL migration
            # For MVP, we assume tables are created manually
            pass

    # User Management
    async def create_user(self, email: str, password: str) -> Optional[User]:
        """Create a new user"""
        if self.demo_mode:
            return await self._demo_create_user(email, password)

        # Check if we have Supabase configuration
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
            error_msg = "Database configuration missing. Please contact support."
            logger.error(f"Cannot create user - missing Supabase config")
            raise RuntimeError(error_msg)

        try:
            import uuid

            import httpx

            # Hash password
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

            logger.info(f"Attempting to create user {email} in database")

            # Generate a UUID for the new user
            user_id = str(uuid.uuid4())

            # Use direct HTTP request to PostgREST API with service role key
            # This ensures RLS is properly bypassed
            url = f"{config.SUPABASE_URL}/rest/v1/users"
            headers = {
                "apikey": config.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            data = {
                "id": user_id,
                "email": email,
                "password_hash": hashed_password.decode("utf-8"),
                "credits_balance": 1,
                "role": "user",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(f"Making direct API call to create user")

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data, timeout=30.0)

                logger.info(f"API response status: {response.status_code}")

                if response.status_code in (200, 201):
                    user_data = (
                        response.json()[0] if isinstance(response.json(), list) else response.json()
                    )
                    logger.info(f"User created successfully: {user_data['id']}")
                    return User(
                        id=user_data["id"],
                        email=user_data["email"],
                        credits_balance=user_data["credits_balance"],
                        role=user_data["role"],
                        created_at=user_data["created_at"],
                    )
                else:
                    error_detail = response.text
                    logger.error(f"API error: {response.status_code} - {error_detail}")
                    raise RuntimeError(f"Database API error: {error_detail}")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating user {email}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(
                f"Error creating user {email}: {type(e).__name__}: {str(e)}", exc_info=True
            )
            raise

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        if self.demo_mode:
            if email in DEMO_USERS:
                user_data = DEMO_USERS[email]
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    credits_balance=user_data["credits_balance"],
                    role=user_data["role"],
                    created_at=user_data["created_at"],
                )
            return None

        try:
            # Use admin_client to bypass RLS for checking existing users
            result = self.admin_client.table("users").select("*").eq("email", email).execute()

            if result.data:
                user_data = result.data[0]
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    credits_balance=user_data["credits_balance"],
                    role=user_data["role"],
                    created_at=user_data["created_at"],
                )
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user login"""
        if self.demo_mode:
            # Demo mode authentication
            if email in DEMO_USERS:
                user_data = DEMO_USERS[email]
                if bcrypt.checkpw(
                    password.encode("utf-8"), user_data["password_hash"].encode("utf-8")
                ):
                    return User(
                        id=user_data["id"],
                        email=user_data["email"],
                        credits_balance=user_data["credits_balance"],
                        role=user_data["role"],
                        created_at=user_data["created_at"],
                    )
            return None

        try:
            # Use admin_client to bypass RLS for authentication
            result = self.admin_client.table("users").select("*").eq("email", email).execute()

            if not result.data:
                # Check if this is a demo user (hybrid mode)
                if email in DEMO_USERS:
                    user_data = DEMO_USERS[email]
                    if bcrypt.checkpw(
                        password.encode("utf-8"), user_data["password_hash"].encode("utf-8")
                    ):
                        return User(
                            id=user_data["id"],
                            email=user_data["email"],
                            credits_balance=user_data["credits_balance"],
                            role=user_data["role"],
                            created_at=user_data["created_at"],
                        )
                return None

            user_data = result.data[0]

            # Verify password
            if bcrypt.checkpw(password.encode("utf-8"), user_data["password_hash"].encode("utf-8")):
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    credits_balance=user_data["credits_balance"],
                    role=user_data["role"],
                    created_at=user_data["created_at"],
                )
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        # Check if this is a demo user first (hybrid mode)
        for email, user_data in DEMO_USERS.items():
            if user_data["id"] == user_id:
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    credits_balance=user_data["credits_balance"],
                    role=user_data["role"],
                    created_at=user_data["created_at"],
                )

        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()

            if result.data:
                user_data = result.data[0]
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    credits_balance=user_data["credits_balance"],
                    role=user_data["role"],
                    created_at=user_data["created_at"],
                )
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    async def get_all_users(self, limit: int = 100) -> List[User]:
        """Get all users from database (admin function)"""
        try:
            # Start with demo users
            all_users = []
            for email, user_data in DEMO_USERS.items():
                all_users.append(
                    User(
                        id=user_data["id"],
                        email=user_data["email"],
                        credits_balance=user_data["credits_balance"],
                        role=user_data["role"],
                        created_at=user_data["created_at"],
                    )
                )

            # Add real users from database (use admin_client to bypass RLS)
            if not self.demo_mode:
                result = self.admin_client.table("users").select("*").limit(limit).execute()
                if result.data:
                    for user_data in result.data:
                        all_users.append(
                            User(
                                id=user_data["id"],
                                email=user_data["email"],
                                credits_balance=user_data["credits_balance"],
                                role=user_data["role"],
                                created_at=user_data["created_at"],
                            )
                        )

            return all_users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    async def update_user_credits(self, user_id: str, credits_to_add: int) -> bool:
        """Add credits to user balance"""
        try:
            # First get current balance
            user = await self.get_user_by_id(user_id)
            if not user:
                return False

            new_balance = user.credits_balance + credits_to_add

            result = (
                self.client.table("users")
                .update({"credits_balance": new_balance})
                .eq("id", user_id)
                .execute()
            )

            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating user credits: {e}")
            return False

    async def deduct_user_credits(self, user_id: str, credits_to_deduct: int) -> bool:
        """Deduct credits from user balance"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user or user.credits_balance < credits_to_deduct:
                return False

            new_balance = user.credits_balance - credits_to_deduct

            result = (
                self.client.table("users")
                .update({"credits_balance": new_balance})
                .eq("id", user_id)
                .execute()
            )

            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deducting user credits: {e}")
            return False

    # Mock Management
    async def create_mock(self, mock_data: Dict[str, Any], creator_id: str) -> Optional[Mock]:
        """Create a new mock exam"""
        try:
            result = (
                self.client.table("mocks")
                .insert(
                    {
                        "title": mock_data["title"],
                        "description": mock_data["description"],
                        "questions_json": json.dumps(mock_data["questions"]),
                        "price_credits": mock_data["price_credits"],
                        "explanation_enabled": mock_data["explanation_enabled"],
                        "time_limit_minutes": mock_data.get("time_limit_minutes"),
                        "category": mock_data.get("category"),
                        "is_active": mock_data.get("is_active", True),
                        "creator_id": creator_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

            if result.data:
                mock_data = result.data[0]
                return Mock(
                    id=mock_data["id"],
                    title=mock_data["title"],
                    description=mock_data["description"],
                    questions=json.loads(mock_data["questions_json"]),
                    price_credits=mock_data["price_credits"],
                    explanation_enabled=mock_data["explanation_enabled"],
                    time_limit_minutes=mock_data["time_limit_minutes"],
                    category=mock_data["category"],
                    is_active=mock_data["is_active"],
                    created_at=mock_data["created_at"],
                )
        except Exception as e:
            logger.error(f"Error creating mock: {e}")
            return None

    async def get_all_mocks(self, active_only: bool = True) -> List[Mock]:
        """Get all mock exams"""
        if self.demo_mode:
            # Return demo mocks
            mocks = []
            for mock_data in DEMO_MOCKS.values():
                if not active_only or mock_data["is_active"]:
                    mocks.append(
                        Mock(
                            id=mock_data["id"],
                            title=mock_data["title"],
                            description=mock_data["description"],
                            questions=mock_data["questions"],
                            price_credits=mock_data["price_credits"],
                            explanation_enabled=mock_data["explanation_enabled"],
                            time_limit_minutes=30,
                            category="Demo",
                            is_active=mock_data["is_active"],
                            created_at=mock_data["created_at"],
                        )
                    )
            return mocks

        try:
            query = self.client.table("mocks").select("*")
            if active_only:
                query = query.eq("is_active", True)

            result = query.execute()

            mocks = []
            for mock_data in result.data:
                mocks.append(
                    Mock(
                        id=mock_data["id"],
                        title=mock_data["title"],
                        description=mock_data["description"],
                        questions=json.loads(mock_data["questions_json"]),
                        price_credits=mock_data["price_credits"],
                        explanation_enabled=mock_data["explanation_enabled"],
                        time_limit_minutes=mock_data["time_limit_minutes"],
                        category=mock_data["category"],
                        is_active=mock_data["is_active"],
                        created_at=mock_data["created_at"],
                    )
                )

            return mocks
        except Exception as e:
            logger.error(f"Error getting mocks: {e}")
            return []

    async def get_mock_by_id(self, mock_id: str) -> Optional[Mock]:
        """Get mock exam by ID"""
        if self.demo_mode:
            # Return demo mock if it exists
            if mock_id in DEMO_MOCKS:
                mock_data = DEMO_MOCKS[mock_id]
                return Mock(
                    id=mock_data["id"],
                    title=mock_data["title"],
                    description=mock_data["description"],
                    questions=mock_data["questions"],
                    price_credits=mock_data["price_credits"],
                    explanation_enabled=mock_data["explanation_enabled"],
                    time_limit_minutes=30,
                    category="Demo",
                    is_active=mock_data["is_active"],
                    created_at=mock_data["created_at"],
                )
            return None

        try:
            result = self.client.table("mocks").select("*").eq("id", mock_id).execute()

            if result.data:
                mock_data = result.data[0]
                return Mock(
                    id=mock_data["id"],
                    title=mock_data["title"],
                    description=mock_data["description"],
                    questions=json.loads(mock_data["questions_json"]),
                    price_credits=mock_data["price_credits"],
                    explanation_enabled=mock_data["explanation_enabled"],
                    time_limit_minutes=mock_data["time_limit_minutes"],
                    category=mock_data["category"],
                    is_active=mock_data["is_active"],
                    created_at=mock_data["created_at"],
                )
        except Exception as e:
            logger.error(f"Error getting mock: {e}")
            return None

    # Attempt Management
    async def create_attempt(
        self,
        user_id: str,
        mock_id: str,
        user_answers: Dict[int, int],
        score: float = None,
        correct_answers: int = None,
        total_questions: int = None,
        time_taken: int = None,
        detailed_results: List[Dict] = None,
        status: str = "completed",
        credits_paid: int = 0,
        questions_submitted: int = 0,
    ) -> Optional[AttemptResponse]:
        """Create a new attempt with enhanced parameters"""
        try:
            # Check if this is a demo user (even in production mode)
            is_demo_user = any(user_data["id"] == user_id for user_data in DEMO_USERS.values())

            if self.demo_mode or is_demo_user:
                # Demo mode - add to demo attempts
                attempt_id = f"demo-attempt-{len(DEMO_ATTEMPTS)}"
                attempt_data = {
                    "id": attempt_id,
                    "user_id": user_id,
                    "mock_id": mock_id,
                    "user_answers": user_answers,
                    "score": score or 0,
                    "correct_answers": correct_answers or 0,
                    "total_questions": total_questions or 0,
                    "time_taken": time_taken,
                    "detailed_results": detailed_results,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                DEMO_ATTEMPTS.append(attempt_data)

                return AttemptResponse(
                    id=attempt_id,
                    user_id=user_id,
                    mock_id=mock_id,
                    user_answers=list(user_answers.values()) if user_answers else [],
                    score=score or 0,
                    total_questions=total_questions or 0,
                    correct_answers=correct_answers or 0,
                    explanation_unlocked=False,
                    timestamp=attempt_data["timestamp"],
                )

            # Get mock to calculate score if not provided
            if score is None or correct_answers is None or total_questions is None:
                mock = await self.get_mock_by_id(mock_id)
                if not mock:
                    logger.error(f"Mock {mock_id} not found, cannot calculate scores")
                    return None

                if total_questions is None:
                    total_questions = len(mock.questions)

                if correct_answers is None:
                    correct_answers = 0
                    for q_index, user_answer in user_answers.items():
                        if (
                            q_index < len(mock.questions)
                            and user_answer == mock.questions[q_index]["correct_index"]
                        ):
                            correct_answers += 1

                if score is None:
                    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

            # Check if we have required configuration
            if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
                logger.error("Missing Supabase configuration for attempt creation")
                return None

            # Use direct HTTP request to PostgREST API to bypass RLS
            import httpx

            url = f"{config.SUPABASE_URL}/rest/v1/attempts"
            headers = {
                "apikey": config.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            data = {
                "user_id": user_id,
                "mock_id": mock_id,
                "user_answers": json.dumps(user_answers),
                "score": score,
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "time_taken": time_taken,
                "detailed_results": json.dumps(detailed_results) if detailed_results else None,
                "status": status,
                "explanation_unlocked": False,
                "credits_paid": credits_paid,
                "questions_submitted": questions_submitted,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(f"Creating attempt for user {user_id}, mock {mock_id}")

            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(url, headers=headers, json=data, timeout=30.0)

                if response.status_code in (200, 201):
                    attempt_data = (
                        response.json()[0] if isinstance(response.json(), list) else response.json()
                    )
                    logger.info(f"Attempt created successfully: {attempt_data['id']}")

                    # Parse user_answers - it's stored as JSON string of dict, need to convert to list
                    user_answers_data = (
                        json.loads(attempt_data["user_answers"])
                        if isinstance(attempt_data["user_answers"], str)
                        else attempt_data["user_answers"]
                    )
                    # Convert dict to list of values (for compatibility with AttemptResponse model)
                    user_answers_list = (
                        list(user_answers_data.values())
                        if isinstance(user_answers_data, dict)
                        else user_answers_data
                    )

                    return AttemptResponse(
                        id=attempt_data["id"],
                        user_id=attempt_data["user_id"],
                        mock_id=attempt_data["mock_id"],
                        user_answers=user_answers_list,
                        score=attempt_data["score"],
                        total_questions=attempt_data["total_questions"],
                        correct_answers=attempt_data["correct_answers"],
                        explanation_unlocked=attempt_data["explanation_unlocked"],
                        timestamp=attempt_data["created_at"],
                    )
                else:
                    error_detail = response.text
                    logger.error(
                        f"API error creating attempt: {response.status_code} - {error_detail}"
                    )
                    return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating attempt: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(
                f"Error creating attempt for user {user_id}: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return None

    async def get_user_attempts(self, user_id: str) -> List[AttemptResponse]:
        """Get all attempts for a user"""
        try:
            result = (
                self.client.table("attempts")
                .select("*")
                .eq("user_id", user_id)
                .order("timestamp", desc=True)
                .execute()
            )

            attempts = []
            for attempt_data in result.data:
                attempts.append(
                    AttemptResponse(
                        id=attempt_data["id"],
                        user_id=attempt_data["user_id"],
                        mock_id=attempt_data["mock_id"],
                        user_answers=json.loads(attempt_data["user_answers_json"]),
                        score=attempt_data["score"],
                        total_questions=attempt_data["total_questions"],
                        correct_answers=attempt_data["correct_answers"],
                        explanation_unlocked=attempt_data["explanation_unlocked"],
                        timestamp=attempt_data["timestamp"],
                    )
                )

            return attempts
        except Exception as e:
            logger.error(f"Error getting user attempts: {e}")
            return []

    async def get_attempt_by_id(self, attempt_id: str) -> Optional[AttemptResponse]:
        """Get attempt by ID"""
        try:
            result = self.client.table("attempts").select("*").eq("id", attempt_id).execute()

            if result.data:
                attempt_data = result.data[0]
                return AttemptResponse(
                    id=attempt_data["id"],
                    user_id=attempt_data["user_id"],
                    mock_id=attempt_data["mock_id"],
                    user_answers=json.loads(attempt_data["user_answers_json"]),
                    score=attempt_data["score"],
                    total_questions=attempt_data["total_questions"],
                    correct_answers=attempt_data["correct_answers"],
                    explanation_unlocked=attempt_data["explanation_unlocked"],
                    timestamp=attempt_data["timestamp"],
                )
        except Exception as e:
            logger.error(f"Error getting attempt: {e}")
            return None

    async def update_attempt_progress(
        self, attempt_id: str, questions_submitted: int, user_answers: Dict[int, int] = None
    ) -> bool:
        """Update the progress of an in-progress attempt"""
        try:
            update_data = {"questions_submitted": questions_submitted}
            if user_answers is not None:
                update_data["user_answers"] = json.dumps(user_answers)

            # Use admin_client to bypass RLS policies
            client = self.admin_client if self.admin_client else self.client
            result = client.table("attempts").update(update_data).eq("id", attempt_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating attempt progress: {e}")
            return False

    async def update_attempt_status(
        self, attempt_id: str, status: str, score: float = None, correct_answers: int = None
    ) -> bool:
        """Update attempt status and optionally score/correct_answers"""
        try:
            # Check if this is a demo attempt
            is_demo_attempt = attempt_id.startswith("demo-attempt-")

            if is_demo_attempt:
                # Update in-memory demo attempts
                for attempt in DEMO_ATTEMPTS:
                    if attempt.get("id") == attempt_id:
                        attempt["status"] = status
                        if score is not None:
                            attempt["score"] = score
                        if correct_answers is not None:
                            attempt["correct_answers"] = correct_answers
                        logger.info(f"Demo attempt {attempt_id} status updated to {status}")
                        return True
                logger.warning(f"Demo attempt {attempt_id} not found in DEMO_ATTEMPTS")
                return True  # Still return success for demo mode

            # Production mode: update in database
            update_data = {"status": status}
            if score is not None:
                update_data["score"] = score
            if correct_answers is not None:
                update_data["correct_answers"] = correct_answers

            # Use admin_client to bypass RLS policies
            client = self.admin_client if self.admin_client else self.client
            result = client.table("attempts").update(update_data).eq("id", attempt_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating attempt status: {e}")
            return False

    async def get_abandoned_attempts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all in-progress attempts for a user that should be considered abandoned"""
        try:
            # Check if this is a demo user - demo users don't have database attempts
            is_demo_user = any(user_data["id"] == user_id for user_data in DEMO_USERS.values())
            if is_demo_user:
                # Demo users use in-memory attempts
                return [
                    a
                    for a in DEMO_ATTEMPTS
                    if a.get("user_id") == user_id and a.get("status") == "in_progress"
                ]

            result = (
                self.client.table("attempts")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "in_progress")
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting abandoned attempts: {e}")
            return []

    async def process_abandoned_attempt_refund(self, attempt_data: Dict[str, Any]) -> bool:
        """Process pro-rata refund for an abandoned attempt"""
        try:
            attempt_id = attempt_data["id"]
            user_id = attempt_data["user_id"]
            credits_paid = attempt_data.get("credits_paid", 0)
            questions_submitted = attempt_data.get("questions_submitted", 0)
            total_questions = attempt_data.get("total_questions", 1)

            # Calculate pro-rata refund
            # Refund = credits_paid * (1 - submitted/total)
            refund_ratio = 1 - (questions_submitted / total_questions)
            refund_amount = credits_paid * refund_ratio

            logger.info(
                f"Processing refund for attempt {attempt_id}: "
                f"{questions_submitted}/{total_questions} submitted, "
                f"refunding {refund_amount:.2f} credits (paid {credits_paid})"
            )

            # Only process refund if amount is significant (> 0.01 credits)
            if refund_amount > 0.01:
                # Add credits back to user
                success = await self.add_credits_to_user(user_id, int(round(refund_amount)))
                if not success:
                    logger.error(f"Failed to refund credits for attempt {attempt_id}")
                    return False

            # Mark attempt as abandoned
            await self.update_attempt_status(attempt_id, "abandoned")

            logger.info(f"Successfully processed refund for attempt {attempt_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing abandoned attempt refund: {e}")
            return False

    async def process_exit_exam_refund(
        self,
        attempt_id: str,
        user_id: str,
        credits_paid: int,
        questions_submitted: int,
        total_questions: int,
    ) -> Dict[str, Any]:
        """Process block-of-10 refund when student exits exam voluntarily

        Refund logic: Refund credits for unattempted questions in blocks of 10, rounded down
        Cost per question × 10 questions per block × number of unattempted blocks
        Example: 49 questions (5 credits), 1 submitted → 48 unattempted → 4 blocks of 10
                 → refund: (5/49) × 10 × 4 = 4.08 credits → rounds to 4 credits
        """
        try:
            # Calculate unattempted questions
            unattempted_questions = total_questions - questions_submitted

            # Calculate blocks of 10 (round down)
            unattempted_blocks = unattempted_questions // 10

            # Calculate refund: cost per question × 10 questions per block × number of blocks
            # This correctly handles exams with question counts not divisible by 10
            if total_questions > 0 and unattempted_blocks > 0:
                cost_per_question = credits_paid / total_questions
                refund_amount = cost_per_question * 10 * unattempted_blocks
            else:
                refund_amount = 0

            logger.info(
                f"Exit exam refund for attempt {attempt_id}: "
                f"{questions_submitted}/{total_questions} submitted, "
                f"{unattempted_questions} unattempted, "
                f"{unattempted_blocks} blocks of 10, "
                f"refunding {refund_amount:.2f} credits (paid {credits_paid})"
            )

            # Process refund if amount is significant
            refund_processed = False
            if refund_amount > 0.01:
                success = await self.add_credits_to_user(user_id, int(round(refund_amount)))
                if success:
                    refund_processed = True
                    logger.info(f"Refunded {int(round(refund_amount))} credits to user {user_id}")
                else:
                    logger.error(f"Failed to refund credits for attempt {attempt_id}")

            # Mark attempt as abandoned
            await self.update_attempt_status(attempt_id, "abandoned")

            return {
                "success": True,
                "refund_processed": refund_processed,
                "refund_amount": int(round(refund_amount)),
                "unattempted_questions": unattempted_questions,
                "unattempted_blocks": unattempted_blocks,
            }

        except Exception as e:
            logger.error(f"Error processing exit exam refund: {e}")
            return {"success": False, "error": str(e)}

    # Support Tickets
    async def create_ticket(self, user_id: str, subject: str, message: str) -> Optional[Ticket]:
        """Create a support ticket"""
        try:
            result = (
                self.client.table("tickets")
                .insert(
                    {
                        "user_id": user_id,
                        "subject": subject,
                        "message": message,
                        "status": "open",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

            if result.data:
                ticket_data = result.data[0]
                return Ticket(
                    id=ticket_data["id"],
                    user_id=ticket_data["user_id"],
                    subject=ticket_data["subject"],
                    message=ticket_data["message"],
                    status=ticket_data["status"],
                    created_at=ticket_data["created_at"],
                )
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return None

    # Modern support ticket APIs (newer table 'support_tickets')
    async def create_support_ticket(self, ticket_data: Dict[str, Any]) -> Optional[str]:
        """Create a new support ticket using support_tickets table

        ticket_data should contain: user_id, subject, description/message, browser, device, error_message, affected_exam, priority, category
        Returns ticket id on success
        """
        try:
            # Check if this is a demo user (hybrid mode with demo user ID) or anonymous ticket
            user_id = ticket_data.get("user_id")
            is_demo_user = user_id in [user_data["id"] for user_data in DEMO_USERS.values()]
            is_anonymous_ticket = user_id == "00000000-0000-0000-0000-000000000000"

            if self.demo_mode or is_demo_user or is_anonymous_ticket:
                # Store demo ticket in memory
                fake_id = f"demo-support-{len(DEMO_TICKETS) + 1}"

                # Get user email from ticket_data first, then try DEMO_USERS lookup
                user_email = ticket_data.get("user_email") or "Unknown user"

                # If not provided in ticket_data, try looking up from DEMO_USERS
                if user_email == "Unknown user":
                    for demo_user_data in DEMO_USERS.values():
                        if demo_user_data["id"] == user_id:
                            user_email = demo_user_data["email"]
                            break

                description = ticket_data.get("description") or ticket_data.get("message")
                ticket = {
                    "id": fake_id,
                    "user_id": user_id,
                    "user_email": user_email,
                    "subject": ticket_data.get("subject"),
                    "message": description,
                    "description": description,
                    "status": "open",
                    "priority": "Medium",
                    "category": "General",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                DEMO_TICKETS.append(ticket)
                save_demo_tickets()  # Save to persistent storage
                logger.info(f"Demo user ticket created: {fake_id} from {user_email}")

                # Send email notification to admin
                try:
                    from email_utils import send_support_ticket_notification
                    send_support_ticket_notification(
                        ticket_id=fake_id,
                        user_email=user_email,
                        subject=ticket_data.get("subject", "No subject"),
                        category=ticket_data.get("category", "General"),
                        priority=ticket_data.get("priority", "Medium"),
                        description=description or "No description provided",
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send email notification: {email_error}")

                return fake_id

            # Tickets table has only: user_id, subject, message, status
            # Include user email in the message since there's no user_email column
            message_text = ticket_data.get("description") or ticket_data.get("message")
            user_email_from_ticket = ticket_data.get("user_email", "")

            # Prepend email to message if provided
            if user_email_from_ticket and user_email_from_ticket not in str(message_text):
                message_text = f"Email: {user_email_from_ticket}\n\n{message_text}"

            payload = {
                "user_id": user_id,
                "subject": ticket_data.get("subject"),
                "message": message_text,
                "status": ticket_data.get("status", "open"),
            }

            # Use admin_client to bypass RLS policies for ticket creation
            # This allows both anonymous and authenticated users to create tickets
            client = self.admin_client if self.admin_client else self.client
            result = client.table("tickets").insert(payload).execute()

            if result.data and len(result.data) > 0:
                ticket_id = result.data[0].get("id")

                # Send email notification to admin
                try:
                    from email_utils import send_support_ticket_notification
                    send_support_ticket_notification(
                        ticket_id=ticket_id,
                        user_email=user_email_from_ticket or "Unknown",
                        subject=ticket_data.get("subject", "No subject"),
                        category=ticket_data.get("category", "General"),
                        priority=ticket_data.get("priority", "Medium"),
                        description=message_text,
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send email notification: {email_error}")

                return ticket_id
            return None
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return None

    async def get_all_support_tickets(self) -> List[Dict[str, Any]]:
        """Retrieve all support tickets (admins can view all)"""
        try:
            if self.demo_mode:
                # Return demo tickets stored in memory
                return DEMO_TICKETS

            # Also return DEMO_TICKETS in hybrid mode (for admin viewing demo user tickets)
            # Use admin_client to bypass RLS and see ALL tickets (including anonymous password reset requests)
            result = (
                self.admin_client.table("tickets")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            all_tickets = result.data if result.data else []

            # Combine real tickets with demo tickets
            all_tickets.extend(DEMO_TICKETS)

            # Sort by created_at descending
            all_tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            return all_tickets
        except Exception as e:
            logger.error(f"Error getting all support tickets: {e}")
            return DEMO_TICKETS  # Return demo tickets on error

    async def get_user_support_tickets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get support tickets submitted by a specific user"""
        try:
            # Check if this is a demo user
            is_demo_user = user_id in [user_data["id"] for user_data in DEMO_USERS.values()]

            if self.demo_mode or is_demo_user:
                # Return demo tickets for this user only
                return [ticket for ticket in DEMO_TICKETS if ticket["user_id"] == user_id]

            # Use admin_client to ensure we can read tickets even if RLS is restrictive
            # This is safe because we're filtering by user_id
            client = self.admin_client if self.admin_client else self.client

            result = (
                client.table("tickets")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            user_tickets = result.data if result.data else []

            # Also include demo tickets for this user in hybrid mode
            demo_user_tickets = [ticket for ticket in DEMO_TICKETS if ticket["user_id"] == user_id]
            user_tickets.extend(demo_user_tickets)

            # Sort by created_at descending
            user_tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            return user_tickets
        except Exception as e:
            logger.error(
                f"Error getting user support tickets for {user_id}: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            # Return demo tickets for this user on error
            return [ticket for ticket in DEMO_TICKETS if ticket["user_id"] == user_id]

    async def update_support_ticket_status(self, ticket_id: str, new_status: str) -> bool:
        """Update status of a support ticket"""
        try:
            # Check if this is a demo ticket
            is_demo_ticket = ticket_id.startswith("demo-support-")

            if self.demo_mode or is_demo_ticket:
                # Update status in DEMO_TICKETS
                for ticket in DEMO_TICKETS:
                    if ticket["id"] == ticket_id:
                        ticket["status"] = new_status
                        save_demo_tickets()  # Save to persistent storage
                        logger.info(f"Updated demo ticket {ticket_id} status to {new_status}")
                        return True
                logger.warning(f"Demo ticket {ticket_id} not found")
                return False

            # Use admin_client to bypass RLS for ticket status updates
            client = self.admin_client if self.admin_client else self.client

            result = (
                client.table("tickets").update({"status": new_status}).eq("id", ticket_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating support ticket status: {e}")
            return False

    async def add_ticket_response(
        self, ticket_id: str, message: str, responder: str = "admin"
    ) -> bool:
        """Add a response to a support ticket.

        Tries to insert into support_ticket_responses; if not available, appends to a 'responses' JSONB field on support_tickets.
        """
        try:
            # Check if this is a demo ticket
            is_demo_ticket = ticket_id.startswith("demo-support-")

            if self.demo_mode or is_demo_ticket:
                # Add response to demo ticket
                for ticket in DEMO_TICKETS:
                    if ticket["id"] == ticket_id:
                        if "responses" not in ticket:
                            ticket["responses"] = []
                        ticket["responses"].append(
                            {
                                "responder": responder,
                                "message": message,
                                "created_at": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                        save_demo_tickets()  # Save to persistent storage
                        logger.info(f"Added response to demo ticket {ticket_id}")
                        return True
                logger.warning(f"Demo ticket {ticket_id} not found")
                return False

            # Check if we have Supabase configuration
            if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
                logger.error("Cannot add ticket response - missing Supabase config")
                return False

            # Use direct HTTP API to bypass RLS issues
            import httpx

            # First, get existing responses
            url = f"{config.SUPABASE_URL}/rest/v1/tickets"
            headers = {
                "apikey": config.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
            }

            logger.info(f"[add_ticket_response] Fetching ticket {ticket_id}")
            logger.info(f"[add_ticket_response] URL: {url}?id=eq.{ticket_id}")

            # Get the ticket
            async with httpx.AsyncClient() as http_client:
                # Fetch current responses
                try:
                    get_response = await http_client.get(
                        f"{url}?id=eq.{ticket_id}&select=responses", headers=headers, timeout=30.0
                    )
                    logger.info(f"[add_ticket_response] GET status: {get_response.status_code}")
                except Exception as fetch_error:
                    logger.error(
                        f"[add_ticket_response] HTTP GET error: {type(fetch_error).__name__}: {str(fetch_error)}"
                    )
                    return False

                if get_response.status_code != 200:
                    logger.error(
                        f"[add_ticket_response] Failed to fetch ticket: {get_response.status_code}"
                    )
                    logger.error(f"[add_ticket_response] Response body: {get_response.text}")
                    return False

                ticket_data = get_response.json()
                logger.info(f"[add_ticket_response] Ticket data: {ticket_data}")

                if not ticket_data or len(ticket_data) == 0:
                    logger.error(f"[add_ticket_response] Ticket {ticket_id} not found in response")
                    return False

                # Get existing responses or initialize empty array
                existing = ticket_data[0].get("responses") or []
                logger.info(f"[add_ticket_response] Existing responses count: {len(existing)}")

                # Add new response
                existing.append(
                    {
                        "responder": responder,
                        "message": message,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

                # Update ticket with new responses
                logger.info(
                    f"[add_ticket_response] Updating ticket with {len(existing)} total responses"
                )
                try:
                    patch_response = await http_client.patch(
                        f"{url}?id=eq.{ticket_id}",
                        headers=headers,
                        json={"responses": existing},
                        timeout=30.0,
                    )
                    logger.info(f"[add_ticket_response] PATCH status: {patch_response.status_code}")
                except Exception as patch_error:
                    logger.error(
                        f"[add_ticket_response] HTTP PATCH error: {type(patch_error).__name__}: {str(patch_error)}"
                    )
                    return False

                if patch_response.status_code in (200, 204):
                    logger.info(
                        f"[add_ticket_response] Successfully added response to ticket {ticket_id}"
                    )
                    return True
                else:
                    logger.error(
                        f"[add_ticket_response] Failed to update ticket: {patch_response.status_code}"
                    )
                    logger.error(f"[add_ticket_response] Response body: {patch_response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error adding ticket response: {e}")
            return False

    # Payment Methods
    async def create_payment(
        self,
        user_id: str,
        stripe_session_id: str,
        amount: float,
        credits_purchased: int,
        status: str = "pending",
    ) -> Optional[Dict]:
        """Create a payment record"""
        try:
            # Check if this is a demo user (even in production mode for testing)
            is_demo_user = user_id in ["student-demo-id", "admin-demo-id", "demo-user-id"]

            if self.demo_mode or is_demo_user:
                # Demo mode or demo user - just return a mock payment
                logger.info(f"Creating mock payment for demo user: {user_id}")
                return {
                    "id": f"demo-payment-{len(DEMO_ATTEMPTS)}",
                    "user_id": user_id,
                    "stripe_session_id": stripe_session_id,
                    "amount": amount,
                    "credits_purchased": credits_purchased,
                    "status": status,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

            # Use admin client to bypass RLS policies
            result = (
                self.admin_client.table("payments")
                .insert(
                    {
                        "user_id": user_id,
                        "stripe_session_id": stripe_session_id,
                        "amount": amount,
                        "credits_purchased": credits_purchased,
                        "status": status,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

            if not result.data:
                logger.error(f"Failed to record payment: Supabase response: {result}")
                if hasattr(result, "error") and result.error:
                    logger.error(f"Supabase error: {result.error}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating payment: {e}", exc_info=True)
            return None

    async def get_payment_by_session_id(self, session_id: str) -> Optional[Dict]:
        """Get payment by Stripe session ID"""
        try:
            # Check if this is a demo/test session
            is_demo_session = session_id.startswith("cs_test_") or self.demo_mode

            if is_demo_session:
                # Demo mode or test session - return None (no existing payments)
                logger.info(f"Demo/test session detected: {session_id}")
                return None

            # Use admin client to bypass RLS policies
            result = (
                self.admin_client.table("payments")
                .select("*")
                .eq("stripe_session_id", session_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting payment by session ID: {e}")
            return None

    async def update_payment_status(self, session_id: str, status: str) -> bool:
        """Update payment status"""
        try:
            if self.demo_mode:
                return True  # Demo mode - always succeed

            # Use admin client to bypass RLS policies
            result = (
                self.admin_client.table("payments")
                .update(
                    {
                        "status": status,
                        "completed_at": (
                            datetime.now(timezone.utc).isoformat()
                            if status == "completed"
                            else None
                        ),
                    }
                )
                .eq("stripe_session_id", session_id)
                .execute()
            )

            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
            return False

    async def add_credits_to_user(self, user_id: str, credits_to_add: int) -> bool:
        """Add credits to user account"""
        try:
            # Check if this is a demo user (even in production mode)
            for email, user_data in DEMO_USERS.items():
                if user_data["id"] == user_id:
                    user_data["credits_balance"] += credits_to_add
                    logger.info(
                        f"Demo user {email} credits added: +{credits_to_add}, new balance: {user_data['credits_balance']}"
                    )
                    return True

            # Production user - update in database
            # Get current user credits (use admin_client to bypass RLS)
            result = (
                self.admin_client.table("users")
                .select("credits_balance")
                .eq("id", user_id)
                .execute()
            )

            if not result.data:
                return False

            current_credits = result.data[0]["credits_balance"]
            new_balance = current_credits + credits_to_add

            # Update user credits (use admin_client to bypass RLS)
            update_result = (
                self.admin_client.table("users")
                .update({"credits_balance": new_balance})
                .eq("id", user_id)
                .execute()
            )

            return len(update_result.data) > 0
        except Exception as e:
            logger.error(f"Error adding credits to user: {e}")
            return False

    async def deduct_credits_from_user(self, user_id: str, credits_to_deduct: int) -> bool:
        """Deduct credits from user account"""
        try:
            logger.info(f"Attempting to deduct {credits_to_deduct} credits from user {user_id}")

            # Check if user is a demo user first (by user_id)
            for email, user_data in DEMO_USERS.items():
                if user_data["id"] == user_id:
                    logger.info(f"Found demo user: {email}")
                    if user_data["credits_balance"] >= credits_to_deduct:
                        user_data["credits_balance"] -= credits_to_deduct
                        logger.info(
                            f"Demo user credits deducted. New balance: {user_data['credits_balance']}"
                        )
                        return True
                    else:
                        logger.error(
                            f"Demo user insufficient credits: has {user_data['credits_balance']}, needs {credits_to_deduct}"
                        )
                        return False

            # Not a demo user - try real database
            # Get current user credits from real database (use admin_client to bypass RLS)
            result = (
                self.admin_client.table("users")
                .select("credits_balance")
                .eq("id", user_id)
                .execute()
            )

            if not result.data:
                logger.error(f"User {user_id} not found in database or DEMO_USERS")
                return False

            current_credits = result.data[0]["credits_balance"]
            logger.info(f"User {user_id} has {current_credits} credits, needs {credits_to_deduct}")

            if current_credits < credits_to_deduct:
                logger.error(
                    f"Insufficient credits: has {current_credits}, needs {credits_to_deduct}"
                )
                return False  # Insufficient credits

            new_balance = current_credits - credits_to_deduct

            # Update user credits (use admin_client to bypass RLS)
            update_result = (
                self.admin_client.table("users")
                .update({"credits_balance": new_balance})
                .eq("id", user_id)
                .execute()
            )

            success = len(update_result.data) > 0
            if success:
                logger.info(
                    f"Successfully deducted {credits_to_deduct} credits. New balance: {new_balance}"
                )
            else:
                logger.error(f"Failed to update credits in database")
            return success
        except Exception as e:
            logger.error(f"Error deducting credits from user: {e}")
            return False

    async def reset_user_password(self, user_id: str, new_password: str) -> bool:
        """Reset user password (admin function)"""
        try:
            # Hash the new password
            password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode(
                "utf-8"
            )

            # Check if this is a demo user
            for email, user_data in DEMO_USERS.items():
                if user_data["id"] == user_id:
                    user_data["password_hash"] = password_hash
                    logger.info(f"Reset password for demo user: {email}")
                    return True

            # Production user - update in database (use admin_client to bypass RLS)
            if not self.demo_mode:
                update_result = (
                    self.admin_client.table("users")
                    .update({"password_hash": password_hash})
                    .eq("id", user_id)
                    .execute()
                )

                success = len(update_result.data) > 0
                if success:
                    logger.info(f"Successfully reset password for user {user_id}")
                return success

            return False
        except Exception as e:
            logger.error(f"Error resetting password for user {user_id}: {e}")
            return False

    # Admin Mock Management Methods
    async def update_mock(self, mock_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a mock exam"""
        try:
            if self.demo_mode:
                # Update demo mock if it exists
                if mock_id in DEMO_MOCKS:
                    DEMO_MOCKS[mock_id].update(update_data)
                    return True
                return False

            result = self.client.table("mocks").update(update_data).eq("id", mock_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating mock: {e}")
            return False

    async def delete_mock(self, mock_id: str) -> bool:
        """Delete a mock exam"""
        try:
            if self.demo_mode:
                # Remove from demo mocks if it exists
                if mock_id in DEMO_MOCKS:
                    del DEMO_MOCKS[mock_id]
                    return True
                return False

            result = self.client.table("mocks").delete().eq("id", mock_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting mock: {e}")
            return False

    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics for admin dashboard"""
        try:
            if self.demo_mode:
                return {
                    "total_users": len(DEMO_USERS),
                    "active_users": len([u for u in DEMO_USERS.values() if u["role"] == "user"]),
                    "admin_users": len([u for u in DEMO_USERS.values() if u["role"] == "admin"]),
                    "total_attempts": len(DEMO_ATTEMPTS),
                    "total_mocks": len(DEMO_MOCKS),
                }

            # Get user stats
            users_result = self.client.table("users").select("role").execute()
            attempts_result = self.client.table("attempts").select("id").execute()
            mocks_result = self.client.table("mocks").select("id").execute()

            total_users = len(users_result.data)
            admin_users = len([u for u in users_result.data if u["role"] == "admin"])
            active_users = total_users - admin_users

            return {
                "total_users": total_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "total_attempts": len(attempts_result.data),
                "total_mocks": len(mocks_result.data),
            }
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "admin_users": 0,
                "total_attempts": 0,
                "total_mocks": 0,
            }

    async def get_recent_attempts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent exam attempts for admin dashboard"""
        try:
            if self.demo_mode:
                return DEMO_ATTEMPTS[-limit:] if DEMO_ATTEMPTS else []

            result = (
                self.client.table("attempts")
                .select("id, user_id, mock_id, score, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data
        except Exception as e:
            logger.error(f"Error getting recent attempts: {e}")
            return []

    async def get_mock_performance_stats(self, mock_id: str) -> Dict[str, Any]:
        """Get performance statistics for a specific mock"""
        try:
            if self.demo_mode:
                # Return demo stats
                mock_attempts = [a for a in DEMO_ATTEMPTS if a.get("mock_id") == mock_id]
                if not mock_attempts:
                    return {"attempts": 0, "avg_score": 0, "pass_rate": 0}

                scores = [a.get("score", 0) for a in mock_attempts]
                avg_score = sum(scores) / len(scores)
                pass_rate = len([s for s in scores if s >= 70]) / len(scores) * 100

                return {
                    "attempts": len(mock_attempts),
                    "avg_score": avg_score,
                    "pass_rate": pass_rate,
                }

            result = self.client.table("attempts").select("score").eq("mock_id", mock_id).execute()

            if not result.data:
                return {"attempts": 0, "avg_score": 0, "pass_rate": 0}

            scores = [attempt["score"] for attempt in result.data]
            avg_score = sum(scores) / len(scores)
            pass_rate = len([s for s in scores if s >= 70]) / len(scores) * 100

            return {"attempts": len(scores), "avg_score": avg_score, "pass_rate": pass_rate}
        except Exception as e:
            logger.error(f"Error getting mock performance stats: {e}")
            return {"attempts": 0, "avg_score": 0, "pass_rate": 0}

    async def get_all_question_pools(self) -> List[Dict[str, Any]]:
        """Get all question pools"""
        try:
            # Question pools always use real database (hybrid mode)
            # Even in demo mode, we want to access real question pools
            # Use admin client to bypass RLS policies
            client = self.admin_client if self.admin_client else self.client
            result = client.table("question_pools").select("*").execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting question pools: {e}")
            return []

    async def create_or_update_question_pool(
        self, pool_name: str, category: str, description: str, created_by: str
    ) -> Optional[Dict[str, Any]]:
        """Create new question pool or update existing one by name"""
        try:
            if self.demo_mode:
                # Demo mode - return mock pool
                return {
                    "id": "demo-pool-001",
                    "pool_name": pool_name,
                    "category": category,
                    "description": description,
                    "total_questions": 0,
                    "unique_questions": 0,
                    "created_by": created_by,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "is_active": True,
                }

            # Use admin_client to bypass RLS policies for question pool operations
            client = self.admin_client if self.admin_client else self.client

            # Check if pool already exists
            result = client.table("question_pools").select("*").eq("pool_name", pool_name).execute()

            if result.data and len(result.data) > 0:
                # Pool exists - update it
                pool = result.data[0]
                update_result = (
                    client.table("question_pools")
                    .update(
                        {
                            "category": category,
                            "description": description,
                            "last_updated": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    .eq("id", pool["id"])
                    .execute()
                )

                return update_result.data[0] if update_result.data else None
            else:
                # Pool doesn't exist - create new
                insert_result = (
                    client.table("question_pools")
                    .insert(
                        {
                            "pool_name": pool_name,
                            "category": category,
                            "description": description,
                            "created_by": created_by,
                            "total_questions": 0,
                            "unique_questions": 0,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "is_active": True,
                        }
                    )
                    .execute()
                )

                return insert_result.data[0] if insert_result.data else None

        except Exception as e:
            logger.error(f"Error creating/updating question pool: {e}")
            return None

    async def get_pool_questions(self, pool_id: str) -> List[Dict[str, Any]]:
        """Get all questions from a question pool"""
        try:
            # Question pools always use real database (hybrid mode)
            # Even in demo mode, we want to access real question pools
            # Use admin client to bypass RLS policies
            client = self.admin_client if self.admin_client else self.client
            result = client.table("pool_questions").select("*").eq("pool_id", pool_id).execute()
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting pool questions: {e}")
            return []

    async def get_random_pool_questions(self, pool_id: str, count: int) -> List[Dict[str, Any]]:
        """Get N random questions from a pool (excluding duplicates)"""
        try:
            # Question pools always use real database (hybrid mode)
            # Use admin client to bypass RLS policies
            client = self.admin_client if self.admin_client else self.client
            result = (
                client.table("pool_questions")
                .select("*")
                .eq("pool_id", pool_id)
                .eq("is_duplicate", False)
                .execute()
            )

            if not result.data:
                return []

            # Randomly sample N questions
            import random

            available_questions = result.data

            if len(available_questions) <= count:
                selected = available_questions
            else:
                selected = random.sample(available_questions, count)

            # Convert to standard format for exam
            formatted_questions = []
            for q in selected:
                formatted_questions.append(
                    {
                        "id": q["id"],  # Include question ID for reporting
                        "pool_id": q["pool_id"],  # Include pool ID for replacements
                        "question": q["question_text"],
                        "choices": (
                            json.loads(q["choices"])
                            if isinstance(q["choices"], str)
                            else q["choices"]
                        ),
                        "correct_index": q["correct_answer"],
                        "explanation_template": q.get("explanation", ""),
                    }
                )

            return formatted_questions

        except Exception as e:
            logger.error(f"Error getting random pool questions: {e}")
            return []

    async def create_upload_batch(
        self, pool_id: str, filename: str, total_questions: int, uploaded_by: str
    ) -> Optional[str]:
        """Create upload batch record and return batch_id"""
        try:
            if self.demo_mode:
                # Demo mode - return mock batch id
                return "demo-batch-001"

            # Use admin_client to bypass RLS policies for upload batch operations
            client = self.admin_client if self.admin_client else self.client

            result = (
                client.table("upload_batches")
                .insert(
                    {
                        "pool_id": pool_id,
                        "filename": filename,
                        "questions_count": total_questions,
                        "duplicates_found": 0,
                        "unique_added": 0,
                        "upload_status": "processing",
                        "uploaded_by": uploaded_by,
                        "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            return None

        except Exception as e:
            logger.error(f"Error creating upload batch: {e}")
            return None

    async def add_questions_to_pool(
        self, pool_id: str, questions: List[Dict[str, Any]], source_file: str, batch_id: str
    ) -> bool:
        """Add questions to pool immediately with document explanations or placeholders.
        AI explanations are generated in background separately."""
        try:
            if self.demo_mode:
                # Demo mode - just return success
                return True

            # Prepare questions for insertion
            questions_to_insert = []
            questions_with_doc_explanations = 0
            questions_needing_ai = 0

            logger.info(
                f"Preparing {len(questions)} questions for upload (skipping AI generation for speed)..."
            )

            for idx, q in enumerate(questions):
                # Use explanation from document if available, otherwise placeholder
                explanation = q.get("explanation", "").strip()

                if explanation and len(explanation) > 10:  # Valid explanation from document
                    questions_with_doc_explanations += 1
                else:
                    # Use simple placeholder - AI will generate later
                    correct_choice = q["choices"][q["correct_index"]]
                    explanation = f"The correct answer is: {correct_choice}"
                    questions_needing_ai += 1

                question_data = {
                    "pool_id": pool_id,
                    "question_text": q["question"],
                    "choices": json.dumps(q["choices"]),
                    "correct_answer": q["correct_index"],
                    "explanation": explanation,
                    "source_file": source_file,
                    "upload_batch_id": batch_id,
                    "is_duplicate": q.get("is_duplicate", False),
                    "similarity_score": q.get("similarity_score"),
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

                # Add scenario if present
                if q.get("scenario"):
                    question_data["topic_tags"] = json.dumps([{"scenario": q["scenario"]}])

                questions_to_insert.append(question_data)

            logger.info(
                f"Questions prepared: {questions_with_doc_explanations} with document explanations, "
                f"{questions_needing_ai} will use AI generation (background)"
            )

            # Batch insert all questions immediately
            if questions_to_insert:
                # Use admin_client to bypass RLS policies for pool question uploads
                result = (
                    self.admin_client.table("pool_questions").insert(questions_to_insert).execute()
                )

                if result.data:
                    # Update batch statistics
                    await self._update_batch_stats(batch_id, len(questions), 0, len(questions))
                    logger.info(f"✅ Successfully inserted {len(questions)} questions to database")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error adding questions to pool: {e}")
            return False

    async def _update_batch_stats(
        self, batch_id: str, questions_count: int, duplicates_found: int, unique_added: int
    ) -> bool:
        """Update upload batch statistics"""
        try:
            if self.demo_mode:
                return True

            # Use admin_client to bypass RLS for batch updates
            result = (
                self.admin_client.table("upload_batches")
                .update(
                    {
                        "questions_count": questions_count,
                        "duplicates_found": duplicates_found,
                        "unique_added": unique_added,
                        "upload_status": "completed",
                    }
                )
                .eq("id", batch_id)
                .execute()
            )

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error updating batch stats: {e}")
            return False

    async def report_question(
        self, question_id: str, user_id: Optional[str] = None, mock_id: Optional[str] = None, reason: Optional[str] = None
    ) -> bool:
        """Report a question as corrupted or impossible to answer"""
        try:
            logger.info(f"[REPORT] Starting report - question_id: {question_id}, user_id: {user_id}, mock_id: {mock_id}")

            if self.demo_mode:
                logger.info(f"Demo mode: Would report question {question_id}")
                return True

            report_data = {
                "question_id": question_id,
                "reported_by": user_id,
                "mock_id": mock_id,
                "report_reason": reason,
                "status": "pending"
            }

            logger.info(f"[REPORT] Report data: {report_data}")

            # Use admin client if user_id is None (demo users) to bypass RLS policies
            client = self.admin_client if user_id is None else self.client
            result = client.table("reported_questions").insert(report_data).execute()

            logger.info(f"[REPORT] Insert result: {result}")

            if result.data:
                logger.info(f"Question {question_id} reported successfully")
                return True

            logger.error(f"[REPORT] No data returned from insert")
            return False

        except Exception as e:
            logger.error(f"Error reporting question: {e}", exc_info=True)
            return False

    async def get_reported_questions(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get reported questions (admin only)"""
        try:
            if self.demo_mode:
                return []

            # Use admin_client to bypass RLS and see all reports
            query = self.admin_client.from_("reported_questions_with_details").select("*")

            if status:
                query = query.eq("status", status)

            result = query.order("reported_at", desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting reported questions: {e}")
            return []

    async def get_pending_reports_count(self) -> int:
        """Get count of pending reported questions (admin only)"""
        try:
            if self.demo_mode:
                return 0

            # Use admin_client to bypass RLS
            result = (
                self.admin_client.table("reported_questions")
                .select("id", count="exact")
                .eq("status", "pending")
                .execute()
            )

            return result.count if hasattr(result, 'count') else 0

        except Exception as e:
            logger.error(f"Error getting pending reports count: {e}")
            return 0

    async def update_report_status(
        self, report_id: str, status: str, admin_notes: Optional[str] = None, admin_id: Optional[str] = None
    ) -> bool:
        """Update the status of a reported question (admin only)"""
        try:
            if self.demo_mode:
                return True

            update_data = {
                "status": status,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }

            if admin_notes:
                update_data["admin_notes"] = admin_notes

            if admin_id:
                update_data["reviewed_by"] = admin_id

            # Use admin_client to bypass RLS
            result = (
                self.admin_client.table("reported_questions")
                .update(update_data)
                .eq("id", report_id)
                .execute()
            )

            return len(result.data) > 0 if result.data else False

        except Exception as e:
            logger.error(f"Error updating report status: {e}")
            return False


# Global database instance
db = DatabaseManager()
