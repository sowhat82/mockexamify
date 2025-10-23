"""
One-off script to generate AI explanations for existing questions
Run this to backfill explanations for questions uploaded before the feature was added
"""

import asyncio
import json
import logging
import sys

from db import db
from openrouter_utils import generate_explanation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def backfill_explanations(pool_id: str = None):
    """Generate explanations for existing questions"""
    try:
        # Use admin_client to bypass RLS policies
        client = db.admin_client if db.admin_client else db.client

        # Get all questions (or from specific pool)
        if pool_id:
            logger.info(f"Fetching questions from pool: {pool_id}")
            result = client.table("pool_questions").select("*").eq("pool_id", pool_id).execute()
        else:
            logger.info("Fetching all questions from database...")
            result = client.table("pool_questions").select("*").execute()

        if not result.data:
            logger.warning("No questions found")
            return

        questions = result.data
        logger.info(f"Found {len(questions)} questions")

        # Filter questions that need explanations
        questions_needing_explanations = []
        for q in questions:
            explanation = q.get("explanation", "")
            # Check if explanation is missing or is just a placeholder
            if not explanation or len(explanation) < 50 or explanation.startswith("The correct answer is:"):
                questions_needing_explanations.append(q)

        logger.info(f"{len(questions_needing_explanations)} questions need explanations")

        if not questions_needing_explanations:
            logger.info("All questions already have explanations!")
            return

        # Generate explanations
        updated_count = 0
        failed_count = 0

        for idx, q in enumerate(questions_needing_explanations):
            try:
                question_text = q["question_text"]
                choices = json.loads(q["choices"]) if isinstance(q["choices"], str) else q["choices"]
                correct_index = q["correct_answer"]

                logger.info(f"[{idx + 1}/{len(questions_needing_explanations)}] Generating explanation for: {question_text[:60]}...")

                # Generate AI explanation
                explanation = await generate_explanation(
                    question=question_text,
                    choices=choices,
                    correct_index=correct_index,
                    scenario="",
                    explanation_seed=q.get("explanation", "")
                )

                # Update in database using admin_client
                update_result = (
                    client.table("pool_questions")
                    .update({"explanation": explanation})
                    .eq("id", q["id"])
                    .execute()
                )

                if update_result.data:
                    updated_count += 1
                    logger.info(f"✅ Updated question {q['id']}")
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to update question {q['id']}")

                # Small delay to respect rate limits
                if (idx + 1) % 2 == 0:  # After every 2 questions
                    await asyncio.sleep(1)

            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Error processing question {q.get('id')}: {e}")
                continue

        logger.info("=" * 60)
        logger.info("BACKFILL COMPLETE!")
        logger.info(f"✅ Successfully updated: {updated_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"📊 Total processed: {len(questions_needing_explanations)}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error in backfill process: {e}")
        raise


async def main():
    """Main entry point"""
    # You can specify a pool_id here if you want to target a specific pool
    # Example: await backfill_explanations(pool_id="your-pool-id-here")

    # Or leave it None to process all questions
    await backfill_explanations(pool_id=None)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
