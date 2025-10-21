"""
Advanced Analytics & Reporting - Production-Ready Analytics Dashboard
Comprehensive performance tracking, study pattern analysis, and detailed reporting
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import openrouter_utils as ai

# Import enhanced modules
from db import DatabaseManager
from models import DifficultyLevel, ExamCategoryCode

# Initialize database manager
db = DatabaseManager()


def show_analytics_dashboard():
    """Advanced analytics and reporting dashboard"""
    st.header("📊 Advanced Analytics & Reporting")
    st.markdown("Comprehensive performance insights and study pattern analysis")

    # Get current user and exam category
    user = st.session_state.get("current_user", {})
    exam_category = st.session_state.get("selected_exam_category", "CACS2")

    # Analytics time range selector
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📈 {exam_category} Performance Analytics")
    with col2:
        time_range = st.selectbox(
            "Time Range", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"], index=1
        )

    # Load comprehensive analytics
    analytics_data = asyncio.run(
        load_comprehensive_analytics(user.get("id"), exam_category, time_range)
    )

    if not analytics_data["has_data"]:
        show_empty_analytics_state()
        return

    # Create tabs for different analytics views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Overview",
            "🎯 Performance",
            "📚 Topic Analysis",
            "⏱️ Study Patterns",
            "📈 Progress Reports",
        ]
    )

    with tab1:
        render_analytics_overview(analytics_data)

    with tab2:
        render_performance_analysis(analytics_data)

    with tab3:
        render_topic_analysis(analytics_data)

    with tab4:
        render_study_patterns(analytics_data)

    with tab5:
        render_progress_reports(analytics_data, exam_category)


async def load_comprehensive_analytics(
    user_id: str, exam_category: str, time_range: str
) -> Dict[str, Any]:
    """Load comprehensive analytics data for the user"""
    try:
        # Calculate date range
        days_back = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90,
            "All time": 365 * 2,  # 2 years max
        }[time_range]

        start_date = datetime.now() - timedelta(days=days_back)

        # Get user attempts
        attempts = await db.get_user_attempts_by_category(user_id, ExamCategoryCode(exam_category))

        # Filter by date range
        filtered_attempts = [attempt for attempt in attempts if attempt.created_at >= start_date]

        if not filtered_attempts:
            return {"has_data": False}

        # Get mastery data
        mastery_data = await db.get_user_mastery_data(user_id, ExamCategoryCode(exam_category))

        # Calculate comprehensive analytics
        analytics = {
            "has_data": True,
            "time_range": time_range,
            "attempts": filtered_attempts,
            "mastery_data": mastery_data,
            "performance_metrics": calculate_performance_metrics(filtered_attempts),
            "topic_analytics": calculate_topic_analytics(filtered_attempts, mastery_data),
            "study_patterns": analyze_study_patterns(filtered_attempts),
            "progress_tracking": calculate_progress_tracking(filtered_attempts),
            "comparative_analysis": calculate_comparative_analysis(filtered_attempts, mastery_data),
            "recommendations": generate_advanced_recommendations(filtered_attempts, mastery_data),
        }

        return analytics

    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        return {"has_data": False}


def calculate_performance_metrics(attempts: List) -> Dict[str, Any]:
    """Calculate detailed performance metrics"""
    if not attempts:
        return {}

    # Calculate scores for each attempt
    scores = []
    total_questions = 0
    total_correct = 0
    time_spent = []
    difficulty_performance = {"easy": [], "medium": [], "hard": []}

    for attempt in attempts:
        if attempt.answers:
            correct_answers = sum(1 for ans in attempt.answers if ans.get("is_correct", False))
            score = (correct_answers / len(attempt.answers)) * 100
            scores.append(score)
            total_questions += len(attempt.answers)
            total_correct += correct_answers

            if attempt.time_spent_seconds:
                time_spent.append(attempt.time_spent_seconds)

            # Track difficulty performance (if available)
            difficulty = getattr(attempt, "difficulty", "medium").lower()
            if difficulty in difficulty_performance:
                difficulty_performance[difficulty].append(score)

    return {
        "total_attempts": len(attempts),
        "total_questions": total_questions,
        "total_correct": total_correct,
        "overall_accuracy": (total_correct / total_questions * 100) if total_questions > 0 else 0,
        "average_score": np.mean(scores) if scores else 0,
        "median_score": np.median(scores) if scores else 0,
        "score_std": np.std(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "scores_list": scores,
        "improvement_trend": calculate_improvement_trend(scores),
        "average_time_per_question": (
            (np.mean(time_spent) / len(attempts[0].answers)) if time_spent and attempts else 0
        ),
        "difficulty_performance": {
            k: {"avg": np.mean(v), "count": len(v)} for k, v in difficulty_performance.items() if v
        },
        "consistency_score": calculate_consistency_score(scores),
    }


def calculate_topic_analytics(attempts: List, mastery_data: List) -> Dict[str, Any]:
    """Calculate detailed topic-level analytics"""
    topic_performance = {}
    topic_time_spent = {}
    topic_question_count = {}

    # Analyze performance by topic from attempts
    for attempt in attempts:
        if hasattr(attempt, "topic_tags") and attempt.topic_tags:
            for topic in attempt.topic_tags:
                if topic not in topic_performance:
                    topic_performance[topic] = []
                    topic_time_spent[topic] = []
                    topic_question_count[topic] = 0

                if attempt.answers:
                    correct = sum(1 for ans in attempt.answers if ans.get("is_correct", False))
                    score = (correct / len(attempt.answers)) * 100
                    topic_performance[topic].append(score)
                    topic_question_count[topic] += len(attempt.answers)

                    if attempt.time_spent_seconds:
                        topic_time_spent[topic].append(attempt.time_spent_seconds)

    # Combine with mastery data
    topic_analytics = {}
    for topic, scores in topic_performance.items():
        mastery = next((m for m in mastery_data if m.topic_tag == topic), None)

        topic_analytics[topic] = {
            "average_score": np.mean(scores),
            "attempts": len(scores),
            "total_questions": topic_question_count[topic],
            "mastery_level": mastery.mastery_level * 100 if mastery else 0,
            "improvement_trend": calculate_improvement_trend(scores),
            "average_time": np.mean(topic_time_spent[topic]) if topic_time_spent[topic] else 0,
            "last_practiced": mastery.last_practiced if mastery else None,
            "difficulty_rating": categorize_topic_difficulty(np.mean(scores)),
        }

    return topic_analytics


def analyze_study_patterns(attempts: List) -> Dict[str, Any]:
    """Analyze user's study patterns and habits"""
    if not attempts:
        return {}

    # Extract study times
    study_times = [attempt.created_at for attempt in attempts]
    study_hours = [t.hour for t in study_times]
    study_days = [t.weekday() for t in study_times]  # 0=Monday, 6=Sunday

    # Calculate session gaps
    sorted_times = sorted(study_times)
    session_gaps = []
    for i in range(1, len(sorted_times)):
        gap = (sorted_times[i] - sorted_times[i - 1]).total_seconds() / 3600  # hours
        session_gaps.append(gap)

    # Study frequency analysis
    daily_sessions = {}
    for time in study_times:
        date_key = time.date()
        daily_sessions[date_key] = daily_sessions.get(date_key, 0) + 1

    # Peak study times
    hour_counts = {hour: study_hours.count(hour) for hour in range(24)}
    peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 12

    # Study consistency
    recent_days = set()
    cutoff_date = datetime.now() - timedelta(days=30)
    for time in study_times:
        if time >= cutoff_date:
            recent_days.add(time.date())

    return {
        "total_study_sessions": len(attempts),
        "average_session_gap_hours": np.mean(session_gaps) if session_gaps else 0,
        "study_frequency_per_week": len(recent_days) * 7 / 30,  # approximate
        "peak_study_hour": peak_hour,
        "favorite_study_days": [
            day
            for day, count in sorted(
                [(day, study_days.count(day)) for day in set(study_days)],
                key=lambda x: x[1],
                reverse=True,
            )[:3]
        ],
        "study_consistency_score": calculate_study_consistency(daily_sessions),
        "session_length_distribution": analyze_session_lengths(attempts),
        "study_streak_current": calculate_current_streak(study_times),
        "study_streak_longest": calculate_longest_streak(study_times),
    }


def calculate_progress_tracking(attempts: List) -> Dict[str, Any]:
    """Calculate detailed progress tracking metrics"""
    if not attempts:
        return {}

    # Sort attempts by date
    sorted_attempts = sorted(attempts, key=lambda x: x.created_at)

    # Calculate rolling averages
    scores = []
    dates = []
    for attempt in sorted_attempts:
        if attempt.answers:
            correct = sum(1 for ans in attempt.answers if ans.get("is_correct", False))
            score = (correct / len(attempt.answers)) * 100
            scores.append(score)
            dates.append(attempt.created_at)

    if len(scores) < 2:
        return {"insufficient_data": True}

    # Calculate moving averages
    window_size = min(5, len(scores))
    moving_avg = []
    for i in range(window_size - 1, len(scores)):
        avg = np.mean(scores[i - window_size + 1 : i + 1])
        moving_avg.append(avg)

    # Progress milestones
    milestones = {
        "first_50_percent": next((i for i, score in enumerate(scores) if score >= 50), None),
        "first_70_percent": next((i for i, score in enumerate(scores) if score >= 70), None),
        "first_80_percent": next((i for i, score in enumerate(scores) if score >= 80), None),
        "first_90_percent": next((i for i, score in enumerate(scores) if score >= 90), None),
    }

    return {
        "score_progression": list(zip(dates, scores)),
        "moving_average": list(zip(dates[window_size - 1 :], moving_avg)),
        "overall_improvement": scores[-1] - scores[0] if len(scores) > 1 else 0,
        "best_performance_streak": calculate_best_streak(scores, threshold=70),
        "recent_performance_trend": calculate_recent_trend(scores[-10:]),
        "milestones_achieved": {k: v for k, v in milestones.items() if v is not None},
        "progress_velocity": calculate_progress_velocity(scores, dates),
        "plateau_detection": detect_performance_plateaus(scores),
    }


def calculate_comparative_analysis(attempts: List, mastery_data: List) -> Dict[str, Any]:
    """Calculate comparative analysis against benchmarks"""
    if not attempts:
        return {}

    # This would typically compare against anonymized population data
    # For now, we'll use simulated benchmarks

    user_avg_score = np.mean(
        [
            (
                sum(1 for ans in attempt.answers if ans.get("is_correct", False))
                / len(attempt.answers)
            )
            * 100
            for attempt in attempts
            if attempt.answers
        ]
    )

    # Simulated population benchmarks
    population_benchmarks = {
        "beginner": 45,  # 0-3 months
        "intermediate": 65,  # 3-6 months
        "advanced": 80,  # 6+ months
        "expert": 90,  # Top 10%
    }

    # Determine user level
    if user_avg_score >= population_benchmarks["expert"]:
        user_level = "expert"
    elif user_avg_score >= population_benchmarks["advanced"]:
        user_level = "advanced"
    elif user_avg_score >= population_benchmarks["intermediate"]:
        user_level = "intermediate"
    else:
        user_level = "beginner"

    return {
        "user_average_score": user_avg_score,
        "user_level": user_level,
        "percentile_rank": calculate_percentile_rank(user_avg_score),
        "benchmark_comparison": {
            level: {
                "difference": user_avg_score - benchmark,
                "achieved": user_avg_score >= benchmark,
            }
            for level, benchmark in population_benchmarks.items()
        },
        "areas_above_average": calculate_areas_above_average(mastery_data),
        "areas_below_average": calculate_areas_below_average(mastery_data),
        "improvement_potential": calculate_improvement_potential(user_avg_score, user_level),
    }


def generate_advanced_recommendations(attempts: List, mastery_data: List) -> Dict[str, Any]:
    """Generate advanced personalized recommendations"""
    if not attempts:
        return {
            "immediate_actions": ["Start practicing to get personalized recommendations"],
            "study_plan": {},
            "focus_areas": [],
            "time_management": {},
        }

    # Analyze performance trends
    recent_scores = []
    for attempt in sorted(attempts, key=lambda x: x.created_at, reverse=True)[:10]:
        if attempt.answers:
            score = (
                sum(1 for ans in attempt.answers if ans.get("is_correct", False))
                / len(attempt.answers)
            ) * 100
            recent_scores.append(score)

    avg_recent_score = np.mean(recent_scores) if recent_scores else 0

    # Generate recommendations based on performance
    recommendations = {
        "immediate_actions": [],
        "study_plan": {},
        "focus_areas": [],
        "time_management": {},
        "difficulty_adjustment": "",
        "practice_frequency": "",
    }

    # Performance-based recommendations
    if avg_recent_score < 60:
        recommendations["immediate_actions"].extend(
            [
                "Focus on foundational concepts",
                "Practice easier questions to build confidence",
                "Review incorrect answers thoroughly",
            ]
        )
        recommendations["difficulty_adjustment"] = "Start with easy questions"
    elif avg_recent_score < 80:
        recommendations["immediate_actions"].extend(
            [
                "Mix easy and medium difficulty questions",
                "Focus on weak topic areas",
                "Practice timed sessions",
            ]
        )
        recommendations["difficulty_adjustment"] = "Gradually increase to medium difficulty"
    else:
        recommendations["immediate_actions"].extend(
            [
                "Challenge yourself with hard questions",
                "Focus on advanced topics",
                "Practice full mock exams",
            ]
        )
        recommendations["difficulty_adjustment"] = "Focus on hard difficulty questions"

    # Topic-based recommendations
    weak_topics = [m.topic_tag for m in mastery_data if m.mastery_level < 0.6]
    if weak_topics:
        recommendations["focus_areas"] = weak_topics[:3]
        recommendations["immediate_actions"].append(
            f"Prioritize studying: {', '.join(weak_topics[:2])}"
        )

    # Study frequency recommendations
    study_pattern = analyze_study_patterns(attempts)
    if study_pattern.get("study_frequency_per_week", 0) < 3:
        recommendations["practice_frequency"] = "Increase practice to 3-4 sessions per week"
    elif study_pattern.get("study_frequency_per_week", 0) > 10:
        recommendations["practice_frequency"] = "Consider reducing frequency to avoid burnout"
    else:
        recommendations["practice_frequency"] = "Maintain current practice frequency"

    return recommendations


# Helper functions for calculations


def calculate_improvement_trend(scores: List[float]) -> str:
    """Calculate improvement trend from scores"""
    if len(scores) < 3:
        return "insufficient_data"

    # Linear regression to find trend
    x = list(range(len(scores)))
    slope = np.polyfit(x, scores, 1)[0]

    if slope > 2:
        return "strong_improvement"
    elif slope > 0.5:
        return "improving"
    elif slope > -0.5:
        return "stable"
    elif slope > -2:
        return "declining"
    else:
        return "strong_decline"


def calculate_consistency_score(scores: List[float]) -> float:
    """Calculate consistency score (lower std dev = higher consistency)"""
    if len(scores) < 2:
        return 0

    std_dev = np.std(scores)
    mean_score = np.mean(scores)

    # Normalize consistency score (0-100, higher is more consistent)
    if mean_score == 0:
        return 0

    coefficient_of_variation = std_dev / mean_score
    consistency = max(0, 100 - (coefficient_of_variation * 100))
    return min(100, consistency)


def categorize_topic_difficulty(average_score: float) -> str:
    """Categorize topic difficulty based on average performance"""
    if average_score >= 80:
        return "easy"
    elif average_score >= 60:
        return "medium"
    else:
        return "hard"


def calculate_study_consistency(daily_sessions: Dict) -> float:
    """Calculate study consistency score"""
    if not daily_sessions:
        return 0

    # Calculate coefficient of variation for daily session counts
    session_counts = list(daily_sessions.values())
    if len(session_counts) < 2:
        return 50  # Neutral score for insufficient data

    mean_sessions = np.mean(session_counts)
    std_sessions = np.std(session_counts)

    if mean_sessions == 0:
        return 0

    cv = std_sessions / mean_sessions
    consistency = max(0, 100 - (cv * 50))  # Convert to 0-100 scale
    return min(100, consistency)


def analyze_session_lengths(attempts: List) -> Dict[str, Any]:
    """Analyze distribution of session lengths"""
    session_lengths = []
    for attempt in attempts:
        if attempt.time_spent_seconds:
            minutes = attempt.time_spent_seconds / 60
            session_lengths.append(minutes)

    if not session_lengths:
        return {"no_data": True}

    return {
        "average_minutes": np.mean(session_lengths),
        "median_minutes": np.median(session_lengths),
        "short_sessions": len([s for s in session_lengths if s < 10]),  # < 10 min
        "medium_sessions": len([s for s in session_lengths if 10 <= s <= 30]),  # 10-30 min
        "long_sessions": len([s for s in session_lengths if s > 30]),  # > 30 min
        "optimal_length_range": "15-25 minutes for best retention",
    }


def calculate_current_streak(study_times: List) -> int:
    """Calculate current consecutive study streak"""
    if not study_times:
        return 0

    # Get unique study dates
    study_dates = sorted(set(t.date() for t in study_times), reverse=True)
    current_date = datetime.now().date()

    streak = 0
    for i, date in enumerate(study_dates):
        expected_date = current_date - timedelta(days=i)
        if date == expected_date:
            streak += 1
        else:
            break

    return streak


def calculate_longest_streak(study_times: List) -> int:
    """Calculate longest consecutive study streak"""
    if not study_times:
        return 0

    study_dates = sorted(set(t.date() for t in study_times))
    longest_streak = 0
    current_streak = 1

    for i in range(1, len(study_dates)):
        if (study_dates[i] - study_dates[i - 1]).days == 1:
            current_streak += 1
        else:
            longest_streak = max(longest_streak, current_streak)
            current_streak = 1

    return max(longest_streak, current_streak)


def calculate_best_streak(scores: List[float], threshold: float = 70) -> int:
    """Calculate best performance streak above threshold"""
    if not scores:
        return 0

    best_streak = 0
    current_streak = 0

    for score in scores:
        if score >= threshold:
            current_streak += 1
            best_streak = max(best_streak, current_streak)
        else:
            current_streak = 0

    return best_streak


def calculate_recent_trend(recent_scores: List[float]) -> str:
    """Calculate trend for recent scores"""
    if len(recent_scores) < 3:
        return "insufficient_data"

    # Compare first half vs second half
    mid_point = len(recent_scores) // 2
    first_half_avg = np.mean(recent_scores[:mid_point])
    second_half_avg = np.mean(recent_scores[mid_point:])

    difference = second_half_avg - first_half_avg

    if difference > 5:
        return "improving"
    elif difference < -5:
        return "declining"
    else:
        return "stable"


def calculate_progress_velocity(scores: List[float], dates: List) -> float:
    """Calculate rate of improvement (points per day)"""
    if len(scores) < 2:
        return 0

    # Linear regression of scores over time
    time_deltas = [(date - dates[0]).days for date in dates]
    if max(time_deltas) == 0:
        return 0

    slope = np.polyfit(time_deltas, scores, 1)[0]
    return slope  # Points per day


def detect_performance_plateaus(scores: List[float]) -> Dict[str, Any]:
    """Detect if user is experiencing performance plateaus"""
    if len(scores) < 10:
        return {"plateau_detected": False, "reason": "insufficient_data"}

    # Look at recent 10 scores
    recent_scores = scores[-10:]
    score_range = max(recent_scores) - min(recent_scores)

    # If recent scores vary by less than 10 points, consider it a plateau
    if score_range < 10:
        avg_score = np.mean(recent_scores)
        return {
            "plateau_detected": True,
            "plateau_level": avg_score,
            "recommendation": get_plateau_recommendation(avg_score),
        }

    return {"plateau_detected": False}


def get_plateau_recommendation(plateau_level: float) -> str:
    """Get recommendation for breaking plateau"""
    if plateau_level < 60:
        return "Focus on fundamentals and easier questions"
    elif plateau_level < 80:
        return "Try different question types and increase difficulty"
    else:
        return "Challenge yourself with advanced topics and exam simulations"


def calculate_percentile_rank(user_score: float) -> int:
    """Calculate percentile rank (simulated)"""
    # Simulated distribution - in reality this would come from actual user data
    # Assuming normal distribution with mean=65, std=15
    from scipy import stats

    percentile = stats.norm.cdf(user_score, loc=65, scale=15) * 100
    return min(99, max(1, int(percentile)))


def calculate_areas_above_average(mastery_data: List) -> List[str]:
    """Calculate topic areas where user is above average"""
    # Simulated average mastery level of 0.65 (65%)
    return [m.topic_tag for m in mastery_data if m.mastery_level > 0.65]


def calculate_areas_below_average(mastery_data: List) -> List[str]:
    """Calculate topic areas where user is below average"""
    return [m.topic_tag for m in mastery_data if m.mastery_level < 0.65]


def calculate_improvement_potential(user_score: float, user_level: str) -> Dict[str, Any]:
    """Calculate improvement potential and target scores"""
    level_targets = {
        "beginner": {"target": 65, "timeframe": "2-3 months"},
        "intermediate": {"target": 80, "timeframe": "1-2 months"},
        "advanced": {"target": 90, "timeframe": "3-4 weeks"},
        "expert": {"target": 95, "timeframe": "2-3 weeks"},
    }

    current_target = level_targets.get(user_level, level_targets["beginner"])
    improvement_needed = max(0, current_target["target"] - user_score)

    return {
        "target_score": current_target["target"],
        "improvement_needed": improvement_needed,
        "estimated_timeframe": current_target["timeframe"],
        "weekly_improvement_target": (
            improvement_needed / 8 if improvement_needed > 0 else 0
        ),  # Assume 8 weeks
    }


# UI Rendering Functions


def show_empty_analytics_state():
    """Show empty state when user has no data"""
    st.info("📊 No analytics data available yet")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        ### 🎯 Start Practicing
        Take your first practice quiz to begin tracking your progress and get personalized insights.
        """
        )
        if st.button("🚀 Start First Practice", type="primary"):
            st.session_state.page = "topic_practice"
            st.rerun()

    with col2:
        st.markdown(
            """
        ### 📚 Browse Topics
        Explore available topics and start with areas that interest you most.
        """
        )
        if st.button("📖 Browse Topics"):
            st.session_state.page = "topic_practice"
            st.rerun()

    with col3:
        st.markdown(
            """
        ### 🎓 Take Mock Exam
        Try a full mock exam to establish your baseline performance.
        """
        )
        if st.button("📝 Mock Exam"):
            st.session_state.page = "mock_exams"
            st.rerun()


def render_analytics_overview(analytics_data: Dict[str, Any]):
    """Render the overview tab with key metrics"""
    st.subheader("📊 Performance Overview")

    metrics = analytics_data["performance_metrics"]

    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Overall Accuracy",
            f"{metrics['overall_accuracy']:.1f}%",
            delta=f"{metrics['improvement_trend'].replace('_', ' ').title()}",
        )

    with col2:
        st.metric(
            "Total Questions",
            metrics["total_questions"],
            delta=f"{metrics['total_attempts']} sessions",
        )

    with col3:
        st.metric(
            "Average Score",
            f"{metrics['average_score']:.1f}%",
            delta=f"±{metrics['score_std']:.1f}% variation",
        )

    with col4:
        st.metric(
            "Best Score",
            f"{metrics['max_score']:.1f}%",
            delta=f"Range: {metrics['max_score'] - metrics['min_score']:.1f}%",
        )

    with col5:
        st.metric(
            "Consistency", f"{metrics['consistency_score']:.0f}/100", delta="Higher is better"
        )

    # Performance distribution chart
    st.subheader("📈 Score Distribution")

    if metrics["scores_list"]:
        fig = px.histogram(
            x=metrics["scores_list"],
            nbins=20,
            title="Score Distribution",
            labels={"x": "Score (%)", "y": "Frequency"},
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Quick insights
    st.subheader("💡 Quick Insights")

    insights = []

    if metrics["improvement_trend"] == "strong_improvement":
        insights.append("🚀 Excellent progress! You're showing strong improvement.")
    elif metrics["improvement_trend"] == "improving":
        insights.append("📈 You're making steady progress. Keep it up!")
    elif metrics["improvement_trend"] == "stable":
        insights.append(
            "📊 Your performance is stable. Consider challenging yourself with harder questions."
        )

    if metrics["consistency_score"] > 80:
        insights.append("🎯 Great consistency in your performance!")
    elif metrics["consistency_score"] < 50:
        insights.append("🎲 Your scores vary quite a bit. Focus on consistent practice habits.")

    if metrics["average_score"] > 80:
        insights.append("⭐ Excellent average score! You're ready for advanced challenges.")
    elif metrics["average_score"] < 60:
        insights.append("📚 Focus on building fundamentals to improve your average score.")

    for insight in insights:
        st.success(insight)


def render_performance_analysis(analytics_data: Dict[str, Any]):
    """Render detailed performance analysis"""
    st.subheader("🎯 Detailed Performance Analysis")

    progress_data = analytics_data["progress_tracking"]
    metrics = analytics_data["performance_metrics"]

    if progress_data.get("insufficient_data"):
        st.info("Take more practice sessions to see detailed performance analysis")
        return

    # Score progression chart
    st.write("**📈 Score Progression Over Time**")

    if progress_data["score_progression"]:
        dates, scores = zip(*progress_data["score_progression"])

        fig = go.Figure()

        # Add raw scores
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=scores,
                mode="markers+lines",
                name="Individual Scores",
                line=dict(color="lightblue", width=2),
                marker=dict(size=6),
            )
        )

        # Add moving average
        if progress_data["moving_average"]:
            ma_dates, ma_scores = zip(*progress_data["moving_average"])
            fig.add_trace(
                go.Scatter(
                    x=ma_dates,
                    y=ma_scores,
                    mode="lines",
                    name="Moving Average (5 sessions)",
                    line=dict(color="red", width=3),
                )
            )

        fig.update_layout(
            title="Performance Progression",
            xaxis_title="Date",
            yaxis_title="Score (%)",
            height=400,
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

    # Performance by difficulty
    st.write("**📊 Performance by Difficulty Level**")

    if metrics["difficulty_performance"]:
        difficulty_data = metrics["difficulty_performance"]

        difficulties = list(difficulty_data.keys())
        avg_scores = [difficulty_data[d]["avg"] for d in difficulties]
        attempt_counts = [difficulty_data[d]["count"] for d in difficulties]

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Average Score by Difficulty", "Attempts by Difficulty"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]],
        )

        fig.add_trace(
            go.Bar(x=difficulties, y=avg_scores, name="Avg Score", marker_color="skyblue"),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Bar(x=difficulties, y=attempt_counts, name="Attempts", marker_color="lightcoral"),
            row=1,
            col=2,
        )

        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Milestones and achievements
    st.write("**🏆 Milestones & Achievements**")

    if progress_data["milestones_achieved"]:
        milestone_names = {
            "first_50_percent": "🥉 First 50% Score",
            "first_70_percent": "🥈 First 70% Score",
            "first_80_percent": "🥇 First 80% Score",
            "first_90_percent": "💎 First 90% Score",
        }

        achieved_milestones = progress_data["milestones_achieved"]

        cols = st.columns(min(4, len(achieved_milestones)))
        for i, (milestone, attempt_num) in enumerate(achieved_milestones.items()):
            with cols[i % len(cols)]:
                st.success(
                    f"{milestone_names.get(milestone, milestone)}\nAchieved on attempt #{attempt_num + 1}"
                )
    else:
        st.info("Keep practicing to unlock achievement milestones!")


def render_topic_analysis(analytics_data: Dict[str, Any]):
    """Render topic-level performance analysis"""
    st.subheader("📚 Topic Performance Analysis")

    topic_analytics = analytics_data["topic_analytics"]

    if not topic_analytics:
        st.info("Practice different topics to see topic-level analysis")
        return

    # Topic performance summary table
    st.write("**📊 Topic Performance Summary**")

    topic_df = pd.DataFrame(
        [
            {
                "Topic": topic,
                "Avg Score (%)": f"{data['average_score']:.1f}",
                "Mastery Level (%)": f"{data['mastery_level']:.1f}",
                "Attempts": data["attempts"],
                "Questions": data["total_questions"],
                "Trend": data["improvement_trend"].replace("_", " ").title(),
                "Difficulty": data["difficulty_rating"].title(),
            }
            for topic, data in topic_analytics.items()
        ]
    )

    # Color code by performance
    def color_performance(val):
        if "Score" in val.name or "Mastery" in val.name:
            numeric_val = float(val.replace("%", ""))
            if numeric_val >= 80:
                return ["background-color: #d4edda"] * len(val)  # Green
            elif numeric_val >= 60:
                return ["background-color: #fff3cd"] * len(val)  # Yellow
            else:
                return ["background-color: #f8d7da"] * len(val)  # Red
        return [""] * len(val)

    styled_df = topic_df.style.apply(color_performance, axis=0)
    st.dataframe(styled_df, use_container_width=True)

    # Topic mastery radar chart
    st.write("**🎯 Topic Mastery Radar**")

    if len(topic_analytics) >= 3:
        topics = list(topic_analytics.keys())[:8]  # Limit to 8 for readability
        mastery_scores = [topic_analytics[topic]["mastery_level"] for topic in topics]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=mastery_scores,
                theta=topics,
                fill="toself",
                name="Mastery Level",
                line_color="rgb(42, 157, 143)",
            )
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title="Topic Mastery Levels",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    # Improvement recommendations
    st.write("**💡 Topic-Specific Recommendations**")

    weak_topics = [
        (topic, data) for topic, data in topic_analytics.items() if data["mastery_level"] < 60
    ]
    strong_topics = [
        (topic, data) for topic, data in topic_analytics.items() if data["mastery_level"] > 80
    ]

    col1, col2 = st.columns(2)

    with col1:
        st.write("**⚡ Focus Areas (Need Improvement)**")
        if weak_topics:
            for topic, data in sorted(weak_topics, key=lambda x: x[1]["mastery_level"])[:5]:
                st.warning(
                    f"**{topic}**: {data['mastery_level']:.1f}% mastery - {data['attempts']} attempts"
                )
        else:
            st.success("Great job! No weak areas identified.")

    with col2:
        st.write("**⭐ Strong Areas**")
        if strong_topics:
            for topic, data in sorted(
                strong_topics, key=lambda x: x[1]["mastery_level"], reverse=True
            )[:5]:
                st.success(f"**{topic}**: {data['mastery_level']:.1f}% mastery - Well done!")
        else:
            st.info("Keep practicing to identify your strong areas!")


def render_study_patterns(analytics_data: Dict[str, Any]):
    """Render study pattern analysis"""
    st.subheader("⏱️ Study Pattern Analysis")

    study_patterns = analytics_data["study_patterns"]

    if not study_patterns:
        st.info("Complete more practice sessions to analyze your study patterns")
        return

    # Study habits overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Study Sessions",
            study_patterns["total_study_sessions"],
            delta=f"{study_patterns['study_frequency_per_week']:.1f}/week",
        )

    with col2:
        peak_hour = study_patterns["peak_study_hour"]
        time_str = f"{peak_hour:02d}:00"
        st.metric("Peak Study Time", time_str, delta="Most active hour")

    with col3:
        st.metric(
            "Current Streak",
            f"{study_patterns['study_streak_current']} days",
            delta=f"Best: {study_patterns['study_streak_longest']} days",
        )

    with col4:
        st.metric(
            "Study Consistency",
            f"{study_patterns['study_consistency_score']:.0f}/100",
            delta="Regularity score",
        )

    # Study time distribution
    st.write("**📅 Study Day Preferences**")

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    favorite_days = study_patterns["favorite_study_days"]

    if favorite_days:
        cols = st.columns(len(favorite_days))
        for i, (day_num, count) in enumerate(favorite_days):
            with cols[i]:
                day_name = day_names[day_num] if day_num < len(day_names) else f"Day {day_num}"
                st.info(f"**{day_name}**\n{count} sessions")

    # Session length analysis
    st.write("**⏰ Session Length Analysis**")

    session_data = study_patterns["session_length_distribution"]

    if not session_data.get("no_data"):
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Average Session", f"{session_data['average_minutes']:.1f} min")
            st.metric("Median Session", f"{session_data['median_minutes']:.1f} min")

        with col2:
            # Session length distribution
            session_lengths = ["Short (<10min)", "Medium (10-30min)", "Long (>30min)"]
            session_counts = [
                session_data["short_sessions"],
                session_data["medium_sessions"],
                session_data["long_sessions"],
            ]

            fig = px.pie(
                values=session_counts, names=session_lengths, title="Session Length Distribution"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        st.info(f"💡 **Tip**: {session_data['optimal_length_range']}")

    # Study pattern recommendations
    st.write("**📋 Study Pattern Recommendations**")

    recommendations = []

    if study_patterns["study_frequency_per_week"] < 3:
        recommendations.append(
            "📈 Increase study frequency to 3-4 sessions per week for better retention"
        )
    elif study_patterns["study_frequency_per_week"] > 8:
        recommendations.append("⚠️ Consider reducing frequency to avoid burnout")

    if study_patterns["study_consistency_score"] < 60:
        recommendations.append("📅 Try to establish a more regular study schedule")

    if study_patterns["study_streak_current"] == 0:
        recommendations.append("🔥 Start a new study streak today!")
    elif study_patterns["study_streak_current"] < 7:
        recommendations.append(
            f"🎯 Extend your streak to 7 days! Currently at {study_patterns['study_streak_current']}"
        )

    if session_data and not session_data.get("no_data"):
        if session_data["average_minutes"] < 10:
            recommendations.append(
                "⏱️ Consider longer study sessions (15-25 minutes) for deeper learning"
            )
        elif session_data["average_minutes"] > 45:
            recommendations.append("💡 Break longer sessions into shorter, focused intervals")

    for rec in recommendations:
        st.info(rec)


def render_progress_reports(analytics_data: Dict[str, Any], exam_category: str):
    """Render detailed progress reports"""
    st.subheader("📈 Comprehensive Progress Report")

    progress_data = analytics_data["progress_tracking"]
    comparative_data = analytics_data["comparative_analysis"]
    recommendations = analytics_data["recommendations"]

    # Progress summary
    st.write("**📊 Progress Summary**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if not progress_data.get("insufficient_data"):
            improvement = progress_data["overall_improvement"]
            st.metric("Overall Improvement", f"{improvement:+.1f}%", delta="Since first attempt")

    with col2:
        user_level = comparative_data.get("user_level", "beginner").title()
        percentile = comparative_data.get("percentile_rank", 50)
        st.metric("Performance Level", user_level, delta=f"{percentile}th percentile")

    with col3:
        if not progress_data.get("insufficient_data"):
            velocity = progress_data.get("progress_velocity", 0)
            st.metric("Progress Rate", f"{velocity:.2f}%/day", delta="Improvement velocity")

    # Benchmark comparison
    st.write("**🎯 Benchmark Comparison**")

    if comparative_data:
        user_score = comparative_data["user_average_score"]
        benchmark_comparison = comparative_data["benchmark_comparison"]

        # Create benchmark chart
        levels = list(benchmark_comparison.keys())
        benchmarks = [85, 75, 65, 45]  # Simulated benchmark scores
        user_scores = [user_score] * len(levels)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=levels,
                y=benchmarks,
                name="Benchmark Scores",
                marker_color="lightgray",
                opacity=0.7,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=levels,
                y=user_scores,
                mode="markers+lines",
                name="Your Score",
                marker=dict(size=12, color="red"),
                line=dict(color="red", width=3),
            )
        )

        fig.update_layout(
            title="Performance vs. Benchmarks",
            xaxis_title="Performance Level",
            yaxis_title="Score (%)",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

    # Detailed recommendations
    st.write("**💡 Personalized Action Plan**")

    if recommendations:
        st.write("**🎯 Immediate Actions:**")
        for action in recommendations["immediate_actions"]:
            st.write(f"• {action}")

        if recommendations["focus_areas"]:
            st.write("**📚 Priority Focus Areas:**")
            for area in recommendations["focus_areas"]:
                st.write(f"• {area}")

        st.write("**📈 Recommended Settings:**")
        st.info(
            f"**Difficulty Level**: {recommendations.get('difficulty_adjustment', 'Continue current level')}"
        )
        st.info(
            f"**Practice Frequency**: {recommendations.get('practice_frequency', 'Maintain current frequency')}"
        )

    # Improvement targets
    if comparative_data and "improvement_potential" in comparative_data:
        potential = comparative_data["improvement_potential"]

        st.write("**🎯 Improvement Targets**")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Target Score",
                f"{potential['target_score']}%",
                delta=f"+{potential['improvement_needed']:.1f}% needed",
            )

        with col2:
            st.metric(
                "Est. Timeframe",
                potential["estimated_timeframe"],
                delta=f"{potential['weekly_improvement_target']:.1f}%/week target",
            )

    # Export report button
    st.write("**📁 Export Options**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Generate PDF Report"):
            st.info("PDF report generation coming soon!")

    with col2:
        if st.button("📈 Export Data"):
            # Create summary data for export
            summary_data = {
                "exam_category": exam_category,
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "performance_summary": analytics_data["performance_metrics"],
                "progress_summary": (
                    progress_data if not progress_data.get("insufficient_data") else {}
                ),
                "recommendations": recommendations,
            }

            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(summary_data, indent=2, default=str),
                file_name=f"progress_report_{exam_category}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
            )

    with col3:
        if st.button("📧 Email Report"):
            st.info("Email report feature coming soon!")


# Main entry point
if __name__ == "__main__":
    show_analytics_dashboard()
