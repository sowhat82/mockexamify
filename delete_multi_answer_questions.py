"""
Delete multi-answer questions from the database.
Multi-answer questions (select all that apply) are not supported by the system.
"""

import re
import json
from typing import List, Tuple
from db import db

# Multi-answer question patterns (same as in document_parser.py)
MULTI_ANSWER_PATTERNS = [
    r"\(select all that apply\)",
    r"\(select all\)",
    r"\(choose all that apply\)",
    r"\(choose all\)",
    r"\(tick all that apply\)",
    r"\(check all that apply\)",
    r"select all (the\s+)?options? that (are )?correct",
    r"select all (the\s+)?correct (options?|answers?|statements?)",
    r"choose all (the\s+)?options? that (are )?correct",
    r"which (of the following )?are correct",
    r"which (of the following )?statements? are (true|correct)",
    r"select (all|multiple) correct answer",
    r"mark all that apply",
    r"identify all (the\s+)?(correct|true)",
]


def detect_multi_answer_question(question_text: str) -> bool:
    """Check if question text contains multi-answer patterns"""
    for pattern in MULTI_ANSWER_PATTERNS:
        if re.search(pattern, question_text, re.IGNORECASE):
            return True
    return False


def find_multi_answer_questions() -> List[Tuple[str, str, str]]:
    """
    Find all multi-answer questions in the database.

    Returns:
        List of tuples: (question_id, pool_id, question_text)
    """
    print("🔍 Searching for multi-answer questions in database...")

    # Get all questions from pool_questions table
    response = db.admin_client.table("pool_questions").select("id, pool_id, question_text").execute()

    if not response.data:
        print("No questions found in database")
        return []

    multi_answer_questions = []

    for question in response.data:
        question_id = question['id']
        pool_id = question['pool_id']
        question_text = question['question_text']

        if detect_multi_answer_question(question_text):
            multi_answer_questions.append((question_id, pool_id, question_text))

    return multi_answer_questions


def delete_multi_answer_questions(question_ids: List[str], dry_run: bool = True) -> int:
    """
    Delete multi-answer questions from the database.

    Args:
        question_ids: List of question IDs to delete
        dry_run: If True, only show what would be deleted (don't actually delete)

    Returns:
        Number of questions deleted
    """
    if not question_ids:
        print("No questions to delete")
        return 0

    if dry_run:
        print(f"\n🔍 DRY RUN: Would delete {len(question_ids)} questions")
        return 0

    print(f"\n🗑️  Deleting {len(question_ids)} multi-answer questions...")

    deleted_count = 0
    for question_id in question_ids:
        try:
            response = db.admin_client.table("pool_questions").delete().eq("id", question_id).execute()
            if response.data:
                deleted_count += 1
                print(f"  ✅ Deleted question {question_id}")
        except Exception as e:
            print(f"  ❌ Failed to delete question {question_id}: {e}")

    return deleted_count


def main(auto_confirm: bool = False):
    """Main execution

    Args:
        auto_confirm: If True, automatically confirm deletion without prompting
    """
    print("=" * 80)
    print("MULTI-ANSWER QUESTION CLEANUP")
    print("=" * 80)

    # Step 1: Find multi-answer questions
    multi_answer_questions = find_multi_answer_questions()

    if not multi_answer_questions:
        print("\n✅ No multi-answer questions found!")
        return

    print(f"\n📊 Found {len(multi_answer_questions)} multi-answer questions:")
    print()

    # Group by pool
    pool_counts = {}
    for question_id, pool_id, question_text in multi_answer_questions:
        if pool_id not in pool_counts:
            pool_counts[pool_id] = []
        pool_counts[pool_id].append((question_id, question_text))

    # Display findings
    for pool_id, questions in pool_counts.items():
        # Get pool name
        pool_response = db.admin_client.table("question_pools").select("pool_name").eq("id", pool_id).execute()
        pool_name = pool_response.data[0]['pool_name'] if pool_response.data else "Unknown Pool"

        print(f"\n📁 Pool: {pool_name} ({pool_id})")
        print(f"   {len(questions)} multi-answer questions")

        for question_id, question_text in questions[:3]:  # Show first 3
            preview = question_text[:100] + "..." if len(question_text) > 100 else question_text
            print(f"   - {question_id}: {preview}")

        if len(questions) > 3:
            print(f"   ... and {len(questions) - 3} more")

    # Step 2: Ask for confirmation
    print("\n" + "=" * 80)
    print("DRY RUN: Showing what would be deleted")
    print("=" * 80)

    question_ids = [q[0] for q in multi_answer_questions]
    delete_multi_answer_questions(question_ids, dry_run=True)

    print("\n" + "=" * 80)

    if auto_confirm:
        print(f"\n🤖 Auto-confirming deletion of {len(multi_answer_questions)} questions...")
        should_delete = True
    else:
        response = input(f"\nDo you want to DELETE these {len(multi_answer_questions)} questions? (yes/no): ")
        should_delete = response.lower() == 'yes'

    if should_delete:
        deleted = delete_multi_answer_questions(question_ids, dry_run=False)
        print(f"\n✅ Successfully deleted {deleted} questions")
    else:
        print("\n❌ Deletion cancelled")


if __name__ == "__main__":
    import sys
    auto_confirm = '--confirm' in sys.argv or '-y' in sys.argv
    main(auto_confirm=auto_confirm)
