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

    # CSS to force expander text to white
    st.markdown(
        """
    <style>
    [data-testid="stExpander"] summary p {
        color: white !important;
    }
    [data-testid="stExpander"] summary {
        color: white !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

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
                <style>
                .pool-info * {{
                    color: #FFFFFF !important;
                }}
                </style>
                <div class="pool-info">
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
    st.markdown(
        '<h3 style="color: white !important;">📝 Pool Questions</h3>', unsafe_allow_html=True
    )

    # CSS to force expander text to white
    st.markdown(
        """
    <style>
    [data-testid="stExpander"] summary p {
        color: white !important;
    }
    [data-testid="stExpander"] summary {
        color: white !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

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
        st.markdown(
            '<p style="color: white !important; font-weight: 500; margin-bottom: 0.5rem;">🔍 Search questions</p>',
            unsafe_allow_html=True,
        )
        search_term = st.text_input(
            "Search questions", placeholder="Type to search...", label_visibility="collapsed"
        )

    with col2:
        st.markdown(
            '<p style="color: white !important; font-weight: 500; margin-bottom: 0.5rem;">Sort by</p>',
            unsafe_allow_html=True,
        )
        sort_by = st.selectbox(
            "Sort by select",
            ["Original Order", "Recent", "Most Shown", "Most Correct", "Most Incorrect"],
            label_visibility="collapsed",
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

    st.markdown(
        f'<p style="color: white !important;"><strong style="color: white !important;">Showing {len(filtered_questions)} of {len(questions)} questions</strong></p>',
        unsafe_allow_html=True,
    )

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

    st.markdown(
        f'<p style="color: white !important;"><strong style="color: white !important;">Question:</strong> {question["question_text"]}</p>',
        unsafe_allow_html=True,
    )

    # Display choices
    st.markdown(
        '<p style="color: white !important;"><strong style="color: white !important;">Choices:</strong></p>',
        unsafe_allow_html=True,
    )
    choices = (
        json.loads(question["choices"])
        if isinstance(question["choices"], str)
        else question["choices"]
    )

    for i, choice in enumerate(choices):
        if i == question["correct_answer"]:
            st.success(f"✅ {i}: {choice} (Correct Answer)")
        else:
            st.markdown(
                f'<p style="color: white !important;">◯ {i}: {choice}</p>', unsafe_allow_html=True
            )

    # Display metadata
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
        <div style="color: white !important;">
        <p style="color: white !important;"><strong style="color: white !important;">Source:</strong> {question.get('source_file', 'Unknown')}</p>

        <p style="color: white !important;"><strong style="color: white !important;">Uploaded:</strong> {question.get('uploaded_at', 'Unknown')}</p>

        <p style="color: white !important;"><strong style="color: white !important;">Difficulty:</strong> {question.get('difficulty', 'Medium')}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div style="color: white !important;">
        <p style="color: white !important;"><strong style="color: white !important;">Statistics:</strong></p>
        <ul style="color: white !important;">
        <li style="color: white !important;">Times shown: {question.get('times_shown', 0)}</li>
        <li style="color: white !important;">Times correct: {question.get('times_correct', 0)}</li>
        <li style="color: white !important;">Times incorrect: {question.get('times_incorrect', 0)}</li>
        </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if question.get("explanation"):
        st.markdown(
            f'<p style="color: white !important;"><strong style="color: white !important;">Explanation:</strong> {question["explanation"]}</p>',
            unsafe_allow_html=True,
        )

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
    st.markdown(
        '<p style="color: white !important;"><strong style="color: white !important;">✏️ Editing Question</strong></p>',
        unsafe_allow_html=True,
    )

    # Parse choices if they're stored as JSON string
    choices = (
        json.loads(question["choices"])
        if isinstance(question["choices"], str)
        else question["choices"]
    )

    with st.form(key=f"edit_form_{question['id']}"):
        # Question text
        st.markdown(
            '<p style="color: #000000 !important;">Question Text:</p>', unsafe_allow_html=True
        )
        new_question_text = st.text_area(
            "Question", value=question["question_text"], height=100, label_visibility="collapsed"
        )

        # Choices
        st.markdown(
            '<p style="color: white !important;">Choices (one per line):</p>',
            unsafe_allow_html=True,
        )
        choices_text = "\n".join(choices)
        new_choices_text = st.text_area(
            "Choices", value=choices_text, height=150, label_visibility="collapsed"
        )

        # Correct answer
        st.markdown(
            '<p style="color: white !important;">Correct Answer (0-based index):</p>',
            unsafe_allow_html=True,
        )
        new_correct_answer = st.number_input(
            "Correct Answer",
            min_value=0,
            max_value=10,
            value=question["correct_answer"],
            label_visibility="collapsed",
        )

        # Explanation
        st.markdown(
            '<p style="color: white !important;">Explanation (optional):</p>',
            unsafe_allow_html=True,
        )
        new_explanation = st.text_area(
            "Explanation",
            value=question.get("explanation", ""),
            height=100,
            label_visibility="collapsed",
        )

        # Difficulty
        st.markdown('<p style="color: white !important;">Difficulty:</p>', unsafe_allow_html=True)
        current_difficulty = question.get("difficulty", "Medium")
        # Handle case-insensitive difficulty matching
        difficulty_map = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
        current_difficulty_display = difficulty_map.get(current_difficulty.lower(), "Medium")

        new_difficulty = st.selectbox(
            "Difficulty",
            options=["Easy", "Medium", "Hard"],
            index=["Easy", "Medium", "Hard"].index(current_difficulty_display),
            label_visibility="collapsed",
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
