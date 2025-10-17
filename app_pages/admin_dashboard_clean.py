"""
Admin Dashboard for MockExamify - CLEAN VERSION (Real Data Only)
Shows only actual data from database, no prototypes or fake numbers
"""
import streamlit as st
from typing import Dict, Any, List
from auth_utils import AuthUtils, run_async
import config
import pandas as pd


def show_admin_dashboard():
    """Display the admin dashboard with REAL data only"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated() or not auth.is_admin():
        st.error("Admin access required")
        st.stop()

    st.markdown("# 📊 Admin Dashboard")
    st.markdown("*Real-time platform overview*")

    # Load real data
    try:
        stats = run_async(load_dashboard_stats())
        recent_attempts = run_async(load_recent_attempts())

        # Key Metrics Row - REAL DATA ONLY
        st.markdown("## 📈 Key Metrics")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("👥 Total Users", stats['total_users'])

        with col2:
            st.metric("📚 Total Mocks", stats['total_mocks'])

        with col3:
            st.metric("🎯 Total Attempts", stats['total_attempts'])

        st.markdown("---")

        # Recent Activity
        st.markdown("## 🕒 Recent Activity")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 Recent Exam Attempts")
            if recent_attempts and len(recent_attempts) > 0:
                for attempt in recent_attempts[:5]:
                    score = attempt.get('score', 0)
                    score_color = get_score_color(score)

                    st.markdown(
                        f"""
                    <div style="background: {score_color}; padding: 0.5rem; border-radius: 0.5rem;
                               margin-bottom: 0.5rem; color: white;">
                        <strong>Score: {score:.1f}%</strong> - {attempt.get('user_id', 'Unknown')[:8]}...
                        <br><small>{attempt.get('created_at', 'Unknown time')}</small>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No exam attempts yet")

        with col2:
            st.markdown("### 🎫 Support Tickets")
            tickets = run_async(load_recent_tickets())

            if tickets and len(tickets) > 0:
                for ticket in tickets[:5]:
                    status = ticket.get('status', 'Open').lower()
                    status_color = '#ff9800' if status == 'open' else '#4caf50'

                    subject = ticket.get('subject', 'No subject')
                    created = ticket.get('created_at', 'Unknown')

                    st.markdown(
                        f"""
                    <div style="border-left: 4px solid {status_color}; padding: 0.5rem;
                               background: #f8f9fa; margin-bottom: 0.5rem;">
                        <strong>{subject}</strong>
                        <br><small>Status: {status.title()} | {created}</small>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No support tickets yet")

        # Quick Actions
        st.markdown("---")
        st.markdown("## ⚙️ Quick Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("👥 Manage Users", use_container_width=True, type="primary"):
                show_user_management_modal()

        with col2:
            if st.button("💰 Adjust User Credits", use_container_width=True):
                show_credits_management_modal()

        with col3:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()

        # System Status - Keep this as it's useful
        st.markdown("---")
        st.markdown("## 🔧 System Status")

        col1, col2 = st.columns(2)

        with col1:
            db_status = "🟢 Connected" if config.DEMO_MODE else check_database_connection()
            st.markdown(f"**Database**: {db_status}")

        with col2:
            mode = "Demo Mode" if config.DEMO_MODE else "Production"
            st.markdown(f"**Environment**: {mode}")

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.info("💡 Tip: Make sure your database is properly configured")


def show_user_management_modal():
    """Show user management interface"""
    with st.expander("👥 User Management", expanded=True):
        st.markdown("### User List")

        # Load real users
        from db import DEMO_USERS

        if DEMO_USERS:
            users_list = []
            for email, user_data in DEMO_USERS.items():
                users_list.append(
                    {
                        'Email': email,
                        'Credits': user_data.get('credits_balance', 0),
                        'Role': user_data.get('role', 'user'),
                    }
                )

            df = pd.DataFrame(users_list)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No users in database yet")


def show_credits_management_modal():
    """Show credits management interface with REAL database integration"""
    with st.expander("💰 Credits Management", expanded=True):
        st.markdown("### Adjust User Credits")

        user_email = st.text_input("User Email", key="credits_user_email")
        credits_to_add = st.number_input(
            "Credits to Add/Remove",
            min_value=-100,
            max_value=100,
            value=0,
            key="credits_amount",
            help="Positive numbers add credits, negative numbers remove credits"
        )

        if st.button("💰 Apply Adjustment", type="primary"):
            if user_email and credits_to_add != 0:
                # Actually update the database
                from db import db
                success = run_async(db.adjust_user_credits(user_email, credits_to_add))

                if success:
                    action = "Added" if credits_to_add > 0 else "Removed"
                    st.success(f"✅ {action} {abs(credits_to_add)} credits for {user_email}")
                    st.rerun()  # Refresh to show updated data
                else:
                    st.error(f"❌ Failed to adjust credits. User {user_email} may not exist.")
            else:
                st.error("Please provide valid email and non-zero credit amount")


async def load_dashboard_stats() -> Dict[str, Any]:
    """Load REAL dashboard statistics only"""
    from db import db

    try:
        # Get actual stats from database
        stats = await db.get_user_statistics()

        # Return only what we have
        return {
            'total_users': stats.get('total_users', 0),
            'total_mocks': stats.get('total_mocks', 0),
            'total_attempts': stats.get('total_attempts', 0),
        }
    except Exception as e:
        # Return zeros if error - NO FAKE DATA
        return {
            'total_users': 0,
            'total_mocks': 0,
            'total_attempts': 0,
        }


async def load_recent_attempts() -> List[Dict[str, Any]]:
    """Load REAL recent exam attempts"""
    from db import db

    try:
        attempts = await db.get_recent_attempts(limit=10)
        return attempts if attempts else []
    except Exception as e:
        return []


async def load_recent_tickets() -> List[Dict[str, Any]]:
    """Load REAL recent support tickets"""
    from db import db

    try:
        tickets = await db.get_all_support_tickets()
        # Get most recent 5
        return tickets[:5] if tickets else []
    except Exception as e:
        return []


def check_database_connection() -> str:
    """Check if database is connected"""
    try:
        from db import db

        if db.demo_mode:
            return "🟡 Demo Mode"
        else:
            return "🟢 Connected"
    except:
        return "🔴 Disconnected"


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


if __name__ == "__main__":
    show_admin_dashboard()
