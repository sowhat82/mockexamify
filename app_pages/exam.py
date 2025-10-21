"""
Enhanced Exam Engine for MockExamify
Comprehensive exam interface with timer, navigation, and result calculation
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

import config
from auth_utils import AuthUtils, run_async
from db import db
from openrouter_utils import generate_explanation
from pdf_utils import generate_exam_results_pdf


def show_exam():
    """Main exam interface - called by streamlit_app.py"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated():
        st.error("Please log in to access the exam page")
        st.stop()

    user = auth.get_current_user()

    # Initialize session state for exam
    if "exam_state" not in st.session_state:
        st.session_state.exam_state = "not_started"
    if "current_mock" not in st.session_state:
        st.session_state.current_mock = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "exam_id" not in st.session_state:
        st.session_state.exam_id = None
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "time_limit" not in st.session_state:
        st.session_state.time_limit = 60  # minutes
    if "flagged_questions" not in st.session_state:
        st.session_state.flagged_questions = set()

    # Check if this is a pool-based exam (coming from dashboard)
    if "pool_exam" in st.session_state and st.session_state.exam_state == "not_started":
        start_pool_exam(st.session_state.pool_exam, user)
        return

    # Route based on exam state
    if st.session_state.exam_state == "not_started":
        show_exam_selection(user)
    elif st.session_state.exam_state == "in_progress":
        show_exam_interface(user)
    elif st.session_state.exam_state == "completed":
        show_exam_results(user)
    else:
        st.error("Invalid exam state")
        reset_exam_state()


def show_exam_selection(user: Dict[str, Any]):
    """Display available exams for selection"""
    st.markdown("# 📝 Take Mock Exam")
    st.markdown("*Choose an exam to test your knowledge*")

    # Load available mocks
    try:
        mocks_raw = run_async(db.get_all_mocks())

        if not mocks_raw:
            st.warning("⚠️ No mock exams available. Please contact admin.")
            return

        # Convert Mock objects to dictionaries
        mocks = []
        for mock in mocks_raw:
            if hasattr(mock, "__dict__"):
                mock_dict = {
                    "id": mock.id,
                    "title": mock.title,
                    "description": mock.description,
                    "category": getattr(mock, "category", "General"),
                    "questions": mock.questions,
                    "price_credits": mock.price_credits,
                    "time_limit_minutes": getattr(mock, "time_limit_minutes", 60),
                    "difficulty": getattr(mock, "difficulty", "Medium"),
                    "explanation_enabled": mock.explanation_enabled,
                    "is_active": mock.is_active,
                }
                mocks.append(mock_dict)
            else:
                mocks.append(mock)

        # Display user credits
        user_data = run_async(db.get_user_by_id(user["id"]))
        credits = user_data.credits_balance if user_data else 0

        # Credits display
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(
                f"""
            <div style="background: linear-gradient(90deg, #1f77b4, #ff7f0e);
                       padding: 1rem; border-radius: 0.5rem; color: white;">
                <h3 style="margin: 0;">💰 Available Credits: {credits}</h3>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            if st.button("💳 Buy Credits", use_container_width=True):
                st.session_state.page = "purchase_credits"
                st.rerun()

        with col3:
            if st.button("📈 Past Attempts", use_container_width=True):
                st.session_state.page = "past_attempts"
                st.rerun()

        st.markdown("---")

        # Mock exam cards
        for mock in mocks:
            try:
                # mock is already a dictionary from conversion above
                # Parse questions
                if isinstance(mock.get("questions"), str):
                    questions = json.loads(mock["questions"])
                else:
                    questions = mock.get("questions", [])

                questions_count = len(questions)
                price_credits = mock.get("price_credits", 1)

                with st.container():
                    # Mock exam card
                    st.markdown(
                        f"""
                    <div style="border: 2px solid #1f77b4; border-radius: 1rem; padding: 1.5rem;
                               margin-bottom: 1rem; background: white;">
                        <h3 style="color: #1f77b4; margin-top: 0;">📚 {mock.get('title', 'Untitled Mock')}</h3>
                        <p style="color: #666; margin-bottom: 1rem;">{mock.get('description', 'No description available')}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Exam details
                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        st.metric("📊 Questions", questions_count)

                    with col2:
                        time_limit = mock.get("time_limit_minutes", 60)
                        st.metric("⏱️ Duration", f"{time_limit} min")

                    with col3:
                        st.metric(
                            "💰 Cost", f"{price_credits} credit{'s' if price_credits > 1 else ''}"
                        )

                    with col4:
                        difficulty = mock.get("difficulty", "Medium").title()
                        st.metric("🎯 Difficulty", difficulty)

                    with col5:
                        if credits >= price_credits:
                            if st.button(
                                f"🚀 Start Exam",
                                key=f"start_{mock['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                start_exam(mock, user)
                        else:
                            st.button("💳 Need Credits", disabled=True, use_container_width=True)

                    st.markdown("---")

            except Exception as e:
                st.error(f"Error loading exam: {e}")

    except Exception as e:
        st.error(f"Error loading exams: {e}")


def start_exam(mock: Dict[str, Any], user: Dict[str, Any]):
    """Initialize and start an exam"""
    try:
        # Parse questions
        if isinstance(mock.get("questions"), str):
            questions = json.loads(mock["questions"])
        else:
            questions = mock.get("questions", [])

        if not questions:
            st.error("No questions found in this exam")
            return

        # Check and deduct credits
        credits_needed = mock.get("price_credits", 1)
        deduct_success = run_async(db.deduct_credits_from_user(user["id"], credits_needed))

        if not deduct_success:
            st.error("Failed to process payment. Please check your credits balance.")
            return

        # Initialize exam session
        st.session_state.current_mock = mock
        st.session_state.questions = questions
        st.session_state.answers = {}
        st.session_state.current_question = 0
        st.session_state.start_time = datetime.now()
        st.session_state.exam_id = str(uuid.uuid4())
        st.session_state.time_limit = mock.get("time_limit_minutes", 60)
        st.session_state.flagged_questions = set()
        st.session_state.exam_state = "in_progress"

        st.success(f"Exam started! You have {st.session_state.time_limit} minutes.")
        st.rerun()

    except Exception as e:
        st.error(f"Error starting exam: {e}")


def start_pool_exam(pool_exam_config: Dict[str, Any], user: Dict[str, Any]):
    """Initialize and start a pool-based exam"""
    try:
        pool_id = pool_exam_config.get("pool_id")
        pool_name = pool_exam_config.get("pool_name")
        question_count = pool_exam_config.get("question_count")
        credits_needed = pool_exam_config.get("price_credits", 1)  # Match dashboard.py key name

        # Get random questions from pool
        questions = run_async(db.get_random_pool_questions(pool_id, question_count))

        if not questions:
            st.error(f"No questions available in {pool_name} pool")
            # Clear pool_exam from session state
            if "pool_exam" in st.session_state:
                del st.session_state.pool_exam
            return

        # Check and deduct credits
        deduct_success = run_async(db.deduct_credits_from_user(user["id"], credits_needed))

        if not deduct_success:
            st.error("Failed to process payment. Please check your credits balance.")
            # Clear pool_exam from session state
            if "pool_exam" in st.session_state:
                del st.session_state.pool_exam
            return

        # Update user's credits in session state
        if "current_user" in st.session_state:
            st.session_state.current_user["credits_balance"] -= credits_needed

        # Create a mock-like structure for pool exam
        pool_mock = {
            "id": pool_id,
            "title": pool_name,
            "description": f"Dynamic exam from {pool_name} pool",
            "is_pool_exam": True,  # Flag to identify pool-based exams
            "pool_id": pool_id,
            "category": pool_exam_config.get("category", "General"),
        }

        # Initialize exam session
        st.session_state.current_mock = pool_mock
        st.session_state.questions = questions
        st.session_state.answers = {}
        st.session_state.current_question = 0
        st.session_state.start_time = datetime.now()
        st.session_state.exam_id = str(uuid.uuid4())
        st.session_state.time_limit = 60  # Default 60 minutes for pool exams
        st.session_state.flagged_questions = set()
        st.session_state.exam_state = "in_progress"

        # Clear pool_exam from session state
        if "pool_exam" in st.session_state:
            del st.session_state.pool_exam

        st.success(f"Exam started! {question_count} questions from {pool_name}")
        st.rerun()

    except Exception as e:
        st.error(f"Error starting pool exam: {e}")
        # Clear pool_exam from session state
        if "pool_exam" in st.session_state:
            del st.session_state.pool_exam


def show_exam_interface(user: Dict[str, Any]):
    """Display the main exam interface"""
    if not st.session_state.current_mock or not st.session_state.questions:
        st.error("Exam data not found")
        reset_exam_state()
        return

    mock = st.session_state.current_mock
    questions = st.session_state.questions
    current_q = st.session_state.current_question

    # Timer disabled per user request
    # # Check time limit
    # if st.session_state.start_time:
    #     elapsed_time = datetime.now() - st.session_state.start_time
    #     time_limit_seconds = st.session_state.time_limit * 60
    #     remaining_seconds = time_limit_seconds - elapsed_time.total_seconds()
    #
    #     if remaining_seconds <= 0:
    #         # Time's up - auto submit
    #         st.warning("⏰ Time's up! Auto-submitting exam...")
    #         submit_exam(user, auto_submit=True)
    #         return

    # Header with progress (timer removed)
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"# 📝 {mock.get('title', 'Mock Exam')}")
        progress = (current_q + 1) / len(questions)
        st.progress(progress, text=f"Question {current_q + 1} of {len(questions)}")

    with col2:
        answered_count = len(st.session_state.answers)
        flagged_count = len(st.session_state.flagged_questions)

        st.markdown(
            f"""
        <div style="background: #f0f8ff; padding: 1rem; border-radius: 0.5rem;">
            <p style="margin: 0; color: #000000;"><strong style="color: #000000;">✅ Answered:</strong> {answered_count}/{len(questions)}</p>
            <p style="margin: 0; color: #000000;"><strong style="color: #000000;">🚩 Flagged:</strong> {flagged_count}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Display current question
    if current_q < len(questions):
        question = questions[current_q]
        display_question(question, current_q, user)

    # Navigation and controls
    st.markdown("---")
    show_exam_navigation(user, len(questions))


def display_question(question: Dict[str, Any], question_index: int, user: Dict[str, Any]):
    """Display a single question with answer choices"""

    # Question header
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f"### Question {question_index + 1}")

    with col2:
        # Flag question button
        is_flagged = question_index in st.session_state.flagged_questions
        flag_text = "🚩 Flagged" if is_flagged else "🏳️ Flag"
        flag_type = "secondary" if is_flagged else "primary"

        if st.button(flag_text, key=f"flag_{question_index}", type=flag_type):
            if is_flagged:
                st.session_state.flagged_questions.discard(question_index)
            else:
                st.session_state.flagged_questions.add(question_index)
            st.rerun()

    # Question text
    question_text = question.get("question", "")
    st.markdown(f"**{question_text}**")

    # Scenario if present
    if "scenario" in question and question["scenario"]:
        with st.expander("📋 Scenario", expanded=False):
            st.markdown(question["scenario"])

    # Answer choices
    choices = question.get("choices", [])
    if not choices:
        st.error("No choices available for this question")
        return

    # Get current answer
    current_answer = st.session_state.answers.get(question_index)

    # Display radio buttons for choices
    answer_choice = st.radio(
        "Select your answer:",
        options=range(len(choices)),
        format_func=lambda x: f"{chr(65 + x)}. {choices[x]}",
        index=current_answer if current_answer is not None else None,
        key=f"answer_{question_index}",
    )

    # Save answer when selected
    if answer_choice is not None:
        st.session_state.answers[question_index] = answer_choice

    # Show answer confidence (optional)
    with st.expander("💡 Answer Confidence (Optional)", expanded=False):
        confidence = st.slider(
            "How confident are you in this answer?",
            0,
            100,
            50,
            help="This helps us understand your learning progress",
            key=f"confidence_{question_index}",
        )


def show_exam_navigation(user: Dict[str, Any], total_questions: int):
    """Display navigation controls for the exam"""
    current_q = st.session_state.current_question

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    # Previous button
    with col1:
        if current_q > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.current_question = current_q - 1
                st.rerun()
        else:
            st.button("⬅️ Previous", disabled=True, use_container_width=True)

    # Next button
    with col2:
        if current_q < total_questions - 1:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.current_question = current_q + 1
                st.rerun()
        else:
            st.button("Next ➡️", disabled=True, use_container_width=True)

    # Question navigator
    with col3:
        with st.expander("🗺️ Question Navigator", expanded=False):
            cols = st.columns(5)
            for i in range(total_questions):
                col_index = i % 5
                with cols[col_index]:
                    # Determine button style
                    if i in st.session_state.answers:
                        if i in st.session_state.flagged_questions:
                            button_text = f"🚩{i+1}"
                            button_type = "secondary"
                        else:
                            button_text = f"✅{i+1}"
                            button_type = "primary"
                    else:
                        if i in st.session_state.flagged_questions:
                            button_text = f"🚩{i+1}"
                            button_type = "secondary"
                        else:
                            button_text = f"⚪{i+1}"
                            button_type = "primary"

                    if st.button(button_text, key=f"nav_{i}", use_container_width=True):
                        st.session_state.current_question = i
                        st.rerun()

    # Review and Submit buttons
    with col4:
        if st.button("📋 Review", use_container_width=True):
            show_review_modal()

    with col5:
        if st.button("✅ Submit", type="primary", use_container_width=True):
            submit_exam(user)


def show_review_modal():
    """Show exam review in a modal"""
    with st.expander("📋 Exam Review", expanded=True):
        st.markdown("### Review Your Answers")

        answered = len(st.session_state.answers)
        total = len(st.session_state.questions)
        flagged = len(st.session_state.flagged_questions)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Answered", f"{answered}/{total}")

        with col2:
            st.metric("Unanswered", total - answered)

        with col3:
            st.metric("Flagged", flagged)

        if answered < total:
            st.warning(f"⚠️ You have {total - answered} unanswered questions")

        if flagged > 0:
            st.info(f"🚩 You have {flagged} flagged questions to review")


def submit_exam(user: Dict[str, Any], auto_submit: bool = False):
    """Submit the exam and calculate results"""
    try:
        if not st.session_state.current_mock or not st.session_state.questions:
            st.error("Exam data not found")
            return

        # Show confirmation dialog unless auto-submit
        if not auto_submit:
            answered = len(st.session_state.answers)
            total = len(st.session_state.questions)

            if answered < total:
                st.warning(f"⚠️ You have {total - answered} unanswered questions. Submit anyway?")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📝 Continue Exam", use_container_width=True):
                        return
                with col2:
                    if st.button("✅ Submit Anyway", type="primary", use_container_width=True):
                        pass  # Continue to submission
                    else:
                        return

        # Calculate results
        questions = st.session_state.questions
        correct_answers = 0
        detailed_results = []

        for i, question in enumerate(questions):
            user_answer = st.session_state.answers.get(i)
            correct_index = question.get("correct_index")
            is_correct = user_answer == correct_index

            if is_correct:
                correct_answers += 1

            detailed_results.append(
                {
                    "question_index": i,
                    "question": question.get("question", ""),
                    "user_answer": user_answer,
                    "correct_answer": correct_index,
                    "is_correct": is_correct,
                    "choices": question.get("choices", []),
                }
            )

        # Calculate score
        total_questions = len(questions)
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        # Calculate time taken
        time_taken = None
        if st.session_state.start_time:
            time_taken = (datetime.now() - st.session_state.start_time).total_seconds()

        # Save attempt to database
        # For pool-based exams, use pool_id as mock_id for tracking
        mock_id = (
            st.session_state.current_mock.get("pool_id") or st.session_state.current_mock["id"]
        )

        attempt_data = {
            "user_id": user["id"],
            "mock_id": mock_id,
            "user_answers": st.session_state.answers,
            "score": score,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "time_taken": int(time_taken) if time_taken else None,
            "detailed_results": detailed_results,
            "status": "completed",
        }

        attempt = run_async(db.create_attempt(**attempt_data))

        if attempt:
            # Store results in session state
            st.session_state.exam_results = {
                "attempt_id": attempt.id,
                "score": score,
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "time_taken": time_taken,
                "detailed_results": detailed_results,
                "auto_submit": auto_submit,
            }

            st.session_state.exam_state = "completed"
            st.success("✅ Exam submitted successfully!")
            st.rerun()
        else:
            st.error("Failed to save exam results. Please try again.")

    except Exception as e:
        st.error(f"Error submitting exam: {e}")


def show_exam_results(user: Dict[str, Any]):
    """Display exam results"""
    if "exam_results" not in st.session_state:
        st.error("No exam results found")
        reset_exam_state()
        return

    results = st.session_state.exam_results

    # Results header
    st.markdown("# 🎉 Exam Completed!")

    if results.get("auto_submit"):
        st.warning("⏰ This exam was auto-submitted due to time limit")

    # Score display
    score = results["score"]
    if score >= 80:
        score_color = "#28a745"  # Green
        score_emoji = "🎉"
        grade = "Excellent"
    elif score >= 70:
        score_color = "#fd7e14"  # Orange
        score_emoji = "👍"
        grade = "Good"
    elif score >= 60:
        score_color = "#ffc107"  # Yellow
        score_emoji = "👌"
        grade = "Average"
    else:
        score_color = "#dc3545"  # Red
        score_emoji = "📚"
        grade = "Needs Improvement"

    st.markdown(
        f"""
    <div style="background: {score_color}; color: white; padding: 2rem; border-radius: 1rem;
               text-align: center; margin-bottom: 2rem;">
        <h1 style="margin: 0; font-size: 3rem;">{score_emoji} {score:.1f}%</h1>
        <h2 style="margin: 0.5rem 0; opacity: 0.9;">{grade}</h2>
        <p style="margin: 0; opacity: 0.8;">
            {results['correct_answers']} out of {results['total_questions']} questions correct
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("✅ Correct", results["correct_answers"])

    with col2:
        incorrect = results["total_questions"] - results["correct_answers"]
        st.metric("❌ Incorrect", incorrect)

    with col3:
        if results["time_taken"]:
            minutes = int(results["time_taken"] // 60)
            seconds = int(results["time_taken"] % 60)
            st.metric("⏱️ Time Taken", f"{minutes}m {seconds}s")
        else:
            st.metric("⏱️ Time Taken", "N/A")

    with col4:
        percentage = (results["correct_answers"] / results["total_questions"]) * 100
        st.metric("📊 Accuracy", f"{percentage:.1f}%")

    # Action buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Take Another Exam", use_container_width=True, type="primary"):
            reset_exam_state()
            st.rerun()

    with col2:
        if st.button("📈 View Past Attempts", use_container_width=True):
            st.session_state.page = "past_attempts"
            st.rerun()

    with col3:
        if st.button("📄 Download PDF", use_container_width=True):
            with st.spinner("Generating PDF report..."):
                success = generate_exam_pdf_download(user, results)
                if success:
                    st.success("PDF generated successfully! Check your downloads.")
                else:
                    st.error("Failed to generate PDF. Please try again.")

    with col4:
        if st.button("🏠 Dashboard", use_container_width=True):
            reset_exam_state()
            st.session_state.page = "dashboard"
            st.rerun()

    # Detailed results
    st.markdown("---")
    st.markdown("## 📊 Detailed Results")

    with st.expander("📋 Question-by-Question Review", expanded=True):
        for i, result in enumerate(results["detailed_results"]):
            is_correct = result["is_correct"]
            icon = "✅" if is_correct else "❌"
            color = "#d4edda" if is_correct else "#f8d7da"

            st.markdown(
                f"""
            <div style="background: {color}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                <strong>{icon} Question {i + 1}:</strong> {result['question']}<br>
                <strong>Your Answer:</strong> {chr(65 + result['user_answer']) if result['user_answer'] is not None else 'Not answered'} - {result['choices'][result['user_answer']] if result['user_answer'] is not None else 'No answer'}<br>
                <strong>Correct Answer:</strong> {chr(65 + result['correct_answer'])} - {result['choices'][result['correct_answer']]}
            </div>
            """,
                unsafe_allow_html=True,
            )


def reset_exam_state():
    """Reset all exam-related session state"""
    keys_to_reset = [
        "exam_state",
        "current_mock",
        "answers",
        "current_question",
        "start_time",
        "exam_id",
        "questions",
        "time_limit",
        "flagged_questions",
        "exam_results",
    ]

    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.exam_state = "not_started"


def generate_exam_pdf_download(user: Dict[str, Any], results: Dict[str, Any]) -> bool:
    """Generate and trigger download of exam results PDF"""
    try:
        # Prepare data for PDF generation
        attempt_data = {
            "id": results.get("attempt_id"),
            "score": results.get("score"),
            "correct_answers": results.get("correct_answers"),
            "total_questions": results.get("total_questions"),
            "time_taken": results.get("time_taken"),
            "detailed_results": results.get("detailed_results"),
            "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_answers": st.session_state.get("answers", {}),
        }

        mock_data = {
            "id": st.session_state.current_mock.get("id"),
            "title": st.session_state.current_mock.get("title"),
            "description": st.session_state.current_mock.get("description"),
            "category": st.session_state.current_mock.get("category", "General"),
            "questions_json": st.session_state.get("questions", []),
            "time_limit_minutes": st.session_state.get("time_limit", 60),
        }

        user_data = {"email": user.get("email"), "id": user.get("id")}

        # Generate PDF
        filepath, download_url = run_async(
            generate_exam_results_pdf(attempt_data, mock_data, user_data, include_explanations=True)
        )

        if filepath:
            # For Streamlit, we can provide a download button
            with open(filepath, "rb") as pdf_file:
                pdf_data = pdf_file.read()

            st.download_button(
                label="📥 Download Your Results PDF",
                data=pdf_data,
                file_name=f"exam_results_{attempt_data['id']}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            return True

        return False

    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return False


def main():
    """Main function for standalone execution"""
    show_exam()


if __name__ == "__main__":
    main()
