"""
Dashboard page for MockExamify
Shows user's credit balance, available mock exams, and navigation
"""
import streamlit as st
import httpx
import asyncio
from typing import List, Dict, Any
import config
from auth_utils import AuthUtils, run_async

def show_dashboard():
    """Display the main dashboard"""
    auth = AuthUtils(config.API_BASE_URL)
    
    if not auth.is_authenticated():
        st.error("Please log in to access the dashboard")
        st.stop()
    
    user = auth.get_current_user()
    if not user:
        st.error("User data not found")
        st.stop()
    
    # Header
    st.markdown("# 📊 Dashboard")
    st.markdown(f"Welcome back, **{user.get('email', 'User')}**!")
    
    # Credit balance section
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        credits = user.get('credits_balance', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #ff7b7b, #ffb347); 
                    padding: 1rem; border-radius: 0.5rem; color: white; margin-bottom: 1rem;">
            <h3 style="margin: 0;">💰 Credits Balance: {credits}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("💳 Purchase Credits", use_container_width=True):
            st.session_state.page = "purchase_credits"
            st.rerun()
    
    with col3:
        if st.button("📈 Past Attempts", use_container_width=True):
            st.session_state.page = "past_attempts"
            st.rerun()
    
    # Admin section
    if auth.is_admin():
        st.markdown("---")
        st.markdown("## 👨‍💼 Admin Panel")
        
        admin_col1, admin_col2, admin_col3 = st.columns(3)
        
        with admin_col1:
            if st.button("📤 Upload Mock Exam", use_container_width=True):
                st.session_state.page = "admin_upload"
                st.rerun()
        
        with admin_col2:
            if st.button("📝 Manage Mock Exams", use_container_width=True):
                st.session_state.page = "admin_manage"
                st.rerun()
        
        with admin_col3:
            if st.button("🎫 View Support Tickets", use_container_width=True):
                st.session_state.page = "admin_tickets"
                st.rerun()
    
    st.markdown("---")
    st.markdown("## 📚 Available Mock Exams")
    
    # Load available mock exams
    try:
        mocks = run_async(load_mock_exams())
        if not mocks:
            st.info("No mock exams available at the moment. Check back soon!")
            return
        
        # Display mock exams in a grid
        for i in range(0, len(mocks), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(mocks):
                    mock = mocks[i + j]
                    show_mock_card(mock, col, credits)
    
    except Exception as e:
        st.error(f"Error loading mock exams: {str(e)}")

def show_mock_card(mock: Dict[str, Any], container, user_credits: int):
    """Display a single mock exam card"""
    with container:
        with st.container():
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem;">
                <h4>{mock.get('title', 'Untitled Mock')}</h4>
                <p>{mock.get('description', 'No description available')}</p>
                <p><strong>Cost:</strong> {mock.get('price_credits', 1)} credits</p>
                <p><strong>Questions:</strong> {len(mock.get('questions', []))} questions</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                can_afford = user_credits >= mock.get('price_credits', 1)
                if st.button(
                    "🚀 Start Exam" if can_afford else "❌ Insufficient Credits",
                    key=f"start_{mock.get('id')}",
                    disabled=not can_afford,
                    use_container_width=True
                ):
                    st.session_state.selected_mock_id = mock.get('id')
                    st.session_state.page = "exam"
                    st.rerun()
            
            with col2:
                if st.button(
                    "📄 View Details",
                    key=f"details_{mock.get('id')}",
                    use_container_width=True
                ):
                    st.session_state.selected_mock_id = mock.get('id')
                    st.session_state.page = "mock_details"
                    st.rerun()

async def load_mock_exams() -> List[Dict[str, Any]]:
    """Load available mock exams from the API or database"""
    try:
        # Check if we should use direct database access
        if config.DEMO_MODE or not config.API_BASE_URL.startswith('http://localhost'):
            # Use direct database access for Streamlit Cloud or demo mode
            from db import db
            mocks = await db.get_all_mocks(active_only=True)
            return mocks
        
        # Use API for local development with running backend
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Add authentication header if available
            headers = {}
            if "user_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.user_token}"
            
            response = await client.get(
                f"{config.API_BASE_URL}/api/mocks",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Fallback to direct database access if API fails
                from db import db
                return await db.get_all_mocks(active_only=True)
                
    except Exception as e:
        # Fallback to direct database access on any error
        try:
            from db import db
            return await db.get_all_mocks(active_only=True)
        except Exception as db_error:
            st.error(f"Error loading mock exams: {str(e)}")
            return []

def show_past_attempts():
    """Show user's past exam attempts"""
    st.markdown("# 📈 Past Attempts")
    
    try:
        attempts = run_async(load_past_attempts())
        
        if not attempts:
            st.info("You haven't taken any exams yet. Start with your first mock exam!")
            if st.button("🏠 Back to Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()
            return
        
        # Display attempts in a table
        for attempt in attempts:
            with st.expander(f"📝 {attempt.get('mock_title', 'Unknown Mock')} - Score: {attempt.get('score', 0)}%"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Score", f"{attempt.get('score', 0)}%")
                
                with col2:
                    st.metric("Questions", f"{attempt.get('total_questions', 0)}")
                
                with col3:
                    completed_at = attempt.get('completed_at', '')
                    if completed_at:
                        st.metric("Completed", completed_at[:10])  # Show date only
                
                if st.button(f"📄 View Details", key=f"view_{attempt.get('id')}"):
                    st.session_state.selected_attempt_id = attempt.get('id')
                    st.session_state.page = "attempt_details"
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error loading past attempts: {str(e)}")
    
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

async def load_past_attempts() -> List[Dict[str, Any]]:
    """Load user's past exam attempts"""
    try:
        # Check if we should use direct database access
        if config.DEMO_MODE or not config.API_BASE_URL.startswith('http://localhost'):
            # Use direct database access for Streamlit Cloud or demo mode
            from db import db
            user_id = st.session_state.current_user.get("id")
            if user_id:
                attempts = await db.get_user_attempts(user_id)
                return attempts
            return []
        
        # Use API for local development with running backend
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {}
            if "user_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.user_token}"
            
            response = await client.get(
                f"{config.API_BASE_URL}/api/user/attempts",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Fallback to direct database access if API fails
                from db import db
                user_id = st.session_state.current_user.get("id")
                if user_id:
                    return await db.get_user_attempts(user_id)
                return []
                
    except Exception as e:
        # Fallback to direct database access on any error
        try:
            from db import db
            user_id = st.session_state.current_user.get("id")
            if user_id:
                return await db.get_user_attempts(user_id)
            return []
        except Exception as db_error:
            return []