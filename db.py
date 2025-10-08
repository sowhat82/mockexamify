"""
Database operations and Supabase integration for MockExamify
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import bcrypt
from models import User, Mock, AttemptResponse, Ticket, QuestionSchema
import config

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
    "admin@demo.com": {
        "id": "demo-admin-001",
        "email": "admin@demo.com",
        "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "credits_balance": 100,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    "user@demo.com": {
        "id": "demo-user-001", 
        "email": "user@demo.com",
        "password_hash": bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "credits_balance": 5,
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
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
                "explanation_template": "2 ** 3 means 2 to the power of 3, which equals 8."
            },
            {
                "question": "Which keyword is used to define a function in Python?",
                "choices": ["function", "def", "define", "func"],
                "correct_index": 1,
                "explanation_template": "The 'def' keyword is used to define functions in Python."
            },
            {
                "question": "What data type is the result of: type([])?",
                "choices": ["dict", "list", "tuple", "set"],
                "correct_index": 1,
                "explanation_template": "[] creates an empty list, so type([]) returns <class 'list'>."
            }
        ],
        "price_credits": 1,
        "explanation_enabled": True,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
}

DEMO_ATTEMPTS = []


class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self):
        self.demo_mode = config.DEMO_MODE
        if self.demo_mode:
            self.client = None
        else:
            from supabase import create_client, Client
            self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    async def initialize_tables(self):
        """Initialize database tables if they don't exist"""
        if self.demo_mode:
            logger.info("Demo mode - skipping table initialization")
            return
            
        try:
            # Check if tables exist by trying to query them
            result = self.client.table('users').select('id').limit(1).execute()
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
            # In demo mode, don't create new users
            logger.info(f"Demo mode - cannot create user {email}")
            return None
            
        try:
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            result = self.client.table('users').insert({
                'email': email,
                'password_hash': hashed_password.decode('utf-8'),
                'credits_balance': 0,
                'role': 'user',
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if result.data:
                user_data = result.data[0]
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    credits_balance=user_data['credits_balance'],
                    role=user_data['role'],
                    created_at=user_data['created_at']
                )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user login"""
        if self.demo_mode:
            # Demo mode authentication
            if email in DEMO_USERS:
                user_data = DEMO_USERS[email]
                if bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                    return User(
                        id=user_data['id'],
                        email=user_data['email'],
                        credits_balance=user_data['credits_balance'],
                        role=user_data['role'],
                        created_at=user_data['created_at']
                    )
            return None
            
        try:
            result = self.client.table('users').select('*').eq('email', email).execute()
            
            if not result.data:
                return None
            
            user_data = result.data[0]
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    credits_balance=user_data['credits_balance'],
                    role=user_data['role'],
                    created_at=user_data['created_at']
                )
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            result = self.client.table('users').select('*').eq('id', user_id).execute()
            
            if result.data:
                user_data = result.data[0]
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    credits_balance=user_data['credits_balance'],
                    role=user_data['role'],
                    created_at=user_data['created_at']
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
            
            result = self.client.table('users').update({
                'credits_balance': new_balance
            }).eq('id', user_id).execute()
            
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
            
            result = self.client.table('users').update({
                'credits_balance': new_balance
            }).eq('id', user_id).execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deducting user credits: {e}")
            return False
    
    # Mock Management
    async def create_mock(self, mock_data: Dict[str, Any], creator_id: str) -> Optional[Mock]:
        """Create a new mock exam"""
        try:
            result = self.client.table('mocks').insert({
                'title': mock_data['title'],
                'description': mock_data['description'],
                'questions_json': json.dumps(mock_data['questions']),
                'price_credits': mock_data['price_credits'],
                'explanation_enabled': mock_data['explanation_enabled'],
                'time_limit_minutes': mock_data.get('time_limit_minutes'),
                'category': mock_data.get('category'),
                'is_active': mock_data.get('is_active', True),
                'creator_id': creator_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if result.data:
                mock_data = result.data[0]
                return Mock(
                    id=mock_data['id'],
                    title=mock_data['title'],
                    description=mock_data['description'],
                    questions=json.loads(mock_data['questions_json']),
                    price_credits=mock_data['price_credits'],
                    explanation_enabled=mock_data['explanation_enabled'],
                    time_limit_minutes=mock_data['time_limit_minutes'],
                    category=mock_data['category'],
                    is_active=mock_data['is_active'],
                    created_at=mock_data['created_at']
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
                if not active_only or mock_data['is_active']:
                    mocks.append(Mock(
                        id=mock_data['id'],
                        title=mock_data['title'],
                        description=mock_data['description'],
                        questions=mock_data['questions'],
                        price_credits=mock_data['price_credits'],
                        explanation_enabled=mock_data['explanation_enabled'],
                        time_limit_minutes=30,
                        category="Demo",
                        is_active=mock_data['is_active'],
                        created_at=mock_data['created_at']
                    ))
            return mocks
            
        try:
            query = self.client.table('mocks').select('*')
            if active_only:
                query = query.eq('is_active', True)
            
            result = query.execute()
            
            mocks = []
            for mock_data in result.data:
                mocks.append(Mock(
                    id=mock_data['id'],
                    title=mock_data['title'],
                    description=mock_data['description'],
                    questions=json.loads(mock_data['questions_json']),
                    price_credits=mock_data['price_credits'],
                    explanation_enabled=mock_data['explanation_enabled'],
                    time_limit_minutes=mock_data['time_limit_minutes'],
                    category=mock_data['category'],
                    is_active=mock_data['is_active'],
                    created_at=mock_data['created_at']
                ))
            
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
                    id=mock_data['id'],
                    title=mock_data['title'],
                    description=mock_data['description'],
                    questions=mock_data['questions'],
                    price_credits=mock_data['price_credits'],
                    explanation_enabled=mock_data['explanation_enabled'],
                    time_limit_minutes=30,
                    category="Demo",
                    is_active=mock_data['is_active'],
                    created_at=mock_data['created_at']
                )
            return None
            
        try:
            result = self.client.table('mocks').select('*').eq('id', mock_id).execute()
            
            if result.data:
                mock_data = result.data[0]
                return Mock(
                    id=mock_data['id'],
                    title=mock_data['title'],
                    description=mock_data['description'],
                    questions=json.loads(mock_data['questions_json']),
                    price_credits=mock_data['price_credits'],
                    explanation_enabled=mock_data['explanation_enabled'],
                    time_limit_minutes=mock_data['time_limit_minutes'],
                    category=mock_data['category'],
                    is_active=mock_data['is_active'],
                    created_at=mock_data['created_at']
                )
        except Exception as e:
            logger.error(f"Error getting mock: {e}")
            return None
    
    # Attempt Management
    async def create_attempt(self, user_id: str, mock_id: str, user_answers: List[int]) -> Optional[AttemptResponse]:
        """Create a new attempt"""
        try:
            # Get mock to calculate score
            mock = await self.get_mock_by_id(mock_id)
            if not mock:
                return None
            
            correct_answers = 0
            total_questions = len(mock.questions)
            
            for i, answer in enumerate(user_answers):
                if i < len(mock.questions) and answer == mock.questions[i]['correct_index']:
                    correct_answers += 1
            
            score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            
            result = self.client.table('attempts').insert({
                'user_id': user_id,
                'mock_id': mock_id,
                'user_answers_json': json.dumps(user_answers),
                'score': score,
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'explanation_unlocked': False,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if result.data:
                attempt_data = result.data[0]
                return AttemptResponse(
                    id=attempt_data['id'],
                    user_id=attempt_data['user_id'],
                    mock_id=attempt_data['mock_id'],
                    user_answers=json.loads(attempt_data['user_answers_json']),
                    score=attempt_data['score'],
                    total_questions=attempt_data['total_questions'],
                    correct_answers=attempt_data['correct_answers'],
                    explanation_unlocked=attempt_data['explanation_unlocked'],
                    timestamp=attempt_data['timestamp']
                )
        except Exception as e:
            logger.error(f"Error creating attempt: {e}")
            return None
    
    async def get_user_attempts(self, user_id: str) -> List[AttemptResponse]:
        """Get all attempts for a user"""
        try:
            result = self.client.table('attempts').select('*').eq('user_id', user_id).order('timestamp', desc=True).execute()
            
            attempts = []
            for attempt_data in result.data:
                attempts.append(AttemptResponse(
                    id=attempt_data['id'],
                    user_id=attempt_data['user_id'],
                    mock_id=attempt_data['mock_id'],
                    user_answers=json.loads(attempt_data['user_answers_json']),
                    score=attempt_data['score'],
                    total_questions=attempt_data['total_questions'],
                    correct_answers=attempt_data['correct_answers'],
                    explanation_unlocked=attempt_data['explanation_unlocked'],
                    timestamp=attempt_data['timestamp']
                ))
            
            return attempts
        except Exception as e:
            logger.error(f"Error getting user attempts: {e}")
            return []
    
    async def get_attempt_by_id(self, attempt_id: str) -> Optional[AttemptResponse]:
        """Get attempt by ID"""
        try:
            result = self.client.table('attempts').select('*').eq('id', attempt_id).execute()
            
            if result.data:
                attempt_data = result.data[0]
                return AttemptResponse(
                    id=attempt_data['id'],
                    user_id=attempt_data['user_id'],
                    mock_id=attempt_data['mock_id'],
                    user_answers=json.loads(attempt_data['user_answers_json']),
                    score=attempt_data['score'],
                    total_questions=attempt_data['total_questions'],
                    correct_answers=attempt_data['correct_answers'],
                    explanation_unlocked=attempt_data['explanation_unlocked'],
                    timestamp=attempt_data['timestamp']
                )
        except Exception as e:
            logger.error(f"Error getting attempt: {e}")
            return None
    
    # Support Tickets
    async def create_ticket(self, user_id: str, subject: str, message: str) -> Optional[Ticket]:
        """Create a support ticket"""
        try:
            result = self.client.table('tickets').insert({
                'user_id': user_id,
                'subject': subject,
                'message': message,
                'status': 'open',
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if result.data:
                ticket_data = result.data[0]
                return Ticket(
                    id=ticket_data['id'],
                    user_id=ticket_data['user_id'],
                    subject=ticket_data['subject'],
                    message=ticket_data['message'],
                    status=ticket_data['status'],
                    created_at=ticket_data['created_at']
                )
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return None


# Global database instance
db = DatabaseManager()