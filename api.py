"""
Enhanced FastAPI backend server for MockExamify
Comprehensive endpoints with proper error handling, documentation, and security
"""
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Depends, Request, Response, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
import stripe
from io import BytesIO

# Local imports
import config
from models import (
    User, UserCreate, UserLogin, DifficultyLevel,
    Question, QuestionSchema, Mock, MockCreate, MockUpdate,
    Attempt, AttemptCreate, AttemptResponse,
    Payment, StripeCheckoutRequest, StripeWebhookEvent,
    TicketCreate, SupportTicket, CreditPackInfo, DashboardStats
)
from db import db
from stripe_utils import StripeUtils
from openrouter_utils import openrouter_manager
from pdf_utils import enhanced_pdf_generator as pdf_generator
from admin_utils import admin_manager

# Initialize stripe manager
stripe_manager = StripeUtils(config.STRIPE_SECRET_KEY)
from security_utils import security_manager, InputValidator, log_admin_action
from production_utils import production_cache as cache_manager, performance_monitor

# Configure comprehensive logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with enhanced configuration
app = FastAPI(
    title="MockExamify API",
    description="Enhanced Backend API for MockExamify - Interactive Mock Exam Platform with Production Features",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501", 
        "https://mockexamify.streamlit.app",
        "https://*.streamlit.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Enhanced Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: str = datetime.utcnow().isoformat()

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()

class PaginatedResponse(BaseModel):
    success: bool = True
    data: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    timestamp: str = datetime.utcnow().isoformat()

# Enhanced Request Models
class QuestionGenerationRequest(BaseModel):
    category_id: str
    topic_id: Optional[str] = None
    difficulty: DifficultyLevel
    count: int = 5
    include_explanations: bool = True

class TopicTaggingRequest(BaseModel):
    question_ids: List[str]
    auto_tag: bool = True

class PaperGenerationRequest(BaseModel):
    category_id: str
    title: str
    difficulty_distribution: Dict[str, int]  # {'easy': 5, 'medium': 10, 'hard': 5}
    topic_coverage: Optional[Dict[str, int]] = None
    time_limit_minutes: int = 120

# Error Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    logger.error(f"Validation error for {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation failed",
            error_code="VALIDATION_ERROR"
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handling"""
    logger.error(f"HTTP error for {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=getattr(exc, 'error_code', 'HTTP_ERROR')
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error for {request.url}: {traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )

# Middleware for rate limiting and security
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security and rate limiting middleware"""
    start_time = datetime.utcnow()
    
    # Get client identifier
    client_ip = request.client.host
    
    # Rate limiting
    is_allowed, remaining = security_manager.check_rate_limit(client_ip)
    if not is_allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=ErrorResponse(
                error="Rate limit exceeded",
                error_code="RATE_LIMIT"
            ).dict()
        )
    
    # Process request
    response = await call_next(request)
    
    # Log performance
    duration = (datetime.utcnow() - start_time).total_seconds()
    performance_monitor.log_api_call(str(request.url), duration, response.status_code)
    
    # Add security headers
    response.headers["X-Rate-Limit-Remaining"] = str(remaining)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Enhanced authentication with session validation"""
    try:
        token = credentials.credentials
        user_id = security_manager.validate_session_token(token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user = await db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Admin authentication dependency
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin privileges"""
    if current_user.role != UserRole.ADMIN:
        log_admin_action("unauthorized_access_attempt", {
            "user_id": current_user.id,
            "user_email": current_user.email
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/login", response_model=APIResponse)
async def login(login_data: UserLogin, request: Request):
    """Enhanced user authentication with security logging"""
    client_ip = request.client.host
    
    # Check if account is locked
    if security_manager.is_account_locked(login_data.email):
        security_manager.log_security_event("locked_account_attempt", "medium", {
            "email": login_data.email,
            "ip": client_ip
        })
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to multiple failed attempts"
        )
    
    # Validate input
    is_valid, error_msg, sanitized_email = security_manager.validate_input(
        login_data.email, "email"
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    try:
        user = await db.authenticate_user(sanitized_email, login_data.password)
        
        if not user:
            # Track failed attempt
            security_manager.track_failed_login(login_data.email)
            security_manager.log_security_event("failed_login", "medium", {
                "email": login_data.email,
                "ip": client_ip
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Clear failed attempts on successful login
        security_manager.clear_failed_attempts(login_data.email)
        
        # Create secure session token
        token = security_manager.create_session_token(user.id)
        
        # Log successful login
        security_manager.log_security_event("successful_login", "low", {
            "user_id": user.id,
            "email": user.email,
            "ip": client_ip
        })
        
        return APIResponse(
            success=True,
            message="Login successful",
            data={
                "token": token,
                "user": user.dict(),
                "session_expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

@app.post("/api/auth/register", response_model=APIResponse)
async def register(user_data: UserCreate, request: Request):
    """Enhanced user registration with validation"""
    client_ip = request.client.host
    
    # Validate input
    is_valid, error_msg, sanitized_email = security_manager.validate_input(
        user_data.email, "email"
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    is_valid, error_msg, _ = security_manager.validate_input(
        user_data.password, "password"
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    try:
        # Check if user already exists
        existing_user = await db.get_user_by_email(sanitized_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Create user
        user_data.email = sanitized_email
        user = await db.create_user(user_data)
        
        # Create session token
        token = security_manager.create_session_token(user.id)
        
        # Log registration
        security_manager.log_security_event("user_registration", "low", {
            "user_id": user.id,
            "email": user.email,
            "ip": client_ip
        })
        
        return APIResponse(
            success=True,
            message="Registration successful",
            data={
                "token": token,
                "user": user.dict(),
                "session_expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service error"
        )

@app.post("/api/auth/logout", response_model=APIResponse)
async def logout(current_user: User = Depends(get_current_user), 
                credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Enhanced logout with session invalidation"""
    try:
        # Invalidate session token
        security_manager.invalidate_session(credentials.credentials)
        
        # Log logout
        security_manager.log_security_event("user_logout", "low", {
            "user_id": current_user.id,
            "email": current_user.email
        })
        
        return APIResponse(
            success=True,
            message="Logout successful"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout service error"
        )

# ============================================================================
# EXAM CATEGORIES & TOPICS ENDPOINTS
# ============================================================================

@app.get("/api/categories", response_model=APIResponse)
async def get_exam_categories():
    """Get all exam categories"""
    try:
        categories = await db.get_exam_categories()
        return APIResponse(
            success=True,
            message="Categories retrieved successfully",
            data=[category.dict() for category in categories]
        )
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get categories")

@app.get("/api/categories/{category_id}/topics", response_model=APIResponse)
async def get_category_topics(category_id: str):
    """Get topics for a specific category"""
    try:
        topics = await db.get_topics_by_category(category_id)
        return APIResponse(
            success=True,
            message="Topics retrieved successfully",
            data=[topic.dict() for topic in topics]
        )
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get topics")

# ============================================================================
# PAPERS & QUESTIONS ENDPOINTS
# ============================================================================

@app.get("/api/papers", response_model=APIResponse)
async def get_papers(
    category_id: Optional[str] = None,
    active_only: bool = True,
    page: int = 1,
    page_size: int = 20
):
    """Get exam papers with pagination"""
    try:
        papers, total = await db.get_papers_paginated(
            category_id=category_id,
            active_only=active_only,
            page=page,
            page_size=page_size
        )
        
        return PaginatedResponse(
            data=[paper.dict() for paper in papers],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total
        )
    except Exception as e:
        logger.error(f"Error getting papers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get papers")

@app.get("/api/papers/{paper_id}", response_model=APIResponse)
async def get_paper_details(paper_id: str):
    """Get detailed paper information"""
    try:
        paper = await db.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        questions = await db.get_paper_questions(paper_id)
        
        return APIResponse(
            success=True,
            message="Paper details retrieved successfully",
            data={
                "paper": paper.dict(),
                "questions": [q.dict() for q in questions],
                "question_count": len(questions)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get paper details")

# ============================================================================
# EXAM ATTEMPTS ENDPOINTS
# ============================================================================

@app.post("/api/attempts/start", response_model=APIResponse)
async def start_exam_attempt(
    attempt_data: AttemptCreate,
    current_user: User = Depends(get_current_user)
):
    """Start a new exam attempt with credit validation"""
    try:
        # Validate user has sufficient credits
        paper = await db.get_paper_by_id(attempt_data.paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        if current_user.credits_balance < paper.credits_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits"
            )
        
        # Deduct credits and create attempt
        attempt = await db.create_attempt(attempt_data, current_user.id)
        await db.deduct_user_credits(current_user.id, paper.credits_cost)
        
        # Log credit transaction
        await db.log_credit_transaction(
            current_user.id,
            -paper.credits_cost,
            CreditTransactionReason.EXAM,
            {"attempt_id": attempt.id, "paper_id": paper.id}
        )
        
        return APIResponse(
            success=True,
            message="Exam attempt started successfully",
            data=attempt.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting attempt: {e}")
        raise HTTPException(status_code=500, detail="Failed to start exam attempt")

@app.post("/api/attempts/{attempt_id}/submit", response_model=APIResponse)
async def submit_exam_attempt(
    attempt_id: str,
    answers: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
):
    """Submit exam attempt with comprehensive validation"""
    try:
        # Validate answers format
        for answer in answers:
            is_valid, error_msg = InputValidator.validate_exam_answer(answer)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid answer format: {error_msg}")
        
        # Process submission
        result = await db.submit_attempt(attempt_id, answers, current_user.id)
        
        # Update user mastery tracking
        await db.update_user_mastery(current_user.id, answers)
        
        return APIResponse(
            success=True,
            message="Exam submitted successfully",
            data=result.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting attempt: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit exam")

@app.get("/api/attempts/user/{user_id}", response_model=APIResponse)
async def get_user_attempts(
    user_id: str,
    current_user: User = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20
):
    """Get user's exam attempts with pagination"""
    # Check if user can access these attempts
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        attempts, total = await db.get_user_attempts_paginated(user_id, page, page_size)
        
        return PaginatedResponse(
            data=[attempt.dict() for attempt in attempts],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total
        )
    except Exception as e:
        logger.error(f"Error getting user attempts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user attempts")

# ============================================================================
# AI & GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/ai/generate-questions", response_model=APIResponse)
async def generate_questions(
    request_data: QuestionGenerationRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Generate questions using AI (Admin only)"""
    try:
        # Log admin action
        log_admin_action("ai_question_generation", {
            "category_id": request_data.category_id,
            "count": request_data.count,
            "difficulty": request_data.difficulty
        })
        
        # Generate questions
        questions = await openrouter_manager.generate_questions(
            category_id=request_data.category_id,
            topic_id=request_data.topic_id,
            difficulty=request_data.difficulty,
            count=request_data.count,
            include_explanations=request_data.include_explanations
        )
        
        return APIResponse(
            success=True,
            message=f"Generated {len(questions)} questions successfully",
            data=questions
        )
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate questions")

@app.post("/api/ai/tag-topics", response_model=APIResponse)
async def tag_question_topics(
    request_data: TopicTaggingRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Auto-tag questions with topics using AI (Admin only)"""
    try:
        log_admin_action("ai_topic_tagging", {
            "question_count": len(request_data.question_ids),
            "auto_tag": request_data.auto_tag
        })
        
        results = await openrouter_manager.tag_question_topics(request_data.question_ids)
        
        return APIResponse(
            success=True,
            message="Topic tagging completed successfully",
            data=results
        )
        
    except Exception as e:
        logger.error(f"Error tagging topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to tag topics")

@app.post("/api/ai/generate-explanations", response_model=APIResponse)
async def generate_explanations(
    question_ids: List[str],
    admin_user: User = Depends(get_admin_user)
):
    """Generate explanations for questions using AI (Admin only)"""
    try:
        log_admin_action("ai_explanation_generation", {
            "question_count": len(question_ids)
        })
        
        results = await openrouter_manager.generate_explanations_batch(question_ids)
        
        return APIResponse(
            success=True,
            message="Explanations generated successfully",
            data=results
        )
        
    except Exception as e:
        logger.error(f"Error generating explanations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate explanations")

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.post("/api/admin/papers/generate", response_model=APIResponse)
async def generate_paper(
    request_data: PaperGenerationRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Generate new paper with AI assistance (Admin only)"""
    try:
        log_admin_action("paper_generation", {
            "category_id": request_data.category_id,
            "title": request_data.title,
            "difficulty_distribution": request_data.difficulty_distribution
        })
        
        paper = await admin_manager.generate_paper(
            category_id=request_data.category_id,
            title=request_data.title,
            difficulty_distribution=request_data.difficulty_distribution,
            topic_coverage=request_data.topic_coverage,
            time_limit_minutes=request_data.time_limit_minutes,
            created_by=admin_user.id
        )
        
        return APIResponse(
            success=True,
            message="Paper generated successfully",
            data=paper.dict()
        )
        
    except Exception as e:
        logger.error(f"Error generating paper: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate paper")

@app.get("/api/admin/analytics", response_model=APIResponse)
async def get_admin_analytics(admin_user: User = Depends(get_admin_user)):
    """Get comprehensive admin analytics"""
    try:
        analytics = await admin_manager.get_comprehensive_analytics()
        
        return APIResponse(
            success=True,
            message="Analytics retrieved successfully",
            data=analytics
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@app.get("/api/admin/security/metrics", response_model=APIResponse)
async def get_security_metrics(admin_user: User = Depends(get_admin_user)):
    """Get security metrics and audit logs (Admin only)"""
    try:
        metrics = security_manager.get_security_metrics()
        
        return APIResponse(
            success=True,
            message="Security metrics retrieved successfully",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get security metrics")

# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================

@app.post("/api/payments/create-checkout", response_model=APIResponse)
async def create_checkout_session(
    checkout_data: StripeCheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session with enhanced validation"""
    try:
        # Validate credit purchase
        is_valid, error_msg = InputValidator.validate_credit_purchase(checkout_data.dict())
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Create checkout session
        checkout_url = await stripe_manager.create_checkout_session(
            user_id=current_user.id,
            credits=checkout_data.credits,
            return_url=checkout_data.return_url
        )
        
        return APIResponse(
            success=True,
            message="Checkout session created successfully",
            data={"checkout_url": checkout_url}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

# ============================================================================
# HEALTH & MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/health", response_model=APIResponse)
async def health_check():
    """Enhanced health check with system status"""
    try:
        # Check database connectivity
        db_status = await db.health_check()
        
        # Check external services
        stripe_status = stripe_manager.health_check()
        ai_status = openrouter_manager.health_check()
        
        # Get performance metrics
        performance_metrics = performance_monitor.get_current_metrics()
        
        status_data = {
            "database": db_status,
            "stripe": stripe_status,
            "ai_service": ai_status,
            "performance": performance_metrics,
            "uptime": performance_monitor.get_uptime(),
            "version": "2.0.0"
        }
        
        return APIResponse(
            success=True,
            message="System healthy",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return APIResponse(
            success=False,
            message="System health check failed",
            data={"error": str(e)}
        )

@app.get("/api/metrics", response_model=APIResponse)
async def get_system_metrics(admin_user: User = Depends(get_admin_user)):
    """Get detailed system metrics (Admin only)"""
    try:
        metrics = {
            "performance": performance_monitor.get_detailed_metrics(),
            "security": security_manager.get_security_metrics(),
            "cache": cache_manager.get_metrics(),
            "database": await db.get_database_metrics()
        }
        
        return APIResponse(
            success=True,
            message="System metrics retrieved successfully",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting MockExamify API v2.0.0...")
    
    # Initialize database (commented out - DB runs in demo mode)
    # await db.initialize_tables()
    
    # Initialize performance monitoring (commented out - optional feature)
    # performance_monitor.start()
    
    # Log startup
    security_manager.log_security_event("api_startup", "low", {
        "version": "2.0.0",
        "environment": config.ENVIRONMENT
    })
    
    logger.info("MockExamify API v2.0.0 started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MockExamify API...")
    
    # Stop performance monitoring (commented out - optional feature)
    # performance_monitor.stop()
    
    # Log shutdown
    security_manager.log_security_event("api_shutdown", "low", {
        "version": "2.0.0"
    })
    
    logger.info("MockExamify API shutdown complete!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )