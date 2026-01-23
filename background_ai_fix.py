"""
Background AI Fix Script
Runs independently to fix questions with OCR errors, typos, and grammar issues.
Spawned after upload to process all questions without browser timeout constraints.
"""
import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_ai_fix.log'),
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


async def run_ai_fix_for_questions(pool_id: str, source_files: List[str] = None):
    """
    Run AI fix on questions from a pool, optionally filtered by source files.

    Args:
        pool_id: The pool ID to process
        source_files: Optional list of source filenames to filter by (for new uploads)
    """
    from db import db
    from openrouter_utils import fix_question_errors

    logger.info(f"Starting AI fix for pool {pool_id}")
    if source_files:
        logger.info(f"Filtering by source files: {source_files}")

    try:
        # Get all questions from the pool
        all_questions = await db.get_pool_questions(pool_id)

        # Filter by source files if specified
        if source_files:
            questions = [q for q in all_questions if q.get('source_file') in source_files]
            logger.info(f"Found {len(questions)} questions from specified source files (out of {len(all_questions)} total)")
        else:
            questions = all_questions
            logger.info(f"Processing all {len(questions)} questions in pool")

        if not questions:
            logger.info("No questions to process")
            return

        total_questions = len(questions)
        processed = 0
        fixed = 0
        errors = 0

        for idx, question in enumerate(questions, 1):
            try:
                question_id = question['id']
                question_text = question['question_text']
                choices = json.loads(question['choices']) if isinstance(question['choices'], str) else question['choices']
                correct_answer = question.get('correct_answer')

                logger.info(f"[{idx}/{total_questions}] Processing question {question_id[:8]}...")

                # Run AI fix
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

                    # Apply the fix
                    if update_question(question_id, updated_data):
                        fixed += 1
                        changes = fix_result.get('changes_made', {})
                        change_summary = []
                        if changes.get('question'):
                            change_summary.extend(changes['question'])
                        if changes.get('choices'):
                            for choice_idx, choice_changes in changes['choices'].items():
                                change_summary.extend([f"Choice {choice_idx}: {c}" for c in choice_changes])
                        if changes.get('answer'):
                            change_summary.extend(changes['answer'])

                        logger.info(f"  ✅ Fixed: {', '.join(change_summary[:3])}{'...' if len(change_summary) > 3 else ''}")
                    else:
                        errors += 1
                        logger.error(f"  ❌ Failed to apply fix to database")
                else:
                    logger.debug(f"  No changes needed")

                # Rate limiting - wait between requests
                await asyncio.sleep(0.5)

                # Progress update every 10 questions
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{total_questions} processed, {fixed} fixed, {errors} errors")

            except Exception as e:
                errors += 1
                logger.error(f"  ❌ Error processing question {idx}: {e}")
                await asyncio.sleep(1)  # Wait longer on error
                continue

        # Final summary
        logger.info("=" * 60)
        logger.info(f"AI FIX COMPLETE")
        logger.info(f"  Total questions: {total_questions}")
        logger.info(f"  Processed: {processed}")
        logger.info(f"  Fixed: {fixed}")
        logger.info(f"  Errors: {errors}")
        logger.info(f"  No changes needed: {processed - fixed - errors}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in AI fix: {e}", exc_info=True)


async def main():
    """Main entry point for background AI fix"""
    if len(sys.argv) < 2:
        logger.error("Usage: python background_ai_fix.py <pool_id> [source_file1,source_file2,...]")
        sys.exit(1)

    pool_id = sys.argv[1]
    source_files = None

    if len(sys.argv) > 2:
        # Parse comma-separated source files
        source_files = sys.argv[2].split(',')
        source_files = [f.strip() for f in source_files if f.strip()]

    logger.info(f"Background AI fix started")
    logger.info(f"  Pool ID: {pool_id}")
    logger.info(f"  Source files: {source_files or 'All'}")

    await run_ai_fix_for_questions(pool_id, source_files)

    logger.info("Background AI fix finished")


if __name__ == "__main__":
    asyncio.run(main())
