"""
Enhanced Pydantic models and schemas for MockExamify Production MVP
Supporting IBF CACS 2 and CMFAS CM-SIP exam categories
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# Enums for type safety
class ExamCategoryCode(str, Enum):
    CACS2 = "CACS2"
    CMSIP = "CMSIP"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionSource(str, Enum):
    UPLOADED = "uploaded"
    AI_GENERATED = "ai_generated"


class PaperMode(str, Enum):
    STATIC = "static"
    GENERATED = "generated"


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    JSON = "json"
    TXT = "txt"


class UploadStatus(str, Enum):
    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"
    INDEXED = "indexed"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CreditReason(str, Enum):
    PURCHASE = "purchase"
    EXAM = "exam"
    EXPLANATIONS = "explanations"
    ADJUSTMENT = "adjustment"
    SIGNUP_BONUS = "signup_bonus"


# User Models
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


# Exam Category Models
class ExamCategoryCreate(BaseModel):
    code: ExamCategoryCode
    name: str
    description: Optional[str] = None


class ExamCategory(BaseModel):
    id: str
    code: ExamCategoryCode
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Topic Models
class TopicCreate(BaseModel):
    category_id: str
    code: str
    name: str
    description: Optional[str] = None
    parent_topic_id: Optional[str] = None


class Topic(BaseModel):
    id: str
    category_id: str
    code: str
    name: str
    description: Optional[str] = None
    parent_topic_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Question Models
class QuestionChoice(BaseModel):
    text: str
    label: str  # A, B, C, D


class QuestionCreate(BaseModel):
    category_id: str
    source: QuestionSource
    stem: str
    choices: List[QuestionChoice] = Field(..., min_items=4, max_items=4)
    correct_index: int = Field(..., ge=0, le=3)
    explanation: Optional[str] = None
    scenario: Optional[str] = None
    difficulty: DifficultyLevel
    primary_topic_id: Optional[str] = None
    extra_topic_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source_doc_id: Optional[str] = None
    variant_of_question_id: Optional[str] = None


class Question(BaseModel):
    id: str
    category_id: str
    source: QuestionSource
    stem: str
    choices: List[QuestionChoice]
    correct_index: int
    explanation: Optional[str] = None
    scenario: Optional[str] = None
    difficulty: DifficultyLevel
    primary_topic_id: Optional[str] = None
    extra_topic_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source_doc_id: Optional[str] = None
    variant_of_question_id: Optional[str] = None
    active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


# Paper Models
class PaperCreate(BaseModel):
    category_id: str
    title: str
    description: Optional[str] = None
    mode: PaperMode
    time_limit_minutes: int = Field(default=60, gt=0)
    num_questions: int = Field(default=20, gt=0)
    difficulty_mix: Dict[str, float] = Field(default={"easy": 0.3, "medium": 0.5, "hard": 0.2})
    topic_coverage: Dict[str, float] = Field(default_factory=dict)


class Paper(BaseModel):
    id: str
    category_id: str
    title: str
    description: Optional[str] = None
    mode: PaperMode
    time_limit_minutes: int
    num_questions: int
    difficulty_mix: Dict[str, float]
    topic_coverage: Dict[str, float]
    active: bool = True
    created_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Upload Models
class UploadCreate(BaseModel):
    category_id: str
    file_name: str
    file_type: FileType
    storage_url: Optional[str] = None


class Upload(BaseModel):
    id: str
    category_id: str
    file_name: str
    file_type: FileType
    storage_url: Optional[str] = None
    status: UploadStatus
    parsed_summary: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Syllabus Models
class SyllabusDocCreate(BaseModel):
    category_id: str
    file_name: str
    file_type: FileType
    storage_url: Optional[str] = None


class SyllabusDoc(BaseModel):
    id: str
    category_id: str
    file_name: str
    file_type: FileType
    storage_url: Optional[str] = None
    status: UploadStatus
    chunk_count: int = 0
    created_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SyllabusChunk(BaseModel):
    id: str
    syllabus_doc_id: str
    chunk_text: str
    chunk_index: int
    topic_guess: Optional[str] = None
    token_count: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Attempt Models
class AttemptCreate(BaseModel):
    user_id: str
    paper_id: str
    mock_id: Optional[str] = None  # For backward compatibility


class AttemptAnswer(BaseModel):
    question_id: str
    selected_index: Optional[int] = None
    time_spent_seconds: int = 0


class AttemptSubmit(BaseModel):
    attempt_id: str
    answers: List[AttemptAnswer]
    time_seconds: int


class Attempt(BaseModel):
    id: str
    user_id: str
    paper_id: str
    mock_id: Optional[str] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None
    score: Optional[float] = None
    time_seconds: Optional[int] = None
    explanations_unlocked: bool = False
    pdf_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# User Mastery Models
class UserMasteryCreate(BaseModel):
    user_id: str
    topic_id: str


class UserMastery(BaseModel):
    id: str
    user_id: str
    topic_id: str
    total_answered: int = 0
    total_correct: int = 0
    current_streak: int = 0
    best_streak: int = 0
    mastery_score: float = 0.0
    last_seen_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Credits Ledger Models
class CreditsLedgerCreate(BaseModel):
    user_id: str
    delta: int
    reason: CreditReason
    meta: Dict[str, Any] = Field(default_factory=dict)


class CreditsLedger(BaseModel):
    id: str
    user_id: str
    delta: int
    reason: CreditReason
    meta: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Support Ticket Models
class TicketCreate(BaseModel):
    user_id: str
    subject: str
    message: str
    priority: TicketPriority = TicketPriority.MEDIUM


class Ticket(BaseModel):
    id: str
    user_id: str
    subject: str
    message: str
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# AI Generation Models
class TopicTaggingRequest(BaseModel):
    question_stem: str
    choices: List[str]
    available_topics: List[Dict[str, str]]  # [{"id": "...", "name": "...", "hint": "..."}]


class TopicTaggingResponse(BaseModel):
    primary_topic_id: str
    confidence: float
    secondary_topic_id: Optional[str] = None
    reasoning: str


class ExplanationRequest(BaseModel):
    question_stem: str
    choices: List[str]
    correct_index: int
    topic_context: Optional[str] = None
    syllabus_snippets: List[str] = Field(default_factory=list)


class QuestionGenerationRequest(BaseModel):
    category_id: str
    topic_id: str
    difficulty: DifficultyLevel
    num_questions: int = Field(default=1, ge=1, le=20)
    syllabus_context: List[str] = Field(default_factory=list)
    include_scenario: bool = False


class GeneratedQuestion(BaseModel):
    stem: str
    choices: List[QuestionChoice]
    correct_index: int
    explanation: str
    scenario: Optional[str] = None
    difficulty: DifficultyLevel
    tags: List[str] = Field(default_factory=list)


class QuestionGenerationResponse(BaseModel):
    questions: List[GeneratedQuestion]
    generated_count: int
    failed_count: int = 0
    errors: List[str] = Field(default_factory=list)


# Adaptive Practice Models
class WeakAreaAnalysis(BaseModel):
    user_id: str
    topic_id: str
    topic_name: str
    mastery_score: float
    total_answered: int
    recommendation: str


class AdaptivePracticeRequest(BaseModel):
    user_id: str
    category_id: str
    num_questions: int = Field(default=10, ge=5, le=50)
    focus_topics: List[str] = Field(default_factory=list)  # Empty = auto-select weak areas


class AdaptivePracticeResponse(BaseModel):
    paper_id: str
    questions: List[Question]
    weak_areas_targeted: List[str]
    estimated_difficulty: DifficultyLevel


# Legacy Models (for backward compatibility)
class QuestionSchema(BaseModel):
    """Legacy question schema for backward compatibility"""
    id: Optional[str] = None
    mock_id: Optional[str] = None
    question: str
    choices: List[str] = Field(..., min_items=2, max_items=6)
    correct_index: int = Field(..., ge=0)
    explanation: Optional[str] = None
    explanation_seed: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = "medium"
    variant_of: Optional[str] = None
    scenario: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MockSchema(BaseModel):
    """Legacy mock schema for backward compatibility"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = "medium"
    time_limit: int = 60
    credits_cost: int = 1
    questions_json: Optional[List[QuestionSchema]] = None
    questions: Optional[List[QuestionSchema]] = None
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AttemptSchema(BaseModel):
    """Legacy attempt schema for backward compatibility"""
    id: Optional[str] = None
    user_id: str
    mock_id: str
    score: Optional[float] = None
    correct_answers: Optional[int] = None
    total_questions: Optional[int] = None
    time_taken: Optional[int] = None
    completed_at: Optional[datetime] = None
    detailed_results: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


# Response Models
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


# Dashboard Models
class DashboardStats(BaseModel):
    total_questions: int
    total_papers: int
    total_attempts: int
    active_users: int
    categories_stats: Dict[str, Dict[str, int]]


class UserProgress(BaseModel):
    user_id: str
    category_id: str
    total_attempts: int
    average_score: float
    best_score: float
    weak_topics: List[WeakAreaAnalysis]
    recent_attempts: List[Attempt]


# File Processing Models
class ParsedQuestion(BaseModel):
    stem: str
    choices: List[str]
    correct_index: Optional[int] = None
    explanation: Optional[str] = None
    scenario: Optional[str] = None
    confidence: float = 0.0
    raw_text: str


class ParseResult(BaseModel):
    success: bool
    questions: List[ParsedQuestion]
    errors: List[str]
    total_parsed: int
    confidence_score: float