"""
Admin Upload Mock Exam Page
Allows admins to upload mock exams via CSV/JSON/PDF/Word files
Supports both single mock exams and question pool management
"""

import asyncio
import csv
import io
import json
import logging
from typing import Any, Dict, List

import streamlit as st

import config
from auth_utils import AuthUtils, run_async
from document_parser import document_parser
from question_pool_manager import question_pool_manager

logger = logging.getLogger(__name__)


async def infer_answer_with_ai(question_text: str, choices: List[str]) -> int:
    """
    Use AI to infer the correct answer by analyzing the question and choices.
    Returns the index of the most likely correct answer (0-based).
    """
    from openrouter_utils import OpenRouterManager

    openrouter = OpenRouterManager()

    # Format choices with letters
    choices_text = "\n".join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])

    prompt = f"""You are an expert in finance and regulatory exams. Analyze this question and determine the correct answer.

Question: {question_text}

Choices:
{choices_text}

Based on your knowledge, which choice is most likely correct? Respond with ONLY the letter (A, B, C, D, or E) of the correct answer, nothing else."""

    try:
        response = await openrouter._generate_text_with_retry(prompt, max_tokens=10)
        answer_letter = response.strip().upper()

        # Convert letter to index
        if answer_letter in ['A', 'B', 'C', 'D', 'E']:
            return ord(answer_letter) - ord('A')
        else:
            # Fallback to first choice if AI returns invalid
            return 0

    except Exception as e:
        logger.error(f"Error inferring answer with AI: {e}")
        return 0  # Default to first choice


def validate_question_quality(questions: List[Dict]) -> tuple[List[Dict], List[Dict], Dict[str, int]]:
    """
    Validate question quality and filter out problematic questions.

    Returns:
        (valid_questions, invalid_questions, quality_stats)
    """
    valid_questions = []
    invalid_questions = []
    quality_stats = {
        "duplicate_choices": 0,
        "empty_choices": 0,
        "missing_correct_answer": 0,
        "insufficient_choices": 0,
    }

    for q in questions:
        issues = []

        # Check 1: Ensure choices exist and is a list
        choices = q.get("choices", [])
        if not isinstance(choices, list):
            try:
                choices = json.loads(choices) if isinstance(choices, str) else []
            except:
                choices = []

        # Check 2: Insufficient choices (need at least 2)
        if len(choices) < 2:
            issues.append("insufficient_choices")
            quality_stats["insufficient_choices"] += 1

        # Check 3: Empty choices
        empty_count = sum(1 for c in choices if not c or (isinstance(c, str) and not c.strip()))
        if empty_count > 0:
            issues.append("empty_choices")
            quality_stats["empty_choices"] += 1

        # Check 4: Duplicate choices (exact matches)
        non_empty_choices = [c for c in choices if c and (not isinstance(c, str) or c.strip())]
        if len(non_empty_choices) != len(set(non_empty_choices)):
            issues.append("duplicate_choices")
            quality_stats["duplicate_choices"] += 1

        # Check 5: Missing or invalid correct answer
        correct_answer = q.get("correct_answer")
        if correct_answer is None or not isinstance(correct_answer, int) or correct_answer < 0 or correct_answer >= len(choices):
            issues.append("missing_correct_answer")
            quality_stats["missing_correct_answer"] += 1

        # Categorize question
        if issues:
            q["validation_issues"] = issues
            invalid_questions.append(q)
        else:
            valid_questions.append(q)

    return valid_questions, invalid_questions, quality_stats


def show_admin_upload():
    """Display admin upload mock exam page"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated() or not auth.is_admin():
        st.error("Admin access required")
        st.stop()

    # Back to dashboard button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Back to Dashboard", key="back_to_dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown("# 📤 Upload Questions")

    # Mode selection
    upload_mode = st.radio(
        "Upload Mode:",
        ["💼 Question Pool (Recommended for multiple versions)", "🎯 Single Mock Exam"],
        index=0,
        horizontal=True,
        help="Question Pool: Merge multiple PDF versions automatically. Single Mock: Create one exam.",
        key="upload_mode_v2",
    )

    is_pool_mode = "Question Pool" in upload_mode

    if is_pool_mode:
        show_question_pool_upload(auth)
    else:
        show_single_mock_upload(auth)


def show_question_pool_upload(auth):
    """Question Pool upload mode - for managing question banks"""
    st.markdown("## 💼 Question Pool Upload")
    st.markdown(
        '<p style="color: white;">📌 Upload multiple PDF versions of the same exam. System automatically detects and removes duplicates!</p>',
        unsafe_allow_html=True,
    )

    with st.form("upload_pool_form"):
        # Pool configuration
        st.markdown(
            '<p style="color: #000000; font-weight: 500; margin-bottom: 0.5rem;">📚 Pool Name *</p>',
            unsafe_allow_html=True,
        )
        pool_name = st.text_input(
            "Pool Name",
            placeholder="e.g., CACS2 Paper 2",
            help="Give your question pool a unique name. All uploads with the same name will merge automatically.",
            label_visibility="collapsed",
        )

        col1, col2 = st.columns(2)

        with col1:
            category_options = [
                "Finance & Accounting",
                "Programming",
                "Mathematics",
                "Science",
                "Business",
                "General",
                "Custom...",
            ]
            st.markdown(
                '<p style="color: #000000; font-weight: 500; margin-bottom: 0.5rem;">Category</p>',
                unsafe_allow_html=True,
            )
            category_selection = st.selectbox(
                "Category Select",
                category_options,
                index=0,
                help="Choose the most appropriate category",
                key="pool_category_v2",
                label_visibility="collapsed",
            )

            if category_selection == "Custom...":
                category = st.text_input(
                    "Custom Category Name",
                    placeholder="e.g., IBF CACS, Professional Certification, Medical, Legal",
                    help="Enter a custom category name",
                    key="pool_custom_category_v2",
                )
            else:
                category = category_selection

        with col2:
            description = st.text_area(
                "Description (Optional)", placeholder="Describe this question pool...", height=100
            )

        st.markdown("### 📁 Upload Questions File(s)")

        uploaded_files = st.file_uploader(
            "Choose PDF/Word/CSV/JSON files",
            type=["csv", "json", "pdf", "docx", "doc"],
            accept_multiple_files=True,
            help="Upload one or more files. Questions will be extracted and merged into the pool.",
        )

        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            enable_ai_detection = st.checkbox(
                "Enable AI Duplicate Detection",
                value=True,
                help="Use AI to detect semantically similar questions (recommended, but uses API credits)",
            )

            similarity_threshold = st.slider(
                "Similarity Threshold (%)",
                min_value=80,
                max_value=100,
                value=95,
                help="Questions with similarity ≥ this value will be marked as duplicates",
            )

        # Submit
        submit_pool = st.form_submit_button(
            "🚀 Upload to Question Pool", use_container_width=True, type="primary"
        )

        if submit_pool:
            if not pool_name:
                st.error("Please enter a pool name")
            elif not uploaded_files:
                st.error("Please upload at least one file")
            else:
                # Store upload parameters in session state
                st.session_state.upload_in_progress = True
                st.session_state.upload_params = {
                    "pool_name": pool_name,
                    "category": category,
                    "description": description,
                    "uploaded_files": uploaded_files,
                    "enable_ai_detection": enable_ai_detection,
                    "similarity_threshold": similarity_threshold / 100.0,
                }
                st.rerun()

    # Process upload outside of form (if triggered)
    if st.session_state.get("upload_in_progress"):
        params = st.session_state.upload_params

        st.markdown(
            '<p style="color: #000000;">Processing question pool upload...</p>',
            unsafe_allow_html=True,
        )

        result = None
        try:
            with st.spinner(""):
                result = run_async(
                    process_pool_upload(
                        pool_name=params["pool_name"],
                        category=params["category"],
                        description=params["description"],
                        uploaded_files=params["uploaded_files"],
                        enable_ai_detection=params["enable_ai_detection"],
                        similarity_threshold=params["similarity_threshold"],
                    )
                )
        finally:
            # CRITICAL: Always clear upload state, even if processing fails
            # This prevents the perpetual blue loader bug
            st.session_state.upload_in_progress = False
            st.session_state.upload_params = None

        if isinstance(result, dict) and result.get("success"):
            # Check if this was background processing
            if result.get("background"):
                # Background processing case - pool created but questions being processed
                st.markdown("---")

                # Navigation buttons for background processing case
                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "📊 Check Pool Status", use_container_width=True, type="primary"
                    ):
                        st.session_state.page = "admin_manage_pools"
                        st.rerun()

                with col2:
                    if st.button("🏠 Back to Dashboard", use_container_width=True):
                        st.session_state.page = "dashboard"
                        st.rerun()
            else:
                # Normal processing case
                st.success("🎉 Question pool updated successfully!")
                st.balloons()

                # Verify upload and show actual question count
                st.markdown("---")
                st.markdown(
                    '<h3 style="color: #000000;">✅ Upload Complete!</h3>', unsafe_allow_html=True
                )

                # Fetch actual current question count from database
                from db import db

                pool_id = result.get("pool_id")
                pool_name_result = result.get("pool_name")

                if pool_id:
                    pool_questions = run_async(db.get_pool_questions(pool_id))
                    actual_count = len(pool_questions)

                    st.info(
                        f"📊 **Pool '{pool_name_result}' now contains {actual_count} total questions**\n\n"
                        f"✅ Upload verified! Questions are immediately available for generating mock exams."
                    )
                else:
                    st.warning(
                        "Upload completed but couldn't verify question count. Please check Manage Pools."
                    )

                # Navigation buttons (now outside form)
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(
                        "📊 View Pool Questions", use_container_width=True, type="primary"
                    ):
                        st.session_state.page = "admin_manage_pools"
                        st.rerun()

                with col2:
                    if st.button("➕ Upload More Questions", use_container_width=True):
                        st.rerun()

                with col3:
                    if st.button("🏠 Back to Dashboard", use_container_width=True):
                        st.session_state.page = "dashboard"
                        st.rerun()
        else:
            # Handle failure case - result could be False or a dict with error
            if isinstance(result, dict):
                error_msg = result.get("error", "Unknown error occurred")
            else:
                error_msg = "No questions could be extracted from the uploaded file(s). Please ensure the document contains valid exam questions in a readable format."
            st.error(f"Failed to update question pool: {error_msg}")
            st.info(
                "💡 **Tips:** Try uploading a different file format (CSV, JSON) or ensure the PDF contains selectable text (not scanned images)."
            )


def show_single_mock_upload(auth):
    """Single mock exam upload mode - traditional approach"""
    st.markdown("## 🎯 Single Mock Exam Upload")
    st.markdown("Upload a new mock exam from CSV, JSON, PDF, or Word document")

    # Upload form
    with st.form("upload_mock_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input(
                "Mock Exam Title *",
                placeholder="e.g., Python Programming Fundamentals",
                help="Clear, descriptive title for the exam",
            )

            category_options = [
                "Finance & Accounting",
                "Programming",
                "Mathematics",
                "Science",
                "Business",
                "General",
                "Custom...",
            ]
            category_selection = st.selectbox(
                "Category",
                category_options,
                index=0,
                help="Choose the most appropriate category",
                key="single_category_v2",
            )

            if category_selection == "Custom...":
                category = st.text_input(
                    "Custom Category Name",
                    placeholder="e.g., IBF CACS, Professional Certification, Medical, Legal",
                    help="Enter a custom category name",
                    key="single_custom_category_v2",
                )
            else:
                category = category_selection

            price_credits = st.number_input(
                "Price (Credits) *",
                min_value=1,
                max_value=50,
                value=5,
                help="Number of credits required to take this exam",
            )

        with col2:
            description = st.text_area(
                "Description *",
                placeholder="Describe what this exam covers...",
                height=100,
                help="Detailed description of the exam content and objectives",
            )

            explanation_enabled = st.checkbox(
                "Enable AI Explanations",
                value=True,
                help="Allow users to unlock AI-generated explanations for answers",
            )

        st.markdown("### 📁 Upload Questions File")

        # File upload with PDF/Word support
        uploaded_file = st.file_uploader(
            "Choose a file (CSV, JSON, PDF, or Word)",
            type=["csv", "json", "pdf", "docx", "doc"],
            help="Upload questions in CSV, JSON, PDF, or Word format",
        )

        # File format help
        with st.expander("📋 File Format Requirements"):
            tab1, tab2, tab3 = st.tabs(["📄 PDF/Word (AI)", "📊 CSV", "📝 JSON"])

            with tab1:
                st.markdown(document_parser.get_file_type_help())

            with tab2:
                st.markdown(
                    """
                **CSV Format:**
                - Columns: `question`, `choice_1`, `choice_2`, `choice_3`, `choice_4`, `correct_index`, `scenario`, `explanation_seed`
                - `correct_index`: 0-based index (0, 1, 2, 3)
                - `scenario`: Optional context/background
                - `explanation_seed`: Optional hint for AI explanation generation

                **Example CSV:**
                ```
                question,choice_1,choice_2,choice_3,choice_4,correct_index,scenario,explanation_seed
                "What is 2+2?","3","4","5","6",1,"Basic math","Addition"
                ```
                """
                )

            with tab3:
                st.markdown(
                    """
                **JSON Format:**
                ```json
                [
                    {
                        "question": "What is the output of print(2 + 2)?",
                        "choices": ["3", "4", "5", "6"],
                        "correct_index": 1,
                        "scenario": "Basic arithmetic in Python",
                        "explanation_seed": "Addition operator"
                    }
                ]
                ```
                """
                )

        # Preview uploaded file
        if uploaded_file is not None:
            st.markdown("### 👀 File Preview")
            try:
                questions = parse_uploaded_file(uploaded_file)

                if questions:
                    st.success(f"✅ Found {len(questions)} questions")

                    # Show first few questions as preview
                    for i, q in enumerate(questions[:3]):
                        with st.expander(f"Question {i+1}: {q['question'][:50]}..."):
                            st.write(f"**Question:** {q['question']}")
                            st.write("**Choices:**")
                            for j, choice in enumerate(q["choices"]):
                                marker = "✅" if j == q["correct_index"] else "◯"
                                st.write(f"  {marker} {j}: {choice}")
                            if q.get("scenario"):
                                st.write(f"**Scenario:** {q['scenario']}")

                    if len(questions) > 3:
                        st.info(f"... and {len(questions) - 3} more questions")

                else:
                    st.error("No valid questions found in the file")

            except Exception as e:
                st.error(f"Error parsing file: {str(e)}")

        # Submit button
        submit_uploaded = st.form_submit_button(
            "🚀 Create Mock Exam", use_container_width=True, type="primary"
        )

        if submit_uploaded:
            if not title or not description:
                st.error("Please fill in all required fields (marked with *)")
                return

            if uploaded_file is None:
                st.error("Please upload a questions file")
                return

            # Process upload
            with st.spinner("Creating mock exam..."):
                success = run_async(
                    process_mock_upload(
                        title=title,
                        description=description,
                        category=category,
                        price_credits=price_credits,
                        explanation_enabled=explanation_enabled,
                        uploaded_file=uploaded_file,
                    )
                )

                if success:
                    st.success("🎉 Mock exam created successfully!")
                    st.balloons()

                    if st.button("📊 Go to Manage Mocks"):
                        st.session_state.page = "admin_manage"
                        st.rerun()
                else:
                    st.error("Failed to create mock exam. Please try again.")


def parse_uploaded_file(uploaded_file, pool_id=None, pool_name=None) -> Any:
    """
    Parse uploaded CSV/JSON/PDF/Word file into questions list

    Returns:
        List[Dict[str, Any]] - List of questions
        OR "__BACKGROUND_PROCESSING__" marker if background OCR was triggered
    """
    file_extension = uploaded_file.name.split(".")[-1].lower()

    if file_extension == "csv":
        return parse_csv_file(uploaded_file)
    elif file_extension == "json":
        return parse_json_file(uploaded_file)
    elif file_extension in ["pdf", "docx", "doc"]:
        # Use AI-powered document parser
        st.info("🤖 Using AI to extract questions from document...")
        success, questions, error = document_parser.parse_document(uploaded_file, pool_id, pool_name)

        if not success:
            raise ValueError(f"Document parsing failed: {error}")

        # Check if background processing was triggered
        # When success=True but questions=[] and error="", it means background OCR was triggered
        if success and not questions and not error:
            return "__BACKGROUND_PROCESSING__"

        return questions
    else:
        raise ValueError(
            f"Unsupported file format: {file_extension}. Please use CSV, JSON, PDF, or Word."
        )


def parse_csv_file(uploaded_file) -> List[Dict[str, Any]]:
    """Parse CSV file into questions list"""
    # Read CSV content
    content = uploaded_file.read().decode("utf-8")
    csv_data = csv.DictReader(io.StringIO(content))

    questions = []

    for row_num, row in enumerate(csv_data, 1):
        try:
            # Extract choices from columns
            choices = []
            for i in range(1, 7):  # Support up to 6 choices
                choice_key = f"choice_{i}"
                if choice_key in row and row[choice_key].strip():
                    choices.append(row[choice_key].strip())

            if len(choices) < 2:
                st.warning(f"Row {row_num}: Skipping question with less than 2 choices")
                continue

            correct_index = int(row["correct_index"])

            # Validate correct_index
            if correct_index >= len(choices):
                st.warning(
                    f"Row {row_num}: Invalid correct_index {correct_index} for {len(choices)} choices"
                )
                continue

            question = {
                "question": row["question"].strip(),
                "choices": choices,
                "correct_index": correct_index,
                "correct_answer": correct_index,  # Normalize to correct_answer for validation
                "scenario": row.get("scenario", "").strip() or None,
                "explanation_seed": row.get("explanation_seed", "").strip() or None,
            }

            questions.append(question)

        except (ValueError, KeyError) as e:
            st.warning(f"Row {row_num}: Error parsing question - {str(e)}")
            continue

    return questions


def parse_json_file(uploaded_file) -> List[Dict[str, Any]]:
    """Parse JSON file into questions list"""
    content = uploaded_file.read().decode("utf-8")
    data = json.loads(content)

    if not isinstance(data, list):
        raise ValueError("JSON file must contain an array of questions")

    questions = []

    for i, item in enumerate(data, 1):
        try:
            if not isinstance(item, dict):
                st.warning(f"Question {i}: Must be an object")
                continue

            # Check for required question field
            if "question" not in item:
                st.warning(f"Question {i}: Missing required field 'question'")
                continue

            # Support both "choices" and "options" field names
            choices = item.get("choices") or item.get("options")
            if not choices:
                st.warning(f"Question {i}: Missing required field 'choices' or 'options'")
                continue

            if not isinstance(choices, list) or len(choices) < 2:
                st.warning(f"Question {i}: Must have at least 2 choices")
                continue

            # Support both "correct_index" and "correct_answer" field names
            correct_index = item.get("correct_index")
            if correct_index is None:
                correct_index = item.get("correct_answer")

            if correct_index is None:
                st.warning(f"Question {i}: Missing required field 'correct_index' or 'correct_answer'")
                continue

            if not isinstance(correct_index, int) or correct_index < 0 or correct_index >= len(choices):
                st.warning(f"Question {i}: Invalid correct_index/correct_answer {correct_index}")
                continue

            question = {
                "question": item["question"],
                "choices": choices,
                "correct_index": correct_index,
                "correct_answer": correct_index,  # Normalize to correct_answer for validation
                "scenario": item.get("scenario"),
                "explanation_seed": item.get("explanation_seed"),
            }

            questions.append(question)

        except Exception as e:
            st.warning(f"Question {i}: Error parsing - {str(e)}")
            continue

    return questions


async def process_mock_upload(
    title: str,
    description: str,
    category: str,
    price_credits: int,
    explanation_enabled: bool,
    uploaded_file,
) -> bool:
    """Process the mock exam upload"""
    try:
        # Parse questions from file
        questions = parse_uploaded_file(uploaded_file)

        if not questions:
            return False

        # Create mock exam in database
        from db import db

        mock_data = {
            "title": title,
            "description": description,
            "category": category,
            "questions_json": questions,
            "price_credits": price_credits,
            "explanation_enabled": explanation_enabled,
            "is_active": True,
        }

        success = await db.create_mock(mock_data)

        if success and explanation_enabled:
            # Optionally generate AI explanations in background
            # This could be done asynchronously
            pass

        return success

    except Exception as e:
        st.error(f"Upload processing error: {str(e)}")
        return False


async def process_pool_upload(
    pool_name, category, description, uploaded_files, enable_ai_detection, similarity_threshold
):
    """Process question pool upload with duplicate detection"""
    try:
        from db import db

        # Create progress placeholder
        progress_placeholder = st.empty()
        stats_placeholder = st.empty()

        # Get or create question pool
        progress_placeholder.info(f"🔍 Setting up question pool '{pool_name}'...")
        pool = await db.create_or_update_question_pool(
            pool_name=pool_name,
            category=category,
            description=description,
            created_by=st.session_state.get("user", {}).get("id"),
        )

        if not pool:
            st.error("Failed to create question pool")
            return False

        pool_id = pool["id"]

        # Get existing questions from pool
        existing_questions = await db.get_pool_questions(pool_id)
        progress_placeholder.info(f"📊 Found {len(existing_questions)} existing questions in pool")

        # Convert existing questions to format expected by question_pool_manager
        existing_q_list = []
        for eq in existing_questions:
            existing_q_list.append(
                {
                    "question": eq["question_text"],
                    "choices": (
                        json.loads(eq["choices"])
                        if isinstance(eq["choices"], str)
                        else eq["choices"]
                    ),
                    "correct_index": eq["correct_answer"],
                }
            )

        # Process each uploaded file
        all_new_questions = []
        total_extracted = 0
        background_processing_triggered = False

        for idx, uploaded_file in enumerate(uploaded_files, 1):
            progress_placeholder.info(
                f"📄 Processing file {idx}/{len(uploaded_files)}: {uploaded_file.name}"
            )

            try:
                # Parse questions from file (pass pool info for background OCR processing)
                questions = parse_uploaded_file(uploaded_file, pool_id, pool_name)

                # Check if background processing was triggered
                if questions == "__BACKGROUND_PROCESSING__":
                    background_processing_triggered = True
                    stats_placeholder.info(
                        f"🔄 Background OCR processing started for {uploaded_file.name}"
                    )
                    continue

                total_extracted += len(questions)

                # Add source filename to each question
                for q in questions:
                    q["source_file"] = uploaded_file.name

                all_new_questions.extend(questions)

                stats_placeholder.success(
                    f"✅ Extracted {len(questions)} questions from {uploaded_file.name}"
                )

            except Exception as e:
                stats_placeholder.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                continue

        # If background processing was triggered, show success message and exit
        if background_processing_triggered:
            progress_placeholder.empty()
            stats_placeholder.empty()

            st.success(
                f"✅ **Background processing started successfully!**\n\n"
                f"📊 Pool '{pool_name}' has been created\n\n"
                f"🔄 Your large scanned PDF is being processed in the background\n\n"
                f"⏱️ Processing typically takes 10-15 minutes per PDF\n\n"
                f"💡 **You can safely close this page.** Questions will be added to the pool automatically when processing completes.\n\n"
                f"Check the pool in a few minutes to see your questions."
            )

            # Return pool_id and success status
            return {"success": True, "pool_id": pool_id, "pool_name": pool_name, "background": True}

        if not all_new_questions:
            st.error("No questions extracted from uploaded files")
            return False

        progress_placeholder.info(
            f"🔍 Detecting duplicates in {len(all_new_questions)} new questions..."
        )

        # Step 1: Detect exact duplicates (fast)
        unique_after_exact, exact_duplicates = question_pool_manager.detect_exact_duplicates(
            all_new_questions, existing_q_list
        )

        stats_placeholder.info(
            f"📊 Exact duplicate detection: {len(exact_duplicates)} exact matches found, "
            f"{len(unique_after_exact)} potentially unique questions remaining"
        )

        # Step 2: AI-powered semantic duplicate detection (if enabled)
        questions_to_add = unique_after_exact
        ai_duplicates_found = 0
        ai_detection_skipped = False

        if enable_ai_detection and unique_after_exact and existing_q_list:
            progress_placeholder.info(
                "🤖 Running AI duplicate detection (this may take a moment)..."
            )

            # For performance, we'll check AI similarity for questions that passed exact check
            final_unique = []

            for idx, new_q in enumerate(unique_after_exact):
                # Check if this question is similar to any existing questions
                similar, error = await question_pool_manager.detect_similar_questions_with_ai(
                    new_q, existing_q_list, threshold=similarity_threshold
                )

                # If we hit a rate limit error, skip the rest of AI detection
                if error and ("rate limit" in error.lower() or "429" in error):
                    ai_detection_skipped = True
                    # Add remaining questions without AI check
                    final_unique.append(new_q)
                    final_unique.extend(unique_after_exact[idx + 1 :])
                    remaining_count = len(unique_after_exact) - idx - 1
                    progress_placeholder.warning(
                        f"⚠️ AI duplicate detection paused due to API rate limits. "
                        f"Continuing with exact matching only for remaining {remaining_count} questions..."
                    )
                    break

                if similar:
                    # Found semantic duplicate
                    ai_duplicates_found += 1
                    new_q["is_duplicate"] = True
                    new_q["similarity_score"] = similar[0][1] * 100  # Convert to percentage
                else:
                    # No similar questions found - add to unique list
                    final_unique.append(new_q)

            questions_to_add = final_unique

            if ai_detection_skipped:
                stats_placeholder.warning(
                    f"⚠️ AI detection: {ai_duplicates_found} semantic duplicates found before rate limit. "
                    f"Remaining questions checked with exact matching only. "
                    "This usually happens when API rate limits are exceeded (20 req/min, 50 req/day for free tier)."
                )
            else:
                stats_placeholder.info(
                    f"🤖 AI detection: {ai_duplicates_found} semantic duplicates found "
                    f"(threshold: {similarity_threshold*100}%)"
                )

        # Auto-fix common text corruption issues and validate questions
        if questions_to_add:
            from question_text_validator import validate_question_batch
            from question_validator import QuestionValidator

            progress_placeholder.info("🔧 Checking for text corruption and auto-fixing...")

            validation_result = validate_question_batch(questions_to_add)
            questions_to_add = validation_result['questions']
            text_stats = validation_result['stats']

            # Show auto-fix results if any fixes were applied
            if text_stats.get('fixed', 0) > 0:
                fixes_summary = []
                for fix_type, count in text_stats.get('fixes_by_type', {}).items():
                    fixes_summary.append(f"  • {fix_type}: {count}x")

                stats_placeholder.success(
                    f"✨ Auto-fixed {text_stats['fixed']} questions:\n" +
                    "\n".join(fixes_summary)
                )

            # Show warnings if any
            if text_stats.get('questions_with_warnings'):
                warning_count = len(text_stats['questions_with_warnings'])
                with st.expander(f"⚠️ {warning_count} questions have warnings (click to review)"):
                    for idx, item in enumerate(text_stats['questions_with_warnings'][:10], 1):
                        st.markdown(f"**{idx}.** {item['text']}")
                        for warning in item['warnings']:
                            st.markdown(f"  - ⚠️ {warning}")

            # Validate questions for critical errors (missing context, case studies, etc.)
            progress_placeholder.info("🔍 Validating questions for completeness...")

            validated_questions = []
            rejected_questions = []

            for q in questions_to_add:
                is_valid, errors = QuestionValidator.validate_question(q)

                if not is_valid:
                    # Extract CRITICAL errors
                    critical_errors = [e for e in errors if 'CRITICAL' in e]
                    q['validation_errors'] = critical_errors
                    rejected_questions.append(q)
                else:
                    validated_questions.append(q)

            # Show validation results if questions were rejected
            if rejected_questions:
                st.error(
                    f"❌ **Validation Failed: {len(rejected_questions)} questions rejected**\n\n"
                    f"These questions have CRITICAL errors and cannot be uploaded:"
                )

                with st.expander(f"📋 View {len(rejected_questions)} Rejected Questions"):
                    for idx, q in enumerate(rejected_questions[:20], 1):  # Show first 20
                        st.markdown(f"**{idx}.** {q['question'][:100]}...")
                        for error in q['validation_errors']:
                            st.markdown(f"   🚫 {error}")
                        st.markdown("---")

                    if len(rejected_questions) > 20:
                        st.markdown(f"... and {len(rejected_questions) - 20} more")

                st.info(
                    f"💡 **{len(validated_questions)} questions passed validation** and will be uploaded.\n\n"
                    f"To fix rejected questions:\n"
                    f"- Add detailed scenario/case study context in the 'scenario' field\n"
                    f"- Or rewrite questions to be self-contained with all necessary information"
                )

            # Update questions_to_add to only include validated questions
            questions_to_add = validated_questions

        # Validate question quality before saving
        if questions_to_add:
            valid_questions, invalid_questions, quality_stats = validate_question_quality(questions_to_add)

            # Show validation results if issues found
            if invalid_questions:
                # Separate questions with ONLY missing answer (can be AI-inferred) from other issues
                missing_answer_only = [
                    q for q in invalid_questions
                    if q.get('validation_issues') == ['missing_correct_answer']
                ]
                other_issues = [q for q in invalid_questions if q not in missing_answer_only]

                # Automatically use AI to infer missing answers
                if missing_answer_only:
                    st.info(
                        f"🤖 **Found {len(missing_answer_only)} questions without answers.**\n\n"
                        f"Automatically using AI to infer correct answers..."
                    )

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    ai_fixed = []
                    for idx, q in enumerate(missing_answer_only):
                        status_text.info(f"🤖 Inferring answer for question {idx+1}/{len(missing_answer_only)}...")
                        progress_bar.progress((idx + 1) / len(missing_answer_only))

                        # Use AI to infer answer
                        correct_index = await infer_answer_with_ai(q['question'], q['choices'])
                        q['correct_answer'] = correct_index
                        del q['validation_issues']  # Remove validation issues
                        ai_fixed.append(q)

                        # Rate limiting
                        await asyncio.sleep(1)

                    progress_bar.empty()
                    status_text.success(f"✅ AI automatically inferred answers for {len(ai_fixed)} questions!")

                    # Add AI-fixed questions to valid questions
                    valid_questions.extend(ai_fixed)
                    missing_answer_only.clear()

                if other_issues:
                    st.warning(
                        f"⚠️ **Quality Check:** Found {len(other_issues)} questions with issues:\n\n"
                        f"- Duplicate choices: {quality_stats['duplicate_choices']}\n"
                        f"- Empty choices: {quality_stats['empty_choices']}\n"
                        f"- Insufficient choices: {quality_stats['insufficient_choices']}\n\n"
                        f"**These questions will be skipped.**"
                    )

                    # Show details of invalid questions in expander
                    with st.expander("📋 View Invalid Questions"):
                        for idx, q in enumerate(other_issues[:10], 1):  # Show first 10
                            st.markdown(f"**{idx}.** {q['question'][:100]}...")
                            st.markdown(f"   Issues: {', '.join(q.get('validation_issues', []))}")
                            if len(other_issues) > 10:
                                st.markdown(f"   ... and {len(other_issues) - 10} more")
                                break

            # Update questions_to_add to only valid questions
            questions_to_add = valid_questions

        # AI Answer Validation
        if questions_to_add:
            from openrouter_utils import validate_answer_correctness

            progress_placeholder.info("🤖 Validating answer correctness with AI (only for questions missing answers)...")

            validated_questions = []
            auto_corrected = []
            low_confidence_warnings = []
            skipped_count = 0

            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, q in enumerate(questions_to_add, 1):
                status_text.info(f"🤖 Processing question {idx}/{len(questions_to_add)}...")
                progress_bar.progress(idx / len(questions_to_add))

                # Extract question data
                question_text = q.get('question_text') or q.get('question', '')
                choices = q.get('choices', [])
                correct_index = q.get('correct_answer') or q.get('correct_index', 0)
                scenario = q.get('scenario', '')

                # Parse choices if JSON string
                if isinstance(choices, str):
                    try:
                        choices = json.loads(choices)
                    except:
                        pass

                # ONLY validate if question was missing correct answer or had validation issues
                # Skip validation for questions with valid pre-provided answers
                validation_issues = q.get('validation_issues', [])
                has_valid_answer = (
                    q.get('correct_answer') is not None and
                    isinstance(q.get('correct_answer'), int) and
                    'missing_correct_answer' not in validation_issues
                )

                if has_valid_answer:
                    # Question already has a valid answer - skip AI validation
                    validated_questions.append(q)
                    skipped_count += 1
                    continue

                try:
                    # Call AI to validate answer (only for questions missing answers)
                    validation = await validate_answer_correctness(
                        question_text, choices, correct_index, scenario
                    )

                    # Auto-correct if AI is confident
                    if validation['should_auto_correct'] and not validation['is_valid']:
                        # Store original for report
                        original_index = correct_index

                        # Update to AI's suggested answer
                        q['correct_answer'] = validation['ai_suggested_index']
                        q['correct_index'] = validation['ai_suggested_index']

                        auto_corrected.append({
                            'question_text': question_text[:100] + ('...' if len(question_text) > 100 else ''),
                            'old_answer': f"{chr(65 + original_index)} - {choices[original_index]}",
                            'new_answer': f"{chr(65 + validation['ai_suggested_index'])} - {choices[validation['ai_suggested_index']]}",
                            'confidence': validation['confidence'],
                            'reasoning': validation['reasoning']
                        })
                    elif not validation['is_valid'] and validation['confidence'] < 0.90:
                        # Low confidence warning
                        low_confidence_warnings.append({
                            'question_text': question_text[:100] + ('...' if len(question_text) > 100 else ''),
                            'current_answer': f"{chr(65 + correct_index)} - {choices[correct_index]}",
                            'suggested_answer': f"{chr(65 + validation['ai_suggested_index'])} - {choices[validation['ai_suggested_index']]}",
                            'confidence': validation['confidence'],
                            'reasoning': validation['reasoning']
                        })

                    validated_questions.append(q)

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error validating answer for question {idx}: {e}")
                    # Continue with original answer on error
                    validated_questions.append(q)

            progress_bar.empty()
            status_text.empty()

            # Show validation summary
            validated_count = len(questions_to_add) - skipped_count
            if skipped_count > 0:
                progress_placeholder.success(
                    f"✅ AI validation complete: {validated_count} questions validated, "
                    f"{skipped_count} questions skipped (already had valid answers)"
                )
            else:
                progress_placeholder.success(f"✅ AI validation complete: {validated_count} questions validated")

            # Update questions_to_add to use validated questions
            questions_to_add = validated_questions

            # Store results in session state for reporting
            st.session_state.answer_validation_results = {
                'auto_corrected': auto_corrected,
                'low_confidence_warnings': low_confidence_warnings,
                'skipped_count': skipped_count
            }

        # Create upload batch record
        batch_id = await db.create_upload_batch(
            pool_id=pool_id,
            filename=f"{len(uploaded_files)} files: " + ", ".join([f.name for f in uploaded_files]),
            total_questions=total_extracted,
            uploaded_by=st.session_state.get("user", {}).get("id"),
        )

        # Add questions to pool
        if questions_to_add:
            progress_placeholder.info(
                f"💾 Adding {len(questions_to_add)} unique questions to pool..."
            )

            success = await db.add_questions_to_pool(
                pool_id=pool_id,
                questions=questions_to_add,
                source_file=", ".join([f.name for f in uploaded_files]),
                batch_id=batch_id,
            )

            if not success:
                st.error("Failed to save questions to database")
                return False

            # Trigger background AI explanation generation (runs independently)
            import os
            import subprocess
            import sys

            # Use current Python interpreter instead of hardcoded venv path
            python_path = sys.executable
            script_path = os.path.join(os.getcwd(), "background_explanation_generator.py")

            # Spawn detached background process
            subprocess.Popen(
                [python_path, script_path, pool_id, batch_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent process
            )

            logger.info(f"Background explanation generator started for pool {pool_id}")

            # Run health check to catch any incomplete explanations (including existing questions)
            try:
                import threading
                from explanation_health_check import run_health_check_sync

                # Run in background thread to avoid blocking upload completion
                health_check_thread = threading.Thread(target=run_health_check_sync, daemon=True)
                health_check_thread.start()
                logger.info("✅ Post-upload health check initiated in background")
            except Exception as e:
                logger.error(f"Failed to start post-upload health check: {e}")

        # Display final results
        progress_placeholder.empty()
        stats_placeholder.empty()

        # Show comprehensive summary
        st.markdown("---")
        st.markdown('<h3 style="color: #000000;">📊 Upload Summary</h3>', unsafe_allow_html=True)

        # Style metrics with black text
        st.markdown(
            """
        <style>
        [data-testid="stMetricLabel"] {
            color: #000000 !important;
        }
        [data-testid="stMetricValue"] {
            color: #000000 !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📁 Files Processed", len(uploaded_files))

        with col2:
            st.metric("📝 Total Extracted", total_extracted)

        with col3:
            st.metric("✅ Unique Added", len(questions_to_add))

        with col4:
            total_duplicates = len(exact_duplicates) + ai_duplicates_found
            st.metric("🔄 Duplicates Skipped", total_duplicates)

        # Show AI Answer Validation Report
        if 'answer_validation_results' in st.session_state:
            results = st.session_state.answer_validation_results
            auto_corrected = results.get('auto_corrected', [])
            low_confidence_warnings = results.get('low_confidence_warnings', [])

            if auto_corrected or low_confidence_warnings:
                st.markdown("---")
                st.markdown("### 🤖 AI Answer Validation Report")

                if auto_corrected:
                    st.success(f"✅ Auto-corrected {len(auto_corrected)} answer(s) (≥90% confidence)")
                    with st.expander("📋 View Auto-Corrected Answers"):
                        for idx, correction in enumerate(auto_corrected, 1):
                            st.markdown(f"**Question {idx}:** {correction['question_text']}")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"❌ **Old Answer:** {correction['old_answer']}")
                            with col2:
                                st.markdown(f"✅ **New Answer:** {correction['new_answer']}")
                            st.markdown(f"**Confidence:** {correction['confidence']:.0%}")
                            st.markdown(f"**Reasoning:** {correction['reasoning']}")
                            if idx < len(auto_corrected):
                                st.markdown("---")

                if low_confidence_warnings:
                    st.warning(f"⚠️ {len(low_confidence_warnings)} question(s) may have incorrect answers (AI not confident enough to auto-correct)")
                    with st.expander("⚠️ View Potential Issues"):
                        for idx, warning in enumerate(low_confidence_warnings, 1):
                            st.markdown(f"**Question {idx}:** {warning['question_text']}")
                            st.markdown(f"**Current Answer:** {warning['current_answer']}")
                            st.markdown(f"**AI Suggests:** {warning['suggested_answer']}")
                            st.markdown(f"**Confidence:** {warning['confidence']:.0%}")
                            st.markdown(f"**Reasoning:** {warning['reasoning']}")
                            st.info("💡 Review this question manually - AI is not confident enough to auto-correct.")
                            if idx < len(low_confidence_warnings):
                                st.markdown("---")

            # Clean up session state
            del st.session_state.answer_validation_results

        # Explanation generation note
        st.info(
            "💡 **About Explanations:**\n\n"
            "✅ Questions with explanations in the document have been preserved\n\n"
            "🤖 **Background AI generation started!** A background process is now generating explanations "
            "for questions without them. This continues even if you close your browser.\n\n"
            "📚 All questions are immediately available for mock exams. "
            "Check `background_explanation_generator.log` for progress details."
        )

        # Detailed breakdown
        with st.expander("📋 Detailed Breakdown"):
            st.markdown(
                f"""
            **Question Pool:** {pool_name}

            **Processing Results:**
            - Files uploaded: {len(uploaded_files)}
            - Total questions extracted: {total_extracted}
            - Exact duplicates found: {len(exact_duplicates)}
            - AI semantic duplicates found: {ai_duplicates_found}
            - **Unique questions added: {len(questions_to_add)}**

            **Pool Status:**
            - Previous questions in pool: {len(existing_q_list)}
            - New total (estimated): {len(existing_q_list) + len(questions_to_add)}
            """
            )

            if uploaded_files:
                st.markdown("**Files Processed:**")
                for f in uploaded_files:
                    st.markdown(f"- {f.name}")

        # Return pool_id and success status for verification
        return {"success": True, "pool_id": pool_id, "pool_name": pool_name}

    except Exception as e:
        st.error(f"Error processing pool upload: {str(e)}")
        logger.error(f"Pool upload error: {e}", exc_info=True)
        return {"success": False}
