#!/usr/bin/env python3
"""
Smart OCR fix - only fix REAL corruption, not valid English like "of a"
"""
import asyncio
import re
import json
from db import db

async def smart_fix():
    """Fix only real OCR errors in questions and choices"""
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
    print(f"\n📊 Scanning {len(questions)} questions for REAL OCR errors...\n")

    # REAL OCR corruption patterns (NOT false positives like "of a")
    fix_patterns = [
        # Space corruptions within recognizable words
        (r'\ballowe\s+d\b', 'allowed'),
        (r'\bneeds\s+t\s+o\b', 'needs to'),
        (r'\bunless\s+t\s+he\b', 'unless the'),
        (r'\bbelon\s+g\b', 'belong'),
        (r'\bMember\s+w\s+ill\b', 'Member will'),
        (r'\bthe\s+o\s+rder\b', 'the order'),
        (r'\bsecurity\s+i\s+s\b', 'security is'),
        (r'\bcorp\s+orate\b', 'corporate'),
        (r'\bCompan\s+y\b', 'Company'),
        (r'\bnegotiating\s+a\s+takeover\b', 'negotiating a takeover'),
        (r'\bcapacity\s+a\s+s\b', 'capacity as'),
        (r'\bjoined\s+P\s+&\s+Q\b', 'joined P & Q'),
        (r'\bsecure\s+a\s+loan\b', 'secure a loan'),
        (r'\bCP\s+F\b', 'CPF'),  # CPF split as "CP F"

        # Already fixed but double-check
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
        (r'\bHe\s+suspect\b', 'He suspects'),
        (r'\bcustom\b(?!\s+duty)', 'customer'),  # "custom" → "customer" (but not "custom duty")
    ]

    fixed_count = 0
    questions_fixed = []

    for q in questions:
        question_text = q['question_text']
        choices = q['choices']
        original_text = question_text
        original_choices = choices.copy() if isinstance(choices, list) else choices

        # Fix question text
        fixed_text = question_text
        for pattern, replacement in fix_patterns:
            fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)

        # Fix choices
        fixed_choices = []
        if isinstance(choices, list):
            for choice in choices:
                if isinstance(choice, str):
                    fixed_choice = choice
                    for pattern, replacement in fix_patterns:
                        fixed_choice = re.sub(pattern, replacement, fixed_choice, flags=re.IGNORECASE)
                    fixed_choices.append(fixed_choice)
                else:
                    fixed_choices.append(choice)
        else:
            fixed_choices = choices

        # Check if anything changed
        if fixed_text != original_text or fixed_choices != original_choices:
            print(f"🔧 Question {q['id']}")

            if fixed_text != original_text:
                print(f"   Question before: {original_text[:80]}...")
                print(f"   Question after:  {fixed_text[:80]}...")

            if fixed_choices != original_choices:
                print(f"   Choices fixed:")
                for i, (old, new) in enumerate(zip(original_choices, fixed_choices)):
                    if old != new:
                        print(f"      {i}. '{old}' → '{new}'")

            # Update in database
            try:
                update_data = {
                    'question_text': fixed_text,
                    'choices': json.dumps(fixed_choices) if isinstance(fixed_choices, list) else fixed_choices
                }

                result = db.admin_client.table("pool_questions").update(update_data).eq("id", q['id']).execute()

                if result.data:
                    print(f"   ✅ Updated\n")
                    fixed_count += 1
                    questions_fixed.append(q['id'])
                else:
                    print(f"   ❌ Failed\n")

            except Exception as e:
                print(f"   ❌ Error: {e}\n")

    print(f"="*80)
    print(f"\n📊 Summary:")
    print(f"   Fixed: {fixed_count} questions")
    print(f"   Total scanned: {len(questions)}")

    if questions_fixed:
        with open('fixed_questions_log.txt', 'w') as f:
            for qid in questions_fixed:
                f.write(f"{qid}\n")
        print(f"\n💾 Saved fixed question IDs to fixed_questions_log.txt")

if __name__ == "__main__":
    asyncio.run(smart_fix())
