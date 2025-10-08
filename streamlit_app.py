"""
MockExamify - Main Streamlit Application
Interactive Mock Exam Platform with Credit System
"""
import streamlit as st
import httpx
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import base64
from io import BytesIO

import config
from models import User, Mock, AttemptResponse, CreditPackInfo

# Configure Streamlit page
st.set_page_config(
    page_title="MockExamify",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: bold;
}

/* Enable browser password saving */
form[data-testid="form"] {
    /* This helps browsers recognize this as a login form */
}

input[data-testid="stTextInput"] input[type="text"]:first-of-type {
    /* Style for email input */
}

input[data-testid="stTextInput"] input[type="password"] {
    /* Style for password input */
}

.credit-balance {
    background: linear-gradient(90deg, #ff7b7b, #ffb347);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: bold;
    margin: 1rem 0;
}

.mock-card {
    border: 1px solid #e0e0e0;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 1rem 0;
    background: white;
}

.score-excellent { color: #28a745; font-weight: bold; }
.score-good { color: #ffc107; font-weight: bold; }
.score-poor { color: #dc3545; font-weight: bold; }

.question-container {
    background: #f8f9fa;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 1rem 0;
    border-left: 4px solid #007bff;
}

.explanation-box {
    background: #e7f3ff;
    border: 1px solid #b3d9ff;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_token' not in st.session_state:
    st.session_state.user_token = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_mock' not in st.session_state:
    st.session_state.current_mock = None
if 'current_attempt' not in st.session_state:
    st.session_state.current_attempt = None
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'last_email' not in st.session_state:
    st.session_state.last_email = "admin@mockexamify.com"  # Default to admin for convenience

# API client
class APIClient:
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.headers = {"Content-Type": "application/json"}
        self.demo_mode = config.DEMO_MODE
        
        # Initialize database manager for demo mode
        if self.demo_mode:
            from db import DatabaseManager
            self.db = DatabaseManager()
        
    def set_auth_token(self, token: str):
        self.headers["Authorization"] = f"Bearer {token}"
    
    async def post(self, endpoint: str, data: Dict = None) -> Dict:
        if self.demo_mode:
            return await self._handle_demo_request(endpoint, data, method="POST")
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=self.headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    async def get(self, endpoint: str, params: Dict = None) -> Dict:
        if self.demo_mode:
            return await self._handle_demo_request(endpoint, params, method="GET")
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=self.headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    async def _handle_demo_request(self, endpoint: str, data: Dict = None, method: str = "GET") -> Dict:
        """Handle API requests in demo mode by calling database directly"""
        try:
            if endpoint == "/api/auth/login" and method == "POST":
                user = await self.db.authenticate_user(data["email"], data["password"])
                if user:
                    return {
                        "access_token": f"demo_token_{user.id}",
                        "token_type": "bearer",
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "credits_balance": user.credits_balance,
                            "role": user.role
                        }
                    }
                else:
                    raise Exception("Invalid credentials")
            
            elif endpoint == "/mocks" and method == "GET":
                mocks = await self.db.get_all_mocks(active_only=True)
                return {
                    "mocks": [
                        {
                            "id": mock.id,
                            "title": mock.title,
                            "description": mock.description,
                            "price_credits": mock.price_credits,
                            "explanation_enabled": mock.explanation_enabled,
                            "time_limit_minutes": mock.time_limit_minutes,
                            "category": mock.category,
                            "question_count": len(mock.questions)
                        }
                        for mock in mocks
                    ]
                }
            
            elif endpoint.startswith("/mocks/") and endpoint.endswith("/start") and method == "POST":
                mock_id = endpoint.split("/")[2]
                # In demo mode, just return success
                return {"message": "Mock started successfully", "attempt_id": f"demo_attempt_{mock_id}"}
            
            elif endpoint.startswith("/mocks/") and not endpoint.endswith("/start") and method == "GET":
                mock_id = endpoint.split("/")[2]
                mock = await self.db.get_mock_by_id(mock_id)
                if mock:
                    return {
                        "id": mock.id,
                        "title": mock.title,
                        "description": mock.description,
                        "questions": mock.questions,
                        "price_credits": mock.price_credits,
                        "explanation_enabled": mock.explanation_enabled,
                        "time_limit_minutes": mock.time_limit_minutes,
                        "category": mock.category
                    }
                else:
                    raise Exception("Mock not found")
                    
            else:
                # Return empty response for unhandled endpoints
                return {"message": "Demo mode - endpoint not implemented", "data": []}
                
        except Exception as e:
            raise Exception(f"Demo API Error: {str(e)}")
    
    async def get_file(self, endpoint: str, params: Dict = None) -> bytes:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=self.headers,
                timeout=60.0
            )
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")

api_client = APIClient()

# Helper functions
def run_async(coro):
    """Run async function in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def format_score_color(score: float) -> str:
    """Return CSS class based on score"""
    if score >= 80:
        return "score-excellent"
    elif score >= 60:
        return "score-good"
    else:
        return "score-poor"

def display_question(question: Dict, question_num: int, user_answer: Optional[int] = None, show_correct: bool = False) -> Optional[int]:
    """Display a question with choices"""
    st.markdown(f"""
    <div class="question-container">
        <h4>Question {question_num}</h4>
        <p>{question['question']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    choices = question['choices']
    choice_labels = [f"{chr(65 + i)}. {choice}" for i, choice in enumerate(choices)]
    
    if show_correct:
        # Show results mode
        correct_index = question['correct_index']
        for i, choice in enumerate(choice_labels):
            if i == correct_index:
                st.success(f"✅ {choice} (Correct Answer)")
            elif user_answer is not None and i == user_answer and i != correct_index:
                st.error(f"❌ {choice} (Your Answer)")
            else:
                st.write(choice)
        return user_answer
    else:
        # Question mode
        selected = st.radio(
            f"Select your answer for Question {question_num}:",
            options=list(range(len(choices))),
            format_func=lambda x: choice_labels[x],
            index=user_answer if user_answer is not None else 0,
            key=f"q_{question_num}"
        )
        return selected

# Authentication functions
def show_login_page():
    """Display login page"""
    st.markdown('<h1 class="main-header">Welcome to MockExamify</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Login to Your Account")
        
        # Add HTML to enable browser password saving
        st.markdown("""
        <script>
        // Add autocomplete attributes to form inputs when they're rendered
        setTimeout(function() {
            const inputs = document.querySelectorAll('input[data-testid="stTextInput"] input');
            if (inputs.length >= 2) {
                inputs[0].setAttribute('autocomplete', 'email');
                inputs[0].setAttribute('name', 'email');
                inputs[1].setAttribute('autocomplete', 'current-password');
                inputs[1].setAttribute('name', 'password');
            }
        }, 100);
        </script>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email", 
                                 placeholder="your.email@example.com", 
                                 key="login_email",
                                 value=st.session_state.last_email)
            password = st.text_input("Password", type="password", key="login_password")
            
            login_btn = st.form_submit_button("Login", use_container_width=True)
            
        # Handle login attempts
        if login_btn and email and password:
            try:
                with st.spinner("Logging in..."):
                    result = run_async(api_client.post("/api/auth/login", {
                        "email": email,
                        "password": password
                    }))
                
                # Remember this email for next time
                st.session_state.last_email = email
                
                st.session_state.user_token = result["token"]
                st.session_state.authenticated = True
                api_client.set_auth_token(result["token"])
                
                # Use login response data instead of fetching profile
                st.session_state.current_user = {
                    "id": result["user_id"],
                    "email": result["email"],
                    "role": result["role"],
                    "credits_balance": int(result.get("credits_balance", 0))
                }
                
                st.success("Login successful!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
        elif login_btn:
            st.error("Please fill in all fields")
        
        st.markdown("---")
        st.markdown("### New to MockExamify?")
        
        with st.form("register_form"):
            reg_email = st.text_input("Email", placeholder="your.email@example.com", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")
            register_btn = st.form_submit_button("Create Account", use_container_width=True)
            
        if register_btn:
            if reg_email and reg_password and reg_password_confirm:
                if reg_password != reg_password_confirm:
                    st.error("Passwords do not match")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    try:
                        with st.spinner("Creating account..."):
                            result = run_async(api_client.post("/api/auth/register", {
                                "email": reg_email,
                                "password": reg_password
                            }))
                        
                        st.success("Account created successfully! Please login.")
                        
                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")
            else:
                st.error("Please fill in all fields")

def show_main_app():
    """Display main application"""
    # Sidebar
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.current_user['email']}")
        
        # Credit balance
        balance = st.session_state.current_user.get('credits_balance', 0)
        st.markdown(f"""
        <div class="credit-balance">
            💳 Credits: {balance}
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        page = st.selectbox(
            "Navigate to:",
            ["Dashboard", "Browse Mocks", "Take Exam", "My Attempts", "Buy Credits", "Support"]
        )
        
        if st.session_state.current_user.get('role') == 'admin':
            admin_page = st.selectbox(
                "Admin Panel:",
                ["None", "Dashboard", "Manage Mocks", "Users", "Tickets"]
            )
            if admin_page != "None":
                page = f"Admin {admin_page}"
        
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content
    if page == "Dashboard":
        show_dashboard()
    elif page == "Browse Mocks":
        show_browse_mocks()
    elif page == "Take Exam":
        show_take_exam()
    elif page == "My Attempts":
        show_my_attempts()
    elif page == "Buy Credits":
        show_buy_credits()
    elif page == "Support":
        show_support()
    elif page.startswith("Admin"):
        show_admin_panel(page.replace("Admin ", ""))

def show_dashboard():
    """Display user dashboard"""
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        attempts = run_async(api_client.get("/api/user/attempts"))
        mocks = run_async(api_client.get("/api/mocks"))
        
        with col1:
            st.metric("Total Attempts", len(attempts))
        
        with col2:
            avg_score = sum(a['score'] for a in attempts) / len(attempts) if attempts else 0
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col3:
            st.metric("Available Mocks", len(mocks))
        
        with col4:
            balance = st.session_state.current_user.get('credits_balance', 0)
            st.metric("Credits Balance", balance)
        
        # Recent attempts
        if attempts:
            st.markdown("### 📈 Recent Attempts")
            for attempt in attempts[:5]:
                mock = next((m for m in mocks if m['id'] == attempt['mock_id']), None)
                mock_title = mock['title'] if mock else "Unknown Mock"
                
                score_class = format_score_color(attempt['score'])
                st.markdown(f"""
                <div class="mock-card">
                    <h4>{mock_title}</h4>
                    <p><span class="{score_class}">Score: {attempt['score']:.1f}%</span> | 
                       Completed: {attempt['timestamp'][:10]}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Browse Mock Exams", use_container_width=True):
                st.session_state.page = "Browse Mocks"
                st.rerun()
        
        with col2:
            if st.button("Buy Credits", use_container_width=True):
                st.session_state.page = "Buy Credits"
                st.rerun()
        
        with col3:
            if st.button("View Attempts", use_container_width=True):
                st.session_state.page = "My Attempts"
                st.rerun()
                
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def show_browse_mocks():
    """Display available mock exams"""
    st.markdown('<h1 class="main-header">📚 Browse Mock Exams</h1>', unsafe_allow_html=True)
    
    try:
        mocks = run_async(api_client.get("/api/mocks"))
        
        if not mocks:
            st.info("No mock exams available at the moment.")
            return
        
        # Filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Search mocks...", placeholder="Enter keywords")
        with col2:
            category_filter = st.selectbox("Category", ["All"] + list(set(m.get('category', 'General') for m in mocks)))
        
        # Filter mocks
        filtered_mocks = mocks
        if search_term:
            filtered_mocks = [m for m in filtered_mocks if search_term.lower() in m['title'].lower() or search_term.lower() in m['description'].lower()]
        if category_filter != "All":
            filtered_mocks = [m for m in filtered_mocks if m.get('category') == category_filter]
        
        # Display mocks
        for mock in filtered_mocks:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="mock-card">
                        <h3>{mock['title']}</h3>
                        <p>{mock['description']}</p>
                        <p><strong>Questions:</strong> {len(mock['questions'])} | 
                           <strong>Category:</strong> {mock.get('category', 'General')} | 
                           <strong>Time Limit:</strong> {mock.get('time_limit_minutes', 'No limit')} min</p>
                        <p><strong>Cost:</strong> {mock['price_credits']} credit(s)</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"Start Exam", key=f"start_{mock['id']}"):
                        balance = st.session_state.current_user.get('credits_balance', 0)
                        if balance >= mock['price_credits']:
                            st.session_state.current_mock = mock
                            st.session_state.current_attempt = None
                            st.session_state.user_answers = {}
                            st.rerun()
                        else:
                            st.error("Insufficient credits! Please purchase more credits.")
                    
                    if st.button(f"Preview", key=f"preview_{mock['id']}"):
                        with st.expander(f"Preview: {mock['title']}"):
                            st.write(f"**Description:** {mock['description']}")
                            st.write(f"**Questions:** {len(mock['questions'])}")
                            st.write(f"**Sample Question:** {mock['questions'][0]['question'][:100]}...")
                            
    except Exception as e:
        st.error(f"Error loading mocks: {str(e)}")

def show_take_exam():
    """Display exam taking interface"""
    if not st.session_state.current_mock:
        st.info("Please select a mock exam from the Browse Mocks page.")
        return
    
    mock = st.session_state.current_mock
    
    if st.session_state.current_attempt:
        # Show results
        show_exam_results()
        return
    
    # Exam taking interface
    st.markdown(f'<h1 class="main-header">📝 {mock["title"]}</h1>', unsafe_allow_html=True)
    
    questions = mock['questions']
    total_questions = len(questions)
    
    # Progress bar
    progress = len(st.session_state.user_answers) / total_questions
    st.progress(progress)
    st.write(f"Progress: {len(st.session_state.user_answers)}/{total_questions} questions answered")
    
    # Time limit warning
    if mock.get('time_limit_minutes'):
        st.warning(f"⏰ Time Limit: {mock['time_limit_minutes']} minutes")
    
    # Questions
    st.markdown("### Questions")
    
    with st.form("exam_form"):
        answers = {}
        
        for i, question in enumerate(questions):
            question_num = i + 1
            current_answer = st.session_state.user_answers.get(i)
            
            answer = display_question(question, question_num, current_answer)
            answers[i] = answer
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.form_submit_button("Save Progress"):
                st.session_state.user_answers.update(answers)
                st.success("Progress saved!")
                st.rerun()
        
        with col2:
            if st.form_submit_button("Submit Exam", type="primary"):
                if len(answers) < total_questions:
                    st.error("Please answer all questions before submitting.")
                else:
                    try:
                        with st.spinner("Submitting exam..."):
                            # Start attempt (deduct credits)
                            run_async(api_client.post("/api/mocks/start-attempt", {"mock_id": mock['id']}))
                            
                            # Submit answers
                            result = run_async(api_client.post("/api/mocks/submit", {
                                "mock_id": mock['id'],
                                "user_answers": list(answers.values())
                            }))
                            
                            st.session_state.current_attempt = result
                            st.session_state.user_answers = answers
                            
                            # Update user credits
                            profile = run_async(api_client.get("/api/user/profile"))
                            st.session_state.current_user = profile
                            
                            st.success("Exam submitted successfully!")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Error submitting exam: {str(e)}")
        
        with col3:
            if st.form_submit_button("Cancel"):
                st.session_state.current_mock = None
                st.session_state.user_answers = {}
                st.rerun()

def show_exam_results():
    """Display exam results"""
    attempt = st.session_state.current_attempt
    mock = st.session_state.current_mock
    
    st.markdown('<h1 class="main-header">📊 Exam Results</h1>', unsafe_allow_html=True)
    
    # Results summary
    score_class = format_score_color(attempt['score'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Score", f"{attempt['score']:.1f}%")
    with col2:
        st.metric("Correct", f"{attempt['correct_answers']}/{attempt['total_questions']}")
    with col3:
        st.metric("Incorrect", attempt['total_questions'] - attempt['correct_answers'])
    with col4:
        st.metric("Completion", "100%")
    
    # Performance message
    score = attempt['score']
    if score >= 80:
        st.success("🎉 Excellent performance! You demonstrated strong understanding.")
    elif score >= 60:
        st.info("👍 Good work! You have a solid grasp of the material.")
    else:
        st.warning("📚 Consider reviewing the material before retaking.")
    
    # Question review
    st.markdown("### 📋 Question Review")
    
    questions = mock['questions']
    user_answers = attempt['user_answers']
    
    for i, question in enumerate(questions):
        question_num = i + 1
        user_answer = user_answers[i] if i < len(user_answers) else None
        
        # Question display
        display_question(question, question_num, user_answer, show_correct=True)
        
        # Show explanation if available and unlocked
        if question.get('explanation_template') and attempt.get('explanation_unlocked'):
            st.markdown(f"""
            <div class="explanation-box">
                <h5>💡 Explanation:</h5>
                <p>{question['explanation_template']}</p>
            </div>
            """, unsafe_allow_html=True)
        elif question.get('explanation_template') and not attempt.get('explanation_unlocked'):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info("💡 Detailed explanation available - Unlock for better understanding!")
            with col2:
                if st.button("Unlock Explanations ($2.99)", key=f"unlock_{i}"):
                    # TODO: Implement explanation unlock
                    st.info("Explanation unlock feature coming soon!")
        
        st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Download PDF", use_container_width=True):
            try:
                with st.spinner("Generating PDF..."):
                    pdf_content = run_async(api_client.get_file(
                        f"/api/mocks/{mock['id']}/pdf",
                        {
                            "attempt_id": attempt['id'],
                            "include_answers": True,
                            "include_explanations": attempt.get('explanation_unlocked', False)
                        }
                    ))
                
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_content,
                    file_name=f"exam_results_{mock['title'].replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
    
    with col2:
        if st.button("Take Another Exam", use_container_width=True):
            st.session_state.current_mock = None
            st.session_state.current_attempt = None
            st.session_state.user_answers = {}
            st.rerun()
    
    with col3:
        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state.current_mock = None
            st.session_state.current_attempt = None
            st.session_state.user_answers = {}
            st.rerun()

def show_my_attempts():
    """Display user's exam attempts"""
    st.markdown('<h1 class="main-header">📈 My Attempts</h1>', unsafe_allow_html=True)
    
    try:
        attempts = run_async(api_client.get("/api/user/attempts"))
        mocks = run_async(api_client.get("/api/mocks"))
        
        if not attempts:
            st.info("You haven't taken any exams yet. Browse available mocks to get started!")
            return
        
        # Summary stats
        total_attempts = len(attempts)
        avg_score = sum(a['score'] for a in attempts) / total_attempts
        best_score = max(a['score'] for a in attempts)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Attempts", total_attempts)
        with col2:
            st.metric("Average Score", f"{avg_score:.1f}%")
        with col3:
            st.metric("Best Score", f"{best_score:.1f}%")
        
        # Attempts table
        st.markdown("### Attempt History")
        
        for attempt in attempts:
            mock = next((m for m in mocks if m['id'] == attempt['mock_id']), None)
            mock_title = mock['title'] if mock else "Unknown Mock"
            
            with st.expander(f"{mock_title} - {attempt['score']:.1f}% ({attempt['timestamp'][:10]})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Score:** {attempt['score']:.1f}%")
                    st.write(f"**Correct Answers:** {attempt['correct_answers']}/{attempt['total_questions']}")
                    st.write(f"**Date:** {attempt['timestamp']}")
                    st.write(f"**Explanations Unlocked:** {'Yes' if attempt.get('explanation_unlocked') else 'No'}")
                
                with col2:
                    if st.button(f"View Details", key=f"details_{attempt['id']}"):
                        if mock:
                            st.session_state.current_mock = mock
                            st.session_state.current_attempt = attempt
                            st.rerun()
                    
                    if st.button(f"Download PDF", key=f"pdf_{attempt['id']}"):
                        try:
                            with st.spinner("Generating PDF..."):
                                pdf_content = run_async(api_client.get_file(
                                    f"/api/mocks/{attempt['mock_id']}/pdf",
                                    {
                                        "attempt_id": attempt['id'],
                                        "include_answers": True,
                                        "include_explanations": attempt.get('explanation_unlocked', False)
                                    }
                                ))
                            
                            st.download_button(
                                label="📄 Download",
                                data=pdf_content,
                                file_name=f"exam_{mock_title.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key=f"download_{attempt['id']}"
                            )
                            
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            
    except Exception as e:
        st.error(f"Error loading attempts: {str(e)}")

def show_buy_credits():
    """Display credit purchase page"""
    st.markdown('<h1 class="main-header">💳 Buy Credits</h1>', unsafe_allow_html=True)
    
    try:
        credit_packs = run_async(api_client.get("/api/stripe/credit-packs"))
        
        st.markdown("### Choose Your Credit Pack")
        st.write("Credits are used to take mock exams. Each exam typically costs 1 credit.")
        
        # Display credit packs
        cols = st.columns(len(credit_packs))
        
        for i, pack in enumerate(credit_packs):
            with cols[i]:
                is_popular = pack.get('popular', False)
                
                if is_popular:
                    st.markdown("🌟 **MOST POPULAR** 🌟")
                
                st.markdown(f"""
                <div class="mock-card" style="text-align: center; {'border: 2px solid #ff7b7b;' if is_popular else ''}">
                    <h3>{pack['name']}</h3>
                    <h2>${pack['price_cents'] / 100:.2f}</h2>
                    <p>{pack['credits']} Credits</p>
                    <p>${pack['price_cents'] / 100 / pack['credits']:.2f} per credit</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Buy {pack['name']}", key=f"buy_{pack['id']}", use_container_width=True):
                    try:
                        with st.spinner("Creating checkout session..."):
                            success_url = "http://localhost:8501/?payment=success"
                            cancel_url = "http://localhost:8501/?payment=cancelled"
                            
                            result = run_async(api_client.post("/api/stripe/create-checkout", {
                                "pack_id": pack['id'],
                                "success_url": success_url,
                                "cancel_url": cancel_url
                            }))
                        
                        st.success("Redirecting to payment...")
                        st.markdown(f'[Complete Purchase]({result["checkout_url"]})')
                        
                    except Exception as e:
                        st.error(f"Error creating checkout: {str(e)}")
        
        # Payment status messages
        query_params = st.query_params
        if "payment" in query_params:
            if query_params["payment"] == "success":
                st.success("🎉 Payment successful! Your credits have been added to your account.")
                # Refresh user data
                profile = run_async(api_client.get("/api/user/profile"))
                st.session_state.current_user = profile
            elif query_params["payment"] == "cancelled":
                st.info("Payment was cancelled. You can try again anytime.")
                
    except Exception as e:
        st.error(f"Error loading credit packs: {str(e)}")

def show_support():
    """Display support page"""
    st.markdown('<h1 class="main-header">🎧 Support</h1>', unsafe_allow_html=True)
    
    # FAQ Section
    st.markdown("### ❓ Frequently Asked Questions")
    
    with st.expander("How do credits work?"):
        st.write("""
        Credits are used to take mock exams. Each exam attempt typically costs 1 credit.
        You can purchase credits in packs, and they never expire. Credits are deducted
        when you start an exam, not when you finish it.
        """)
    
    with st.expander("Can I retake an exam?"):
        st.write("""
        Yes! You can retake any exam as many times as you want. Each attempt will cost
        the specified number of credits. Your highest score will be displayed in your
        dashboard.
        """)
    
    with st.expander("What are explanations?"):
        st.write("""
        Explanations provide detailed reasoning for each question's correct answer.
        Some exams include free explanations, while others may require an additional
        purchase to unlock the explanations.
        """)
    
    with st.expander("How do I download my results?"):
        st.write("""
        After completing an exam, you can download a PDF of your results from the
        results page or from your "My Attempts" section. The PDF includes your
        answers, correct answers, and explanations (if unlocked).
        """)
    
    # Contact form
    st.markdown("### 📧 Contact Support")
    st.write("Can't find what you're looking for? Send us a message!")
    
    with st.form("support_form"):
        subject = st.selectbox(
            "Subject",
            ["General Question", "Technical Issue", "Billing Question", "Feature Request", "Other"]
        )
        message = st.text_area(
            "Message",
            placeholder="Please describe your question or issue in detail...",
            height=150
        )
        
        if st.form_submit_button("Send Message"):
            if subject and message:
                try:
                    with st.spinner("Sending message..."):
                        run_async(api_client.post("/api/tickets", {
                            "subject": subject,
                            "message": message
                        }))
                    
                    st.success("Message sent successfully! We'll get back to you soon.")
                    
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")
            else:
                st.error("Please fill in all fields")

def show_admin_panel(panel_type):
    """Display admin panel"""
    st.markdown(f'<h1 class="main-header">🛠️ Admin {panel_type}</h1>', unsafe_allow_html=True)
    
    if panel_type == "Dashboard":
        show_admin_dashboard()
    elif panel_type == "Manage Mocks":
        show_admin_mocks()
    elif panel_type == "Users":
        show_admin_users()
    elif panel_type == "Tickets":
        show_admin_tickets()

def show_admin_dashboard():
    """Display admin dashboard"""
    try:
        stats = run_async(api_client.get("/api/admin/dashboard"))
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", stats['total_users'])
        with col2:
            st.metric("Total Mocks", stats['total_mocks'])
        with col3:
            st.metric("Total Attempts", stats['total_attempts'])
        with col4:
            st.metric("Revenue", f"${stats['revenue_cents'] / 100:.2f}")
        
        # Quick actions
        st.markdown("### Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Create New Mock", use_container_width=True):
                st.session_state.admin_action = "create_mock"
                st.rerun()
        
        with col2:
            if st.button("Generate AI Mock", use_container_width=True):
                st.session_state.admin_action = "ai_mock"
                st.rerun()
        
        with col3:
            if st.button("View All Users", use_container_width=True):
                st.session_state.admin_action = "users"
                st.rerun()
                
    except Exception as e:
        st.error(f"Error loading admin dashboard: {str(e)}")

def show_admin_mocks():
    """Display mock management interface"""
    st.markdown("### 📚 Mock Management")
    
    # Generate AI Mock
    with st.expander("🤖 Generate AI Mock"):
        with st.form("ai_mock_form"):
            topic = st.text_input("Topic", placeholder="e.g., Python Programming, Mathematics")
            col1, col2 = st.columns(2)
            with col1:
                num_questions = st.number_input("Number of Questions", min_value=5, max_value=50, value=10)
            with col2:
                difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
            
            if st.form_submit_button("Generate Mock"):
                if topic:
                    try:
                        with st.spinner("Generating mock with AI..."):
                            result = run_async(api_client.post("/api/admin/mocks/generate", {
                                "topic": topic,
                                "num_questions": num_questions,
                                "difficulty": difficulty
                            }))
                        
                        st.success(f"Generated mock: {result['title']}")
                        
                    except Exception as e:
                        st.error(f"Error generating mock: {str(e)}")
                else:
                    st.error("Please enter a topic")

def show_admin_users():
    """Display user management interface"""
    try:
        users = run_async(api_client.get("/api/admin/users"))
        
        st.markdown(f"### 👥 Users ({len(users)})")
        
        for user in users:
            with st.expander(f"{user['email']} - {user['role']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Credits:** {user['credits_balance']}")
                    st.write(f"**Role:** {user['role']}")
                    st.write(f"**Joined:** {user['created_at'][:10]}")
                
                with col2:
                    new_role = st.selectbox(
                        "Change Role",
                        ["user", "admin"],
                        index=0 if user['role'] == 'user' else 1,
                        key=f"role_{user['id']}"
                    )
                    
                    if st.button("Update Role", key=f"update_{user['id']}"):
                        # TODO: Implement role update
                        st.success("Role updated (feature coming soon)")
                        
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")

def show_admin_tickets():
    """Display ticket management interface"""
    try:
        tickets = run_async(api_client.get("/api/admin/tickets"))
        
        st.markdown(f"### 🎫 Support Tickets ({len(tickets)})")
        
        for ticket in tickets:
            status_color = {"open": "🔴", "in_progress": "🟡", "closed": "🟢"}
            
            with st.expander(f"{status_color.get(ticket['status'], '⚪')} {ticket['subject']}"):
                st.write(f"**From:** {ticket['user_id']}")
                st.write(f"**Status:** {ticket['status']}")
                st.write(f"**Created:** {ticket['created_at'][:10]}")
                st.write(f"**Message:** {ticket['message']}")
                
                new_status = st.selectbox(
                    "Update Status",
                    ["open", "in_progress", "closed"],
                    index=["open", "in_progress", "closed"].index(ticket['status']),
                    key=f"status_{ticket['id']}"
                )
                
                if st.button("Update Status", key=f"update_ticket_{ticket['id']}"):
                    # TODO: Implement status update
                    st.success("Status updated (feature coming soon)")
                    
    except Exception as e:
        st.error(f"Error loading tickets: {str(e)}")

# Main application logic
def main():
    """Main application entry point"""
    # Show demo mode banner if in demo mode
    if config.DEMO_MODE:
        st.info("🎯 **MockExamify Demo Mode** - Using mock data. No external services required! "
                "Login with: admin@demo.com/admin123 or user@demo.com/user123")
    
    # Initialize API client with token if available
    if st.session_state.user_token:
        api_client.set_auth_token(st.session_state.user_token)
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main()