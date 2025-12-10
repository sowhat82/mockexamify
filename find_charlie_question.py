#!/usr/bin/env python3
"""
Find the TR John question about Charlie (custom/customer)
"""
import asyncio
from db import db

async def find_question():
    """Find the Charlie question"""
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

    print(f"✅ Found pool: {target_pool['pool_name']} (ID: {target_pool['id']})")

    # Get questions from pool
    questions = await db.get_pool_questions(target_pool['id'])
    print(f"\n📊 Total questions in pool: {len(questions)}")

    # Find questions with corruption patterns
    corrupted_questions = []

    for q in questions:
        question_text = q['question_text']
        choices = q['choices']

        # Check for space-in-word corruption (common OCR error)
        # Pattern: word with space in middle like "Charli e", "pa rt", "ma rket"
        import re
        has_space_corruption = False

        # Look for patterns like "word [space] e" or "word [space] t"
        if re.search(r'\b\w+\s+[a-z]\b', question_text):
            has_space_corruption = True

        # Also check choices
        if isinstance(choices, list):
            for choice in choices:
                if isinstance(choice, str) and re.search(r'\b\w+\s+[a-z]\b', choice):
                    has_space_corruption = True

        # Check for specific patterns from user's report
        if 'Charlie' in question_text or 'Charli' in question_text:
            if 'drug trafficking' in question_text or 'custom' in question_text:
                print(f"\n🎯 Found Charlie/drug trafficking question:")
                print(f"   ID: {q['id']}")
                print(f"   Question: {question_text[:200]}...")
                print(f"   Full Question: {question_text}")
                print(f"   Choices: {choices}")
                print(f"   Correct Answer: {q['correct_answer']}")

                corrupted_questions.append(q['id'])

    if corrupted_questions:
        print(f"\n💾 Found {len(corrupted_questions)} question(s)")
        with open('charlie_question_ids.txt', 'w') as f:
            for qid in corrupted_questions:
                f.write(f"{qid}\n")

if __name__ == "__main__":
    asyncio.run(find_question())
