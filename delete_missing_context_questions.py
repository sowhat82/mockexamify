#!/usr/bin/env python3
"""
Delete the 4 questions with missing context
"""

from db import DatabaseManager

# Questions with missing context
MISSING_CONTEXT_IDS = [
    "70a6b1a2-1bfb-47ad-aab9-4be1fa50e49c",  # Given the following details, what is the clean price...
    "27a67830-6db4-41c7-b999-13c5d2f6fab0",  # evaluate the following statements...
    "d914f2f9-276f-403d-b120-8d718a44e6c1",  # Given the following exchange rates...
    "02b3a6ff-272c-42cb-be84-9ffbd47e11f8",  # Given the following details, what is the clean price...
]

def main():
    db = DatabaseManager()

    print(f"Deleting {len(MISSING_CONTEXT_IDS)} questions with missing context...\n")

    for qid in MISSING_CONTEXT_IDS:
        # Get question details before deleting
        result = db.admin_client.table("pool_questions").select("question_text, pool_id").eq("id", qid).execute()

        if result.data:
            question = result.data[0]
            print(f"Deleting: {qid}")
            print(f"  Question: {question['question_text'][:80]}...")

            # Delete the question
            db.admin_client.table("pool_questions").delete().eq("id", qid).execute()
            print(f"  ✅ Deleted\n")
        else:
            print(f"⚠️  Question {qid} not found (may have been deleted already)\n")

    print(f"{'='*80}")
    print(f"Deletion complete!")
    print(f"Deleted {len(MISSING_CONTEXT_IDS)} questions with missing context from CACS Paper 2 pool")

if __name__ == "__main__":
    main()
