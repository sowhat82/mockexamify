#!/usr/bin/env python3
"""
Restore and fix the Charlie question that was incorrectly deleted
"""
import asyncio
import re
import json
from db import db

async def restore_question():
    """Restore the Charlie question with fixes applied"""

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

    pool_id = target_pool['id']
    print(f"✅ Found pool: {target_pool['pool_name']} (ID: {pool_id})")

    # Original question data (with OCR errors)
    original_question = "TR John received information that his custom Charli e is involved in drug trafficking activities. He suspect that Charlie may be using pa rt of proceed from his drug trafficking activities to speculate in the stock ma rket. TR John should"

    original_choices = [
        "Do nothing",
        "Informed Charlie of his suspicious",
        "Stop trading for Charlie so as not to get into trou ble",
        "Informed his compliance department of his suspicion s"
    ]

    # Apply OCR fixes
    fixed_question = original_question
    fixed_question = re.sub(r'\bcustom\b', 'customer', fixed_question, flags=re.IGNORECASE)
    fixed_question = re.sub(r'\bCharli\s+e\b', 'Charlie', fixed_question, flags=re.IGNORECASE)
    fixed_question = re.sub(r'\bHe suspect\b', 'He suspects', fixed_question, flags=re.IGNORECASE)
    fixed_question = re.sub(r'\bpa\s+rt\b', 'part', fixed_question, flags=re.IGNORECASE)
    fixed_question = re.sub(r'\bma\s+rket\b', 'market', fixed_question, flags=re.IGNORECASE)

    # Fix choices
    fixed_choices = []
    for choice in original_choices:
        fixed_choice = choice
        fixed_choice = re.sub(r'\btrou\s+ble\b', 'trouble', fixed_choice, flags=re.IGNORECASE)
        fixed_choice = re.sub(r'\bsuspicion\s+s\b', 'suspicions', fixed_choice, flags=re.IGNORECASE)
        fixed_choice = re.sub(r'\bInformed\b', 'Inform', fixed_choice)  # Grammar: "should Inform" not "should Informed"
        fixed_choice = re.sub(r'\bsuspicious\b', 'suspicions', fixed_choice)  # "of his suspicions" not "of his suspicious"
        fixed_choices.append(fixed_choice)

    print("\n📝 Original question:")
    print(f"   {original_question[:80]}...")
    print("\n✨ Fixed question:")
    print(f"   {fixed_question}")
    print("\n📋 Fixed choices:")
    for i, choice in enumerate(fixed_choices):
        print(f"   {i}. {choice}")

    # Create question data
    question_data = {
        'pool_id': pool_id,
        'question_text': fixed_question,
        'choices': json.dumps(fixed_choices),
        'correct_answer': 3,
        'explanation': 'Under anti-money laundering regulations, a Trading Representative who suspects that a client may be involved in money laundering activities (such as using proceeds from drug trafficking to trade in the stock market) must immediately inform their compliance department. This is a legal requirement to prevent money laundering and comply with regulatory obligations.',
        'source_file': 'CMFAS M1B'
    }

    # Insert into database
    try:
        result = db.admin_client.table("pool_questions").insert(question_data).execute()

        if result.data:
            new_id = result.data[0]['id']
            print(f"\n✅ Question restored successfully!")
            print(f"   New ID: {new_id}")
            print(f"   Pool: {target_pool['pool_name']}")
        else:
            print(f"\n❌ Failed to restore question - no data returned")

    except Exception as e:
        print(f"\n❌ Failed to restore question: {e}")

if __name__ == "__main__":
    asyncio.run(restore_question())
