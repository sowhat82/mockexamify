"""
Background AI Fix with Pattern Detection
Runs independently to fix selected questions and find similar errors in the same source files.
Auto-applies all fixes without manual approval.
"""
import asyncio
import json
import logging
import sys
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_ai_fix_pattern.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def update_question(question_id: str, updated_data: Dict[str, Any]) -> bool:
    """Update a specific question in the database"""
    try:
        from db import db
        client = db.admin_client if db.admin_client else db.client
        response = (
            client.table("pool_questions").update(updated_data).eq("id", question_id).execute()
        )
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error updating question {question_id}: {e}")
        return False


async def run_ai_fix_with_patterns(pool_id: str, question_ids: List[str], task_id: str = None):
    """
    Run AI fix on selected questions with pattern detection.
    Automatically applies all fixes.

    Args:
        pool_id: The pool ID
        question_ids: List of question IDs to analyze (starting points for pattern detection)
        task_id: Task ID for status tracking
    """
    from db import db
    from openrouter_utils import fix_question_errors
    from background_task_status import start_task, update_task_progress, complete_task, fail_task

    logger.info("=" * 60)
    logger.info("BACKGROUND AI FIX WITH PATTERN DETECTION")
    logger.info(f"Pool ID: {pool_id}")
    logger.info(f"Selected questions: {len(question_ids)}")
    logger.info("=" * 60)

    try:
        # Get all questions from the pool
        all_questions = await db.get_pool_questions(pool_id)
        questions_by_id = {q['id']: q for q in all_questions}

        # Get pool name for status display
        pools = await db.get_all_question_pools()
        pool_name = next((p['pool_name'] for p in pools if p['id'] == pool_id), "Unknown Pool")

        # Get source files from selected questions
        source_files = set()
        for qid in question_ids:
            q = questions_by_id.get(qid)
            if q and q.get('source_file'):
                source_files.add(q.get('source_file'))

        logger.info(f"Source files from selection: {source_files}")

        # Get all questions from the same source files
        questions_to_process = []
        if source_files:
            questions_to_process = [q for q in all_questions if q.get('source_file') in source_files]
            logger.info(f"Found {len(questions_to_process)} questions from same source files")
        else:
            # If no source files, just process selected questions
            questions_to_process = [questions_by_id[qid] for qid in question_ids if qid in questions_by_id]
            logger.info(f"No source files found, processing {len(questions_to_process)} selected questions only")

        if not questions_to_process:
            logger.info("No questions to process")
            if task_id:
                complete_task(task_id, 0, 0, 0, "No questions to process")
            return

        total_questions = len(questions_to_process)

        # Register task
        if task_id:
            source_desc = f" from {list(source_files)[0][:30]}..." if source_files else ""
            start_task(
                task_id=task_id,
                task_type="ai_fix_pattern",
                description=f"AI Fix with pattern detection{source_desc}",
                total_items=total_questions,
                pool_id=pool_id,
                pool_name=pool_name
            )

        processed = 0
        fixed = 0
        errors = 0

        for idx, question in enumerate(questions_to_process, 1):
            try:
                question_id = question['id']
                question_text = question['question_text']
                choices = json.loads(question['choices']) if isinstance(question['choices'], str) else question['choices']
                correct_answer = question.get('correct_answer')

                logger.info(f"[{idx}/{total_questions}] Analyzing question {question_id[:8]}...")

                # Update status
                if task_id:
                    update_task_progress(task_id, processed, fixed, errors, f"Question {idx}/{total_questions}")

                # Run AI fix with answer validation
                fix_result = await fix_question_errors(
                    question_text=question_text,
                    choices=choices,
                    correct_answer=correct_answer,
                    validate_answer=True
                )

                processed += 1

                # Check if there are changes to apply
                if fix_result.get('has_changes'):
                    # Prepare update data
                    updated_data = {
                        'question_text': fix_result['fixed_question'],
                        'choices': json.dumps(fix_result['fixed_choices'])
                    }

                    # Update correct answer if changed
                    if fix_result.get('answer_changed') and fix_result.get('suggested_correct_answer') is not None:
                        updated_data['correct_answer'] = fix_result['suggested_correct_answer']
                        logger.info(f"  -> Answer changed: {correct_answer} -> {fix_result['suggested_correct_answer']}")

                    # Update explanation if regenerated
                    if fix_result.get('explanation_regenerated') and fix_result.get('new_explanation'):
                        updated_data['explanation'] = fix_result['new_explanation']

                    # Apply the fix immediately (auto-approve)
                    if update_question(question_id, updated_data):
                        fixed += 1
                        changes = fix_result.get('changes_made', {})
                        change_summary = []
                        if changes.get('question'):
                            change_summary.extend(changes['question'])
                        if changes.get('choices'):
                            if isinstance(changes['choices'], dict):
                                for choice_idx, choice_changes in changes['choices'].items():
                                    change_summary.extend([f"Choice {choice_idx}: {c}" for c in choice_changes])
                            elif isinstance(changes['choices'], list):
                                for choice_idx, choice_changes in enumerate(changes['choices']):
                                    if choice_changes:
                                        change_summary.extend([f"Choice {choice_idx}: {c}" for c in choice_changes])
                        if changes.get('answer'):
                            change_summary.extend(changes['answer'])

                        logger.info(f"  ✅ Fixed & Applied: {', '.join(change_summary[:3])}{'...' if len(change_summary) > 3 else ''}")
                    else:
                        errors += 1
                        logger.error(f"  ❌ Failed to apply fix to database")
                else:
                    logger.debug(f"  No changes needed")

                # Rate limiting
                await asyncio.sleep(0.5)

                # Progress update every 10 questions
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{total_questions} analyzed, {fixed} fixed, {errors} errors")
                    if task_id:
                        update_task_progress(task_id, processed, fixed, errors, f"Question {idx}/{total_questions}")

            except Exception as e:
                errors += 1
                logger.error(f"  ❌ Error processing question {idx}: {e}")
                await asyncio.sleep(1)
                continue

        # Final summary
        logger.info("=" * 60)
        logger.info("AI FIX WITH PATTERN DETECTION COMPLETE")
        logger.info(f"  Source files scanned: {list(source_files)}")
        logger.info(f"  Total questions analyzed: {total_questions}")
        logger.info(f"  Processed: {processed}")
        logger.info(f"  Fixed & Applied: {fixed}")
        logger.info(f"  Errors: {errors}")
        logger.info(f"  No changes needed: {processed - fixed - errors}")
        logger.info("=" * 60)

        # Mark task complete
        if task_id:
            complete_task(task_id, processed, fixed, errors)

    except Exception as e:
        logger.error(f"Fatal error in AI fix with patterns: {e}", exc_info=True)
        if task_id:
            fail_task(task_id, str(e))


async def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        logger.error("Usage: python background_ai_fix_pattern.py <pool_id> <question_id1,question_id2,...>")
        sys.exit(1)

    pool_id = sys.argv[1]
    question_ids = sys.argv[2].split(',')
    question_ids = [qid.strip() for qid in question_ids if qid.strip()]

    # Generate task ID
    task_id = f"ai_fix_pattern_{uuid.uuid4().hex[:8]}"

    logger.info(f"Background AI fix with pattern detection started")
    logger.info(f"  Task ID: {task_id}")
    logger.info(f"  Pool ID: {pool_id}")
    logger.info(f"  Selected question IDs: {len(question_ids)}")

    await run_ai_fix_with_patterns(pool_id, question_ids, task_id)

    logger.info("Background AI fix with pattern detection finished")


if __name__ == "__main__":
    asyncio.run(main())
