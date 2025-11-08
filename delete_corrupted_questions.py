"""
Script to delete corrupted questions from the question pool
"""
import asyncio
from db import db

async def delete_corrupted_questions():
    """Delete all corrupted questions identified in corrupted_question_ids.txt"""

    # Read corrupted question IDs
    with open('corrupted_question_ids.txt', 'r') as f:
        corrupted_ids = [line.strip() for line in f if line.strip()]

    print(f"Found {len(corrupted_ids)} corrupted question IDs to delete")

    # Confirm deletion
    response = input(f"\nAre you sure you want to delete {len(corrupted_ids)} corrupted questions? (yes/no): ")
    if response.lower() != 'yes':
        print("Deletion cancelled")
        return

    # Delete questions using admin client
    deleted_count = 0
    failed_count = 0

    for i, question_id in enumerate(corrupted_ids, 1):
        try:
            # Use admin client to bypass RLS
            client = db.admin_client if db.admin_client else db.client

            result = client.table("pool_questions").delete().eq("id", question_id).execute()

            if result.data:
                deleted_count += 1
                print(f"[{i}/{len(corrupted_ids)}] Deleted question {question_id}")
            else:
                failed_count += 1
                print(f"[{i}/{len(corrupted_ids)}] Failed to delete {question_id} - not found")

        except Exception as e:
            failed_count += 1
            print(f"[{i}/{len(corrupted_ids)}] Error deleting {question_id}: {e}")

    print(f"\n{'='*60}")
    print(f"Deletion complete:")
    print(f"  Successfully deleted: {deleted_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {len(corrupted_ids)}")
    print(f"{'='*60}")

    # Update question pool stats
    pool_id = '8a032a2a-9d71-476b-81d3-7980fac9ec8e'
    remaining_questions = await db.get_pool_questions(pool_id)
    print(f"\nRemaining questions in pool: {len(remaining_questions)}")

if __name__ == "__main__":
    asyncio.run(delete_corrupted_questions())
