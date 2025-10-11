"""
Enhanced Dashboard page for MockExamify
Comprehensive user dashboard with statistics, quick actions, and exam management
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    from auth_utils import AuthUtils, run_async
    import config
    AUTH_AVAILABLE = True
except ImportError as e:
    st.error(f"Configuration error: {e}")
    AUTH_AVAILABLE = False
    # Provide fallback
    class AuthUtils:
        def __init__(self, *args, **kwargs):
            pass
        def is_authenticated(self):
            return False
        def get_current_user(self):
            return None
    def run_async(func):
        return None

def show_dashboard():
    """Display the enhanced main dashboard"""
    if not AUTH_AVAILABLE:
        st.error("Dashboard configuration error. Please check your environment setup.")
        st.info("This might be due to missing configuration files or dependencies.")
        return
    
    try:
        auth = AuthUtils(config.API_BASE_URL)
    except Exception as e:
        st.error(f"Authentication system error: {e}")
        return
    
    if not auth.is_authenticated():
        st.error("Please log in to access the dashboard")
        st.stop()
    
    user = auth.get_current_user()
    if not user:
        st.error("User data not found")
        st.stop()
    
    # Dashboard header with personalized greeting
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning"
    elif current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    user_name = user.get('name', user.get('email', 'User')).split('@')[0]
    st.markdown(f"# 📊 Dashboard")
    st.markdown(f"*{greeting}, **{user_name}**! Ready to boost your exam performance?*")
    
    # Quick stats overview
    show_quick_stats(user)
    
    # Action buttons section
    show_quick_actions()
    
    # Admin panel (if user is admin)
    if auth.is_admin():
        show_admin_panel()
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Available Exams", "📈 Your Progress", "🔥 Recent Activity"])
    
    with tab1:
        show_available_exams(user)
    
    with tab2:
        show_progress_overview(user)
    
    with tab3:
        show_recent_activity(user)

def show_quick_stats(user: Dict[str, Any]):
    """Display quick statistics cards"""
    st.markdown("## 📊 Quick Overview")
    
    # Load user statistics
    stats = run_async(load_user_statistics(user['id']))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        credits = user.get('credits_balance', 0)
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 1rem;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">{credits}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">💰 Credits Available</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_attempts = stats.get('total_attempts', 0)
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 1.5rem;
            border-radius: 1rem;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">{total_attempts}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">📝 Exams Taken</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_score = stats.get('average_score', 0)
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 1.5rem;
            border-radius: 1rem;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">{avg_score:.1f}%</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">📊 Average Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        streak = stats.get('current_streak', 0)
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            padding: 1.5rem;
            border-radius: 1rem;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">{streak}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">🔥 Day Streak</div>
        </div>
        """, unsafe_allow_html=True)

def show_quick_actions():
    """Display quick action buttons"""
    st.markdown("---")
    st.markdown("## ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💳 Purchase Credits", use_container_width=True, type="primary"):
            st.session_state.page = "purchase_credits"
            st.rerun()
    
    with col2:
        if st.button("📈 View Progress", use_container_width=True):
            st.session_state.page = "past_attempts"
            st.rerun()
    
    with col3:
        if st.button("💬 Contact Support", use_container_width=True):
            st.session_state.page = "contact_support"
            st.rerun()
    
    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.show_settings = True

def show_admin_panel():
    """Display admin panel for admin users"""
    st.markdown("---")
    st.markdown("## 👨‍💼 Admin Panel")
    
    admin_col1, admin_col2, admin_col3, admin_col4 = st.columns(4)
    
    with admin_col1:
        if st.button("📤 Upload Mock Exam", use_container_width=True):
            st.session_state.page = "admin_upload"
            st.rerun()
    
    with admin_col2:
        if st.button("📝 Manage Exams", use_container_width=True):
            st.session_state.page = "admin_manage"
            st.rerun()
    
    with admin_col3:
        if st.button("🎫 Support Tickets", use_container_width=True):
            st.session_state.page = "admin_tickets"
            st.rerun()
    
    with admin_col4:
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.page = "admin_analytics"
            st.rerun()

def show_available_exams(user: Dict[str, Any]):
    """Display available mock exams with enhanced filtering"""
    st.markdown("### 🎯 Available Mock Exams")
    
    # Load mock exams
    try:
        mocks = run_async(load_mock_exams())
        
        if not mocks:
            show_no_exams_message()
            return
        
        # Filter and search options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Search exams", placeholder="Search by title or topic...")
        
        with col2:
            difficulty_filter = st.selectbox(
                "📊 Difficulty",
                ["All", "Easy", "Medium", "Hard"]
            )
        
        with col3:
            price_filter = st.selectbox(
                "💰 Price Range",
                ["All", "1 Credit", "2-3 Credits", "4+ Credits"]
            )
        
        # Apply filters
        filtered_mocks = apply_exam_filters(mocks, search_term, difficulty_filter, price_filter)
        
        if not filtered_mocks:
            st.info("No exams match your search criteria. Try adjusting the filters.")
            return
        
        # Display filtered mocks
        st.markdown(f"*Showing {len(filtered_mocks)} exams*")
        
        # Display in grid layout
        for i in range(0, len(filtered_mocks), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(filtered_mocks):
                    mock = filtered_mocks[i + j]
                    show_enhanced_mock_card(mock, col, user)
    
    except Exception as e:
        st.error(f"Error loading mock exams: {str(e)}")

def mock_to_dict(mock) -> Dict[str, Any]:
    """Convert Mock object to dictionary for backward compatibility"""
    if hasattr(mock, 'to_dict'):
        return mock.to_dict()
    elif hasattr(mock, '__dict__'):
        # Handle Pydantic models
        return {
            'id': getattr(mock, 'id', ''),
            'title': getattr(mock, 'title', 'Untitled Mock'),
            'description': getattr(mock, 'description', 'No description'),
            'questions': getattr(mock, 'questions', []),
            'questions_json': getattr(mock, 'questions', []),
            'price_credits': getattr(mock, 'price_credits', 1),
            'explanation_enabled': getattr(mock, 'explanation_enabled', True),
            'time_limit_minutes': getattr(mock, 'time_limit_minutes', 60),
            'category': getattr(mock, 'category', 'General'),
            'difficulty': getattr(mock, 'difficulty', 'medium'),
            'is_active': getattr(mock, 'is_active', True),
            'created_at': getattr(mock, 'created_at', None),
        }
    else:
        # Already a dictionary
        return mock


def show_enhanced_mock_card(mock_obj: Any, container, user: Dict[str, Any]):
    """Display an enhanced mock exam card"""
    # Convert Mock object to dictionary
    mock = mock_to_dict(mock_obj)
    
    with container:
        user_credits = user.get('credits_balance', 0)
        price = mock.get('price_credits', 1)
        can_afford = user_credits >= price
        
        # Determine difficulty color
        difficulty = mock.get('difficulty', 'medium').lower()
        difficulty_colors = {
            'easy': '#27ae60',
            'medium': '#f39c12',
            'hard': '#e74c3c'
        }
        difficulty_color = difficulty_colors.get(difficulty, '#95a5a6')
        
        st.markdown(f"""
        <div style="
            border: 1px solid #e1e5e9;
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.2s ease;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #2c3e50; font-size: 1.1rem;">
                    {mock.get('title', 'Untitled Mock')}
                </h4>
                <div style="
                    background: {difficulty_color};
                    color: white;
                    padding: 0.3rem 0.8rem;
                    border-radius: 1rem;
                    font-size: 0.8rem;
                    font-weight: bold;
                ">
                    {difficulty.title()}
                </div>
            </div>
            
            <p style="color: #7f8c8d; margin-bottom: 1rem; font-size: 0.9rem;">
                {mock.get('description', 'No description available')[:100]}{'...' if len(mock.get('description', '')) > 100 else ''}
            </p>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div style="display: flex; gap: 1rem;">
                    <span style="color: #34495e; font-size: 0.9rem;">
                        <strong>💰 {price}</strong> credit{'s' if price != 1 else ''}
                    </span>
                    <span style="color: #34495e; font-size: 0.9rem;">
                        <strong>📝 {len(mock.get('questions_json', mock.get('questions', [])))}</strong> questions
                    </span>
                </div>
                <span style="color: #7f8c8d; font-size: 0.8rem;">
                    ⏱️ {mock.get('time_limit_minutes', 60)} min
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            button_text = "🚀 Start Exam" if can_afford else f"❌ Need {price - user_credits} more credits"
            button_type = "primary" if can_afford else "secondary"
            
            if st.button(
                button_text,
                key=f"start_{mock.get('id')}",
                disabled=not can_afford,
                use_container_width=True,
                type=button_type
            ):
                st.session_state.current_mock_id = mock.get('id')
                st.session_state.page = "exam"
                st.rerun()
        
        with col2:
            if st.button(
                "👁️ Preview",
                key=f"preview_{mock.get('id')}",
                use_container_width=True
            ):
                st.session_state.preview_mock = mock

def show_progress_overview(user: Dict[str, Any]):
    """Display user progress overview"""
    st.markdown("### 📈 Your Progress")
    
    try:
        stats = run_async(load_user_statistics(user['id']))
        attempts = run_async(load_recent_attempts(user['id'], limit=10))
        
        if not attempts:
            st.info("Complete your first exam to see your progress here!")
            return
        
        # Progress metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Performance Trends")
            
            # Create score trend chart
            if len(attempts) >= 2:
                scores = [attempt.get('score', 0) for attempt in reversed(attempts)]
                dates = [f"Exam {i+1}" for i in range(len(scores))]
                
                chart_data = {'Exam': dates, 'Score (%)': scores}
                st.line_chart(chart_data, x='Exam', y='Score (%)')
            else:
                st.info("Take more exams to see your progress trend!")
        
        with col2:
            st.markdown("#### 🎯 Improvement Areas")
            
            weak_areas = stats.get('weak_areas', [])
            strong_areas = stats.get('strong_areas', [])
            
            if weak_areas:
                st.markdown("**Areas to focus on:**")
                for area in weak_areas:
                    st.markdown(f"📚 {area}")
            
            if strong_areas:
                st.markdown("**Your strengths:**")
                for area in strong_areas[:3]:  # Show top 3
                    st.markdown(f"✅ {area}")
        
        # Recent exam performance
        st.markdown("#### 🎯 Recent Performance")
        
        for attempt in attempts[:5]:  # Show last 5
            score = attempt.get('score', 0)
            title = attempt.get('mock_title', 'Unknown Exam')
            date = attempt.get('created_at', '')
            
            # Format date
            try:
                date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%b %d, %Y')
            except:
                formatted_date = 'Unknown date'
            
            # Score color
            if score >= 80:
                score_color = "#27ae60"
                icon = "🏆"
            elif score >= 60:
                score_color = "#3498db"
                icon = "✅"
            else:
                score_color = "#e74c3c"
                icon = "📚"
            
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.8rem;
                margin-bottom: 0.5rem;
                border: 1px solid #e1e5e9;
                border-radius: 0.5rem;
                background: #f8f9fa;
            ">
                <div>
                    <strong>{icon} {title}</strong><br>
                    <small style="color: #7f8c8d;">{formatted_date}</small>
                </div>
                <div style="color: {score_color}; font-weight: bold; font-size: 1.2rem;">
                    {score:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading progress data: {str(e)}")

def show_recent_activity(user: Dict[str, Any]):
    """Display recent user activity"""
    st.markdown("### 🔥 Recent Activity")
    
    try:
        activities = run_async(load_user_activities(user['id']))
        
        if not activities:
            st.info("No recent activity. Start taking exams to see your activity here!")
            return
        
        for activity in activities:
            activity_type = activity.get('type', 'unknown')
            created_at = activity.get('created_at', '')
            description = activity.get('description', '')
            
            # Format date
            try:
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_ago = get_time_ago(date_obj)
            except:
                time_ago = 'Some time ago'
            
            # Activity icons
            icons = {
                'exam_completed': '📝',
                'credits_purchased': '💳',
                'explanation_unlocked': '💡',
                'pdf_downloaded': '📄',
                'login': '🔐'
            }
            
            icon = icons.get(activity_type, '📌')
            
            st.markdown(f"""
            <div style="
                display: flex;
                align-items: center;
                padding: 1rem;
                margin-bottom: 0.5rem;
                border-left: 3px solid #3498db;
                background: #f8f9fa;
                border-radius: 0 0.5rem 0.5rem 0;
            ">
                <div style="font-size: 1.5rem; margin-right: 1rem;">{icon}</div>
                <div>
                    <div style="font-weight: bold; color: #2c3e50;">{description}</div>
                    <div style="color: #7f8c8d; font-size: 0.9rem;">{time_ago}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading activity data: {str(e)}")

def show_no_exams_message():
    """Show message when no exams are available"""
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📚</div>
        <h3>No Mock Exams Available</h3>
        <p style="color: #666; margin-bottom: 2rem;">
            Check back soon for new mock exams, or contact our team if you're looking for specific content.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("💬 Contact Support", use_container_width=True):
        st.session_state.page = "contact_support"
        st.rerun()

def apply_exam_filters(mocks: List[Any], search_term: str, 
                      difficulty_filter: str, price_filter: str) -> List[Dict[str, Any]]:
    """Apply filters to exam list"""
    # Convert all mocks to dictionaries first
    mock_dicts = [mock_to_dict(mock) for mock in mocks]
    filtered = mock_dicts.copy()
    
    # Search filter
    if search_term:
        filtered = [
            mock for mock in filtered
            if search_term.lower() in mock.get('title', '').lower() or
               search_term.lower() in mock.get('description', '').lower() or
               search_term.lower() in mock.get('topic', '').lower() or
               search_term.lower() in mock.get('category', '').lower()
        ]
    
    # Difficulty filter
    if difficulty_filter != "All":
        filtered = [
            mock for mock in filtered
            if mock.get('difficulty', '').lower() == difficulty_filter.lower()
        ]
    
    # Price filter
    if price_filter != "All":
        if price_filter == "1 Credit":
            filtered = [mock for mock in filtered if mock.get('price_credits', 1) == 1]
        elif price_filter == "2-3 Credits":
            filtered = [mock for mock in filtered if 2 <= mock.get('price_credits', 1) <= 3]
        elif price_filter == "4+ Credits":
            filtered = [mock for mock in filtered if mock.get('price_credits', 1) >= 4]
    
    return filtered

def get_time_ago(date_obj: datetime) -> str:
    """Get human-readable time ago string"""
    now = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
    diff = now - date_obj
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

# Enhanced async functions
async def load_mock_exams() -> List[Dict[str, Any]]:
    """Load available mock exams with enhanced fallback"""
    try:
        from db import db_manager as db
        mocks = await db.get_all_mocks(active_only=True)
        return mocks
    except Exception as e:
        st.error(f"Error loading mock exams: {str(e)}")
        return []

async def load_user_statistics(user_id: str) -> Dict[str, Any]:
    """Load comprehensive user statistics"""
    try:
        from db import db_manager as db
        return await db.get_user_statistics(user_id)
    except Exception as e:
        return {
            'total_attempts': 0,
            'average_score': 0,
            'current_streak': 0,
            'weak_areas': [],
            'strong_areas': []
        }

async def load_recent_attempts(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Load recent exam attempts"""
    try:
        from db import db_manager as db
        return await db.get_user_attempts(user_id, limit=limit)
    except Exception as e:
        return []

async def load_user_activities(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Load recent user activities"""
    try:
        from db import db_manager as db
        return await db.get_user_activities(user_id, limit=limit)
    except Exception as e:
        return []

# Handle modals and overlays
def handle_dashboard_modals():
    """Handle dashboard modals and overlays"""
    # Settings modal
    if st.session_state.get('show_settings'):
        with st.expander("⚙️ Settings", expanded=True):
            show_user_settings()
            
            if st.button("❌ Close Settings"):
                del st.session_state.show_settings
                st.rerun()
    
    # Mock preview modal
    if 'preview_mock' in st.session_state:
        mock = st.session_state.preview_mock
        
        with st.expander(f"👁️ Preview: {mock.get('title', 'Mock Exam')}", expanded=True):
            show_mock_preview(mock)
            
            if st.button("❌ Close Preview"):
                del st.session_state.preview_mock
                st.rerun()

def show_user_settings():
    """Show user settings panel"""
    st.markdown("### ⚙️ User Settings")
    
    # Email notifications
    email_notifications = st.checkbox("📧 Email notifications", value=True)
    
    # Theme preference
    theme = st.selectbox("🎨 Theme", ["Light", "Dark", "Auto"])
    
    # Timezone
    timezone = st.selectbox("🌍 Timezone", ["UTC", "EST", "PST", "GMT"])
    
    # Privacy settings
    st.markdown("#### 🔒 Privacy")
    public_profile = st.checkbox("Make my progress visible to others", value=False)
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")

def show_mock_preview(mock: Dict[str, Any]):
    """Show mock exam preview"""
    st.markdown(f"**Description:** {mock.get('description', 'No description')}")
    st.markdown(f"**Difficulty:** {mock.get('difficulty', 'Medium').title()}")
    st.markdown(f"**Questions:** {len(mock.get('questions_json', []))}")
    st.markdown(f"**Time Limit:** {mock.get('time_limit_minutes', 60)} minutes")
    st.markdown(f"**Cost:** {mock.get('price_credits', 1)} credits")
    
    # Show sample questions
    questions = mock.get('questions_json', mock.get('questions', []))
    if questions:
        st.markdown("#### 📝 Sample Questions:")
        
        for i, question in enumerate(questions[:3]):  # Show first 3 questions
            with st.expander(f"Question {i+1}"):
                st.markdown(f"**{question.get('question', '')}**")
                
                choices = question.get('choices', [])
                for j, choice in enumerate(choices):
                    st.markdown(f"{chr(65+j)}. {choice}")

# Run dashboard with modal handling
if __name__ == "__main__":
    show_dashboard()
    handle_dashboard_modals()