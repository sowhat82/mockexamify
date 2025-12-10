#!/usr/bin/env python3
"""
Delete the corrupted Charlie question
"""
import asyncio
from db import db

async def delete_question():
    """Delete the corrupted Charlie question"""
    question_id = "bb03db55-139a-4077-a97d-0d9e750bbb56"

    print(f"🗑️ Deleting corrupted Charlie question: {question_id}")

    try:
        result = db.admin_client.table("pool_questions").delete().eq("id", question_id).execute()

        if result.data:
            print(f"✅ Successfully deleted question")
        else:
            print(f"⚠️ Question not found (may already be deleted)")

    except Exception as e:
        print(f"❌ Failed to delete question: {e}")

if __name__ == "__main__":
    asyncio.run(delete_question())
