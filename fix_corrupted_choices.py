#!/usr/bin/env python3
"""
Fix the corrupted double-encoded choices
"""
import asyncio
import re
import json
from db import db

async def fix_question():
    """Fix the corrupted choices"""

    question_id = "d328283d-6cff-42d6-bd39-6762cd5e41f1"

    # Get the question
    questions = db.admin_client.table("pool_questions").select("*").eq("id", question_id).execute()

    if not questions.data:
        print(f"❌ Question not found")
        return

    question = questions.data[0]
    choices_raw = question['choices']

    print(f"✅ Found question: {question['question_text'][:80]}...")

    # Parse the double-encoded JSON
    if isinstance(choices_raw, str):
        # First parse: get the list of characters
        char_list = json.loads(choices_raw)
        # Join the characters back into a string
        json_string = ''.join(char_list)
        # Second parse: get the actual choices list
        original_choices = json.loads(json_string)
    else:
        original_choices = choices_raw

    print(f"\n📋 Original choices:")
    for i, choice in enumerate(original_choices):
        print(f"   {i}. {choice}")

    # Fix "reimburse ment" → "reimbursement"
    fixed_choices = []
    for choice in original_choices:
        if isinstance(choice, str):
            fixed_choice = re.sub(r'\breimburse\s+ment\b', 'reimbursement', choice, flags=re.IGNORECASE)
            fixed_choices.append(fixed_choice)
        else:
            fixed_choices.append(choice)

    print(f"\n✨ Fixed choices:")
    for i, choice in enumerate(fixed_choices):
        print(f"   {i}. {choice}")

    # Update in database with correct JSON encoding
    try:
        update_data = {
            'choices': json.dumps(fixed_choices)
        }

        result = db.admin_client.table("pool_questions").update(update_data).eq("id", question_id).execute()

        if result.data:
            print(f"\n✅ Fixed and updated successfully!")
        else:
            print(f"\n❌ Update failed")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_question())
