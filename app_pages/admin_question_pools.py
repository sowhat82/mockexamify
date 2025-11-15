"""
Admin Question Pool Management Page
View, edit, and manage question pools
"""

import json
import re
from typing import Any, Dict, List

import streamlit as st

import config
from auth_utils import AuthUtils, run_async


def show_admin_question_pools():
    """Display question pool management page"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated() or not auth.is_admin():
        st.error("Admin access required")
        st.stop()

    # Back to dashboard button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Back to Dashboard", key="back_to_dashboard_pools"):
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown("# 💼 Question Pool Management")
    st.markdown("View and manage your question pools")

    # Load question pools
    pools = run_async(load_question_pools())

    if not pools:
        st.info("📭 No question pools found. Upload some questions to get started!")
        if st.button("➕ Upload Questions", use_container_width=True):
            st.session_state.page = "admin_upload"
            st.rerun()
        return

    # Display pools overview
    st.markdown("### 📚 Your Question Pools")

    for pool in pools:
        with st.expander(
            f"**{pool['pool_name']}** - {pool['unique_questions']} unique questions", expanded=False
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(
                    f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1.5rem;
                    border-radius: 0.75rem;
                    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
                    color: white;
                ">
                <p><strong>Category:</strong> {pool.get('category', 'Uncategorized')}</p>
                <p><strong>Description:</strong> {pool.get('description', 'No description')}</p>
                <p><strong>Statistics:</strong></p>
                <ul>
                <li>Total questions uploaded: {pool.get('total_questions', 0)}</li>
                <li>Unique questions (after deduplication): {pool.get('unique_questions', 0)}</li>
                <li>Duplicates removed: {pool.get('total_questions', 0) - pool.get('unique_questions', 0)}</li>
                </ul>
                <p><strong>Last Updated:</strong> {pool.get('last_updated', 'Unknown')}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                if st.button(f"👁️ View Questions", key=f"view_{pool['id']}"):
                    st.session_state.viewing_pool = pool["id"]
                    st.rerun()

                if st.button(f"➕ Add More Questions", key=f"add_{pool['id']}"):
                    st.session_state.page = "admin_upload"
                    st.session_state.pool_name = pool["pool_name"]
                    st.rerun()

                if st.button(f"🗑️ Delete Pool", key=f"delete_{pool['id']}", type="secondary"):
                    st.session_state.confirm_delete_pool = pool["id"]
                    st.rerun()

    # Show questions if a pool is selected
    if hasattr(st.session_state, "viewing_pool") and st.session_state.viewing_pool:
        show_pool_questions(st.session_state.viewing_pool)

    # Handle delete confirmation
    if hasattr(st.session_state, "confirm_delete_pool") and st.session_state.confirm_delete_pool:
        show_delete_confirmation(st.session_state.confirm_delete_pool, pools)


def show_pool_questions(pool_id: str):
    """Display questions in a specific pool"""
    st.markdown("---")
    st.markdown("### 📝 Pool Questions")

    questions = run_async(load_pool_questions(pool_id))

    if not questions:
        st.info("No questions found in this pool")
        if st.button("⬅️ Back to Pools"):
            del st.session_state.viewing_pool
            st.rerun()
        return

    # Filter and search
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Search questions", placeholder="Type to search..."
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Original Order", "Recent", "Most Shown", "Most Correct", "Most Incorrect"],
        )

    with col3:
        if st.button("⬅️ Back to Pools"):
            del st.session_state.viewing_pool
            st.rerun()

    # Filter questions based on search
    filtered_questions = questions
    if search_term:
        filtered_questions = [
            q for q in questions if search_term.lower() in q["question_text"].lower()
        ]

    # Sort questions
    if sort_by == "Original Order":
        # Sort by original upload time (uploaded_at or created_at), oldest first
        filtered_questions.sort(key=lambda x: x.get("uploaded_at", x.get("created_at", "")))
    elif sort_by == "Recent":
        # Sort by original upload time, newest first
        filtered_questions.sort(
            key=lambda x: x.get("uploaded_at", x.get("created_at", "")), reverse=True
        )
    elif sort_by == "Most Shown":
        filtered_questions.sort(key=lambda x: x.get("times_shown", 0), reverse=True)
    elif sort_by == "Most Correct":
        filtered_questions.sort(key=lambda x: x.get("times_correct", 0), reverse=True)
    elif sort_by == "Most Incorrect":
        filtered_questions.sort(key=lambda x: x.get("times_incorrect", 0), reverse=True)

    st.markdown(f"**Showing {len(filtered_questions)} of {len(questions)} questions**")

    # Display questions
    for idx, question in enumerate(filtered_questions, 1):
        # Clean up the preview text - remove extra whitespace, newlines, and normalize spaces
        question_text = question.get("question_text", "")

        # Aggressive text cleaning for preview
        # 1. Convert to string
        preview_text = str(question_text)
        # 2. Remove ALL control characters and zero-width characters
        preview_text = re.sub(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\ufeff]", "", preview_text)
        # 3. Remove multiple whitespace (spaces, tabs, newlines) and replace with single space
        preview_text = re.sub(r"\s+", " ", preview_text)
        # 4. Strip leading/trailing whitespace
        preview_text = preview_text.strip()
        # 5. Truncate to 100 characters
        preview_text = preview_text[:100] if len(preview_text) > 100 else preview_text

        with st.expander(f"Q{idx}: {preview_text}{'...' if len(preview_text) >= 100 else ''}"):
            display_question_details(question)


def display_question_details(question: Dict[str, Any]):
    """Display detailed question information"""

    # Check if this question is being edited
    if (
        hasattr(st.session_state, "editing_question")
        and st.session_state.editing_question == question["id"]
    ):
        show_edit_question_form(question)
        return

    # Parse choices
    choices = (
        json.loads(question["choices"])
        if isinstance(question["choices"], str)
        else question["choices"]
    )

    # Build choices HTML
    choices_html = ""
    for i, choice in enumerate(choices):
        if i == question["correct_answer"]:
            choices_html += f'<p style="color: #4ade80; margin: 0.25rem 0;">✅ {i}: {choice} (Correct Answer)</p>'
        else:
            choices_html += f'<p style="color: white; margin: 0.25rem 0;">◯ {i}: {choice}</p>'

    # Explanation HTML
    explanation_html = ""
    if question.get("explanation"):
        explanation_html = f'<p style="color: white; margin-top: 1rem;"><strong>Explanation:</strong></p><p style="color: white;">{question["explanation"]}</p>'

    # Display everything in a gradient box
    details_html = f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
        color: white;
    ">
        <p style="color: white;"><strong>Question:</strong></p>
        <p style="color: white; margin-bottom: 1rem;">{question["question_text"]}</p>

        <p style="color: white;"><strong>Choices:</strong></p>
        {choices_html}

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div>
                <p style="color: white;"><strong>Source:</strong> {question.get('source_file', 'Unknown')}</p>
                <p style="color: white;"><strong>Uploaded:</strong> {question.get('uploaded_at', 'Unknown')}</p>
                <p style="color: white;"><strong>Difficulty:</strong> {question.get('difficulty', 'Medium')}</p>
            </div>
            <div>
                <p style="color: white;"><strong>Statistics:</strong></p>
                <ul style="color: white;">
                    <li>Times shown: {question.get('times_shown', 0)}</li>
                    <li>Times correct: {question.get('times_correct', 0)}</li>
                    <li>Times incorrect: {question.get('times_incorrect', 0)}</li>
                </ul>
            </div>
        </div>

        {explanation_html}
    </div>
    """
    st.html(details_html)

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button(f"✏️ Edit", key=f"edit_{question['id']}"):
            st.session_state.editing_question = question["id"]
            st.rerun()

    with col2:
        if st.button(f"🗑️ Delete", key=f"delete_q_{question['id']}", type="secondary"):
            success = run_async(delete_question(question["id"]))
            if success:
                st.success("Question deleted!")
                st.rerun()
            else:
                st.error("Failed to delete question")


def show_edit_question_form(question: Dict[str, Any]):
    """Display edit form for a question"""
    st.markdown("**✏️ Editing Question**")

    # Parse choices if they're stored as JSON string
    choices = (
        json.loads(question["choices"])
        if isinstance(question["choices"], str)
        else question["choices"]
    )

    with st.form(key=f"edit_form_{question['id']}"):
        # Question text
        new_question_text = st.text_area(
            "Question Text", value=question["question_text"], height=100
        )

        # Choices
        choices_text = "\n".join(choices)
        new_choices_text = st.text_area(
            "Choices (one per line)", value=choices_text, height=150
        )

        # Correct answer
        new_correct_answer = st.number_input(
            "Correct Answer (0-based index)",
            min_value=0,
            max_value=10,
            value=question["correct_answer"],
        )

        # Explanation
        new_explanation = st.text_area(
            "Explanation (optional)",
            value=question.get("explanation", ""),
            height=100,
        )

        # Difficulty
        current_difficulty = question.get("difficulty", "Medium")
        # Handle case-insensitive difficulty matching
        difficulty_map = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
        current_difficulty_display = difficulty_map.get(current_difficulty.lower(), "Medium")

        new_difficulty = st.selectbox(
            "Difficulty",
            options=["Easy", "Medium", "Hard"],
            index=["Easy", "Medium", "Hard"].index(current_difficulty_display),
        )

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button(
                "💾 Save Changes", use_container_width=True, type="primary"
            )

        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            # Parse new choices
            new_choices = [
                choice.strip() for choice in new_choices_text.split("\n") if choice.strip()
            ]

            # Validate
            if not new_question_text.strip():
                st.error("Question text cannot be empty")
            elif len(new_choices) < 2:
                st.error("Please provide at least 2 choices")
            elif new_correct_answer >= len(new_choices):
                st.error(
                    f"Correct answer index ({new_correct_answer}) must be less than number of choices ({len(new_choices)})"
                )
            else:
                # Update question
                updated_data = {
                    "question_text": new_question_text.strip(),
                    "choices": json.dumps(new_choices),
                    "correct_answer": new_correct_answer,
                    "explanation": new_explanation.strip() if new_explanation else None,
                    "difficulty": new_difficulty,
                }

                success = run_async(update_question(question["id"], updated_data))

                if success:
                    st.success("✅ Question updated successfully!")
                    del st.session_state.editing_question
                    st.rerun()
                else:
                    st.error("❌ Failed to update question")

        if cancel:
            del st.session_state.editing_question
            st.rerun()


def show_delete_confirmation(pool_id: str, pools: List[Dict[str, Any]]):
    """Show delete confirmation dialog"""
    pool = next((p for p in pools if p["id"] == pool_id), None)

    if not pool:
        return

    st.markdown("---")
    st.warning(f"⚠️ Are you sure you want to delete the pool **{pool['pool_name']}**?")
    st.markdown(f"This will delete {pool['unique_questions']} questions permanently.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Yes, Delete Pool", type="primary", use_container_width=True):
            success = run_async(delete_pool(pool_id))
            if success:
                st.success("Pool deleted successfully!")
                del st.session_state.confirm_delete_pool
                st.rerun()
            else:
                st.error("Failed to delete pool")

    with col2:
        if st.button("⬅️ Cancel", use_container_width=True):
            del st.session_state.confirm_delete_pool
            st.rerun()


async def load_question_pools() -> List[Dict[str, Any]]:
    """Load all question pools"""
    try:
        from db import db

        return await db.get_all_question_pools()
    except Exception as e:
        st.error(f"Error loading question pools: {str(e)}")
        return []


async def load_pool_questions(pool_id: str) -> List[Dict[str, Any]]:
    """Load questions from a specific pool"""
    try:
        from db import db

        return await db.get_pool_questions(pool_id)
    except Exception as e:
        st.error(f"Error loading pool questions: {str(e)}")
        return []


async def delete_pool(pool_id: str) -> bool:
    """Delete a question pool"""
    try:
        from db import db

        if db.demo_mode:
            return True

        # Use admin_client to bypass RLS for pool deletion
        client = db.admin_client if db.admin_client else db.client

        # In production, set is_active to False instead of hard delete
        response = (
            client.table("question_pools")
            .update({"is_active": False})
            .eq("id", pool_id)
            .execute()
        )

        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting pool: {str(e)}")
        return False


async def delete_question(question_id: str) -> bool:
    """Delete a specific question"""
    try:
        from db import db

        if db.demo_mode:
            return True

        # Use admin_client to bypass RLS for question deletion
        client = db.admin_client if db.admin_client else db.client

        response = client.table("pool_questions").delete().eq("id", question_id).execute()

        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting question: {str(e)}")
        return False


async def update_question(question_id: str, updated_data: Dict[str, Any]) -> bool:
    """Update a specific question"""
    try:
        from db import db

        if db.demo_mode:
            st.warning("Demo mode: Changes not saved")
            return True

        # Use admin_client to bypass RLS for question updates
        client = db.admin_client if db.admin_client else db.client

        response = (
            client.table("pool_questions").update(updated_data).eq("id", question_id).execute()
        )

        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating question: {str(e)}")
        return False


# Main entry point
if __name__ == "__main__":
    show_admin_question_pools()
