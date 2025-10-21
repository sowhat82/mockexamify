"""
Past Attempts page for MockExamify
Comprehensive exam history and progress tracking
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

import config
from auth_utils import AuthUtils, run_async


def show_past_attempts():
    """Display comprehensive past attempts history"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated():
        st.error("Please log in to view your exam history")
        st.stop()

    user = auth.get_current_user()

    # Header
    st.markdown("# 📈 Exam History & Progress")
    st.markdown("*Track your performance and identify areas for improvement*")

    # Load user attempts
    try:
        attempts = run_async(load_user_attempts(user["id"]))

        if not attempts:
            show_empty_state()
            return

        # Performance overview
        show_performance_overview(attempts)

        # Filter and sort options
        filtered_attempts = show_filter_options(attempts)

        # Attempts list
        show_attempts_list(filtered_attempts, user)

    except Exception as e:
        st.error(f"Error loading exam history: {str(e)}")


def show_empty_state():
    """Show empty state when no attempts found"""
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
        <div style="text-align: center; padding: 3rem 1rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📚</div>
            <h3>No Exam Attempts Yet</h3>
            <p style="color: #666; margin-bottom: 2rem;">
                Start taking mock exams to build your progress history and track your improvement over time.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Call to action buttons
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🎯 Take Your First Exam", use_container_width=True, type="primary"):
            st.session_state.page = "dashboard"
            st.rerun()

        if st.button("💳 Purchase Credits", use_container_width=True):
            st.session_state.page = "purchase_credits"
            st.rerun()


def show_performance_overview(attempts: List[Dict[str, Any]]):
    """Display performance overview statistics"""
    st.markdown("## 📊 Performance Overview")

    # Calculate statistics
    total_attempts = len(attempts)
    total_score = sum(attempt.get("score", 0) for attempt in attempts)
    avg_score = total_score / total_attempts if total_attempts > 0 else 0

    # Best score
    best_score = max((attempt.get("score", 0) for attempt in attempts), default=0)

    # Recent performance (last 5 attempts)
    recent_attempts = sorted(attempts, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    recent_avg = (
        sum(attempt.get("score", 0) for attempt in recent_attempts) / len(recent_attempts)
        if recent_attempts
        else 0
    )

    # Pass rate (>=60%)
    passing_attempts = sum(1 for attempt in attempts if attempt.get("score", 0) >= 60)
    pass_rate = (passing_attempts / total_attempts * 100) if total_attempts > 0 else 0

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Attempts", total_attempts, help="Total number of mock exams completed")

    with col2:
        st.metric(
            "Average Score",
            f"{avg_score:.1f}%",
            delta=f"{recent_avg - avg_score:+.1f}%" if len(recent_attempts) >= 2 else None,
            help="Your overall average score across all attempts",
        )

    with col3:
        st.metric("Best Score", f"{best_score:.1f}%", help="Your highest score achieved")

    with col4:
        st.metric("Pass Rate", f"{pass_rate:.1f}%", help="Percentage of exams passed (≥60%)")

    # Progress chart
    if len(attempts) >= 2:
        show_progress_chart(attempts)


def show_progress_chart(attempts: List[Dict[str, Any]]):
    """Display progress chart"""
    st.markdown("### 📈 Score Progression")

    # Sort attempts by date
    sorted_attempts = sorted(attempts, key=lambda x: x.get("created_at", ""))

    # Prepare data for chart
    dates = []
    scores = []

    for attempt in sorted_attempts:
        try:
            date_str = attempt.get("created_at", "")
            if date_str:
                # Parse date (assumes ISO format)
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                dates.append(date_obj.strftime("%m/%d"))
                scores.append(attempt.get("score", 0))
        except:
            continue

    if dates and scores:
        # Create chart data
        chart_data = {"Date": dates, "Score (%)": scores}

        st.line_chart(chart_data, x="Date", y="Score (%)")


def show_filter_options(attempts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Show filter and sort options"""
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Date filter
        date_filter = st.selectbox(
            "📅 Time Period",
            ["All Time", "Last 7 Days", "Last 30 Days", "Last 3 Months"],
            help="Filter attempts by time period",
        )

    with col2:
        # Score filter
        score_filter = st.selectbox(
            "🎯 Score Range",
            ["All Scores", "Passed (≥60%)", "Failed (<60%)", "Excellent (≥80%)"],
            help="Filter attempts by score range",
        )

    with col3:
        # Sort order
        sort_order = st.selectbox(
            "📋 Sort By",
            ["Newest First", "Oldest First", "Highest Score", "Lowest Score"],
            help="Sort attempts by date or score",
        )

    # Apply filters
    filtered_attempts = apply_filters(attempts, date_filter, score_filter, sort_order)

    st.markdown(f"*Showing {len(filtered_attempts)} of {len(attempts)} attempts*")

    return filtered_attempts


def apply_filters(
    attempts: List[Dict[str, Any]], date_filter: str, score_filter: str, sort_order: str
) -> List[Dict[str, Any]]:
    """Apply filters to attempts list"""
    filtered = attempts.copy()

    # Date filter
    if date_filter != "All Time":
        now = datetime.now()

        if date_filter == "Last 7 Days":
            cutoff = now - timedelta(days=7)
        elif date_filter == "Last 30 Days":
            cutoff = now - timedelta(days=30)
        elif date_filter == "Last 3 Months":
            cutoff = now - timedelta(days=90)

        filtered = [
            attempt
            for attempt in filtered
            if attempt.get("created_at")
            and datetime.fromisoformat(attempt["created_at"].replace("Z", "+00:00")) >= cutoff
        ]

    # Score filter
    if score_filter == "Passed (≥60%)":
        filtered = [attempt for attempt in filtered if attempt.get("score", 0) >= 60]
    elif score_filter == "Failed (<60%)":
        filtered = [attempt for attempt in filtered if attempt.get("score", 0) < 60]
    elif score_filter == "Excellent (≥80%)":
        filtered = [attempt for attempt in filtered if attempt.get("score", 0) >= 80]

    # Sort order
    if sort_order == "Newest First":
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_order == "Oldest First":
        filtered.sort(key=lambda x: x.get("created_at", ""))
    elif sort_order == "Highest Score":
        filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
    elif sort_order == "Lowest Score":
        filtered.sort(key=lambda x: x.get("score", 0))

    return filtered


def show_attempts_list(attempts: List[Dict[str, Any]], user: Dict[str, Any]):
    """Display list of exam attempts"""
    st.markdown("---")
    st.markdown("## 📝 Exam Attempts")

    for i, attempt in enumerate(attempts):
        show_attempt_card(attempt, user, i)


def show_attempt_card(attempt: Dict[str, Any], user: Dict[str, Any], index: int):
    """Display individual attempt card"""
    # Get attempt details
    score = attempt.get("score", 0)
    correct_count = attempt.get("correct_count", 0)
    total_questions = attempt.get("total_questions", 0)
    created_at = attempt.get("created_at", "")
    mock_title = attempt.get("mock_title", "Unknown Exam")
    attempt_id = attempt.get("id", "")

    # Format date
    try:
        date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
    except:
        formatted_date = "Unknown date"

    # Determine score color and grade
    if score >= 80:
        score_color = "#27ae60"
        grade = "🏆 Excellent"
        score_emoji = "🎉"
    elif score >= 60:
        score_color = "#3498db"
        grade = "✅ Pass"
        score_emoji = "👍"
    else:
        score_color = "#e74c3c"
        grade = "📚 Needs Improvement"
        score_emoji = "💪"

    # Card container
    with st.container():
        st.markdown(
            f"""
        <div style="
            border: 1px solid #e1e5e9;
            border-left: 4px solid {score_color};
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #2c3e50;">{score_emoji} {mock_title}</h4>
                <div style="text-align: right;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: {score_color};">
                        {score:.1f}%
                    </div>
                    <div style="font-size: 0.8rem; color: #7f8c8d;">
                        {grade}
                    </div>
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <span style="color: #34495e;">📊 {correct_count}/{total_questions} correct</span>
                </div>
                <div>
                    <span style="color: #7f8c8d;">📅 {formatted_date}</span>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Action buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("👁️ View Details", key=f"view_{index}", use_container_width=True):
                show_attempt_details(attempt)

        with col2:
            if st.button("📄 Download PDF", key=f"pdf_{index}", use_container_width=True):
                download_attempt_pdf(attempt, user)

        with col3:
            explanations_unlocked = attempt.get("explanations_unlocked", False)
            if explanations_unlocked:
                if st.button("💡 View Explanations", key=f"exp_{index}", use_container_width=True):
                    show_explanations(attempt)
            else:
                if st.button(
                    "🔓 Unlock Explanations", key=f"unlock_{index}", use_container_width=True
                ):
                    unlock_explanations_modal(attempt, user)

        with col4:
            if st.button("🔄 Retake Exam", key=f"retake_{index}", use_container_width=True):
                retake_exam(attempt)


def show_attempt_details(attempt: Dict[str, Any]):
    """Show detailed attempt results in modal"""
    st.session_state.show_attempt_details = attempt


def show_explanations(attempt: Dict[str, Any]):
    """Show explanations for attempt"""
    st.session_state.show_explanations = attempt


def unlock_explanations_modal(attempt: Dict[str, Any], user: Dict[str, Any]):
    """Show explanations unlock modal"""
    st.session_state.unlock_explanations_attempt = attempt


def download_attempt_pdf(attempt: Dict[str, Any], user: Dict[str, Any]):
    """Download PDF report for attempt"""
    try:
        from pdf_utils import pdf_generator

        with st.spinner("Generating PDF report..."):
            pdf_data = pdf_generator.create_attempt_report(
                attempt=attempt,
                user=user,
                include_explanations=attempt.get("explanations_unlocked", False),
            )

            if pdf_data:
                st.download_button(
                    label="📄 Download Report",
                    data=pdf_data,
                    file_name=f"exam_report_{attempt.get('id', 'unknown')}.pdf",
                    mime="application/pdf",
                )
            else:
                st.error("Failed to generate PDF report")

    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")


def retake_exam(attempt: Dict[str, Any]):
    """Retake the same exam"""
    mock_id = attempt.get("mock_id")
    if mock_id:
        st.session_state.current_mock_id = mock_id
        st.session_state.page = "exam"
        st.rerun()
    else:
        st.error("Cannot retake exam - exam not found")


async def load_user_attempts(user_id: str) -> List[Dict[str, Any]]:
    """Load user's exam attempts from database"""
    try:
        from db import db

        return await db.get_user_attempts(user_id)
    except Exception as e:
        st.error(f"Error loading attempts: {str(e)}")
        return []


# Handle modals/overlays
def handle_modals():
    """Handle modal displays"""
    # Attempt details modal
    if "show_attempt_details" in st.session_state:
        attempt = st.session_state.show_attempt_details

        with st.expander("📊 Detailed Results", expanded=True):
            show_detailed_results(attempt)

            if st.button("❌ Close Details"):
                del st.session_state.show_attempt_details
                st.rerun()

    # Explanations modal
    if "show_explanations" in st.session_state:
        attempt = st.session_state.show_explanations

        with st.expander("💡 Explanations", expanded=True):
            show_explanations_content(attempt)

            if st.button("❌ Close Explanations"):
                del st.session_state.show_explanations
                st.rerun()

    # Unlock explanations modal
    if "unlock_explanations_attempt" in st.session_state:
        attempt = st.session_state.unlock_explanations_attempt

        with st.expander("🔓 Unlock Explanations", expanded=True):
            show_unlock_explanations_content(attempt)

            if st.button("❌ Cancel"):
                del st.session_state.unlock_explanations_attempt
                st.rerun()


def show_detailed_results(attempt: Dict[str, Any]):
    """Show detailed results for an attempt"""
    st.markdown("### 📊 Question-by-Question Results")

    questions = attempt.get("questions", [])
    user_answers = attempt.get("user_answers", [])

    for i, question in enumerate(questions):
        user_answer_idx = user_answers[i] if i < len(user_answers) else -1
        correct_idx = question.get("correct_index", 0)
        is_correct = user_answer_idx == correct_idx

        with st.expander(f"{'✅' if is_correct else '❌'} Question {i+1}"):
            st.markdown(f"**Question:** {question.get('question', '')}")

            choices = question.get("choices", [])
            for j, choice in enumerate(choices):
                if j == correct_idx:
                    st.markdown(f"✅ **{chr(65+j)}. {choice}** (Correct Answer)")
                elif j == user_answer_idx:
                    st.markdown(f"❌ **{chr(65+j)}. {choice}** (Your Answer)")
                else:
                    st.markdown(f"◯ {chr(65+j)}. {choice}")


def show_explanations_content(attempt: Dict[str, Any]):
    """Show explanations content"""
    explanations = run_async(get_attempt_explanations(attempt["id"]))

    if explanations:
        for i, explanation in enumerate(explanations):
            if explanation:
                st.markdown(f"### 💡 Question {i+1} Explanation")
                st.markdown(explanation)
                st.markdown("---")
    else:
        st.info("No explanations available for this attempt.")


def show_unlock_explanations_content(attempt: Dict[str, Any]):
    """Show unlock explanations modal content"""
    st.markdown("### 🔓 Unlock AI Explanations")
    st.markdown("Get detailed explanations for all questions in this exam attempt.")

    cost = 2  # Credits needed
    user = AuthUtils(config.API_BASE_URL).get_current_user()
    current_credits = user.get("credits_balance", 0)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Cost:** {cost} credits")
        st.markdown(f"**Your credits:** {current_credits}")

    with col2:
        if current_credits >= cost:
            if st.button("🔓 Unlock Now", use_container_width=True, type="primary"):
                success = run_async(
                    unlock_explanations_for_attempt(attempt["id"], user["id"], cost)
                )
                if success:
                    st.success("✅ Explanations unlocked!")
                    del st.session_state.unlock_explanations_attempt
                    st.rerun()
                else:
                    st.error("Failed to unlock explanations")
        else:
            st.error(f"Need {cost - current_credits} more credits")
            if st.button("💳 Purchase Credits", use_container_width=True):
                st.session_state.page = "purchase_credits"
                st.rerun()


async def get_attempt_explanations(attempt_id: str) -> List[str]:
    """Get explanations for an attempt"""
    try:
        from db import db

        return await db.get_attempt_explanations(attempt_id)
    except:
        return []


async def unlock_explanations_for_attempt(attempt_id: str, user_id: str, cost: int) -> bool:
    """Unlock explanations for an attempt"""
    try:
        from db import db

        # Deduct credits
        success = await db.deduct_user_credits(user_id, cost)
        if not success:
            return False

        # Mark explanations as unlocked
        return await db.unlock_explanations(attempt_id)

    except Exception as e:
        return False


# Initialize and run
if __name__ == "__main__":
    show_past_attempts()
    handle_modals()
