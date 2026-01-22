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

                if st.button(f"✏️ Rename Pool", key=f"rename_{pool['id']}"):
                    st.session_state.rename_pool_id = pool["id"]
                    st.session_state.rename_pool_current_name = pool["pool_name"]
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

    # Handle rename
    if hasattr(st.session_state, "rename_pool_id") and st.session_state.rename_pool_id:
        show_rename_pool_dialog(st.session_state.rename_pool_id, st.session_state.rename_pool_current_name)

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

    # Initialize selected questions in session state
    if 'selected_questions' not in st.session_state:
        st.session_state.selected_questions = set()

    # Filter and search
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search questions", placeholder="Type to search...")

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Original Order", "Recent", "Most Shown", "Most Correct", "Most Incorrect"],
        )

    with col3:
        if st.button("⬅️ Back to Pools"):
            del st.session_state.viewing_pool
            st.session_state.selected_questions = set()  # Clear selections
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

    # Bulk actions section
    # Count currently selected questions
    selected_count = len(st.session_state.selected_questions)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**Showing {len(filtered_questions)} of {len(questions)} questions**")

    with col2:
        # Select/Deselect all visible questions
        if st.button("☑️ Select All Visible", key="select_all_visible"):
            # Add all filtered question IDs to selection
            for idx, q in enumerate(filtered_questions, 1):
                question_id = q['id']
                st.session_state.selected_questions.add(question_id)
                # Also update checkbox widget state to match
                checkbox_key = f"select_{question_id}_{idx}"
                st.session_state[checkbox_key] = True
            st.rerun()

    with col3:
        if st.button("⬜ Clear Selection", key="clear_selection"):
            # Clear selection set
            selected_ids = list(st.session_state.selected_questions)
            st.session_state.selected_questions = set()
            # Also clear checkbox widget states
            for idx, q in enumerate(filtered_questions, 1):
                checkbox_key = f"select_{q['id']}_{idx}"
                if checkbox_key in st.session_state:
                    st.session_state[checkbox_key] = False
            st.rerun()

    # Bulk action buttons (only show if questions are selected)
    if selected_count > 0:
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.warning(f"⚠️ {selected_count} question(s) selected")
        with col2:
            if st.button(f"🤖 AI Fix {selected_count} Selected", key="ai_fix_selected_btn", type="secondary"):
                st.session_state.ai_fix_mode = True
                st.rerun()
        with col3:
            if st.button(f"🗑️ Delete {selected_count} Selected", key="delete_selected_btn", type="primary"):
                st.session_state.confirm_bulk_delete = True
                st.rerun()

        # Show confirmation dialog
        if st.session_state.get('confirm_bulk_delete', False):
            st.error(f"⚠️ Are you sure you want to delete {selected_count} question(s)? This cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete", key="confirm_bulk_delete_yes"):
                    # Perform bulk delete
                    success_count = 0
                    for question_id in list(st.session_state.selected_questions):
                        if run_async(delete_question(question_id)):
                            success_count += 1

                    st.success(f"✅ Successfully deleted {success_count} question(s)")
                    st.session_state.selected_questions = set()
                    st.session_state.confirm_bulk_delete = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="confirm_bulk_delete_no"):
                    st.session_state.confirm_bulk_delete = False
                    st.rerun()
            st.markdown("---")

    # Show AI fix preview if in AI fix mode
    if st.session_state.get('ai_fix_mode', False):
        show_ai_fix_preview()
        return  # Don't show normal question list while in AI fix mode

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

        # Create checkbox and expander in columns
        col1, col2 = st.columns([0.5, 9.5])

        with col1:
            # Checkbox for selecting this question
            question_id = question['id']
            is_selected = question_id in st.session_state.selected_questions
            checkbox_key = f"select_{question_id}_{idx}"

            # Define callback to handle checkbox changes with proper closure
            def make_toggle_callback(q_id, key):
                def callback():
                    if st.session_state[key]:
                        st.session_state.selected_questions.add(q_id)
                    else:
                        st.session_state.selected_questions.discard(q_id)
                return callback

            st.checkbox(
                "",
                value=is_selected,
                key=checkbox_key,
                label_visibility="collapsed",
                on_change=make_toggle_callback(question_id, checkbox_key)
            )

        with col2:
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
        new_choices_text = st.text_area("Choices (one per line)", value=choices_text, height=150)

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
        current_difficulty_display = difficulty_map.get(
            (current_difficulty or "Medium").lower(), "Medium"
        )

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

                success = update_question(question["id"], updated_data)

                if success:
                    st.success("✅ Question updated successfully!")
                    del st.session_state.editing_question
                    st.rerun()
                else:
                    st.error("❌ Failed to update question")

        if cancel:
            del st.session_state.editing_question
            st.rerun()


def show_rename_pool_dialog(pool_id: str, current_name: str):
    """Show rename pool dialog"""
    st.markdown("---")
    st.markdown("### ✏️ Rename Pool")

    with st.form(key=f"rename_form_{pool_id}"):
        new_name = st.text_input(
            "New pool name",
            value=current_name,
            max_chars=100,
            help="Enter a unique name for this pool"
        )

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("✅ Rename", type="primary", use_container_width=True)

        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            if not new_name or not new_name.strip():
                st.error("Pool name cannot be empty")
            elif new_name.strip() == current_name:
                st.info("Name unchanged")
                del st.session_state.rename_pool_id
                del st.session_state.rename_pool_current_name
                st.rerun()
            else:
                success = run_async(rename_pool(pool_id, new_name.strip()))
                if success:
                    st.success(f"Pool renamed to '{new_name.strip()}' successfully!")
                    del st.session_state.rename_pool_id
                    del st.session_state.rename_pool_current_name
                    st.rerun()
                else:
                    st.error("Failed to rename pool. Name may already exist.")

        if cancel:
            del st.session_state.rename_pool_id
            del st.session_state.rename_pool_current_name
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


async def rename_pool(pool_id: str, new_name: str) -> bool:
    """Rename a question pool"""
    try:
        from db import db

        return await db.rename_question_pool(pool_id, new_name)
    except Exception as e:
        st.error(f"Error renaming pool: {str(e)}")
        return False


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
            client.table("question_pools").update({"is_active": False}).eq("id", pool_id).execute()
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


def update_question(question_id: str, updated_data: Dict[str, Any]) -> bool:
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


async def process_ai_fixes(question_ids: List[str], pool_id: str = None, enable_pattern_detection: bool = True) -> Dict[str, Any]:
    """
    Process AI fixes for selected questions and optionally find similar errors in the pool.

    Args:
        question_ids: List of question IDs to fix
        pool_id: Pool ID for pattern detection across pool
        enable_pattern_detection: If True, detect patterns and find similar questions

    Returns:
        Dict with:
            - fix_results: List of fix suggestions with before/after content
            - patterns_detected: List of error patterns found
            - similar_questions_found: List of additional question IDs with similar errors
            - total_questions_to_fix: Total number of questions that will be fixed
    """
    from openrouter_utils import fix_question_errors, openrouter_manager
    from db import db
    import logging

    logger = logging.getLogger(__name__)
    fix_results = []
    all_patterns = []
    source_files = set()  # Track source files of selected questions

    # Track validation stats for efficiency reporting
    validation_stats = {
        "quick_pass": 0,  # Questions that passed quick validation
        "full_analysis": 0,  # Questions that needed full analysis
        "total_validated": 0
    }

    # Phase 1: Fix initially selected questions
    for question_id in question_ids:
        try:
            # Load question from database
            response = db.admin_client.table("pool_questions").select("*").eq("id", question_id).execute()

            if not response.data:
                logger.warning(f"Question {question_id} not found")
                continue

            question = response.data[0]
            question_text = question['question_text']
            choices = json.loads(question['choices']) if isinstance(question['choices'], str) else question['choices']
            correct_answer = question.get('correct_answer')

            # Track source file for pattern detection
            source_file = question.get('source_file')
            if source_file:
                source_files.add(source_file)

            # Call AI to fix (including answer validation)
            fix_result = await fix_question_errors(
                question_text=question_text,
                choices=choices,
                correct_answer=correct_answer,
                validate_answer=True  # Enable answer validation
            )

            # Track validation stats
            if fix_result.get('answer_validation'):
                validation_stats["total_validated"] += 1
                stage = fix_result['answer_validation'].get('validation_stage', 'unknown')
                if stage == 'quick':
                    validation_stats["quick_pass"] += 1
                elif stage == 'full':
                    validation_stats["full_analysis"] += 1

            fix_results.append({
                "question_id": question_id,
                "pool_id": question.get('pool_id'),
                "original_question": question_text,
                "fixed_question": fix_result['fixed_question'],
                "original_choices": choices,
                "fixed_choices": fix_result['fixed_choices'],
                "changes_made": fix_result['changes_made'],
                "has_changes": fix_result.get('has_changes', True),
                "original_correct_answer": fix_result.get('original_correct_answer'),
                "suggested_correct_answer": fix_result.get('suggested_correct_answer'),
                "answer_changed": fix_result.get('answer_changed', False),
                "answer_validation": fix_result.get('answer_validation'),
                "new_explanation": fix_result.get('new_explanation'),
                "explanation_regenerated": fix_result.get('explanation_regenerated', False),
                "original_explanation": question.get('explanation'),
                "error": fix_result.get('error'),
                "from_pattern_match": False  # This was directly selected
            })

            # Detect patterns from this fix
            if enable_pattern_detection and fix_result.get('has_changes'):
                patterns = await openrouter_manager.detect_error_patterns(
                    fix_result, question_text, choices
                )
                all_patterns.extend(patterns)

        except Exception as e:
            logger.error(f"Error processing fix for question {question_id}: {e}")
            fix_results.append({
                "question_id": question_id,
                "has_changes": False,
                "error": str(e),
                "from_pattern_match": False
            })

    # Phase 2: Find similar questions with same error patterns
    similar_question_ids = []
    if enable_pattern_detection and all_patterns and pool_id:
        try:
            similar_question_ids = await find_similar_errors_in_pool(
                pool_id=pool_id,
                patterns=all_patterns,
                exclude_question_ids=question_ids,
                source_files=list(source_files)  # Only check questions from same source files
            )

            logger.info(f"Found {len(similar_question_ids)} questions with similar errors from source files: {source_files}")

            # Process fixes for similar questions with progress tracking
            total_to_analyze = len(similar_question_ids)
            for idx, question_id in enumerate(similar_question_ids, 1):
                # Update progress UI if available
                try:
                    import streamlit as st
                    if hasattr(st, 'session_state'):
                        if '_ai_fix_progress_bar' in st.session_state:
                            progress = idx / total_to_analyze
                            st.session_state._ai_fix_progress_bar.progress(progress)
                        if '_ai_fix_status_text' in st.session_state:
                            st.session_state._ai_fix_status_text.text(f"🔍 Analyzing question {idx} of {total_to_analyze}...")
                        st.session_state._ai_fix_current = idx
                except:
                    pass  # Progress updates are optional

                try:
                    response = db.admin_client.table("pool_questions").select("*").eq("id", question_id).execute()

                    if not response.data:
                        continue

                    question = response.data[0]
                    question_text = question['question_text']
                    choices = json.loads(question['choices']) if isinstance(question['choices'], str) else question['choices']
                    correct_answer = question.get('correct_answer')

                    fix_result = await fix_question_errors(
                        question_text=question_text,
                        choices=choices,
                        correct_answer=correct_answer,
                        validate_answer=True
                    )

                    # Track validation stats for pattern-matched questions
                    if fix_result.get('answer_validation'):
                        validation_stats["total_validated"] += 1
                        stage = fix_result['answer_validation'].get('validation_stage', 'unknown')
                        if stage == 'quick':
                            validation_stats["quick_pass"] += 1
                        elif stage == 'full':
                            validation_stats["full_analysis"] += 1

                    # Only add if there are actual changes
                    if fix_result.get('has_changes'):
                        fix_results.append({
                            "question_id": question_id,
                            "pool_id": question.get('pool_id'),
                            "original_question": question_text,
                            "fixed_question": fix_result['fixed_question'],
                            "original_choices": choices,
                            "fixed_choices": fix_result['fixed_choices'],
                            "changes_made": fix_result['changes_made'],
                            "has_changes": True,
                            "original_correct_answer": fix_result.get('original_correct_answer'),
                            "suggested_correct_answer": fix_result.get('suggested_correct_answer'),
                            "answer_changed": fix_result.get('answer_changed', False),
                            "answer_validation": fix_result.get('answer_validation'),
                            "new_explanation": fix_result.get('new_explanation'),
                            "explanation_regenerated": fix_result.get('explanation_regenerated', False),
                            "original_explanation": question.get('explanation'),
                            "error": fix_result.get('error'),
                            "from_pattern_match": True  # This was found via pattern matching
                        })

                except Exception as e:
                    logger.error(f"Error processing similar question {question_id}: {e}")

        except Exception as e:
            logger.error(f"Error finding similar questions: {e}")

    return {
        "fix_results": fix_results,
        "patterns_detected": all_patterns,
        "similar_questions_found": len([f for f in fix_results if f.get('from_pattern_match')]),
        "total_questions_to_fix": len([f for f in fix_results if f.get('has_changes')]),
        "validation_stats": validation_stats,
        "source_files": list(source_files)
    }


async def find_similar_errors_in_pool(
    pool_id: str,
    patterns: List[Dict[str, Any]],
    exclude_question_ids: List[str] = None,
    source_files: List[str] = None
) -> List[str]:
    """
    Find questions in the pool that match the detected error patterns.

    Args:
        pool_id: The pool ID to search in
        patterns: List of error patterns from detect_error_patterns()
        exclude_question_ids: Question IDs to exclude from search
        source_files: Only check questions from these source files (e.g., same PDF/DOCX)

    Returns:
        List of question IDs that match the patterns
    """
    from db import db
    import json
    import re
    import logging

    logger = logging.getLogger(__name__)

    if exclude_question_ids is None:
        exclude_question_ids = []

    # Get all questions from the pool
    all_questions = await db.get_pool_questions(pool_id)

    # Filter to only questions from the same source files
    if source_files:
        all_questions = [q for q in all_questions if q.get('source_file') in source_files]
        logger.info(f"Filtering to {len(all_questions)} questions from source files: {source_files}")

    matching_question_ids = set()

    # Check if we have patterns that require full source file validation
    has_wrong_answer_pattern = any(p.get('pattern_type') == 'wrong_answer' for p in patterns)
    has_grammar_spelling_pattern = any(p.get('pattern_type') in ['grammar', 'spelling', 'word_usage', 'text_error'] for p in patterns)
    has_ocr_spacing_pattern = any(p.get('pattern_type') in ['ocr_space', 'missing_space'] for p in patterns)

    if has_wrong_answer_pattern:
        logger.info(f"Wrong answer pattern detected - will validate questions from same source file(s)")

    if has_grammar_spelling_pattern:
        logger.info(f"Grammar/spelling/text error pattern detected - will validate questions from same source file(s)")

    for question in all_questions:
        question_id = question.get('id')

        # Skip excluded questions
        if question_id in exclude_question_ids:
            continue

        question_text = question.get('question_text', '')
        choices = json.loads(question.get('choices', '[]')) if isinstance(question.get('choices'), str) else question.get('choices', [])
        correct_answer = question.get('correct_answer')

        # Check each pattern
        for pattern in patterns:
            pattern_type = pattern.get('pattern_type')

            # OCR and spacing errors: Only check for exact text matches (these repeat exactly)
            if pattern_type in ['ocr_space', 'missing_space']:
                search_pattern = pattern.get('search_pattern', '')

                # Use case-insensitive search for better matching
                if search_pattern:
                    if search_pattern.lower() in question_text.lower():
                        matching_question_ids.add(question_id)
                        logger.info(f"Found {pattern_type} pattern '{search_pattern}' in question {question_id}")

                    # Also check in choices
                    for choice in choices:
                        if search_pattern.lower() in choice.lower():
                            matching_question_ids.add(question_id)
                            logger.info(f"Found {pattern_type} pattern '{search_pattern}' in choice of question {question_id}")

            # Grammar, spelling, word usage, text errors: Validate ALL questions
            # because similar types of errors could appear with different text
            elif pattern_type in ['spelling', 'grammar', 'word_usage', 'text_error']:
                matching_question_ids.add(question_id)
                logger.info(f"Adding question {question_id} for {pattern_type} validation")

            # Wrong answer: Validate all questions in pool
            elif pattern_type == 'wrong_answer':
                # When wrong answers are detected, validate all questions in pool
                # because wrong answers could be scattered across A, B, C, D randomly
                # The AI will validate each one to determine if it's actually wrong
                matching_question_ids.add(question_id)

    return list(matching_question_ids)


def apply_approved_fixes(fix_results: List[Dict[str, Any]]):
    """Apply approved fixes to database with progress tracking"""
    approved_ids = st.session_state.approved_fixes
    success_count = 0
    error_count = 0
    errors = []

    # Get approved fixes
    approved_fixes = [fix for fix in fix_results if fix['question_id'] in approved_ids]
    total_fixes = len(approved_fixes)

    # Show progress bar if there are multiple fixes
    if total_fixes > 1:
        progress_bar = st.progress(0)
        status_text = st.empty()

    for idx, fix in enumerate(approved_fixes, 1):
        # Update progress
        if total_fixes > 1:
            progress = idx / total_fixes
            progress_bar.progress(progress)
            status_text.text(f"Updating question {idx} of {total_fixes}...")

        # Update question in database
        updated_data = {
            'question_text': fix['fixed_question'],
            'choices': json.dumps(fix['fixed_choices'])
        }

        # Also update correct answer if it was changed
        if fix.get('answer_changed') and fix.get('suggested_correct_answer') is not None:
            updated_data['correct_answer'] = fix['suggested_correct_answer']

        # Also update explanation if it was regenerated
        if fix.get('explanation_regenerated') and fix.get('new_explanation'):
            updated_data['explanation'] = fix['new_explanation']

        try:
            if update_question(fix['question_id'], updated_data):
                success_count += 1
            else:
                error_count += 1
                errors.append(f"Question {idx}: Update failed")
        except Exception as e:
            error_count += 1
            errors.append(f"Question {idx}: {str(e)}")

    # Clear progress indicators
    if total_fixes > 1:
        progress_bar.empty()
        status_text.empty()

    # Show errors if any
    if error_count > 0:
        st.warning(f"⚠️ {error_count} fix(es) failed to apply")
        with st.expander("View errors"):
            for error in errors:
                st.error(error)

    return success_count


def show_ai_fix_preview():
    """Display AI fix preview with approval interface"""

    st.markdown("## 🤖 AI Fix Preview with Pattern Detection")
    st.markdown("AI will detect error patterns and automatically find similar issues from the same source document.")

    st.info("""
    **How Pattern Detection Works:**
    - **Scope:** Only checks questions from the same source file (PDF/DOCX) as the selected question(s)
    - **Grammar, spelling, text errors:** AI validates ALL questions from the same source for similar types of errors
    - **OCR/spacing errors:** Only searches for exact text matches in the same source
    - **Wrong answers:** AI validates ALL questions from the same source

    This targets errors that are likely to repeat from the same source document.
    """)

    # Get fix results from session state (computed once)
    if 'ai_fix_results_data' not in st.session_state:
        question_ids = list(st.session_state.selected_questions)
        pool_id = st.session_state.get('viewing_pool')

        # Get pool size and source files to show user what to expect
        from db import db
        pool_questions = run_async(db.get_pool_questions(pool_id))

        # Get source files from selected questions
        selected_source_files = set()
        for qid in question_ids:
            q = next((q for q in pool_questions if q['id'] == qid), None)
            if q and q.get('source_file'):
                selected_source_files.add(q.get('source_file'))

        # Count questions from the same source files
        questions_from_same_source = [q for q in pool_questions if q.get('source_file') in selected_source_files]
        total_questions_to_check = len(questions_from_same_source)

        if selected_source_files:
            source_file_names = ', '.join([f'"{sf}"' for sf in selected_source_files])
            st.info(f"🔍 AI will analyze {len(question_ids)} selected question(s), then scan {total_questions_to_check} questions from the same source file(s): {source_file_names}")
        else:
            st.info(f"🔍 AI will analyze {len(question_ids)} selected question(s).")

        # Create progress tracking UI elements
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Store UI elements in session state so async function can update them
        st.session_state._ai_fix_progress_bar = progress_bar
        st.session_state._ai_fix_status_text = status_text
        st.session_state._ai_fix_total = total_questions_to_check
        st.session_state._ai_fix_current = 0

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"AI Fix Debug: pool_id={pool_id}, question_ids={question_ids}, questions_to_check={total_questions_to_check}, source_files={selected_source_files}")

        # Call enhanced process_ai_fixes with pattern detection
        fix_data = run_async(process_ai_fixes(
            question_ids=question_ids,
            pool_id=pool_id,
            enable_pattern_detection=True
        ))

        # Clear progress UI
        progress_bar.empty()
        status_text.empty()

        # Show completion summary
        similar_count = fix_data.get('similar_questions_found', 0)
        total_analyzed = len(question_ids) + similar_count
        total_with_fixes = len([f for f in fix_data.get('fix_results', []) if f.get('has_changes')])
        source_files_checked = fix_data.get('source_files', [])

        if source_files_checked:
            source_file_names = ', '.join([f'"{sf}"' for sf in source_files_checked])
            st.success(f"✅ Analysis complete! Analyzed {total_analyzed} question(s) from source file(s): {source_file_names}")
        else:
            st.success(f"✅ Analysis complete! Analyzed {total_analyzed} question(s).")

        st.info(f"📊 Found {total_with_fixes} question(s) with errors that need fixing.")

        # Clean up session state
        if '_ai_fix_progress_bar' in st.session_state:
            del st.session_state._ai_fix_progress_bar
        if '_ai_fix_status_text' in st.session_state:
            del st.session_state._ai_fix_status_text
        if '_ai_fix_total' in st.session_state:
            del st.session_state._ai_fix_total
        if '_ai_fix_current' in st.session_state:
            del st.session_state._ai_fix_current

        logger.info(f"AI Fix Results: patterns={len(fix_data.get('patterns_detected', []))}, similar_found={fix_data.get('similar_questions_found', 0)}")

        st.session_state.ai_fix_results_data = fix_data

    fix_data = st.session_state.ai_fix_results_data
    fix_results = fix_data.get('fix_results', [])
    patterns_detected = fix_data.get('patterns_detected', [])
    similar_questions_found = fix_data.get('similar_questions_found', 0)
    validation_stats = fix_data.get('validation_stats', {})

    # Show validation efficiency stats
    if validation_stats.get('total_validated', 0) > 0:
        quick_pass = validation_stats.get('quick_pass', 0)
        full_analysis = validation_stats.get('full_analysis', 0)
        total = validation_stats['total_validated']

        savings_pct = (quick_pass / total * 100) if total > 0 else 0

        st.success(f"⚡ **Validation Efficiency:** {savings_pct:.0f}% API cost savings")
        st.markdown(f"- {quick_pass} question(s) passed quick validation (cheaper)")
        st.markdown(f"- {full_analysis} question(s) needed full analysis (all 4 choices)")
        st.markdown(f"- Total: {total} question(s) validated")

    # Show pattern detection summary - ALWAYS show this section
    st.markdown("### 🔍 Pattern Detection")

    if patterns_detected:
        st.success(f"✅ **Pattern detection found issues:**")
        st.markdown(f"- **{len(patterns_detected)}** error pattern(s) detected")
        st.markdown(f"- **{similar_questions_found}** additional question(s) found with similar errors")

        with st.expander("📋 View Detected Patterns", expanded=True):
            for idx, pattern in enumerate(patterns_detected, 1):
                pattern_type = pattern.get('pattern_type', 'unknown')
                description = pattern.get('description', 'No description')

                if pattern_type == 'wrong_answer':
                    st.warning(f"**Pattern {idx}:** Wrong answer detected - validating pool")
                    st.markdown(f"- When wrong answers are found, AI validates a sample of questions from the pool")
                    st.markdown(f"- Wrong answers can be scattered across A, B, C, D options")
                    st.markdown(f"- Each question is validated individually to confirm if answer is actually wrong")
                    st.markdown(f"- **Original issue:** {pattern.get('reasoning', 'N/A')[:200]}...")
                elif pattern_type in ['grammar', 'spelling', 'word_usage', 'text_error']:
                    st.warning(f"**Pattern {idx}:** {pattern_type.replace('_', ' ').title()} error detected - validating source file")
                    st.markdown(f"- **Specific error found:** {description}")
                    st.markdown(f"- **Action:** AI is validating ALL questions from the same source file for similar types of errors")
                    st.markdown(f"- Grammar, spelling, and text errors can appear in many forms")
                    st.markdown(f"- Each question from the same source is checked individually for {pattern_type.replace('_', ' ')} issues")
                elif pattern_type in ['ocr_space', 'missing_space']:
                    st.info(f"**Pattern {idx}:** {description}")
                    st.markdown(f"- **Search method:** Looking for exact text matches only")
                    if pattern.get('search_pattern'):
                        st.code(f"Looking for: '{pattern.get('search_pattern')}'")
                else:
                    st.info(f"**Pattern {idx}:** {description}")
                    if pattern.get('search_pattern'):
                        st.code(f"Looking for: '{pattern.get('search_pattern')}'")
    else:
        st.info("ℹ️ **No error patterns detected** - Each question has unique errors or no additional similar questions found in pool")

    # Filter to only show questions with changes
    questions_with_changes = [f for f in fix_results if f.get('has_changes', False)]
    questions_with_errors = [f for f in fix_results if f.get('error')]

    # Separate directly selected vs pattern-matched questions
    directly_selected = [f for f in questions_with_changes if not f.get('from_pattern_match')]
    pattern_matched = [f for f in questions_with_changes if f.get('from_pattern_match')]

    # Show errors if any
    if questions_with_errors:
        st.warning(f"⚠️ {len(questions_with_errors)} question(s) could not be processed:")
        for fix in questions_with_errors:
            st.error(f"Error: {fix.get('error', 'Unknown error')}")

    if not questions_with_changes:
        st.success("✅ No errors found! All selected questions look good.")
        if st.button("⬅️ Back to Questions"):
            st.session_state.ai_fix_mode = False
            if 'ai_fix_results_data' in st.session_state:
                del st.session_state.ai_fix_results_data
            st.rerun()
        return

    # Show summary
    st.info(f"📊 **Total: {len(questions_with_changes)} question(s) with errors to fix**")
    if pattern_matched:
        st.markdown(f"- {len(directly_selected)} originally selected")
        st.markdown(f"- {len(pattern_matched)} found by pattern detection")

    # Initialize approval tracking
    if 'approved_fixes' not in st.session_state:
        st.session_state.approved_fixes = set()

    # Bulk approval controls
    st.markdown("---")
    approved_count = len(st.session_state.approved_fixes)
    total_count = len(questions_with_changes)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if approved_count == 0:
            st.markdown(f"**Review {total_count} fix(es)** - None selected")
        elif approved_count == total_count:
            st.success(f"**✅ All {total_count} fix(es) selected**")
        else:
            st.info(f"**{approved_count} of {total_count} fix(es) selected**")
    with col2:
        all_selected = (approved_count == total_count)
        if st.button("✅ Select All", key="select_all_fixes", use_container_width=True, disabled=all_selected):
            # Approve all questions with changes
            for fix in questions_with_changes:
                st.session_state.approved_fixes.add(fix['question_id'])
            st.toast(f"✅ Selected all {len(questions_with_changes)} fixes!", icon="✅")
            st.rerun()
    with col3:
        none_selected = (approved_count == 0)
        if st.button("❌ Deselect All", key="deselect_all_fixes", use_container_width=True, disabled=none_selected):
            st.session_state.approved_fixes = set()
            st.toast("❌ Deselected all fixes", icon="ℹ️")
            st.rerun()

    # Display each fix for review
    for idx, fix in enumerate(questions_with_changes, 1):
        st.markdown("---")

        # Show header with pattern match badge and approval status
        question_id = fix['question_id']
        is_approved = question_id in st.session_state.approved_fixes
        approval_badge = "✅ **SELECTED**" if is_approved else "⬜ Not selected"

        header_text = f"### Question {idx} of {len(questions_with_changes)}"
        if fix.get('from_pattern_match'):
            st.markdown(f"{header_text} 🔍 *Found by Pattern Detection* | {approval_badge}")
        else:
            st.markdown(f"{header_text} | {approval_badge}")

        # Show changes summary
        changes_summary = []
        if fix['changes_made'].get('question'):
            changes_summary.extend(fix['changes_made']['question'])
        if fix['changes_made'].get('choices'):
            choices_changes = fix['changes_made']['choices']
            # Handle both dict format {"0": [...], "1": [...]} and list format [[], [], []]
            if isinstance(choices_changes, dict):
                for choice_idx, choice_changes in choices_changes.items():
                    if choice_changes:  # Only show if there are changes
                        changes_summary.extend([f"Choice {choice_idx}: {c}" for c in choice_changes])
            elif isinstance(choices_changes, list):
                for choice_idx, choice_changes in enumerate(choices_changes):
                    if choice_changes:  # Only show if there are changes
                        changes_summary.extend([f"Choice {choice_idx}: {c}" for c in choice_changes])
        if fix['changes_made'].get('answer'):
            changes_summary.extend(fix['changes_made']['answer'])
        if fix['changes_made'].get('explanation'):
            changes_summary.extend(fix['changes_made']['explanation'])

        # Show answer change prominently if present
        if fix.get('answer_changed'):
            validation = fix.get('answer_validation', {})
            st.error(f"⚠️ **INCORRECT ANSWER DETECTED**")
            st.markdown(f"""
**AI detected the correct answer may be wrong:**
- Original: **{chr(65 + fix['original_correct_answer'])}**. {fix['original_choices'][fix['original_correct_answer']]}
- Suggested: **{chr(65 + fix['suggested_correct_answer'])}**. {fix['original_choices'][fix['suggested_correct_answer']]}
- Confidence: **{validation.get('confidence', 0):.0%}**

**Reasoning:** {validation.get('reasoning', 'No reasoning provided')}
""")

            # Show explanation regeneration info
            if fix.get('explanation_regenerated'):
                st.success("✅ **Explanation Regenerated** - A new explanation has been generated for the corrected answer")

                # Show explanation preview
                with st.expander("📖 View New Explanation"):
                    st.markdown(fix.get('new_explanation', 'No explanation available'))

                if fix.get('original_explanation'):
                    with st.expander("📖 View Original Explanation (for comparison)"):
                        st.markdown(fix['original_explanation'])

        if changes_summary:
            st.markdown("**All Changes:**")
            for change in changes_summary:
                st.markdown(f"- {change}")

        # Before/After comparison
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ❌ Before")
            st.text_area(
                "Question",
                value=fix['original_question'],
                height=100,
                key=f"before_q_{idx}",
                disabled=True
            )
            st.markdown("**Choices:**")
            for i, choice in enumerate(fix['original_choices']):
                # Mark the original correct answer
                is_correct = (i == fix.get('original_correct_answer'))
                label = f"{'✓ ' if is_correct else ''}Choice {chr(65 + i)}"
                st.text_input(
                    label,
                    value=choice,
                    key=f"before_c_{idx}_{i}",
                    disabled=True
                )

        with col2:
            st.markdown("#### ✅ After")
            st.text_area(
                "Question",
                value=fix['fixed_question'],
                height=100,
                key=f"after_q_{idx}",
                disabled=True
            )
            st.markdown("**Choices:**")
            for i, choice in enumerate(fix['fixed_choices']):
                # Mark the suggested correct answer (may be different from original)
                is_correct = (i == fix.get('suggested_correct_answer'))
                label = f"{'✓ ' if is_correct else ''}Choice {chr(65 + i)}"
                st.text_input(
                    label,
                    value=choice,
                    key=f"after_c_{idx}_{i}",
                    disabled=True
                )

        # Approval buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                f"✅ {'Approved' if is_approved else 'Approve'} Fix {idx}",
                key=f"approve_{idx}",
                type="primary" if not is_approved else "secondary",
                disabled=is_approved
            ):
                st.session_state.approved_fixes.add(question_id)
                st.toast(f"✅ Fix {idx} approved!", icon="✅")
                st.rerun()

        with col2:
            if st.button(
                f"⏭️ Skip {idx}",
                key=f"skip_{idx}",
                disabled=not is_approved
            ):
                st.session_state.approved_fixes.discard(question_id)
                st.toast(f"⏭️ Fix {idx} unapproved", icon="ℹ️")
                st.rerun()

    # Apply all approved fixes
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{len(st.session_state.approved_fixes)} fix(es) approved**")
    with col2:
        if st.button(
            "💾 Apply All Approved",
            type="primary",
            disabled=len(st.session_state.approved_fixes) == 0
        ):
            # Show loading spinner while applying fixes
            with st.spinner(f"Applying {len(st.session_state.approved_fixes)} fix(es) to database..."):
                success_count = apply_approved_fixes(fix_results)

            # Show success message
            st.success(f"✅ Successfully applied {success_count} fix(es) to the database!")
            st.toast(f"✅ {success_count} questions updated!", icon="🎉")

            # Wait a moment so user can see the success message
            import time
            time.sleep(1.5)

            # Cleanup
            st.session_state.ai_fix_mode = False
            st.session_state.selected_questions = set()
            if 'ai_fix_results_data' in st.session_state:
                del st.session_state.ai_fix_results_data
            if 'approved_fixes' in st.session_state:
                del st.session_state.approved_fixes
            st.rerun()

    with col3:
        if st.button("❌ Cancel", key="cancel_ai_fix"):
            st.session_state.ai_fix_mode = False
            if 'ai_fix_results_data' in st.session_state:
                del st.session_state.ai_fix_results_data
            if 'approved_fixes' in st.session_state:
                del st.session_state.approved_fixes
            st.rerun()


# Main entry point
if __name__ == "__main__":
    show_admin_question_pools()
