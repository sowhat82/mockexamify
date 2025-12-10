#!/usr/bin/env python3
"""
Scan for REAL OCR corruption (not false positives like "a TR")
"""
import asyncio
import re
from db import db

async def scan_pool():
    """Scan pool for truly corrupted questions"""
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
    print("\n🔍 Scanning for REAL OCR corruption (ignoring false positives)...\n")

    corrupted_questions = []

    # Real corruption patterns (space in middle of recognizable words)
    corruption_words = [
        r'\bCharli\s+e\b', r'\bpa\s+rt\b', r'\bma\s+rket\b', r'\btrou\s+ble\b',
        r'\bsuspicion\s+s\b', r'\bordinar\s+y\b', r'\bfi\s+nancial\b',
        r'\bgo\s+od\b', r'\bvar\s+ious\b', r'\bn\s+ot\b', r'\borde\s+r\b',
        r'\bdoe\s+s\b', r'\ballo\s+we\s+d\b', r'\bbasi\s+s\b', r'\brea\s+lized\b',
        r'\bprofi\s+t\b', r'\bi\s+nvestment\b', r'\bopen\s+a\s+CPF\b',
        r'\bfo\s+r\b', r'\btha\s+t\b', r'\brequ\s+ires\s+a\b', r'\boffenc\s+e\b',
        r'\bMembe\s+r\s+w\b', r'\bcor\s+p\s+orate\b', r'\bar\s+e\s+covered\b',
        r'\bdifferen\s+c\s+e\b', r'\binfor\s+m\s+a\b', r'\brefe\s+r\s+ence\b',
        r'\bdea\s+ling\b', r'\bdetecte\s+d\b', r'\bsuspect\s+ed\b'
    ]

    for idx, q in enumerate(questions, 1):
        question_text = q['question_text']
        choices = q['choices']
        corruptions_found = []

        # Check question text
        for pattern in corruption_words:
            if re.search(pattern, question_text, re.IGNORECASE):
                match = re.search(pattern, question_text, re.IGNORECASE)
                corruptions_found.append(f"In question: '{match.group()}'")

        # Check choices
        if isinstance(choices, list):
            for choice_idx, choice in enumerate(choices):
                if isinstance(choice, str):
                    for pattern in corruption_words:
                        if re.search(pattern, choice, re.IGNORECASE):
                            match = re.search(pattern, choice, re.IGNORECASE)
                            corruptions_found.append(f"In choice {choice_idx}: '{match.group()}'")

        # If corruptions found, add to list
        if corruptions_found:
            corrupted_questions.append({
                'id': q['id'],
                'question': question_text[:100],
                'corruptions': corruptions_found
            })

            print(f"{len(corrupted_questions)}. ID: {q['id']}")
            print(f"   Question: {question_text[:80]}...")
            for corruption in corruptions_found:
                print(f"   ⚠️ {corruption}")
            print()

    # Summary
    print("="*80)
    print(f"\n📊 Scan Results:")
    print(f"   Total questions scanned: {len(questions)}")
    print(f"   Questions with REAL corruption: {len(corrupted_questions)}")
    print(f"   Clean questions: {len(questions) - len(corrupted_questions)}")

    if corrupted_questions:
        # Save IDs to file
        with open('real_corrupted_ids.txt', 'w') as f:
            for q in corrupted_questions:
                f.write(f"{q['id']}\n")

        print(f"\n💾 Saved {len(corrupted_questions)} corrupted question IDs to real_corrupted_ids.txt")
        print("\n⚠️ These questions have actual OCR errors and should be deleted or fixed")

if __name__ == "__main__":
    asyncio.run(scan_pool())
