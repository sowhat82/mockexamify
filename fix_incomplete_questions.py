#!/usr/bin/env python3
"""
Detect and fix questions with missing context (case studies, product descriptions).
"""

import asyncio
import logging
import re
from typing import List, Dict, Tuple
from db import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Patterns that indicate missing context
INCOMPLETE_PATTERNS = [
    r'^The basis of which',
    r'^This product',
    r'^According to the case study',
    r'^Based on the scenario',
    r'^In the example',
    r'^The product described',
    r'^Under this arrangement',
    r'^For this investment',
    r'^In this case',
    r'^The structure outlined',
    r'^The instrument mentioned',
    r'^The investment product',  # References specific product without context
    r'^The investment.*profile',  # References specific investment without context
    r'basis.*mandatory\s*redemption.*determined',  # Specific to your example
    r'payout.*maturity.*determined by the\s*$',  # Questions ending with incomplete thought
    r'determined by the\s*Choices',  # Question text bleeding into choices
    r'^Referring to',
    r'^For the',
    r'^With reference to',
]


def detect_incomplete_questions(questions: List[Dict]) -> List[Tuple[Dict, str]]:
    """
    Detect questions that likely reference missing context.

    Returns list of (question, reason) tuples
    """
    incomplete = []

    for q in questions:
        question_text = q.get('question_text', '').strip()

        # Check against patterns
        for pattern in INCOMPLETE_PATTERNS:
            if re.search(pattern, question_text, re.IGNORECASE):
                incomplete.append((q, f"Matches pattern: {pattern}"))
                break

        # Additional heuristics
        # Check if question starts with article + noun without context
        if re.match(r'^The\s+\w+\s+(of|for|in)\s+which', question_text, re.IGNORECASE):
            if (q, f"Starts with 'The X of/for/in which' pattern") not in incomplete:
                incomplete.append((q, "Starts with 'The X of/for/in which' pattern"))
            continue

        # Check for references to "this/that product/fund/instrument" without context
        if re.search(r'\b(this|that)\s+(fund|product|instrument|security|option|structure)\b', question_text, re.IGNORECASE):
            if not any(item[0] == q for item in incomplete):
                incomplete.append((q, "References 'this/that fund/product/instrument' without context"))
            continue

    return incomplete


async def analyze_pool_questions(pool_id: str, pool_name: str, verbose: bool = False):
    """Analyze questions in a pool for incomplete context"""

    logger.info(f"Analyzing questions in pool: {pool_name} ({pool_id})")

    # Get all questions from the pool
    result = db.admin_client.table("pool_questions").select("*").eq("pool_id", pool_id).execute()

    if not result.data:
        logger.warning(f"No questions found in pool {pool_name}")
        return

    questions = result.data
    logger.info(f"Found {len(questions)} questions in pool")

    # Show sample questions if verbose
    if verbose:
        print("\n" + "="*80)
        print("SAMPLE QUESTIONS (first 5):")
        if questions:
            print(f"Available fields: {list(questions[0].keys())}")
            for idx, q in enumerate(questions[:5], 1):
                question_text = q.get('question') or q.get('question_text') or q.get('text') or str(q)
                print(f"\n[{idx}] Question: {question_text[:150]}")
        print("="*80 + "\n")

    # Detect incomplete questions
    incomplete = detect_incomplete_questions(questions)

    if not incomplete:
        logger.info("✅ No incomplete questions detected!")
        return

    logger.warning(f"⚠️ Found {len(incomplete)} potentially incomplete questions:")
    print("\n" + "="*80)

    for idx, (q, reason) in enumerate(incomplete, 1):
        print(f"\n[{idx}] ID: {q['id']}")
        print(f"Source: {q.get('source_file', 'Unknown')}")
        print(f"Reason: {reason}")
        question_text = q.get('question_text', '')
        print(f"Question: {question_text[:200]}...")
        print(f"Choices: {len(q.get('choices', []))} options")
        print("-" * 80)

    return incomplete


async def remove_incomplete_questions(pool_id: str, question_ids: List[str]):
    """Remove questions by ID"""

    logger.info(f"Removing {len(question_ids)} incomplete questions...")

    for q_id in question_ids:
        try:
            db.admin_client.table("pool_questions").delete().eq("id", q_id).execute()
            logger.info(f"✅ Removed question {q_id}")
        except Exception as e:
            logger.error(f"❌ Failed to remove question {q_id}: {e}")

    logger.info(f"✅ Removal complete!")


async def attempt_self_heal(pool_id: str, incomplete_questions: List[Tuple[Dict, str]]):
    """
    Attempt to add context to incomplete questions using AI.

    This would require:
    1. Access to the original document or OCR text
    2. Finding the case study/context that precedes the question
    3. Using AI to merge the context into the question
    """

    logger.info("Self-healing not yet implemented")
    logger.info("Would need to:")
    logger.info("  1. Locate original document or OCR text")
    logger.info("  2. Find preceding case study/context")
    logger.info("  3. Use AI to merge context into question")

    # For now, just return False to indicate self-heal not available
    return False


async def main():
    """Main entry point"""

    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_incomplete_questions.py <pool_id> [action] [--verbose]")
        print("")
        print("Actions:")
        print("  analyze  - Detect and display incomplete questions (default)")
        print("  remove   - Remove all detected incomplete questions")
        print("  heal     - Attempt to self-heal questions (not yet implemented)")
        print("")
        print("Options:")
        print("  --verbose  - Show sample questions during analysis")
        sys.exit(1)

    pool_id = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "analyze"
    verbose = '--verbose' in sys.argv

    # Get pool name
    pool_result = db.admin_client.table("question_pools").select("*").eq("id", pool_id).execute()

    if not pool_result.data:
        logger.error(f"Pool {pool_id} not found")
        sys.exit(1)

    pool_name = pool_result.data[0]['pool_name']

    if action == "analyze":
        await analyze_pool_questions(pool_id, pool_name, verbose)

    elif action == "remove":
        incomplete = await analyze_pool_questions(pool_id, pool_name, verbose)

        if not incomplete:
            return

        # Confirm removal
        print(f"\n⚠️  About to remove {len(incomplete)} questions. Continue? (yes/no): ", end="")
        confirm = input().strip().lower()

        if confirm == "yes":
            question_ids = [q['id'] for q, _ in incomplete]
            await remove_incomplete_questions(pool_id, question_ids)
        else:
            logger.info("Removal cancelled")

    elif action == "heal":
        incomplete = await analyze_pool_questions(pool_id, pool_name, verbose)

        if not incomplete:
            return

        success = await attempt_self_heal(pool_id, incomplete)

        if not success:
            logger.warning("Self-healing not available. Use 'remove' action instead.")


if __name__ == "__main__":
    asyncio.run(main())
