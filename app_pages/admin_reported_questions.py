"""
Admin page for viewing and managing reported questions
"""
import json
from typing import Any, Dict, List

import streamlit as st

from auth_utils import run_async
from db import db


def show_admin_reported_questions():
    """Admin page to view and manage reported questions"""

    # Back to Dashboard button
    if st.button("← Back to Dashboard", type="secondary"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown("# 🚨 Reported Questions")
    st.markdown("View and manage questions reported by users as corrupted or problematic")
    st.markdown("---")

    # Get pending reports count
    pending_count = run_async(db.get_pending_reports_count())

    # Stats section
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔔 Pending Reports", pending_count)

    with col2:
        # Filter by status
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "reviewed", "resolved", "dismissed"]
        )

    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Get reported questions
    if status_filter == "All":
        reported_questions = run_async(db.get_reported_questions(status=None, limit=200))
    else:
        reported_questions = run_async(db.get_reported_questions(status=status_filter, limit=200))

    if not reported_questions:
        st.info(f"No {status_filter if status_filter != 'All' else ''} reported questions found")
        return

    st.markdown(f"### {len(reported_questions)} Reported Question(s)")

    # Display reported questions
    for idx, report in enumerate(reported_questions, 1):
        display_reported_question(report, idx)


def display_reported_question(report: Dict[str, Any], idx: int):
    """Display a single reported question with details and actions"""

    # Parse choices
    choices = report.get("choices", [])
    if isinstance(choices, str):
        try:
            choices = json.loads(choices)
        except:
            choices = []

    # Status badge color
    status = report.get("status", "pending")
    status_colors = {
        "pending": "🔴",
        "reviewed": "🟡",
        "resolved": "🟢",
        "dismissed": "⚪"
    }
    status_badge = status_colors.get(status, "⚪")

    # Question preview
    question_text = report.get("question_text", "")[:100]
    pool_name = report.get("pool_name", "Unknown Pool")

    # Create expander with summary
    with st.expander(
        f"{status_badge} Report #{idx}: {question_text}... | Pool: {pool_name}",
        expanded=(status == "pending" and idx <= 3)  # Auto-expand first 3 pending
    ):
        # Report details
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**Question ID:** `{report.get('question_id')}`")
            st.markdown(f"**Pool:** {pool_name}")

            # Handle reporter display
            reporter_email = report.get('reporter_email')
            if reporter_email and reporter_email.lower() != 'none':
                st.markdown(f"**Reported by:** {reporter_email}")
            else:
                st.markdown(f"**Reported by:** Demo User / Anonymous")

            st.markdown(f"**Reported at:** {report.get('reported_at', 'N/A')}")
            st.markdown(f"**Status:** {status.upper()}")

        with col2:
            # Status indicator box
            status_html = f"""
            <div style="background: {'#fff3cd' if status == 'pending' else '#d4edda' if status == 'resolved' else '#f8d7da' if status == 'dismissed' else '#cfe2ff'};
                        padding: 1rem; border-radius: 0.5rem; text-align: center;">
                <div style="font-size: 2rem;">{status_badge}</div>
                <div style="font-weight: bold; text-transform: uppercase;">{status}</div>
            </div>
            """
            st.markdown(status_html, unsafe_allow_html=True)

        st.markdown("---")

        # Question content
        st.markdown("### 📝 Question Content")
        question_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1.5rem; border-radius: 0.75rem; color: white; margin-bottom: 1rem;">
            <p style="color: white; margin-bottom: 1rem;"><strong>Question:</strong></p>
            <p style="color: white; font-size: 1.1rem; margin-bottom: 1.5rem;">{report.get('question_text', 'N/A')}</p>

            <p style="color: white; margin-bottom: 0.5rem;"><strong>Choices:</strong></p>
        """

        correct_answer = report.get("correct_answer", -1)
        for i, choice in enumerate(choices):
            if i == correct_answer:
                question_html += f'<p style="color: #4ade80; margin: 0.25rem 0;">✅ {i}: {choice} (Correct Answer)</p>'
            else:
                question_html += f'<p style="color: white; margin: 0.25rem 0;">◯ {i}: {choice}</p>'

        question_html += "</div>"
        st.markdown(question_html, unsafe_allow_html=True)

        # Report reason
        if report.get("report_reason"):
            st.markdown("### 💬 Report Reason")
            st.markdown(
                f"""
                <div style="background: #fff3cd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ffc107;">
                    {report.get("report_reason")}
                </div>
                """,
                unsafe_allow_html=True
            )

        # Admin notes (if any)
        if report.get("admin_notes"):
            st.markdown("### 📌 Admin Notes")
            st.markdown(
                f"""
                <div style="background: #e7f3ff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2196F3;">
                    {report.get("admin_notes")}
                </div>
                """,
                unsafe_allow_html=True
            )
            if report.get("reviewed_at"):
                st.caption(f"Reviewed at: {report.get('reviewed_at')}")

        st.markdown("---")

        # Admin actions
        st.markdown("### ⚙️ Admin Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            new_status = st.selectbox(
                "Update Status",
                ["pending", "reviewed", "resolved", "dismissed"],
                index=["pending", "reviewed", "resolved", "dismissed"].index(status),
                key=f"status_{report['id']}"
            )

        with col2:
            admin_notes = st.text_area(
                "Admin Notes",
                value=report.get("admin_notes", ""),
                key=f"notes_{report['id']}",
                height=100
            )

        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Save Changes", key=f"save_{report['id']}", type="primary", use_container_width=True):
                # Update report status
                success = run_async(
                    db.update_report_status(
                        report_id=report["id"],
                        status=new_status,
                        admin_notes=admin_notes,
                        admin_id=st.session_state.user.get("id") if st.session_state.get("user") else None
                    )
                )

                if success:
                    st.success("✅ Report updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update report")

        # Quick actions
        st.markdown("#### Quick Actions")
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)

        with action_col1:
            if st.button("✅ Mark Resolved", key=f"resolve_{report['id']}", use_container_width=True):
                success = run_async(
                    db.update_report_status(
                        report_id=report["id"],
                        status="resolved",
                        admin_id=st.session_state.user.get("id") if st.session_state.get("user") else None
                    )
                )
                if success:
                    st.success("Marked as resolved!")
                    st.rerun()

        with action_col2:
            if st.button("❌ Dismiss", key=f"dismiss_{report['id']}", use_container_width=True):
                success = run_async(
                    db.update_report_status(
                        report_id=report["id"],
                        status="dismissed",
                        admin_id=st.session_state.user.get("id") if st.session_state.get("user") else None
                    )
                )
                if success:
                    st.success("Report dismissed!")
                    st.rerun()

        with action_col3:
            if st.button("📝 View in Pool", key=f"view_pool_{report['id']}", use_container_width=True):
                # Navigate to question pools page
                st.session_state.page = "admin_question_pools"
                st.session_state.viewing_pool = report.get("pool_id")
                st.rerun()

        with action_col4:
            # Copy question ID button
            st.markdown(
                f"""
                <div style="text-align: center; padding: 0.5rem;">
                    <small style="color: #6c757d;">Question ID copied on click</small>
                </div>
                """,
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    show_admin_reported_questions()
