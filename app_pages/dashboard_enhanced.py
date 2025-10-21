"""
Enhanced Dashboard - Production-Ready User Analytics and Recommendations
Comprehensive user performance tracking and personalized study recommendations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import openrouter_utils as ai

# Import enhanced modules
from db import DatabaseManager
from models import DifficultyLevel, ExamCategoryCode

# Initialize database manager
db = DatabaseManager()


def show_enhanced_dashboard():
    """Enhanced dashboard with analytics and recommendations"""
    st.header("🏠 Dashboard")

    # Get current user and exam category
    user = st.session_state.get("current_user", {})
    exam_category = st.session_state.get("selected_exam_category", "CACS2")

    # Load user analytics
    analytics_data = asyncio.run(load_user_analytics(user.get("id"), exam_category))

    # Top row - Key metrics
    render_key_metrics(analytics_data)

    # Second row - Performance charts and recommendations
    col1, col2 = st.columns([2, 1])

    with col1:
        render_performance_charts(analytics_data)

    with col2:
        render_personalized_recommendations(analytics_data, exam_category)

    # Third row - Recent activity and quick actions
    render_recent_activity_and_actions(analytics_data, exam_category)


async def load_user_analytics(user_id: int, exam_category: str) -> Dict[str, Any]:
    """Load comprehensive user analytics data"""
    try:
        # Get user attempts for the category
        attempts = await db.get_user_attempts_by_category(user_id, ExamCategoryCode(exam_category))

        # Get user mastery data
        mastery_data = await db.get_user_mastery_data(user_id, ExamCategoryCode(exam_category))

        # Calculate analytics
        analytics = {
            "total_attempts": len(attempts),
            "total_questions": sum(len(attempt.answers) for attempt in attempts),
            "avg_score": calculate_average_score(attempts),
            "study_streak": calculate_study_streak(attempts),
            "time_spent_minutes": sum(attempt.time_spent_seconds for attempt in attempts) // 60,
            "attempts_data": attempts,
            "mastery_data": mastery_data,
            "performance_trend": calculate_performance_trend(attempts),
            "weak_areas": identify_weak_areas(mastery_data),
            "strong_areas": identify_strong_areas(mastery_data),
            "recommendation_data": generate_recommendation_data(attempts, mastery_data),
        }

        return analytics

    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        return generate_placeholder_analytics()


def calculate_average_score(attempts: List) -> float:
    """Calculate average score across all attempts"""
    if not attempts:
        return 0.0

    total_score = 0
    total_questions = 0

    for attempt in attempts:
        if attempt.answers:
            correct_answers = sum(1 for ans in attempt.answers if ans.get("is_correct", False))
            total_score += correct_answers
            total_questions += len(attempt.answers)

    return (total_score / total_questions * 100) if total_questions > 0 else 0.0


def calculate_study_streak(attempts: List) -> int:
    """Calculate current study streak in days"""
    if not attempts:
        return 0

    # Sort attempts by date
    sorted_attempts = sorted(attempts, key=lambda x: x.created_at, reverse=True)

    streak = 0
    current_date = datetime.now().date()

    for attempt in sorted_attempts:
        attempt_date = attempt.created_at.date()

        if (current_date - attempt_date).days == streak:
            streak += 1
            current_date = attempt_date
        else:
            break

    return streak


def calculate_performance_trend(attempts: List) -> List[Dict]:
    """Calculate performance trend over time"""
    if not attempts:
        return []

    # Sort attempts by date
    sorted_attempts = sorted(attempts, key=lambda x: x.created_at)

    trend_data = []
    for attempt in sorted_attempts[-10:]:  # Last 10 attempts
        if attempt.answers:
            correct_answers = sum(1 for ans in attempt.answers if ans.get("is_correct", False))
            score = (correct_answers / len(attempt.answers)) * 100

            trend_data.append(
                {
                    "date": attempt.created_at.strftime("%Y-%m-%d"),
                    "score": score,
                    "questions": len(attempt.answers),
                }
            )

    return trend_data


def identify_weak_areas(mastery_data: List) -> List[str]:
    """Identify user's weak areas based on mastery data"""
    weak_areas = []

    for mastery in mastery_data:
        if mastery.mastery_level < 0.6:  # Less than 60% mastery
            weak_areas.append(mastery.topic_tag)

    return weak_areas[:5]  # Top 5 weak areas


def identify_strong_areas(mastery_data: List) -> List[str]:
    """Identify user's strong areas based on mastery data"""
    strong_areas = []

    for mastery in mastery_data:
        if mastery.mastery_level > 0.8:  # More than 80% mastery
            strong_areas.append(mastery.topic_tag)

    return strong_areas[:5]  # Top 5 strong areas


def generate_recommendation_data(attempts: List, mastery_data: List) -> Dict[str, Any]:
    """Generate personalized recommendations"""
    recommendations = {"next_actions": [], "study_focus": [], "difficulty_recommendation": "medium"}

    if not attempts:
        recommendations["next_actions"] = [
            "Take your first practice quiz to establish baseline",
            "Start with easy difficulty questions",
            "Focus on core concepts first",
        ]
        return recommendations

    # Analyze recent performance
    recent_attempts = sorted(attempts, key=lambda x: x.created_at, reverse=True)[:5]
    recent_avg_score = calculate_average_score(recent_attempts)

    # Difficulty recommendation
    if recent_avg_score > 80:
        recommendations["difficulty_recommendation"] = "hard"
        recommendations["next_actions"].append("Challenge yourself with hard difficulty questions")
    elif recent_avg_score > 60:
        recommendations["difficulty_recommendation"] = "medium"
        recommendations["next_actions"].append("Continue with medium difficulty questions")
    else:
        recommendations["difficulty_recommendation"] = "easy"
        recommendations["next_actions"].append("Focus on easy questions to build confidence")

    # Study focus recommendations
    weak_areas = identify_weak_areas(mastery_data)
    if weak_areas:
        recommendations["study_focus"] = weak_areas[:3]
        recommendations["next_actions"].append(f"Focus on improving: {', '.join(weak_areas[:2])}")

    return recommendations


def generate_placeholder_analytics() -> Dict[str, Any]:
    """Generate placeholder analytics for new users"""
    return {
        "total_attempts": 0,
        "total_questions": 0,
        "avg_score": 0.0,
        "study_streak": 0,
        "time_spent_minutes": 0,
        "attempts_data": [],
        "mastery_data": [],
        "performance_trend": [],
        "weak_areas": [],
        "strong_areas": [],
        "recommendation_data": {
            "next_actions": [
                "Welcome to MockExamify! Start with a practice quiz",
                "Explore different topics to find your interests",
                "Set a daily study goal to build momentum",
            ],
            "study_focus": [],
            "difficulty_recommendation": "easy",
        },
    }


def render_key_metrics(analytics_data: Dict[str, Any]):
    """Render key performance metrics"""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Study Streak",
            f"{analytics_data['study_streak']} days",
            delta="+1" if analytics_data["study_streak"] > 0 else None,
        )

    with col2:
        st.metric(
            "Avg Score",
            f"{analytics_data['avg_score']:.1f}%",
            delta=(
                f"+{analytics_data['avg_score']:.1f}%" if analytics_data["avg_score"] > 0 else None
            ),
        )

    with col3:
        st.metric(
            "Total Questions",
            analytics_data["total_questions"],
            delta=f"+{len(analytics_data.get('attempts_data', []))}",
        )

    with col4:
        st.metric(
            "Practice Sessions",
            analytics_data["total_attempts"],
            delta="+1" if analytics_data["total_attempts"] > 0 else None,
        )

    with col5:
        hours_studied = analytics_data["time_spent_minutes"] / 60
        st.metric(
            "Hours Studied",
            f"{hours_studied:.1f}h",
            delta=f"+{hours_studied:.1f}h" if hours_studied > 0 else None,
        )


def render_performance_charts(analytics_data: Dict[str, Any]):
    """Render performance visualization charts"""
    st.subheader("📊 Performance Analytics")

    # Performance trend chart
    if analytics_data["performance_trend"]:
        trend_df = pd.DataFrame(analytics_data["performance_trend"])

        fig = px.line(trend_df, x="date", y="score", title="Score Trend Over Time", markers=True)
        fig.update_layout(xaxis_title="Date", yaxis_title="Score (%)", height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📈 Take some practice quizzes to see your performance trend!")

    # Topic mastery chart
    if analytics_data["mastery_data"]:
        mastery_df = pd.DataFrame(
            [
                {
                    "topic": mastery.topic_tag,
                    "mastery": mastery.mastery_level * 100,
                    "attempts": mastery.attempts_count,
                }
                for mastery in analytics_data["mastery_data"][:10]  # Top 10 topics
            ]
        )

        fig = px.bar(
            mastery_df,
            x="topic",
            y="mastery",
            title="Topic Mastery Levels",
            color="mastery",
            color_continuous_scale="RdYlGn",
        )
        fig.update_layout(
            xaxis_title="Topics", yaxis_title="Mastery Level (%)", height=300, xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📚 Practice different topics to see your mastery levels!")


def render_personalized_recommendations(analytics_data: Dict[str, Any], exam_category: str):
    """Render personalized study recommendations"""
    st.subheader("🎯 Personalized Recommendations")

    recommendations = analytics_data["recommendation_data"]

    # Next actions
    st.write("**📋 Recommended Actions:**")
    for action in recommendations["next_actions"]:
        st.write(f"• {action}")

    # Difficulty recommendation
    difficulty = recommendations["difficulty_recommendation"]
    difficulty_colors = {"easy": "#28a745", "medium": "#ffc107", "hard": "#dc3545"}
    difficulty_color = difficulty_colors.get(difficulty, "#6c757d")

    st.markdown(
        f"""
    <div style="
        background: {difficulty_color}20;
        border-left: 4px solid {difficulty_color};
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    ">
        <strong>🎚️ Recommended Difficulty:</strong><br>
        <span style="color: {difficulty_color}; font-weight: bold; text-transform: uppercase;">
            {difficulty}
        </span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Study focus areas
    if recommendations["study_focus"]:
        st.write("**🔍 Focus Areas:**")
        for area in recommendations["study_focus"]:
            st.write(f"• {area}")

    # Quick action buttons
    st.markdown("---")
    st.write("**⚡ Quick Actions:**")

    if st.button("🎯 Start Recommended Practice", type="primary", use_container_width=True):
        st.session_state.practice_mode = "recommended"
        st.session_state.practice_config = {
            "difficulty": difficulty,
            "focus_areas": recommendations["study_focus"],
            "exam_category": exam_category,
        }
        st.session_state.page = "exam"
        st.rerun()

    if analytics_data["weak_areas"]:
        if st.button("⚡ Practice Weak Areas", use_container_width=True):
            st.session_state.page = "weak_areas"
            st.rerun()

    if st.button("🧠 Adaptive Practice", use_container_width=True):
        st.session_state.page = "adaptive_practice"
        st.rerun()


def render_recent_activity_and_actions(analytics_data: Dict[str, Any], exam_category: str):
    """Render recent activity and quick action cards"""
    st.subheader("📈 Recent Activity & Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**📝 Recent Practice Sessions**")

        recent_attempts = sorted(
            analytics_data["attempts_data"], key=lambda x: x.created_at, reverse=True
        )[:5]

        if recent_attempts:
            for attempt in recent_attempts:
                score = 0
                if attempt.answers:
                    correct = sum(1 for ans in attempt.answers if ans.get("is_correct", False))
                    score = (correct / len(attempt.answers)) * 100

                score_color = "#28a745" if score >= 70 else "#ffc107" if score >= 50 else "#dc3545"

                with st.container():
                    st.markdown(
                        f"""
                    <div style="
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 0.75rem;
                        margin: 0.5rem 0;
                        background: white;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{attempt.created_at.strftime('%Y-%m-%d %H:%M')}</strong><br>
                                <small>{len(attempt.answers) if attempt.answers else 0} questions</small>
                            </div>
                            <div style="color: {score_color}; font-weight: bold; font-size: 1.2rem;">
                                {score:.1f}%
                            </div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No recent practice sessions. Start your first practice!")

    with col2:
        st.write("**🚀 Quick Practice Options**")

        # Quick practice cards
        practice_options = [
            {
                "title": "📚 Topic Practice",
                "description": "Practice specific topics",
                "page": "topic_practice",
                "icon": "🎯",
            },
            {
                "title": "📝 Mock Exam",
                "description": "Full-length practice exam",
                "page": "mock_exams",
                "icon": "⏱️",
            },
            {
                "title": "🧠 Smart Practice",
                "description": "AI-powered adaptive questions",
                "page": "adaptive_practice",
                "icon": "🤖",
            },
        ]

        for option in practice_options:
            if st.button(
                f"{option['icon']} {option['title']}",
                help=option["description"],
                use_container_width=True,
                key=f"quick_{option['page']}",
            ):
                st.session_state.page = option["page"]
                st.rerun()


# Compatibility with existing dashboard
def show_dashboard():
    """Compatibility wrapper for existing dashboard calls"""
    show_enhanced_dashboard()


def handle_dashboard_modals():
    """Handle any dashboard modals (kept for compatibility)"""
    pass
