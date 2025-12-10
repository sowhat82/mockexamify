#!/usr/bin/env python3
"""
Auto-fix corrupted questions by removing spaces in middle of words
"""
import asyncio
import re
import json
from db import db

async def fix_questions():
    """Fix the corrupted questions"""
    # Get CMFAS M1B pool
    pools = await db.get_all_question_pools()

    target_pool = None
    for pool in pools:
        if 'cmfas' in pool['pool_name'].lower() and 'm1b' in pool['pool_name'].lower():
            target_pool = pool
            break

    if not target_pool:
        print("❌ Pool 'CMFAS M1B' not found")
        return

    # Read corrupted question IDs
    with open('real_corrupted_ids.txt', 'r') as f:
        question_ids = [line.strip() for line in f if line.strip()]

    print(f"🔧 Auto-fixing {len(question_ids)} corrupted questions...\n")

    # Get all questions from pool
    questions = await db.get_pool_questions(target_pool['id'])

    # Create a map of ID to question
    question_map = {q['id']: q for q in questions}

    # Fix patterns
    fix_patterns = [
        (r'\bCharli\s+e\b', 'Charlie'),
        (r'\bpa\s+rt\b', 'part'),
        (r'\bma\s+rket\b', 'market'),
        (r'\btrou\s+ble\b', 'trouble'),
        (r'\bsuspicion\s+s\b', 'suspicions'),
        (r'\bfi\s+nancial\b', 'financial'),
        (r'\bgo\s+od\b', 'good'),
        (r'\bvar\s+ious\b', 'various'),
        (r'\borde\s+r\b', 'order'),
        (r'\bdoe\s+s\b', 'does'),
        (r'\bbasi\s+s\b', 'basis'),
        (r'\brea\s+lized\b', 'realized'),
        (r'\bprofi\s+t\b', 'profit'),
        (r'\bi\s+nvestment\b', 'investment'),
        (r'\bfo\s+r\b', 'for'),
        (r'\btha\s+t\b', 'that'),
        (r'\brequ\s+ires\b', 'requires'),
        (r'\boffenc\s+e\b', 'offence'),
        (r'\bar\s+e\s+covered\b', 'are covered'),
        (r'\bsuspect\s+ed\b', 'suspected'),
        (r'\bHe suspect\b', 'He suspects'),
        (r'\bcustom\b', 'customer'),
    ]

    fixed_count = 0

    for idx, question_id in enumerate(question_ids, 1):
        if question_id not in question_map:
            print(f"{idx}. ⚠️ Question {question_id} not found")
            continue

        question = question_map[question_id]
        original_text = question['question_text']
        original_choices = question['choices']

        # Fix question text
        fixed_text = original_text
        for pattern, replacement in fix_patterns:
            fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)

        # Fix choices
        fixed_choices = []
        if isinstance(original_choices, list):
            for choice in original_choices:
                if isinstance(choice, str):
                    fixed_choice = choice
                    for pattern, replacement in fix_patterns:
                        fixed_choice = re.sub(pattern, replacement, fixed_choice, flags=re.IGNORECASE)
                    fixed_choices.append(fixed_choice)
                else:
                    fixed_choices.append(choice)
        else:
            fixed_choices = original_choices

        # Check if anything changed
        if fixed_text != original_text or fixed_choices != original_choices:
            print(f"{idx}. 🔧 Question {question_id}")
            print(f"   Before: {original_text[:80]}...")
            print(f"   After:  {fixed_text[:80]}...")

            # Update in database
            try:
                update_data = {
                    'question_text': fixed_text,
                    'choices': json.dumps(fixed_choices) if isinstance(fixed_choices, list) else fixed_choices
                }

                result = db.admin_client.table("pool_questions").update(update_data).eq("id", question_id).execute()

                if result.data:
                    print(f"   ✅ Updated")
                    fixed_count += 1
                else:
                    print(f"   ❌ Failed")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        print()

    print(f"📊 Fixed {fixed_count}/{len(question_ids)} questions")

if __name__ == "__main__":
    asyncio.run(fix_questions())
