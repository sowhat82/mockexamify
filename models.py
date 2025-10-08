"""
Pydantic models and schemas for MockExamify
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    

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
    question: str
    choices: List[str] = Field(..., min_items=2, max_items=6)
    correct_index: int = Field(..., ge=0)
    explanation_template: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = "medium"


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
    questions: List[Dict[str, Any]]  # JSON field
    price_credits: int
    explanation_enabled: bool
    time_limit_minutes: Optional[int]
    category: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AttemptCreate(BaseModel):
    mock_id: str
    user_answers: List[int]  # List of selected choice indices


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
    success_url: str
    cancel_url: str


class StripeWebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)


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