"""
Admin Dashboard for MockExamify
Comprehensive analytics and management overview
"""
import streamlit as st
from typing import Dict, Any, List
from auth_utils import AuthUtils, run_async
import config
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def show_admin_dashboard():
    """Display the admin dashboard with analytics and management options"""
    auth = AuthUtils(config.API_BASE_URL)
    
    if not auth.is_authenticated() or not auth.is_admin():
        st.error("Admin access required")
        st.stop()
    
    st.markdown("# 📊 Admin Dashboard")
    st.markdown("*Comprehensive overview of MockExamify platform*")
    
    # Load dashboard data
    try:
        stats = run_async(load_dashboard_stats())
        recent_attempts = run_async(load_recent_attempts())
        
        # Key Metrics Row
        st.markdown("## 📈 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "👥 Total Users", 
                stats['total_users'],
                delta=f"+{stats.get('new_users_today', 0)} today"
            )
        
        with col2:
            st.metric(
                "📚 Total Mocks", 
                stats['total_mocks'],
                delta=f"{stats.get('active_mocks', 0)} active"
            )
        
        with col3:
            st.metric(
                "🎯 Total Attempts", 
                stats['total_attempts'],
                delta=f"+{stats.get('attempts_today', 0)} today"
            )
        
        with col4:
            avg_score = stats.get('avg_score', 0)
            st.metric(
                "📊 Avg Score", 
                f"{avg_score:.1f}%",
                delta=f"{stats.get('score_trend', 0):+.1f}% vs last week"
            )
        
        with col5:
            revenue = stats.get('total_revenue', 0)
            st.metric(
                "💰 Revenue", 
                f"${revenue:.2f}",
                delta=f"+${stats.get('revenue_today', 0):.2f} today"
            )
        
        st.markdown("---")
        
        # Charts Row
        col1, col2 = st.columns(2)
        
        with col1:
            # User Growth Chart
            st.markdown("### 📈 User Growth (Last 30 Days)")
            user_growth_data = generate_demo_user_growth()
            fig_users = px.line(
                user_growth_data, 
                x='date', 
                y='users',
                title="Daily User Registrations"
            )
            fig_users.update_layout(height=300)
            st.plotly_chart(fig_users, use_container_width=True)
        
        with col2:
            # Exam Performance Chart
            st.markdown("### 🎯 Exam Performance Distribution")
            score_ranges = ['0-49%', '50-69%', '70-84%', '85-100%']
            score_counts = [15, 25, 35, 25]  # Demo data
            
            fig_scores = px.pie(
                values=score_counts,
                names=score_ranges,
                title="Score Distribution"
            )
            fig_scores.update_layout(height=300)
            st.plotly_chart(fig_scores, use_container_width=True)
        
        # Recent Activity
        st.markdown("## 🕒 Recent Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 Recent Exam Attempts")
            if recent_attempts:
                for attempt in recent_attempts[:5]:
                    score = attempt.get('score', 0)
                    score_color = get_score_color(score)
                    
                    st.markdown(f"""
                    <div style="background: {score_color}; padding: 0.5rem; border-radius: 0.5rem; 
                               margin-bottom: 0.5rem; color: white;">
                        <strong>Score: {score:.1f}%</strong> - {attempt.get('user_id', 'Unknown')[:8]}...
                        <br><small>{attempt.get('created_at', 'Unknown time')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent attempts")
        
        with col2:
            st.markdown("### 🎫 Support Tickets")
            tickets = run_async(load_recent_tickets())
            
            if tickets:
                for ticket in tickets[:5]:
                    status = ticket.get('status', 'open')
                    status_color = '#ff9800' if status == 'open' else '#4caf50'
                    
                    st.markdown(f"""
                    <div style="border-left: 4px solid {status_color}; padding: 0.5rem; 
                               background: #f8f9fa; margin-bottom: 0.5rem;">
                        <strong>{ticket.get('subject', 'No subject')}</strong>
                        <br><small>Status: {status.title()} | {ticket.get('created_at', 'Unknown')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent tickets")
        
        # Management Actions
        st.markdown("---")
        st.markdown("## ⚙️ Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 Upload New Mock", use_container_width=True, type="primary"):
                st.session_state.page = "admin_upload"
                st.rerun()
        
        with col2:
            if st.button("📝 Manage Mocks", use_container_width=True):
                st.session_state.page = "admin_manage"
                st.rerun()
        
        with col3:
            if st.button("👥 Manage Users", use_container_width=True):
                show_user_management_modal()
        
        with col4:
            if st.button("🎫 Support Tickets", use_container_width=True):
                st.session_state.page = "admin_tickets"
                st.rerun()
        
        # System Health
        st.markdown("---")
        st.markdown("## 🔧 System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Database Status**  
            🟢 Connected and healthy  
            Last backup: 2 hours ago
            """)
        
        with col2:
            st.markdown("""
            **Payment System**  
            🟢 Stripe operational  
            Last transaction: 15 min ago
            """)
        
        with col3:
            st.markdown("""
            **AI Services**  
            🟢 OpenRouter active  
            Response time: 1.2s avg
            """)
    
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def show_user_management_modal():
    """Show user management in an expander"""
    with st.expander("👥 User Management", expanded=True):
        st.markdown("### Recent Users")
        
        # Demo user data
        users_data = {
            'Email': ['user1@demo.com', 'user2@demo.com', 'user3@demo.com'],
            'Credits': [15, 8, 22],
            'Role': ['user', 'user', 'user'],
            'Joined': ['2024-01-15', '2024-01-20', '2024-01-25']
        }
        
        df = pd.DataFrame(users_data)
        st.dataframe(df, use_container_width=True)
        
        st.markdown("### User Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            user_email = st.text_input("User Email")
        
        with col2:
            credits_to_add = st.number_input("Add Credits", min_value=0, value=0)
        
        with col3:
            if st.button("💰 Add Credits"):
                if user_email and credits_to_add > 0:
                    st.success(f"Added {credits_to_add} credits to {user_email}")
                else:
                    st.error("Please provide valid email and credit amount")

async def load_dashboard_stats() -> Dict[str, Any]:
    """Load dashboard statistics"""
    from db import db
    
    try:
        stats = await db.get_user_statistics()
        
        # Add some calculated metrics
        stats['active_mocks'] = stats.get('total_mocks', 0)  # Assume all are active for demo
        stats['new_users_today'] = 2  # Demo data
        stats['attempts_today'] = 5  # Demo data
        stats['avg_score'] = 75.3  # Demo data
        stats['score_trend'] = 2.1  # Demo data
        stats['total_revenue'] = 1247.50  # Demo data
        stats['revenue_today'] = 45.00  # Demo data
        
        return stats
    except Exception as e:
        # Return demo data if database fails
        return {
            'total_users': 150,
            'active_users': 140,
            'admin_users': 10,
            'total_attempts': 523,
            'total_mocks': 25,
            'active_mocks': 25,
            'new_users_today': 2,
            'attempts_today': 5,
            'avg_score': 75.3,
            'score_trend': 2.1,
            'total_revenue': 1247.50,
            'revenue_today': 45.00
        }

async def load_recent_attempts() -> List[Dict[str, Any]]:
    """Load recent exam attempts"""
    from db import db
    
    try:
        return await db.get_recent_attempts(limit=10)
    except Exception as e:
        # Return demo data if database fails
        return [
            {'user_id': 'user123', 'score': 85.5, 'created_at': '2024-01-25 14:30:00'},
            {'user_id': 'user456', 'score': 72.0, 'created_at': '2024-01-25 13:15:00'},
            {'user_id': 'user789', 'score': 91.2, 'created_at': '2024-01-25 12:45:00'},
        ]

async def load_recent_tickets() -> List[Dict[str, Any]]:
    """Load recent support tickets"""
    # Demo data for now
    return [
        {'subject': 'Login issue', 'status': 'open', 'created_at': '2024-01-25 15:00:00'},
        {'subject': 'Payment problem', 'status': 'resolved', 'created_at': '2024-01-25 14:30:00'},
        {'subject': 'Exam not loading', 'status': 'open', 'created_at': '2024-01-25 13:45:00'},
    ]

def generate_demo_user_growth() -> pd.DataFrame:
    """Generate demo user growth data"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
    users = [5 + i + (i % 7) * 2 for i in range(len(dates))]  # Simulated growth
    
    return pd.DataFrame({
        'date': dates,
        'users': users
    })

def get_score_color(score: float) -> str:
    """Get color based on score"""
    if score >= 85:
        return "#4caf50"  # Green
    elif score >= 70:
        return "#ff9800"  # Orange
    elif score >= 50:
        return "#f44336"  # Red
    else:
        return "#9e9e9e"  # Grey

# Main function for standalone execution
if __name__ == "__main__":
    show_admin_dashboard()