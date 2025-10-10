"""
Exam interface for MockExamify
Handles the complete exam flow: questions, timer, scoring, and explanations
"""
import streamlit as st
import httpx
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import config
from auth_utils import AuthUtils, run_async

def show_exam():
    """Display the exam interface"""
    auth = AuthUtils(config.API_BASE_URL)
    
    if not auth.is_authenticated():
        st.error("Please log in to take an exam")
        st.stop()
    
    mock_id = st.session_state.get('selected_mock_id')
    if not mock_id:
        st.error("No exam selected")
        if st.button("🏠 Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    # Initialize exam state
    if 'exam_state' not in st.session_state:
        try:
            mock_data = run_async(load_mock_exam(mock_id))
            if not mock_data:
                st.error("Failed to load exam data")
                return
            
            st.session_state.exam_state = {
                'mock_data': mock_data,
                'current_question': 0,
                'answers': {},
                'start_time': datetime.now(),
                'exam_submitted': False,
                'score': None,
                'explanations_unlocked': False
            }
        except Exception as e:
            st.error(f"Error initializing exam: {str(e)}")
            return
    
    exam_state = st.session_state.exam_state
    mock_data = exam_state['mock_data']
    questions = mock_data.get('questions', [])
    
    if exam_state['exam_submitted']:
        show_exam_results(exam_state)
        return
    
    # Exam header
    st.markdown(f"# 📝 {mock_data.get('title', 'Mock Exam')}")
    
    # Progress bar
    progress = (exam_state['current_question'] + 1) / len(questions)
    st.progress(progress)
    st.markdown(f"**Question {exam_state['current_question'] + 1} of {len(questions)}**")
    
    # Timer
    elapsed_time = datetime.now() - exam_state['start_time']
    time_limit = timedelta(minutes=len(questions) * 2)  # 2 minutes per question
    remaining_time = time_limit - elapsed_time
    
    if remaining_time.total_seconds() <= 0:
        st.error("⏰ Time's up! Submitting your exam automatically.")
        submit_exam()
        return
    
    # Display remaining time
    minutes_left = int(remaining_time.total_seconds() // 60)
    seconds_left = int(remaining_time.total_seconds() % 60)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.markdown(f"""
        <div style="background: #f0f0f0; padding: 0.5rem; border-radius: 0.3rem; text-align: center;">
            ⏰ <strong>{minutes_left:02d}:{seconds_left:02d}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Current question
    if questions:
        current_q = questions[exam_state['current_question']]
        show_question(current_q, exam_state['current_question'])
    
    # Navigation buttons
    st.markdown("---")
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
    
    with nav_col1:
        if exam_state['current_question'] > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                exam_state['current_question'] -= 1
                st.rerun()
    
    with nav_col2:
        if exam_state['current_question'] < len(questions) - 1:
            if st.button("Next ➡️", use_container_width=True):
                exam_state['current_question'] += 1
                st.rerun()
    
    with nav_col3:
        if st.button("📋 Review Answers", use_container_width=True):
            show_answer_review()
    
    with nav_col4:
        if st.button("✅ Submit Exam", use_container_width=True, type="primary"):
            if confirm_submission():
                submit_exam()

def show_question(question: Dict[str, Any], question_idx: int):
    """Display a single question with multiple choice options"""
    st.markdown(f"### {question.get('question', 'Question text missing')}")
    
    # Scenario text if available
    if 'scenario' in question:
        st.markdown(f"**Scenario:** {question['scenario']}")
    
    choices = question.get('choices', [])
    if not choices:
        st.error("No choices available for this question")
        return
    
    # Get current answer
    current_answer = st.session_state.exam_state['answers'].get(question_idx)
    
    # Display radio buttons for choices
    selected = st.radio(
        "Select your answer:",
        options=list(range(len(choices))),
        format_func=lambda x: f"{chr(65 + x)}. {choices[x]}",
        index=current_answer if current_answer is not None else None,
        key=f"question_{question_idx}"
    )
    
    # Save the answer
    if selected is not None:
        st.session_state.exam_state['answers'][question_idx] = selected

def show_answer_review():
    """Show a review of all answers"""
    with st.expander("📋 Answer Review", expanded=True):
        exam_state = st.session_state.exam_state
        questions = exam_state['mock_data']['questions']
        answers = exam_state['answers']
        
        for i, question in enumerate(questions):
            answer_idx = answers.get(i)
            answer_text = "Not answered"
            
            if answer_idx is not None:
                choices = question.get('choices', [])
                if answer_idx < len(choices):
                    answer_text = f"{chr(65 + answer_idx)}. {choices[answer_idx]}"
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button(f"Go to Q{i+1}", key=f"goto_{i}"):
                    st.session_state.exam_state['current_question'] = i
                    st.rerun()
            
            with col2:
                st.markdown(f"**Q{i+1}:** {answer_text}")

def confirm_submission() -> bool:
    """Confirm exam submission"""
    exam_state = st.session_state.exam_state
    questions = exam_state['mock_data']['questions']
    answered = len(exam_state['answers'])
    total = len(questions)
    
    if answered < total:
        st.warning(f"You have answered {answered} out of {total} questions. Are you sure you want to submit?")
        return st.button("Yes, Submit Now", type="primary")
    else:
        return True

def submit_exam():
    """Submit the exam and calculate results"""
    exam_state = st.session_state.exam_state
    
    try:
        # Calculate score
        questions = exam_state['mock_data']['questions']
        correct_answers = 0
        
        for i, question in enumerate(questions):
            user_answer = exam_state['answers'].get(i)
            correct_answer = question.get('correct_index')
            
            if user_answer == correct_answer:
                correct_answers += 1
        
        score = int((correct_answers / len(questions)) * 100) if questions else 0
        exam_state['score'] = score
        exam_state['correct_answers'] = correct_answers
        exam_state['exam_submitted'] = True
        
        # Submit to server
        run_async(submit_exam_to_server(exam_state))
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error submitting exam: {str(e)}")

def show_exam_results(exam_state: Dict[str, Any]):
    """Display exam results and options"""
    mock_data = exam_state['mock_data']
    score = exam_state['score']
    correct_answers = exam_state['correct_answers']
    total_questions = len(mock_data['questions'])
    
    st.markdown("# 🎉 Exam Complete!")
    st.balloons()
    
    # Score display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Final Score", f"{score}%")
    
    with col2:
        st.metric("Correct Answers", f"{correct_answers}/{total_questions}")
    
    with col3:
        grade = get_grade(score)
        st.metric("Grade", grade)
    
    # Results breakdown
    st.markdown("## 📊 Results Breakdown")
    
    questions = mock_data['questions']
    answers = exam_state['answers']
    
    for i, question in enumerate(questions):
        user_answer = answers.get(i)
        correct_answer = question.get('correct_index')
        choices = question.get('choices', [])
        
        is_correct = user_answer == correct_answer
        
        with st.expander(f"Q{i+1}: {'✅' if is_correct else '❌'} {question.get('question', '')[:50]}..."):
            st.markdown(f"**Question:** {question.get('question', '')}")
            
            # Show choices with indicators
            for j, choice in enumerate(choices):
                if j == correct_answer:
                    st.markdown(f"✅ **{chr(65 + j)}. {choice}** (Correct Answer)")
                elif j == user_answer:
                    st.markdown(f"❌ **{chr(65 + j)}. {choice}** (Your Answer)")
                else:
                    st.markdown(f"   {chr(65 + j)}. {choice}")
            
            # Show explanation if available and unlocked
            if exam_state.get('explanations_unlocked') and 'explanation' in question:
                st.markdown("**Explanation:**")
                st.info(question['explanation'])
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏠 Back to Dashboard", use_container_width=True):
            clear_exam_state()
            st.session_state.page = "dashboard"
            st.rerun()
    
    with col2:
        if st.button("📄 Download PDF", use_container_width=True):
            download_exam_pdf(exam_state)
    
    with col3:
        explanation_cost = 2  # Credits needed for explanations
        user = AuthUtils(config.API_BASE_URL).get_current_user()
        user_credits = user.get('credits_balance', 0) if user else 0
        
        if not exam_state.get('explanations_unlocked'):
            if mock_data.get('explanation_enabled', False):
                if user_credits >= explanation_cost:
                    if st.button(f"🔓 Unlock Explanations ({explanation_cost} credits)", use_container_width=True):
                        unlock_explanations(exam_state)
                else:
                    st.button(f"❌ Need {explanation_cost} credits", disabled=True, use_container_width=True)
    
    with col4:
        if st.button("🔄 Retake Exam", use_container_width=True):
            clear_exam_state()
            st.rerun()

def get_grade(score: int) -> str:
    """Convert score to letter grade"""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def unlock_explanations(exam_state: Dict[str, Any]):
    """Unlock explanations for the exam"""
    try:
        # Generate explanations using OpenRouter
        explanations = run_async(generate_explanations(exam_state))
        
        if explanations:
            # Add explanations to questions
            questions = exam_state['mock_data']['questions']
            for i, explanation in enumerate(explanations):
                if i < len(questions):
                    questions[i]['explanation'] = explanation
            
            exam_state['explanations_unlocked'] = True
            
            # Deduct credits from user (this would be handled by the API)
            run_async(deduct_credits_for_explanations())
            
            st.success("Explanations unlocked successfully!")
            st.rerun()
        else:
            st.error("Failed to generate explanations")
            
    except Exception as e:
        st.error(f"Error unlocking explanations: {str(e)}")

def clear_exam_state():
    """Clear exam state from session"""
    if 'exam_state' in st.session_state:
        del st.session_state.exam_state
    if 'selected_mock_id' in st.session_state:
        del st.session_state.selected_mock_id

def download_exam_pdf(exam_state: Dict[str, Any]):
    """Generate and download exam PDF"""
    try:
        # This would call the PDF generation utility
        st.info("PDF generation feature coming soon!")
        # pdf_data = run_async(generate_exam_pdf(exam_state))
        # st.download_button("Download PDF", pdf_data, "exam_results.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

async def load_mock_exam(mock_id: str) -> Optional[Dict[str, Any]]:
    """Load mock exam data from the API"""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {}
            if "user_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.user_token}"
            
            response = await client.get(
                f"{config.API_BASE_URL}/api/mocks/{mock_id}",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
    except Exception as e:
        return None

async def submit_exam_to_server(exam_state: Dict[str, Any]):
    """Submit exam results to the server"""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {}
            if "user_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.user_token}"
            
            attempt_data = {
                "mock_id": exam_state['mock_data']['id'],
                "answers": exam_state['answers'],
                "score": exam_state['score'],
                "completed_at": datetime.now().isoformat()
            }
            
            response = await client.post(
                f"{config.API_BASE_URL}/api/attempts",
                json=attempt_data,
                headers=headers,
                timeout=10.0
            )
            
            return response.status_code == 200
            
    except Exception as e:
        return False

async def generate_explanations(exam_state: Dict[str, Any]) -> List[str]:
    """Generate explanations using OpenRouter API"""
    # This would be implemented using the OpenRouter utils
    # For now, return placeholder explanations
    questions = exam_state['mock_data']['questions']
    return [q.get('explanation_template', 'Explanation not available') for q in questions]

async def deduct_credits_for_explanations():
    """Deduct credits for explanation unlock"""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {}
            if "user_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.user_token}"
            
            response = await client.post(
                f"{config.API_BASE_URL}/api/user/deduct_credits",
                json={"amount": 2, "reason": "explanations"},
                headers=headers,
                timeout=10.0
            )
            
            return response.status_code == 200
            
    except Exception as e:
        return False