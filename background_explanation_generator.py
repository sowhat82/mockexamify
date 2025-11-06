"""
Background AI Explanation Generator
Runs independently to generate explanations for questions with placeholders
"""
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_explanation_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def generate_explanations_for_pool(pool_id: str, batch_id: str = None):
    """Generate AI explanations for questions that have placeholder explanations"""
    from db import db
    from openrouter_utils import generate_explanation

    logger.info(f"Starting explanation generation for pool {pool_id}")

    try:
        # Get all questions from the pool
        questions = await db.get_pool_questions(pool_id)

        # Filter questions that need AI explanations
        # Placeholder format: "The correct answer is: {choice}"
        questions_needing_ai = []
        for q in questions:
            explanation = q.get("explanation", "")
            # Check if it's a placeholder (starts with "The correct answer is:")
            if explanation.startswith("The correct answer is:"):
                questions_needing_ai.append(q)

        total_needing_ai = len(questions_needing_ai)

        if total_needing_ai == 0:
            logger.info("No questions need AI explanation generation")
            return

        logger.info(f"Found {total_needing_ai} questions needing AI explanations")

        # Update batch status to show generation is in progress
        if batch_id:
            await db._update_batch_stats(
                batch_id,
                len(questions),
                0,
                len(questions)
            )

        # Generate explanations with rate limiting
        successful = 0
        failed = 0

        for idx, question in enumerate(questions_needing_ai, 1):
            try:
                logger.info(f"Generating explanation {idx}/{total_needing_ai}")

                # Parse choices (might be JSON string)
                choices = question.get("choices")
                if isinstance(choices, str):
                    choices = json.loads(choices)

                # Generate AI explanation
                explanation = await generate_explanation(
                    question=question.get("question_text"),
                    choices=choices,
                    correct_index=question.get("correct_answer"),
                    scenario="",
                    explanation_seed=""
                )

                # Update question with new explanation
                update_result = db.admin_client.table("pool_questions").update(
                    {"explanation": explanation}
                ).eq("id", question.get("id")).execute()

                if update_result.data:
                    successful += 1
                    logger.info(f"✅ Updated question {idx}/{total_needing_ai}")
                else:
                    failed += 1
                    logger.error(f"❌ Failed to update question {idx}/{total_needing_ai}")

                # Rate limiting: Wait 1 second between requests to avoid throttling
                # Paid tier should handle this easily, but we want to be respectful
                await asyncio.sleep(1.0)

                # Every 10 questions, log progress
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{total_needing_ai} completed ({successful} successful, {failed} failed)")

            except Exception as e:
                failed += 1
                logger.error(f"Error generating explanation for question {idx}: {e}")
                # On error, wait a bit longer before retrying next question
                await asyncio.sleep(2.0)
                continue

        logger.info(
            f"Explanation generation complete! "
            f"Total: {total_needing_ai}, Successful: {successful}, Failed: {failed}"
        )

    except Exception as e:
        logger.error(f"Fatal error in explanation generation: {e}", exc_info=True)


async def main():
    """Main entry point for background worker"""
    if len(sys.argv) < 2:
        logger.error("Usage: python background_explanation_generator.py <pool_id> [batch_id]")
        sys.exit(1)

    pool_id = sys.argv[1]
    batch_id = sys.argv[2] if len(sys.argv) > 2 else None

    logger.info(f"Background explanation generator started for pool: {pool_id}")
    await generate_explanations_for_pool(pool_id, batch_id)
    logger.info("Background explanation generator finished")


if __name__ == "__main__":
    asyncio.run(main())
