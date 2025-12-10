#!/usr/bin/env python3
"""
Delete incomplete questions from CMFAS M1B pool
"""
import asyncio
from db import db

async def delete_questions():
    """Delete the incomplete questions"""
    # Read question IDs from file
    with open('cmfas_m1b_incomplete_ids.txt', 'r') as f:
        question_ids = [line.strip() for line in f if line.strip()]

    print(f"🗑️ Deleting {len(question_ids)} incomplete questions from CMFAS M1B pool...\n")

    deleted_count = 0
    failed_count = 0

    for idx, question_id in enumerate(question_ids, 1):
        try:
            # Delete using admin client to bypass RLS
            result = db.admin_client.table("pool_questions").delete().eq("id", question_id).execute()

            if result.data:
                print(f"{idx}. ✅ Deleted question {question_id}")
                deleted_count += 1
            else:
                print(f"{idx}. ⚠️ Question {question_id} not found (may already be deleted)")
                failed_count += 1

        except Exception as e:
            print(f"{idx}. ❌ Failed to delete question {question_id}: {e}")
            failed_count += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Deleted: {deleted_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   Total: {len(question_ids)}")

if __name__ == "__main__":
    asyncio.run(delete_questions())
