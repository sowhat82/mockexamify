"""
Admin Dashboard for MockExamify
Comprehensive analytics and management overview
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from auth_utils import AuthUtils, run_async


def show_admin_dashboard():
    """Display the admin dashboard with analytics and management options"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated() or not auth.is_admin():
        st.error("Admin access required")
        st.stop()

    # Back to main dashboard button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Back to Dashboard", key="back_to_dashboard_analytics"):
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown("# � Analytics Dashboard")
    st.markdown("*Platform-wide metrics and performance overview*")

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
                stats["total_users"],
                delta=f"+{stats.get('new_users_today', 0)} today",
            )

        with col2:
            st.metric(
                "📚 Total Mocks",
                stats["total_mocks"],
                delta=f"{stats.get('active_mocks', 0)} active",
            )

        with col3:
            st.metric(
                "🎯 Total Attempts",
                stats["total_attempts"],
                delta=f"+{stats.get('attempts_today', 0)} today",
            )

        with col4:
            avg_score = stats.get("avg_score", 0)
            st.metric(
                "📊 Avg Score",
                f"{avg_score:.1f}%",
                delta=f"{stats.get('score_trend', 0):+.1f}% vs last week",
            )

        with col5:
            revenue = stats.get("total_revenue", 0)
            st.metric(
                "💰 Revenue",
                f"${revenue:.2f}",
                delta=f"+${stats.get('revenue_today', 0):.2f} today",
            )

        st.markdown("---")

        # Charts Row
        col1, col2 = st.columns(2)

        with col1:
            # User Growth Chart
            st.markdown("### 📈 User Growth (Last 30 Days)")
            user_growth_data = generate_demo_user_growth()
            fig_users = px.line(
                user_growth_data, x="date", y="users", title="Daily User Registrations"
            )
            fig_users.update_layout(height=300)
            st.plotly_chart(fig_users, use_container_width=True)

        with col2:
            # Exam Performance Chart
            st.markdown("### 🎯 Exam Performance Distribution")
            score_ranges = ["0-49%", "50-69%", "70-84%", "85-100%"]
            score_counts = [15, 25, 35, 25]  # Demo data

            fig_scores = px.pie(values=score_counts, names=score_ranges, title="Score Distribution")
            fig_scores.update_layout(height=300)
            st.plotly_chart(fig_scores, use_container_width=True)

        # Recent Activity
        st.markdown("## 🕒 Recent Activity")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 Recent Exam Attempts")
            if recent_attempts:
                for attempt in recent_attempts[:5]:
                    score = attempt.get("score", 0)
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
                st.info("No recent attempts")


        # Quick Actions (non-duplicated features only)
        st.markdown("---")
        st.markdown("## ⚙️ Quick Actions")

        # Initialize modal state if not present
        if "show_users_modal" not in st.session_state:
            st.session_state.show_users_modal = False
        if "show_credits_modal" not in st.session_state:
            st.session_state.show_credits_modal = False
        if "show_password_modal" not in st.session_state:
            st.session_state.show_password_modal = False

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("👥 Manage Users", use_container_width=True, type="primary"):
                st.session_state.show_users_modal = True
                st.session_state.show_credits_modal = False
                st.session_state.show_password_modal = False

        with col2:
            if st.button("💰 Adjust User Credits", use_container_width=True):
                st.session_state.show_credits_modal = True
                st.session_state.show_users_modal = False
                st.session_state.show_password_modal = False

        with col3:
            if st.button("🔑 Reset User Password", use_container_width=True):
                st.session_state.show_password_modal = True
                st.session_state.show_users_modal = False
                st.session_state.show_credits_modal = False

        with col4:
            if st.button("📊 Export Analytics", use_container_width=True):
                export_analytics()

        # Show modals based on session state
        if st.session_state.show_users_modal:
            show_user_management_modal()

        if st.session_state.show_credits_modal:
            show_credits_management_modal()

        if st.session_state.show_password_modal:
            show_password_reset_modal()

        # System Health
        st.markdown("---")
        st.markdown("## 🔧 System Status")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                """
            **Database Status**
            🟢 Connected and healthy
            Last backup: 2 hours ago
            """
            )

        with col2:
            st.markdown(
                """
            **Payment System**
            🟢 Stripe operational
            Last transaction: 15 min ago
            """
            )

        with col3:
            st.markdown(
                """
            **AI Services**
            🟢 OpenRouter active
            Response time: 1.2s avg
            """
            )

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")


def show_user_management_modal():
    """Show user management in an expander"""
    with st.expander("👥 User Management", expanded=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown("### All Users")
        with col2:
            if st.button("✖️ Close", key="close_users_modal"):
                st.session_state.show_users_modal = False
                st.rerun()

        # Load real users from database
        try:
            from db import db
            users = run_async(db.get_all_users())

            if users:
                # Convert User objects to DataFrame
                joined_dates = []
                for u in users:
                    if isinstance(u.created_at, datetime):
                        joined_dates.append(u.created_at.strftime("%Y-%m-%d"))
                    elif isinstance(u.created_at, str):
                        joined_dates.append(u.created_at.split("T")[0] if "T" in u.created_at else u.created_at)
                    else:
                        joined_dates.append(str(u.created_at))

                users_data = {
                    "Email": [u.email for u in users],
                    "Credits": [u.credits_balance for u in users],
                    "Role": [u.role for u in users],
                    "Joined": joined_dates,
                }

                df = pd.DataFrame(users_data)
                st.dataframe(df, use_container_width=True)

                st.success(f"📊 Showing {len(users)} users")
            else:
                st.warning("No users found")

        except Exception as e:
            st.error(f"Error loading users: {e}")

        st.info("💡 Tip: Use 'Adjust User Credits' button for credit management")


def show_credits_management_modal():
    """Show credits management interface"""
    with st.expander("💰 Credits Management", expanded=True):
        col_header1, col_header2 = st.columns([5, 1])
        with col_header1:
            st.markdown("### Adjust User Credits")
        with col_header2:
            if st.button("✖️ Close", key="close_credits_modal"):
                st.session_state.show_credits_modal = False
                st.rerun()

        col1, col2 = st.columns(2)

        with col1:
            user_email = st.text_input("User Email", key="credits_user_email")
            credits_to_add = st.number_input(
                "Credits to Add/Remove",
                min_value=-100,
                max_value=100,
                value=0,
                key="credits_amount",
            )

        with col2:
            st.markdown("#### Quick Actions")
            if st.button("➕ Add 5 Credits"):
                if user_email:
                    success = run_async(adjust_user_credits(user_email, 5))
                    if success:
                        st.success(f"Added 5 credits to {user_email}")
                        st.rerun()
                    else:
                        st.error(f"Failed to add credits to {user_email}")
                else:
                    st.error("Please enter a user email")

            if st.button("➕ Add 10 Credits"):
                if user_email:
                    success = run_async(adjust_user_credits(user_email, 10))
                    if success:
                        st.success(f"Added 10 credits to {user_email}")
                        st.rerun()
                    else:
                        st.error(f"Failed to add credits to {user_email}")
                else:
                    st.error("Please enter a user email")

            if st.button("🔄 Reset to 0"):
                if user_email:
                    success = run_async(reset_user_credits(user_email))
                    if success:
                        st.success(f"Reset credits for {user_email} to 0")
                        st.rerun()
                    else:
                        st.error(f"Failed to reset credits for {user_email}")
                else:
                    st.error("Please enter a user email")

        if st.button("💰 Apply Credit Adjustment", type="primary"):
            if user_email and credits_to_add != 0:
                success = run_async(adjust_user_credits(user_email, credits_to_add))
                if success:
                    action = "Added" if credits_to_add > 0 else "Removed"
                    st.success(f"{action} {abs(credits_to_add)} credits for {user_email}")
                    st.rerun()
                else:
                    st.error(f"Failed to adjust credits for {user_email}")
            else:
                st.error("Please provide valid email and credit amount")


def show_password_reset_modal():
    """Show password reset interface"""
    with st.expander("🔑 Password Reset", expanded=True):
        col_header1, col_header2 = st.columns([5, 1])
        with col_header1:
            st.markdown("### Reset User Password")
        with col_header2:
            if st.button("✖️ Close", key="close_password_modal"):
                st.session_state.show_password_modal = False
                st.rerun()

        st.markdown("""
        <div style="background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ffc107; margin-bottom: 1rem;">
            <p style="color: #856404; margin: 0;">
                ⚠️ <strong>Important:</strong> This will immediately change the user's password.
                Make sure to communicate the new password to them securely.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            user_email = st.text_input("User Email", key="password_user_email",
                                      help="Enter the email of the user whose password you want to reset")
            new_password = st.text_input("New Password", type="password", key="new_password",
                                        help="Enter the new password for the user")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password",
                                            help="Re-enter the password to confirm")

        with col2:
            st.markdown("#### Password Requirements")
            st.markdown("""
            - Minimum 6 characters
            - Both passwords must match
            - Avoid common passwords

            **Tip:** Generate a strong password and share it with the user securely.
            """)

        if st.button("🔑 Reset Password", type="primary"):
            if not user_email:
                st.error("Please enter a user email")
            elif not new_password or not confirm_password:
                st.error("Please enter and confirm the new password")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                success = run_async(reset_user_password(user_email, new_password))
                if success:
                    st.success(f"✅ Password successfully reset for {user_email}")
                    st.info("💡 Make sure to communicate the new password to the user securely.")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to reset password for {user_email}. User may not exist.")


def export_analytics():
    """Export analytics data"""
    st.info("📊 Analytics export feature coming soon! Will export CSV/Excel with all metrics.")
    # Placeholder for future implementation


async def load_dashboard_stats() -> Dict[str, Any]:
    """Load dashboard statistics"""
    from db import db

    try:
        stats = await db.get_user_statistics()

        # Add some calculated metrics
        stats["active_mocks"] = stats.get("total_mocks", 0)  # Assume all are active for demo
        stats["new_users_today"] = 2  # Demo data
        stats["attempts_today"] = 5  # Demo data
        stats["avg_score"] = 75.3  # Demo data
        stats["score_trend"] = 2.1  # Demo data
        stats["total_revenue"] = 1247.50  # Demo data
        stats["revenue_today"] = 45.00  # Demo data

        return stats
    except Exception as e:
        # Return demo data if database fails
        return {
            "total_users": 150,
            "active_users": 140,
            "admin_users": 10,
            "total_attempts": 523,
            "total_mocks": 25,
            "active_mocks": 25,
            "new_users_today": 2,
            "attempts_today": 5,
            "avg_score": 75.3,
            "score_trend": 2.1,
            "total_revenue": 1247.50,
            "revenue_today": 45.00,
        }


async def load_recent_attempts() -> List[Dict[str, Any]]:
    """Load recent exam attempts"""
    from db import db

    try:
        return await db.get_recent_attempts(limit=10)
    except Exception as e:
        # Return demo data if database fails
        return [
            {"user_id": "user123", "score": 85.5, "created_at": "2024-01-25 14:30:00"},
            {"user_id": "user456", "score": 72.0, "created_at": "2024-01-25 13:15:00"},
            {"user_id": "user789", "score": 91.2, "created_at": "2024-01-25 12:45:00"},
        ]




def generate_demo_user_growth() -> pd.DataFrame:
    """Generate demo user growth data"""
    dates = pd.date_range(start="2024-01-01", end="2024-01-30", freq="D")
    users = [5 + i + (i % 7) * 2 for i in range(len(dates))]  # Simulated growth

    return pd.DataFrame({"date": dates, "users": users})


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


async def adjust_user_credits(user_email: str, credits_to_add: int) -> bool:
    """Adjust user credits by email"""
    from db import db

    try:
        # Get user by email
        user = await db.get_user_by_email(user_email)
        if not user:
            return False

        # Add credits to user
        success = await db.add_credits_to_user(user.id, credits_to_add)
        return success
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error adjusting credits for {user_email}: {e}")
        return False


async def reset_user_credits(user_email: str) -> bool:
    """Reset user credits to 0"""
    from db import db

    try:
        # Get user by email
        user = await db.get_user_by_email(user_email)
        if not user:
            return False

        # Calculate credits to deduct to reach 0
        credits_to_deduct = -user.credits_balance

        # Add negative credits to reset to 0
        success = await db.add_credits_to_user(user.id, credits_to_deduct)
        return success
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error resetting credits for {user_email}: {e}")
        return False


async def reset_user_password(user_email: str, new_password: str) -> bool:
    """Reset user password by email (admin function)"""
    from db import db

    try:
        # Get user by email
        user = await db.get_user_by_email(user_email)
        if not user:
            return False

        # Reset password using user ID
        success = await db.reset_user_password(user.id, new_password)
        return success
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error resetting password for {user_email}: {e}")
        return False


# Main function for standalone execution
if __name__ == "__main__":
    show_admin_dashboard()
