"""
FastAPI backend server for MockExamify
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request, Response, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import stripe
from io import BytesIO

# Local imports
import config
from models import (
    User, UserCreate, UserLogin, Mock, MockCreate, MockUpdate,
    AttemptCreate, AttemptResponse, StripeCheckoutRequest,
    TicketCreate, OpenRouterRequest, PDFRequest, CreditPackInfo
)
from db import db
from stripe_utils import stripe_manager
from openrouter_utils import openrouter_manager
from pdf_utils import pdf_generator
from admin_utils import admin_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MockExamify API",
    description="Backend API for MockExamify - Interactive Mock Exam Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://your-streamlit-app.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

class TokenData(BaseModel):
    user_id: str

# Mock JWT implementation (replace with proper JWT in production)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    try:
        # In production, properly decode and verify JWT token
        # For MVP, we'll use a simple token format: "user_{user_id}"
        token = credentials.credentials
        if not token.startswith("user_"):
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        user_id = token.replace("user_", "")
        user = await db.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is admin"""
    if not admin_manager.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and validate configuration"""
    try:
        config.validate_config()
        await db.initialize_tables()
        logger.info("MockExamify API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

# Health check
@app.get("/health")
async def health_check():
    """API health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Authentication endpoints
@app.post("/api/auth/register", response_model=Dict[str, str])
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await db.create_user(user_data.email, user_data.password)
        if not user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Generate token (in production, use proper JWT)
        token = f"user_{user.id}"
        
        return {"token": token, "user_id": user.id, "email": user.email}
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail="Registration failed")

@app.post("/api/auth/login", response_model=Dict[str, str])
async def login_user(login_data: UserLogin):
    """Login user"""
    try:
        user = await db.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate token (in production, use proper JWT)
        token = f"user_{user.id}"
        
        return {
            "token": token, 
            "user_id": user.id, 
            "email": user.email, 
            "role": user.role,
            "credits_balance": str(user.credits_balance)
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Login failed")

# User endpoints
@app.get("/api/user/profile", response_model=User)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@app.get("/api/user/attempts", response_model=List[AttemptResponse])
async def get_user_attempts(current_user: User = Depends(get_current_user)):
    """Get user's exam attempts"""
    return await db.get_user_attempts(current_user.id)

# Mock exam endpoints
@app.get("/api/mocks", response_model=List[Mock])
async def get_all_mocks():
    """Get all active mock exams"""
    return await db.get_all_mocks(active_only=True)

@app.get("/api/mocks/{mock_id}", response_model=Mock)
async def get_mock(mock_id: str):
    """Get specific mock exam"""
    mock = await db.get_mock_by_id(mock_id)
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")
    return mock

@app.post("/api/mocks/start-attempt")
async def start_mock_attempt(mock_id: str, current_user: User = Depends(get_current_user)):
    """Start a mock exam attempt (deduct credits)"""
    try:
        mock = await db.get_mock_by_id(mock_id)
        if not mock:
            raise HTTPException(status_code=404, detail="Mock not found")
        
        if not mock.is_active:
            raise HTTPException(status_code=400, detail="Mock is not active")
        
        # Check if user has enough credits
        if current_user.credits_balance < mock.price_credits:
            raise HTTPException(status_code=400, detail="Insufficient credits")
        
        # Deduct credits
        success = await db.deduct_user_credits(current_user.id, mock.price_credits)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to deduct credits")
        
        return {"message": "Attempt started", "credits_deducted": mock.price_credits}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting attempt: {e}")
        raise HTTPException(status_code=500, detail="Failed to start attempt")

@app.post("/api/mocks/submit", response_model=AttemptResponse)
async def submit_mock_attempt(attempt_data: AttemptCreate, current_user: User = Depends(get_current_user)):
    """Submit mock exam attempt"""
    try:
        attempt = await db.create_attempt(
            current_user.id,
            attempt_data.mock_id,
            attempt_data.user_answers
        )
        
        if not attempt:
            raise HTTPException(status_code=400, detail="Failed to create attempt")
        
        return attempt
        
    except Exception as e:
        logger.error(f"Error submitting attempt: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit attempt")

# PDF generation endpoints
@app.get("/api/mocks/{mock_id}/pdf")
async def download_mock_pdf(
    mock_id: str,
    attempt_id: Optional[str] = None,
    include_answers: bool = False,
    include_explanations: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Download mock exam PDF"""
    try:
        mock = await db.get_mock_by_id(mock_id)
        if not mock:
            raise HTTPException(status_code=404, detail="Mock not found")
        
        attempt = None
        if attempt_id:
            attempt = await db.get_attempt_by_id(attempt_id)
            if not attempt or attempt.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Check if explanations are unlocked if requested
            if include_explanations and not attempt.explanation_unlocked:
                raise HTTPException(status_code=400, detail="Explanations not unlocked")
        
        pdf_content = await pdf_generator.generate_exam_pdf(
            mock=mock,
            attempt=attempt,
            user=current_user,
            include_answers=include_answers,
            include_explanations=include_explanations
        )
        
        if not pdf_content:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        filename = f"mock_{mock_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

# Stripe payment endpoints
@app.get("/api/stripe/credit-packs", response_model=List[CreditPackInfo])
async def get_credit_packs():
    """Get available credit packs"""
    packs = []
    for pack_id, pack_info in config.CREDIT_PACKS.items():
        packs.append(CreditPackInfo(
            id=pack_id,
            name=pack_info["name"],
            credits=pack_info["credits"],
            price_cents=pack_info["price"],
            popular=(pack_id == "standard")  # Mark standard as popular
        ))
    return packs

@app.post("/api/stripe/create-checkout")
async def create_stripe_checkout(
    checkout_request: StripeCheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session"""
    try:
        checkout_url = await stripe_manager.create_checkout_session(
            user=current_user,
            pack_id=checkout_request.pack_id,
            success_url=checkout_request.success_url,
            cancel_url=checkout_request.cancel_url
        )
        
        if not checkout_url:
            raise HTTPException(status_code=400, detail="Failed to create checkout session")
        
        return {"checkout_url": checkout_url}
        
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout")

@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not stripe_manager.verify_webhook_signature(payload, signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        event = stripe.Event.construct_from(
            json.loads(payload.decode('utf-8')),
            stripe.api_key
        )
        
        if event.type == "checkout.session.completed":
            success = await stripe_manager.handle_checkout_completed(event.data.object)
            if not success:
                logger.error("Failed to handle checkout completion")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

# Support ticket endpoints
@app.post("/api/tickets", response_model=Dict[str, str])
async def create_support_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a support ticket"""
    try:
        ticket = await db.create_ticket(
            current_user.id,
            ticket_data.subject,
            ticket_data.message
        )
        
        if not ticket:
            raise HTTPException(status_code=400, detail="Failed to create ticket")
        
        return {"message": "Ticket created successfully", "ticket_id": ticket.id}
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ticket")

# OpenRouter AI endpoints
@app.post("/api/openrouter/generate-explanation")
async def generate_explanation(
    request: OpenRouterRequest,
    current_user: User = Depends(get_admin_user)  # Admin only
):
    """Generate explanation using OpenRouter AI"""
    try:
        if not openrouter_manager.is_configured():
            raise HTTPException(status_code=503, detail="OpenRouter not configured")
        
        explanation = await openrouter_manager.generate_explanation(
            question=request.question,
            choices=request.choices,
            correct_answer=request.correct_answer,
            context=request.context
        )
        
        if not explanation:
            raise HTTPException(status_code=500, detail="Failed to generate explanation")
        
        return {"explanation": explanation}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate explanation")

# Admin endpoints
@app.get("/api/admin/dashboard")
async def get_admin_dashboard(admin_user: User = Depends(get_admin_user)):
    """Get admin dashboard data"""
    try:
        stats = await admin_manager.get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@app.get("/api/admin/users")
async def get_all_users(
    limit: int = 100,
    offset: int = 0,
    admin_user: User = Depends(get_admin_user)
):
    """Get all users (admin only)"""
    try:
        users = await admin_manager.get_all_users(limit, offset)
        return users
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get users")

@app.post("/api/admin/mocks", response_model=Mock)
async def create_admin_mock(
    mock_data: MockCreate,
    admin_user: User = Depends(get_admin_user)
):
    """Create a new mock exam (admin only)"""
    try:
        mock = await db.create_mock(mock_data.dict(), admin_user.id)
        if not mock:
            raise HTTPException(status_code=400, detail="Failed to create mock")
        return mock
    except Exception as e:
        logger.error(f"Error creating mock: {e}")
        raise HTTPException(status_code=500, detail="Failed to create mock")

@app.post("/api/admin/mocks/generate")
async def generate_ai_mock(
    topic: str,
    num_questions: int = 10,
    difficulty: str = "medium",
    admin_user: User = Depends(get_admin_user)
):
    """Generate mock exam using AI (admin only)"""
    try:
        mock = await admin_manager.create_mock_from_ai(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            creator_id=admin_user.id
        )
        
        if not mock:
            raise HTTPException(status_code=500, detail="Failed to generate mock")
        
        return mock
    except Exception as e:
        logger.error(f"Error generating AI mock: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate mock")

@app.get("/api/admin/mocks/{mock_id}/analytics")
async def get_mock_analytics(
    mock_id: str,
    admin_user: User = Depends(get_admin_user)
):
    """Get analytics for a specific mock (admin only)"""
    try:
        analytics = await admin_manager.get_mock_analytics(mock_id)
        return analytics
    except Exception as e:
        logger.error(f"Error getting mock analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@app.get("/api/admin/tickets")
async def get_all_tickets(
    status: Optional[str] = None,
    admin_user: User = Depends(get_admin_user)
):
    """Get all support tickets (admin only)"""
    try:
        tickets = await admin_manager.get_all_tickets(status)
        return tickets
    except Exception as e:
        logger.error(f"Error getting tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tickets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)