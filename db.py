"""
Enhanced database operations for MockExamify Production MVP
Supporting IBF CACS 2 and CMFAS CM-SIP exam categories
"""
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
import bcrypt
from supabase import create_client, Client
from models import (
    User, ExamCategory, Topic, Question, Paper, Upload, SyllabusDoc, 
    Attempt, UserMastery, CreditsLedger, Ticket,
    ExamCategoryCode, DifficultyLevel, QuestionSource, PaperMode,
    FileType, UploadStatus, TicketStatus, CreditReason
)
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Enhanced database manager with comprehensive CRUD operations"""
    
    def __init__(self):
        self.demo_mode = config.DEMO_MODE
        if self.demo_mode:
            logger.info("Running in demo mode - database mocked")
            self._init_demo_data()
        else:
            logger.info("Running in production mode - connecting to Supabase")
            self.supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    def _init_demo_data(self):
        """Initialize demo data for testing"""
        self.demo_users = {
            "admin@mockexamify.com": {
                "id": "demo-admin-001",
                "email": "admin@mockexamify.com",
                "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "credits_balance": 100,
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            "student@test.com": {
                "id": "demo-student-001",
                "email": "student@test.com",
                "password_hash": bcrypt.hashpw("student123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "credits_balance": 25,
                "role": "user",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        self.demo_categories = [
            {
                "id": "cat-cacs2",
                "code": "CACS2",
                "name": "IBF CACS Level 2",
                "description": "Capital Markets and Financial Advisory Services Level 2",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "cat-cmsip",
                "code": "CMSIP", 
                "name": "CMFAS CM-SIP",
                "description": "Capital Markets and Financial Advisory Services - Securities Investment Products",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        self.demo_topics = [
            # CACS2 Topics
            {"id": "topic-risk", "category_id": "cat-cacs2", "code": "RISK_MGMT", "name": "Risk Management"},
            {"id": "topic-portfolio", "category_id": "cat-cacs2", "code": "PORTFOLIO", "name": "Portfolio Management"},
            {"id": "topic-derivatives", "category_id": "cat-cacs2", "code": "DERIVATIVES", "name": "Derivatives"},
            {"id": "topic-ethics", "category_id": "cat-cacs2", "code": "ETHICS", "name": "Professional Ethics"},
            # CMSIP Topics
            {"id": "topic-securities", "category_id": "cat-cmsip", "code": "SECURITIES", "name": "Securities Markets"},
            {"id": "topic-analysis", "category_id": "cat-cmsip", "code": "ANALYSIS", "name": "Investment Analysis"},
            {"id": "topic-regulations", "category_id": "cat-cmsip", "code": "REGULATIONS", "name": "Market Regulations"},
            {"id": "topic-products", "category_id": "cat-cmsip", "code": "PRODUCTS", "name": "Investment Products"},
        ]
        
        # Initialize empty collections for other demo data
        self.demo_questions = []
        self.demo_papers = []
        self.demo_attempts = []
        self.demo_uploads = []
        self.demo_tickets = []

    # ==================== EXAM CATEGORIES ====================
    
    async def get_exam_categories(self) -> List[ExamCategory]:
        """Get all exam categories"""
        if self.demo_mode:
            return [ExamCategory(**cat) for cat in self.demo_categories]
        
        try:
            result = self.supabase.table('exam_categories').select('*').order('name').execute()
            return [ExamCategory(**row) for row in result.data]
        except Exception as e:
            logger.error(f"Error fetching exam categories: {e}")
            return []
    
    async def get_exam_category_by_code(self, code: ExamCategoryCode) -> Optional[ExamCategory]:
        """Get exam category by code"""
        if self.demo_mode:
            for cat in self.demo_categories:
                if cat["code"] == code:
                    return ExamCategory(**cat)
            return None
        
        try:
            result = self.supabase.table('exam_categories').select('*').eq('code', code).execute()
            if result.data:
                return ExamCategory(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching exam category {code}: {e}")
            return None

    # ==================== TOPICS ====================
    
    async def get_topics_by_category(self, category_id: str) -> List[Topic]:
        """Get all topics for a category"""
        if self.demo_mode:
            return [Topic(**topic, created_at=datetime.now(timezone.utc)) 
                   for topic in self.demo_topics if topic["category_id"] == category_id]
        
        try:
            result = self.supabase.table('topics').select('*').eq('category_id', category_id).order('name').execute()
            return [Topic(**row) for row in result.data]
        except Exception as e:
            logger.error(f"Error fetching topics for category {category_id}: {e}")
            return []
    
    async def create_topic(self, topic_data: Dict[str, Any]) -> Optional[Topic]:
        """Create a new topic"""
        if self.demo_mode:
            topic = {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                **topic_data
            }
            self.demo_topics.append(topic)
            return Topic(**topic)
        
        try:
            result = self.supabase.table('topics').insert(topic_data).execute()
            if result.data:
                return Topic(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creating topic: {e}")
            return None

    # ==================== QUESTIONS ====================
    
    async def get_questions_by_category(self, category_id: str, limit: int = 100) -> List[Question]:
        """Get questions by category with optional limit"""
        if self.demo_mode:
            # Return demo questions or generate some basic ones
            return []
        
        try:
            result = (self.supabase.table('questions')
                     .select('*')
                     .eq('category_id', category_id)
                     .eq('active', True)
                     .order('created_at', desc=True)
                     .limit(limit)
                     .execute())
            return [Question(**row) for row in result.data]
        except Exception as e:
            logger.error(f"Error fetching questions for category {category_id}: {e}")
            return []
    
    async def create_question(self, question_data: Dict[str, Any]) -> Optional[Question]:
        """Create a new question"""
        if self.demo_mode:
            question = {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "active": True,
                **question_data
            }
            self.demo_questions.append(question)
            return Question(**question)
        
        try:
            result = self.supabase.table('questions').insert(question_data).execute()
            if result.data:
                return Question(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creating question: {e}")
            return None
    
    async def bulk_create_questions(self, questions_data: List[Dict[str, Any]]) -> List[Question]:
        """Create multiple questions in bulk"""
        if self.demo_mode:
            created_questions = []
            for q_data in questions_data:
                question = {
                    "id": str(uuid.uuid4()),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "active": True,
                    **q_data
                }
                self.demo_questions.append(question)
                created_questions.append(Question(**question))
            return created_questions
        
        try:
            result = self.supabase.table('questions').insert(questions_data).execute()
            return [Question(**row) for row in result.data]
        except Exception as e:
            logger.error(f"Error bulk creating questions: {e}")
            return []

    async def update_question_topic(self, question_id: str, primary_topic_id: str, 
                                  extra_topic_ids: List[str] = None) -> bool:
        """Update question topic assignments"""
        if self.demo_mode:
            # Find and update demo question
            for i, q in enumerate(self.demo_questions):
                if q["id"] == question_id:
                    self.demo_questions[i]["primary_topic_id"] = primary_topic_id
                    if extra_topic_ids:
                        self.demo_questions[i]["extra_topic_ids"] = extra_topic_ids
                    return True
            return False
        
        try:
            update_data = {"primary_topic_id": primary_topic_id}
            if extra_topic_ids:
                update_data["extra_topic_ids"] = extra_topic_ids
            
            result = self.supabase.table('questions').update(update_data).eq('id', question_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating question topic: {e}")
            return False

    # ==================== PAPERS ====================
    
    async def get_papers_by_category(self, category_id: str, active_only: bool = True) -> List[Paper]:
        """Get papers by category"""
        if self.demo_mode:
            return [Paper(**paper) for paper in self.demo_papers 
                   if paper.get("category_id") == category_id and (not active_only or paper.get("active", True))]
        
        try:
            query = self.supabase.table('papers').select('*').eq('category_id', category_id)
            if active_only:
                query = query.eq('active', True)
            result = query.order('created_at', desc=True).execute()
            return [Paper(**row) for row in result.data]
        except Exception as e:
            logger.error(f"Error fetching papers for category {category_id}: {e}")
            return []
    
    async def create_paper(self, paper_data: Dict[str, Any]) -> Optional[Paper]:
        """Create a new paper"""
        if self.demo_mode:
            paper = {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "active": True,
                **paper_data
            }
            self.demo_papers.append(paper)
            return Paper(**paper)
        
        try:
            result = self.supabase.table('papers').insert(paper_data).execute()
            if result.data:
                return Paper(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creating paper: {e}")
            return None

    async def generate_adaptive_paper(self, category_id: str, user_id: str, 
                                    num_questions: int = 10) -> Optional[Paper]:
        """Generate an adaptive paper based on user's weak areas"""
        # Get user's mastery data to identify weak topics
        weak_topics = await self.get_user_weak_topics(user_id, category_id, limit=5)
        
        # Generate paper focusing on weak areas
        paper_data = {
            "category_id": category_id,
            "title": f"Adaptive Practice - {datetime.now().strftime('%Y%m%d_%H%M')}",
            "description": "Personalized practice focusing on weak areas",
            "mode": PaperMode.GENERATED,
            "time_limit_minutes": max(num_questions * 2, 15),  # 2 mins per question minimum
            "num_questions": num_questions,
            "topic_coverage": {topic["topic_id"]: 1.0 / len(weak_topics) for topic in weak_topics} if weak_topics else {},
            "created_by": user_id
        }
        
        return await self.create_paper(paper_data)

    # ==================== USER MASTERY ====================
    
    async def get_user_mastery(self, user_id: str, category_id: str = None) -> List[UserMastery]:
        """Get user mastery data, optionally filtered by category"""
        if self.demo_mode:
            return []  # Return empty for demo mode
        
        try:
            query = self.supabase.table('user_mastery').select('*').eq('user_id', user_id)
            if category_id:
                # Join with topics to filter by category
                query = (self.supabase.table('user_mastery')
                        .select('*, topics!inner(category_id)')
                        .eq('user_id', user_id)
                        .eq('topics.category_id', category_id))
            
            result = query.order('mastery_score').execute()
            return [UserMastery(**row) for row in result.data]
        except Exception as e:
            logger.error(f"Error fetching user mastery: {e}")
            return []
    
    async def get_user_weak_topics(self, user_id: str, category_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user's weakest topics for targeted practice"""
        if self.demo_mode:
            # Return some demo weak topics
            topics = await self.get_topics_by_category(category_id)
            return [{"topic_id": t.id, "topic_name": t.name, "mastery_score": 40.0} 
                   for t in topics[:limit]]
        
        try:
            result = (self.supabase.table('user_mastery')
                     .select('*, topics!inner(id, name, category_id)')
                     .eq('user_id', user_id)
                     .eq('topics.category_id', category_id)
                     .order('mastery_score')
                     .limit(limit)
                     .execute())
            
            return [{"topic_id": row["topic_id"], 
                    "topic_name": row["topics"]["name"],
                    "mastery_score": row["mastery_score"]} for row in result.data]
        except Exception as e:
            logger.error(f"Error fetching weak topics: {e}")
            return []
    
    async def update_user_mastery(self, user_id: str, topic_id: str, 
                                is_correct: bool, time_spent: int = 0) -> bool:
        """Update user mastery after answering a question"""
        if self.demo_mode:
            return True  # Mock success in demo mode
        
        try:
            # Try to get existing mastery record
            existing = (self.supabase.table('user_mastery')
                       .select('*')
                       .eq('user_id', user_id)
                       .eq('topic_id', topic_id)
                       .execute())
            
            if existing.data:
                # Update existing record
                mastery = existing.data[0]
                new_total_answered = mastery['total_answered'] + 1
                new_total_correct = mastery['total_correct'] + (1 if is_correct else 0)
                new_streak = mastery['current_streak'] + 1 if is_correct else 0
                new_best_streak = max(mastery['best_streak'], new_streak)
                
                update_data = {
                    'total_answered': new_total_answered,
                    'total_correct': new_total_correct,
                    'current_streak': new_streak,
                    'best_streak': new_best_streak,
                    'last_seen_at': datetime.now(timezone.utc).isoformat()
                }
                
                result = (self.supabase.table('user_mastery')
                         .update(update_data)
                         .eq('user_id', user_id)
                         .eq('topic_id', topic_id)
                         .execute())
            else:
                # Create new mastery record
                mastery_data = {
                    'user_id': user_id,
                    'topic_id': topic_id,
                    'total_answered': 1,
                    'total_correct': 1 if is_correct else 0,
                    'current_streak': 1 if is_correct else 0,
                    'best_streak': 1 if is_correct else 0,
                    'last_seen_at': datetime.now(timezone.utc).isoformat()
                }
                
                result = self.supabase.table('user_mastery').insert(mastery_data).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error updating user mastery: {e}")
            return False

    # ==================== ATTEMPTS ====================
    
    async def create_attempt(self, user_id: str, paper_id: str) -> Optional[Attempt]:
        """Create a new attempt"""
        attempt_data = {
            "user_id": user_id,
            "paper_id": paper_id,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        if self.demo_mode:
            attempt = {
                "id": str(uuid.uuid4()),
                **attempt_data,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.demo_attempts.append(attempt)
            return Attempt(**attempt)
        
        try:
            result = self.supabase.table('attempts').insert(attempt_data).execute()
            if result.data:
                return Attempt(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creating attempt: {e}")
            return None
    
    async def submit_attempt(self, attempt_id: str, answers: List[Dict], 
                           time_seconds: int) -> Tuple[float, int, int]:
        """Submit attempt and calculate score"""
        # This is a simplified version - full implementation would:
        # 1. Get all questions for the paper
        # 2. Calculate score based on correct answers
        # 3. Update user mastery for each topic
        # 4. Store detailed answer records
        
        if self.demo_mode:
            # Mock scoring
            correct_count = sum(1 for ans in answers if ans.get('selected_index') == ans.get('correct_index', 0))
            total_questions = len(answers)
            score = (correct_count / total_questions * 100) if total_questions > 0 else 0
            
            # Update demo attempt
            for attempt in self.demo_attempts:
                if attempt["id"] == attempt_id:
                    attempt.update({
                        "submitted_at": datetime.now(timezone.utc).isoformat(),
                        "score": score,
                        "time_seconds": time_seconds
                    })
                    break
            
            return score, correct_count, total_questions
        
        try:
            # Calculate score (simplified)
            total_questions = len(answers)
            correct_count = 0
            
            # Update attempt record
            update_data = {
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "time_seconds": time_seconds
            }
            
            # For full implementation, we'd need to:
            # 1. Get question data to check correct answers
            # 2. Store individual answer records
            # 3. Update mastery tracking
            
            score = (correct_count / total_questions * 100) if total_questions > 0 else 0
            update_data["score"] = score
            
            self.supabase.table('attempts').update(update_data).eq('id', attempt_id).execute()
            
            return score, correct_count, total_questions
        except Exception as e:
            logger.error(f"Error submitting attempt: {e}")
            return 0.0, 0, len(answers)

    # ==================== UPLOADS & SYLLABUS ====================
    
    async def create_upload_record(self, upload_data: Dict[str, Any]) -> Optional[Upload]:
        """Create upload record"""
        if self.demo_mode:
            upload = {
                "id": str(uuid.uuid4()),
                "status": UploadStatus.PENDING,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **upload_data
            }
            self.demo_uploads.append(upload)
            return Upload(**upload)
        
        try:
            result = self.supabase.table('uploads').insert(upload_data).execute()
            if result.data:
                return Upload(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creating upload record: {e}")
            return None
    
    async def update_upload_status(self, upload_id: str, status: UploadStatus, 
                                 parsed_summary: Dict = None, error_message: str = None) -> bool:
        """Update upload processing status"""
        if self.demo_mode:
            for upload in self.demo_uploads:
                if upload["id"] == upload_id:
                    upload["status"] = status
                    if parsed_summary:
                        upload["parsed_summary"] = parsed_summary
                    if error_message:
                        upload["error_message"] = error_message
                    return True
            return False
        
        try:
            update_data = {"status": status}
            if parsed_summary:
                update_data["parsed_summary"] = parsed_summary
            if error_message:
                update_data["error_message"] = error_message
            
            result = self.supabase.table('uploads').update(update_data).eq('id', upload_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating upload status: {e}")
            return False

    # ==================== CREDITS ====================
    
    async def add_credits(self, user_id: str, amount: int, reason: CreditReason, 
                         meta: Dict[str, Any] = None) -> bool:
        """Add credits to user account and record in ledger"""
        if self.demo_mode:
            # Update demo user credits
            for email, user in self.demo_users.items():
                if user["id"] == user_id:
                    user["credits_balance"] += amount
                    return True
            return False
        
        try:
            # Record in ledger
            ledger_data = {
                "user_id": user_id,
                "delta": amount,
                "reason": reason,
                "meta": meta or {}
            }
            self.supabase.table('credits_ledger').insert(ledger_data).execute()
            
            # Update user balance
            result = (self.supabase.table('users')
                     .select('credits_balance')
                     .eq('id', user_id)
                     .execute())
            
            if result.data:
                current_balance = result.data[0]['credits_balance']
                new_balance = current_balance + amount
                
                self.supabase.table('users').update({
                    'credits_balance': new_balance
                }).eq('id', user_id).execute()
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding credits: {e}")
            return False

    # ==================== LEGACY SUPPORT ====================
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (legacy support)"""
        if self.demo_mode:
            user_data = self.demo_users.get(email)
            if user_data:
                return User(**user_data)
            return None
        
        try:
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user by email: {e}")
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        if self.demo_mode:
            user_data = self.demo_users.get(email)
            if user_data:
                # Check password hash
                stored_hash = user_data.get("password_hash", "")
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    return User(**user_data)
            return None
        
        try:
            # Get user by email first
            user = await self.get_user_by_email(email)
            if user and hasattr(user, 'password_hash'):
                # Check password hash
                if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                    return user
            return None
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        if self.demo_mode:
            for user_data in self.demo_users.values():
                if user_data.get("id") == user_id:
                    return User(**user_data)
            return None
        
        try:
            result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None
    
    async def create_user(self, email: str, password_hash: str) -> Optional[User]:
        """Create new user (legacy support)"""
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "credits_balance": 5,  # Signup bonus
            "role": "user"
        }
        
        if self.demo_mode:
            user = {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                **user_data
            }
            self.demo_users[email] = user
            return User(**user)
        
        try:
            result = self.supabase.table('users').insert(user_data).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    # ==================== USER ANALYTICS & PERFORMANCE ====================
    
    async def get_user_attempts_by_category(self, user_id: str, exam_category: ExamCategoryCode, 
                                          limit: int = 50) -> List[Attempt]:
        """Get user's attempts for a specific exam category"""
        if self.demo_mode:
            # Return demo attempts for the user and category
            user_attempts = [
                attempt for attempt in self.demo_attempts 
                if attempt.get('user_id') == user_id and 
                   attempt.get('exam_category') == exam_category.value
            ][:limit]
            return [Attempt(**attempt) for attempt in user_attempts]
        
        try:
            result = self.supabase.table('attempts') \
                .select('*, papers!inner(*)')  \
                .eq('user_id', user_id) \
                .eq('papers.exam_category', exam_category.value) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            return [Attempt(**attempt) for attempt in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Error getting user attempts: {e}")
            return []
    
    async def get_user_mastery_data(self, user_id: str, exam_category: ExamCategoryCode) -> List[UserMastery]:
        """Get user's topic mastery data for a specific category"""
        if self.demo_mode:
            # Generate demo mastery data
            demo_mastery = [
                {
                    "id": f"mastery-{i}",
                    "user_id": user_id,
                    "topic_tag": topic["name"],
                    "exam_category": exam_category.value,
                    "mastery_level": 0.6 + (i * 0.1) % 0.4,  # Random between 0.6-1.0
                    "attempts_count": 5 + (i * 2),
                    "correct_count": 3 + i,
                    "last_practiced": datetime.now(timezone.utc) - timedelta(days=i),
                    "created_at": datetime.now(timezone.utc) - timedelta(days=i*2)
                }
                for i, topic in enumerate(self.demo_topics[:5])
            ]
            return [UserMastery(**mastery) for mastery in demo_mastery]
        
        try:
            result = self.supabase.table('user_mastery') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('exam_category', exam_category.value) \
                .order('mastery_level', desc=False) \
                .execute()
            
            return [UserMastery(**mastery) for mastery in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Error getting user mastery data: {e}")
            return []
    
    async def update_user_mastery(self, user_id: str, topic_tag: str, exam_category: ExamCategoryCode,
                                is_correct: bool) -> bool:
        """Update user's mastery level for a topic"""
        if self.demo_mode:
            # Update demo mastery data
            logger.info(f"Demo: Updated mastery for {user_id}, topic: {topic_tag}, correct: {is_correct}")
            return True
        
        try:
            # Get existing mastery record
            existing = self.supabase.table('user_mastery') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('topic_tag', topic_tag) \
                .eq('exam_category', exam_category.value) \
                .execute()
            
            if existing.data:
                # Update existing record
                mastery = existing.data[0]
                new_attempts = mastery['attempts_count'] + 1
                new_correct = mastery['correct_count'] + (1 if is_correct else 0)
                new_mastery_level = new_correct / new_attempts
                
                self.supabase.table('user_mastery') \
                    .update({
                        'attempts_count': new_attempts,
                        'correct_count': new_correct,
                        'mastery_level': new_mastery_level,
                        'last_practiced': datetime.now(timezone.utc).isoformat()
                    }) \
                    .eq('id', mastery['id']) \
                    .execute()
            else:
                # Create new record
                mastery_data = {
                    'user_id': user_id,
                    'topic_tag': topic_tag,
                    'exam_category': exam_category.value,
                    'attempts_count': 1,
                    'correct_count': 1 if is_correct else 0,
                    'mastery_level': 1.0 if is_correct else 0.0,
                    'last_practiced': datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.table('user_mastery').insert(mastery_data).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error updating user mastery: {e}")
            return False
    
    async def get_untagged_questions(self, exam_category: ExamCategoryCode, limit: int = 100) -> List[Question]:
        """Get questions without topic tags for AI tagging"""
        if self.demo_mode:
            # Return demo questions without tags
            untagged = [q for q in self.demo_questions if not q.get('topic_tags')][:limit]
            return [Question(**question) for question in untagged]
        
        try:
            result = self.supabase.table('questions') \
                .select('*') \
                .eq('exam_category', exam_category.value) \
                .or_('topic_tags.is.null,topic_tags.eq.{}') \
                .limit(limit) \
                .execute()
            
            return [Question(**question) for question in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Error getting untagged questions: {e}")
            return []
    
    async def update_question_tags(self, question_id: int, tags: List[str]) -> bool:
        """Update question topic tags"""
        if self.demo_mode:
            logger.info(f"Demo: Updated tags for question {question_id}: {tags}")
            return True
        
        try:
            self.supabase.table('questions') \
                .update({'topic_tags': tags}) \
                .eq('id', question_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating question tags: {e}")
            return False
    
    async def get_questions_with_basic_explanations(self, exam_category: ExamCategoryCode, 
                                                  limit: int = 50) -> List[Question]:
        """Get questions with basic explanations that need enhancement"""
        if self.demo_mode:
            # Return demo questions with short explanations
            basic_explanation_questions = [
                q for q in self.demo_questions 
                if q.get('explanation_seed') and len(q.get('explanation_seed', '')) < 100
            ][:limit]
            return [Question(**question) for question in basic_explanation_questions]
        
        try:
            result = self.supabase.table('questions') \
                .select('*') \
                .eq('exam_category', exam_category.value) \
                .not_.is_('explanation_seed', 'null') \
                .textSearch('explanation_seed', '') \
                .limit(limit) \
                .execute()
            
            return [Question(**question) for question in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Error getting questions with basic explanations: {e}")
            return []
    
    async def update_question_explanation(self, question_id: int, explanation: str) -> bool:
        """Update question explanation"""
        if self.demo_mode:
            logger.info(f"Demo: Updated explanation for question {question_id}")
            return True
        
        try:
            self.supabase.table('questions') \
                .update({'explanation_seed': explanation}) \
                .eq('id', question_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating question explanation: {e}")
            return False
    
    async def update_question_difficulty(self, question_id: int, difficulty: DifficultyLevel) -> bool:
        """Update question difficulty level"""
        if self.demo_mode:
            logger.info(f"Demo: Updated difficulty for question {question_id} to {difficulty}")
            return True
        
        try:
            self.supabase.table('questions') \
                .update({'difficulty': difficulty.value}) \
                .eq('id', question_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating question difficulty: {e}")
            return False
    
    async def get_recent_uploads(self, limit: int = 10) -> List[Upload]:
        """Get recent file uploads"""
        if self.demo_mode:
            # Return demo uploads
            recent_uploads = sorted(
                self.demo_uploads, 
                key=lambda x: x.get('created_at', ''), 
                reverse=True
            )[:limit]
            return [Upload(**upload) for upload in recent_uploads]
        
        try:
            result = self.supabase.table('uploads') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            return [Upload(**upload) for upload in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Error getting recent uploads: {e}")
            return []


# Global database manager instance
db_manager = DatabaseManager()

# Legacy functions for backward compatibility
async def get_user_by_email(email: str) -> Optional[User]:
    return await db_manager.get_user_by_email(email)

async def create_user(email: str, password_hash: str) -> Optional[User]:
    return await db_manager.create_user(email, password_hash)

async def get_exam_categories() -> List[ExamCategory]:
    return await db_manager.get_exam_categories()

async def get_topics_by_category(category_id: str) -> List[Topic]:
    return await db_manager.get_topics_by_category(category_id)

async def get_questions_by_category(category_id: str, limit: int = 100) -> List[Question]:
    return await db_manager.get_questions_by_category(category_id, limit)

async def create_question(question_data: Dict[str, Any]) -> Optional[Question]:
    return await db_manager.create_question(question_data)

async def get_papers_by_category(category_id: str) -> List[Paper]:
    return await db_manager.get_papers_by_category(category_id)

async def create_attempt(user_id: str, paper_id: str) -> Optional[Attempt]:
    return await db_manager.create_attempt(user_id, paper_id)

async def add_credits(user_id: str, amount: int, reason: CreditReason) -> bool:
    return await db_manager.add_credits(user_id, amount, reason)