#!/usr/bin/env python3
"""
Bulk delete corrupted questions (Q50-Q85) from CACS Paper 2
"""

import asyncio
import json
from typing import Dict, List, Any


async def bulk_delete_corrupted():
    """Delete corrupted questions from the pool"""
    print("🗑️  Bulk Delete Corrupted Questions")
    print("=" * 70)
    print()

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Import database
    from db import db

    # Get the CACS Paper 2 pool
    pools = await db.get_all_question_pools()
    cacs_pool = next((p for p in pools if "CACS" in p['pool_name']), None)

    if not cacs_pool:
        print("❌ CACS Paper 2 pool not found")
        return

    pool_id = cacs_pool['id']
    print(f"📚 Pool: {cacs_pool['pool_name']}")
    print(f"   ID: {pool_id}")
    print(f"   Current Total: {cacs_pool.get('total_questions', 0)} questions")
    print(f"   Current Unique: {cacs_pool.get('unique_questions', 0)} questions")
    print()

    # Get all questions
    questions = await db.get_pool_questions(pool_id)
    print(f"✅ Retrieved {len(questions)} questions")
    print()

    # Sort by uploaded_at or created_at to get original order
    questions.sort(key=lambda x: x.get('uploaded_at', x.get('created_at', '')))

    # Identify corrupted questions
    corrupted_questions = []

    for idx, q in enumerate(questions):
        # Parse choices
        choices = q['choices']
        if isinstance(choices, str):
            try:
                choices = json.loads(choices)
            except:
                choices = []

        # Check if choices are just single letters (corrupted)
        is_corrupted = all(
            isinstance(choice, str) and len(choice.strip()) <= 2
            for choice in choices
        )

        if is_corrupted:
            corrupted_questions.append({
                'index': idx,
                'q_num': idx + 1,
                'id': q['id'],
                'question_text': q.get('question_text', '')[:60],
                'choices': choices
            })

    print(f"🔍 Analysis:")
    print(f"   Total questions: {len(questions)}")
    print(f"   Corrupted questions: {len(corrupted_questions)}")
    print(f"   Questions to keep: {len(questions) - len(corrupted_questions)}")
    print()

    if not corrupted_questions:
        print("✅ No corrupted questions found!")
        return

    # Show what will be deleted
    print("📋 Questions to be deleted:")
    q_nums = [q['q_num'] for q in corrupted_questions]
    print(f"   Q{min(q_nums)} - Q{max(q_nums)} ({len(corrupted_questions)} questions)")
    print()

    # Confirm deletion
    print("⚠️  This will permanently delete these questions from the database.")
    print(f"   After deletion, you'll have {len(questions) - len(corrupted_questions)} questions remaining.")
    print()
    print("🔄 Proceeding with deletion...")
    print()

    # Delete corrupted questions
    deleted_count = 0
    failed_count = 0

    for i, q in enumerate(corrupted_questions, 1):
        try:
            # Use admin client to delete
            result = db.admin_client.table("pool_questions").delete().eq("id", q['id']).execute()

            if result.data:
                deleted_count += 1
                if i % 10 == 0:
                    print(f"   ✅ Deleted {i}/{len(corrupted_questions)} questions...")
            else:
                failed_count += 1
                print(f"   ⚠️  Failed to delete Q{q['q_num']}")
        except Exception as e:
            failed_count += 1
            print(f"   ❌ Error deleting Q{q['q_num']}: {e}")

    print()
    print("=" * 70)
    print("📊 Deletion Summary:")
    print(f"   ✅ Successfully deleted: {deleted_count} questions")
    if failed_count > 0:
        print(f"   ❌ Failed to delete: {failed_count} questions")
    print()

    # Update pool statistics
    remaining_count = len(questions) - deleted_count
    print("🔄 Updating pool statistics...")

    try:
        update_result = db.admin_client.table("question_pools").update({
            "total_questions": remaining_count,
            "unique_questions": remaining_count
        }).eq("id", pool_id).execute()

        if update_result.data:
            print("   ✅ Pool statistics updated")
            print(f"   New total: {remaining_count} questions")
        else:
            print("   ⚠️  Could not update pool statistics")
    except Exception as e:
        print(f"   ⚠️  Error updating pool statistics: {e}")

    print()
    print("=" * 70)
    print("✅ Bulk deletion complete!")
    print()
    print("📌 Next Steps:")
    print("   1. Refresh your admin dashboard")
    print("   2. View the pool - should now show 49 questions")
    print("   3. Re-upload the original document when ready to restore Q50-Q85")
    print()


if __name__ == "__main__":
    asyncio.run(bulk_delete_corrupted())
