"""
Database operations and Supabase integration for MockExamify
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
DEMO_USERS = {
    "admin@mockexamify.com": {
        "id": "demo-admin-001",
        "email": "admin@mockexamify.com",
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
        "credits_balance": 10,
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

        try:
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

            result = (
                self.client.table("users")
                .insert(
                    {
                        "email": email,
                        "password_hash": hashed_password.decode("utf-8"),
                        "credits_balance": 5,  # Give new users 5 free credits
                        "role": "user",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

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
            logger.error(f"Error creating user: {e}")
            return None

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
            result = self.client.table("users").select("*").eq("email", email).execute()

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
            result = self.client.table("users").select("*").eq("email", email).execute()

            if not result.data:
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

            result = (
                self.client.table("attempts")
                .insert(
                    {
                        "user_id": user_id,
                        "mock_id": mock_id,
                        "user_answers": json.dumps(user_answers),
                        "score": score,
                        "correct_answers": correct_answers,
                        "total_questions": total_questions,
                        "time_taken": time_taken,
                        "detailed_results": (
                            json.dumps(detailed_results) if detailed_results else None
                        ),
                        "status": status,
                        "explanation_unlocked": False,
                        "credits_paid": credits_paid,
                        "questions_submitted": questions_submitted,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

            if result.data:
                attempt_data = result.data[0]
                return AttemptResponse(
                    id=attempt_data["id"],
                    user_id=attempt_data["user_id"],
                    mock_id=attempt_data["mock_id"],
                    user_answers=json.loads(attempt_data["user_answers"]),
                    score=attempt_data["score"],
                    total_questions=attempt_data["total_questions"],
                    correct_answers=attempt_data["correct_answers"],
                    explanation_unlocked=attempt_data["explanation_unlocked"],
                    timestamp=attempt_data["created_at"],
                )
        except Exception as e:
            logger.error(f"Error creating attempt: {e}")
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

            result = (
                self.client.table("attempts")
                .update(update_data)
                .eq("id", attempt_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating attempt progress: {e}")
            return False

    async def update_attempt_status(
        self, attempt_id: str, status: str, score: float = None, correct_answers: int = None
    ) -> bool:
        """Update attempt status and optionally score/correct_answers"""
        try:
            update_data = {"status": status}
            if score is not None:
                update_data["score"] = score
            if correct_answers is not None:
                update_data["correct_answers"] = correct_answers

            result = (
                self.client.table("attempts")
                .update(update_data)
                .eq("id", attempt_id)
                .execute()
            )
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
                return [a for a in DEMO_ATTEMPTS if a.get("user_id") == user_id and a.get("status") == "in_progress"]

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
            if self.demo_mode:
                # Return a fake UUID-like string
                fake_id = f"demo-support-{len(DEMO_ATTEMPTS) + 1}"
                return fake_id

            payload = {
                "user_id": ticket_data.get("user_id"),
                "user_email": ticket_data.get("user_email"),
                "subject": ticket_data.get("subject"),
                "message": ticket_data.get("description") or ticket_data.get("message"),
                "browser": ticket_data.get("browser"),
                "device": ticket_data.get("device"),
                "error_message": ticket_data.get("error_message"),
                "affected_exam": ticket_data.get("affected_exam"),
                # Store status in Title Case to match UI expectations (e.g., 'Open', 'Resolved')
                "status": ticket_data.get("status", "Open"),
                "priority": ticket_data.get("priority", "Medium"),
                "category": ticket_data.get("category", "Other"),
                "attachment_url": ticket_data.get("attachment_url"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            result = self.client.table("support_tickets").insert(payload).execute()
            if result.data and len(result.data) > 0:
                return result.data[0].get("id")
            return None
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return None

    async def get_all_support_tickets(self) -> List[Dict[str, Any]]:
        """Retrieve all support tickets (admins can view all)"""
        try:
            if self.demo_mode:
                # Build demo list from fallback tickets
                demo_list = []
                # Convert DEMO_ATTEMPTS or DEMO_MOCKS if necessary; keep empty for demo
                return demo_list

            result = (
                self.client.table("support_tickets")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting all support tickets: {e}")
            return []

    async def get_user_support_tickets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get support tickets submitted by a specific user"""
        try:
            if self.demo_mode:
                return []

            result = (
                self.client.table("support_tickets")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting user support tickets: {e}")
            return []

    async def update_support_ticket_status(self, ticket_id: str, new_status: str) -> bool:
        """Update status of a support ticket"""
        try:
            if self.demo_mode:
                return True

            result = (
                self.client.table("support_tickets")
                .update({"status": new_status})
                .eq("id", ticket_id)
                .execute()
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
            if self.demo_mode:
                return True

            # Prefer a dedicated responses table if present
            try:
                resp_result = (
                    self.client.table("support_ticket_responses")
                    .insert(
                        {
                            "ticket_id": ticket_id,
                            "responder": responder,
                            "message": message,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    .execute()
                )
                if resp_result.data:
                    return True
            except Exception:
                # Fallback: append to JSONB 'responses' array on support_tickets
                try:
                    # Get existing responses
                    ticket = (
                        self.client.table("support_tickets")
                        .select("responses")
                        .eq("id", ticket_id)
                        .execute()
                    )
                    existing = []
                    if ticket.data and len(ticket.data) > 0 and ticket.data[0].get("responses"):
                        existing = ticket.data[0]["responses"]

                    existing.append(
                        {
                            "responder": responder,
                            "message": message,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                    update = (
                        self.client.table("support_tickets")
                        .update({"responses": existing})
                        .eq("id", ticket_id)
                        .execute()
                    )
                    return len(update.data) > 0
                except Exception as e:
                    logger.error(f"Error appending response to support ticket: {e}")
                    return False

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
            if self.demo_mode:
                # Demo mode - just return a mock payment
                return {
                    "id": f"demo-payment-{len(DEMO_ATTEMPTS)}",
                    "user_id": user_id,
                    "stripe_session_id": stripe_session_id,
                    "amount": amount,
                    "credits_purchased": credits_purchased,
                    "status": status,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

            result = (
                self.client.table("payments")
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

            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return None

    async def get_payment_by_session_id(self, session_id: str) -> Optional[Dict]:
        """Get payment by Stripe session ID"""
        try:
            if self.demo_mode:
                # Demo mode - return None (no existing payments)
                return None

            result = (
                self.client.table("payments")
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

            result = (
                self.client.table("payments")
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
            if self.demo_mode:
                # Update demo user data
                for email, user_data in DEMO_USERS.items():
                    if user_data["id"] == user_id:
                        user_data["credits_balance"] += credits_to_add
                        return True
                return False

            # Get current user credits
            result = (
                self.client.table("users").select("credits_balance").eq("id", user_id).execute()
            )

            if not result.data:
                return False

            current_credits = result.data[0]["credits_balance"]
            new_balance = current_credits + credits_to_add

            # Update user credits
            update_result = (
                self.client.table("users")
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
            # Get current user credits from real database
            result = (
                self.client.table("users").select("credits_balance").eq("id", user_id).execute()
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

            # Update user credits
            update_result = (
                self.client.table("users")
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

            # Check if pool already exists
            result = (
                self.client.table("question_pools").select("*").eq("pool_name", pool_name).execute()
            )

            if result.data and len(result.data) > 0:
                # Pool exists - update it
                pool = result.data[0]
                update_result = (
                    self.client.table("question_pools")
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
                    self.client.table("question_pools")
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
            result = (
                client.table("pool_questions").select("*").eq("pool_id", pool_id).execute()
            )
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

            result = (
                self.client.table("upload_batches")
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
        """Add questions to pool with duplicate tracking and AI explanation generation"""
        try:
            if self.demo_mode:
                # Demo mode - just return success
                return True

            # Prepare questions for insertion
            questions_to_insert = []

            logger.info(f"Generating AI explanations for {len(questions)} questions...")

            for idx, q in enumerate(questions):
                # Generate AI explanation if not already present
                explanation = q.get("explanation")

                if not explanation or explanation == q.get("explanation_seed"):
                    try:
                        logger.info(f"Generating explanation for question {idx + 1}/{len(questions)}")
                        explanation = await generate_explanation(
                            question=q["question"],
                            choices=q["choices"],
                            correct_index=q["correct_index"],
                            scenario=q.get("scenario", ""),
                            explanation_seed=q.get("explanation_seed", "")
                        )
                    except Exception as e:
                        logger.error(f"Error generating explanation for question {idx + 1}: {e}")
                        # Use fallback explanation
                        correct_choice = q["choices"][q["correct_index"]]
                        explanation = f"The correct answer is: {correct_choice}"

                question_data = {
                    "pool_id": pool_id,
                    "question_text": q["question"],
                    "choices": json.dumps(q["choices"]),
                    "correct_answer": q["correct_index"],
                    "explanation": explanation,  # Store full AI-generated explanation
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

            logger.info(f"AI explanation generation complete for {len(questions)} questions")

            # Batch insert all questions
            if questions_to_insert:
                result = self.client.table("pool_questions").insert(questions_to_insert).execute()

                if result.data:
                    # Update batch statistics
                    await self._update_batch_stats(batch_id, len(questions), 0, len(questions))
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

            result = (
                self.client.table("upload_batches")
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


# Global database instance
db = DatabaseManager()
