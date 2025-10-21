"""
Comprehensive Pydantic models and schemas for MockExamify MVP
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions and mocks"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    terms_accepted: bool = Field(default=False)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    id: str
    email: str
    credits_balance: int = 0
    role: str = "user"  # user or admin
    subscription_status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionSchema(BaseModel):
    """Schema for individual questions"""

    id: Optional[str] = None
    mock_id: Optional[str] = None
    question: str
    choices: List[str] = Field(..., min_items=2, max_items=6)
    correct_index: int = Field(..., ge=0)
    explanation: Optional[str] = None
    explanation_seed: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = "medium"
    variant_of: Optional[str] = None  # For question variants
    scenario: Optional[str] = None  # For scenario-based questions
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Alias for backward compatibility
Question = QuestionSchema


class QuestionChoice(BaseModel):
    """Individual choice for a question"""

    text: str
    is_correct: bool = False


class ParsedQuestion(BaseModel):
    """Parsed question from document"""

    question: str
    choices: List[str]
    correct_index: int
    explanation: Optional[str] = None
    scenario: Optional[str] = None
    source_file: Optional[str] = None


class ParseResult(BaseModel):
    """Result from document parsing"""

    success: bool
    questions: List[ParsedQuestion] = []
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class MockCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    questions: List[QuestionSchema] = Field(..., min_items=1)
    price_credits: int = Field(default=1, ge=0)
    explanation_enabled: bool = Field(default=True)
    time_limit_minutes: Optional[int] = Field(default=60, ge=1)
    category: Optional[str] = "General"
    is_active: bool = Field(default=True)


class MockUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    questions: Optional[List[QuestionSchema]] = None
    price_credits: Optional[int] = None
    explanation_enabled: Optional[bool] = None
    time_limit_minutes: Optional[int] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class Mock(BaseModel):
    id: str
    title: str
    description: str
    questions: List[Dict[str, Any]]  # JSON field for backward compatibility
    price_credits: int
    explanation_enabled: bool
    time_limit_minutes: Optional[int]
    category: Optional[str]
    difficulty: Optional[str] = "medium"  # Add difficulty field
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "questions": self.questions,
            "price_credits": self.price_credits,
            "explanation_enabled": self.explanation_enabled,
            "time_limit_minutes": self.time_limit_minutes,
            "category": self.category,
            "difficulty": self.difficulty,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "questions_json": self.questions,  # Alias for backward compatibility
        }


class AttemptCreate(BaseModel):
    mock_id: str
    user_answers: List[int]  # List of selected choice indices


class Attempt(BaseModel):
    id: str
    user_id: str
    mock_id: str
    user_answers: List[int]
    score: float
    total_questions: int
    correct_answers: int
    explanations_unlocked: bool = False
    time_taken: Optional[int] = None  # in seconds
    status: str = "completed"  # in_progress, completed, abandoned
    detailed_results: Optional[Dict[str, Any]] = None
    pdf_url: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttemptResponse(BaseModel):
    id: str
    user_id: str
    mock_id: str
    user_answers: List[int]
    score: float
    total_questions: int
    correct_answers: int
    explanation_unlocked: bool
    timestamp: datetime

    class Config:
        from_attributes = True


class StripeCheckoutRequest(BaseModel):
    pack_id: str  # starter, standard, premium
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class StripeWebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]


class Payment(BaseModel):
    id: str
    user_id: str
    stripe_session_id: str
    amount: float
    credits_purchased: int
    status: str  # pending, completed, failed
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportTicket(BaseModel):
    id: str
    user_id: str
    user_email: Optional[str] = None  # For display purposes
    subject: str
    message: str
    browser: Optional[str] = None
    device: Optional[str] = None
    error_message: Optional[str] = None
    affected_exam: Optional[str] = None
    status: str = "open"  # open, resolved, closed
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    browser: Optional[str] = None
    device: Optional[str] = None
    error_message: Optional[str] = None
    affected_exam: Optional[str] = None


class Ticket(BaseModel):
    id: str
    user_id: str
    subject: str
    message: str
    status: str = "open"  # open, in_progress, closed
    created_at: datetime

    class Config:
        from_attributes = True


class OpenRouterRequest(BaseModel):
    question: str
    choices: List[str]
    correct_answer: str
    context: Optional[str] = None


class OpenRouterResponse(BaseModel):
    explanation: str
    confidence: Optional[float] = None


class PDFRequest(BaseModel):
    attempt_id: str
    include_explanations: bool = False


class DashboardStats(BaseModel):
    total_users: int
    total_mocks: int
    total_attempts: int
    revenue_cents: int
    active_users_last_30_days: int


class CreditPackInfo(BaseModel):
    id: str
    name: str
    credits: int
    price_cents: int
    popular: bool = False
    stripe_price_id: Optional[str] = None
