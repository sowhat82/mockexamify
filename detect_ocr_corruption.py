#!/usr/bin/env python3
"""
Detect and remove questions with OCR text corruption (spelling errors, malformed text).
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


# Common OCR corruption patterns
OCR_CORRUPTION_PATTERNS = [
    # Letter 'o' or 'O' instead of number '0' in prices
    (r'\$[oO]\.', 'Dollar sign followed by letter o/O instead of zero (e.g., $o.00)'),

    # Common word corruptions (m/n confusion)
    (r'\bordinai-y\b', 'ordinai-y instead of ordinary'),
    (r'\bordinan/\b', 'ordinan/ instead of ordinary'),
    (r'\bstmctures\b', 'stmctures instead of structures'),
    (r'\binvestrnent\b', 'investrnent instead of investment'),
    (r'\bgovernrnent\b', 'governrnent instead of government'),
    (r'\bmanagernent\b', 'managernent instead of management'),
    (r'\bperforrnance\b', 'performrnance instead of performance'),
    (r'\brnake\b', 'rnake instead of make'),
    (r'\brnay\b', 'rnay instead of may'),
    (r'\brnust\b', 'rnust instead of must'),
    (r'\brnore\b', 'rnore instead of more'),

    # Number/letter confusion in percentages
    (r'\b[Il]00\%', 'Letter I or l instead of 1 in 100%'),

    # Multiple consecutive spaces (likely OCR artifact)
    (r'\s{4,}', 'Four or more consecutive spaces'),

    # Obvious text bleeding/corruption
    (r'determined by the\s*Choices', 'Question text bleeding into choices'),
    (r'\.{3,}Choices', 'Question ending with ... directly into Choices'),
]


def detect_ocr_corruption(question_text: str) -> List[Tuple[str, str]]:
    """
    Detect OCR corruption in question text.

    Returns list of (pattern, description) tuples for matched corruptions
    """
    corruptions = []

    for pattern, description in OCR_CORRUPTION_PATTERNS:
        if re.search(pattern, question_text, re.IGNORECASE):
            corruptions.append((pattern, description))

    return corruptions


async def analyze_pool_questions(pool_id: str, pool_name: str, verbose: bool = False):
    """Analyze questions in a pool for OCR corruption"""

    logger.info(f"Analyzing questions in pool: {pool_name} ({pool_id})")

    # Get all questions from the pool
    result = db.admin_client.table("pool_questions").select("*").eq("pool_id", pool_id).execute()

    if not result.data:
        logger.warning(f"No questions found in pool {pool_name}")
        return

    questions = result.data
    logger.info(f"Found {len(questions)} questions in pool")

    # Detect corrupted questions
    corrupted = []

    for q in questions:
        question_text = q.get('question_text', '').strip()
        corruptions = detect_ocr_corruption(question_text)

        if corruptions:
            corrupted.append((q, corruptions))

    if not corrupted:
        logger.info("✅ No OCR-corrupted questions detected!")
        return

    logger.warning(f"⚠️  Found {len(corrupted)} questions with OCR corruption:")
    print("\n" + "="*80)

    for idx, (q, corruptions) in enumerate(corrupted, 1):
        print(f"\n[{idx}] ID: {q['id']}")
        print(f"Source: {q.get('source_file', 'Unknown')}")
        print(f"Corruptions found:")
        for pattern, description in corruptions:
            print(f"  - {description}")
        question_text = q.get('question_text', '')
        print(f"Question: {question_text[:200]}...")
        print(f"Choices: {q.get('choices', [])}")
        print("-" * 80)

    return corrupted


async def remove_corrupted_questions(pool_id: str, question_ids: List[str]):
    """Remove questions by ID"""

    logger.info(f"Removing {len(question_ids)} corrupted questions...")

    for q_id in question_ids:
        try:
            db.admin_client.table("pool_questions").delete().eq("id", q_id).execute()
            logger.info(f"✅ Removed question {q_id}")
        except Exception as e:
            logger.error(f"❌ Failed to remove question {q_id}: {e}")

    logger.info(f"✅ Removal complete!")


async def main():
    """Main entry point"""

    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python detect_ocr_corruption.py <pool_id> [action] [--verbose]")
        print("")
        print("Actions:")
        print("  analyze  - Detect and display OCR-corrupted questions (default)")
        print("  remove   - Remove all detected corrupted questions")
        print("")
        print("Options:")
        print("  --verbose  - Show additional details")
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
        corrupted = await analyze_pool_questions(pool_id, pool_name, verbose)

        if not corrupted:
            return

        # Confirm removal
        print(f"\n⚠️  About to remove {len(corrupted)} questions. Continue? (yes/no): ", end="")
        confirm = input().strip().lower()

        if confirm == "yes":
            question_ids = [q['id'] for q, _ in corrupted]
            await remove_corrupted_questions(pool_id, question_ids)
        else:
            logger.info("Removal cancelled")


if __name__ == "__main__":
    asyncio.run(main())
