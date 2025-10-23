#!/usr/bin/env python3
"""
Investigate question choices corruption in CACS Paper 2
Specifically checking Q50 onwards for corrupted answer choices
"""

import asyncio
import json
from typing import Dict, List, Any


async def investigate_questions():
    """Check question data for corruption"""
    print("🔍 Investigating Question Choices in CACS Paper 2")
    print("=" * 70)
    print()

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Import database
    from db import db

    # Get the CACS Paper 2 pool
    pools = await db.get_all_question_pools()
    cacs_pool = next((p for p in pools if "CACS" in p['pool_name']), None)

    if not cacs_pool:
        print("❌ CACS Paper 2 pool not found")
        return

    pool_id = cacs_pool['id']
    print(f"📚 Pool: {cacs_pool['pool_name']}")
    print(f"   ID: {pool_id}")
    print()

    # Get all questions
    questions = await db.get_pool_questions(pool_id)
    print(f"✅ Retrieved {len(questions)} questions")
    print()

    # Sort by uploaded_at or created_at to get original order
    questions.sort(key=lambda x: x.get('uploaded_at', x.get('created_at', '')))

    # Check questions around Q50 onwards
    print("🔍 Analyzing Questions 45-55 and last 10 questions:")
    print("-" * 70)

    # Check questions 45-55 (indices 44-54)
    target_indices = list(range(44, min(55, len(questions))))
    # Also check last 10 questions
    target_indices.extend(list(range(max(0, len(questions) - 10), len(questions))))
    # Remove duplicates and sort
    target_indices = sorted(set(target_indices))

    issues_found = []

    for idx in target_indices:
        if idx >= len(questions):
            continue

        q = questions[idx]
        q_num = idx + 1

        # Parse choices
        choices = q['choices']
        if isinstance(choices, str):
            try:
                choices = json.loads(choices)
            except:
                choices = []

        # Check if choices are just single letters
        is_corrupted = all(
            isinstance(choice, str) and len(choice.strip()) <= 2
            for choice in choices
        )

        question_text = q.get('question_text', '')[:80]

        print(f"\nQ{q_num} (Index {idx}):")
        print(f"  Question: {question_text}...")
        print(f"  Choices: {choices}")
        print(f"  Correct Answer: {q.get('correct_answer')}")
        print(f"  ⚠️  CORRUPTED: {is_corrupted}")

        if is_corrupted:
            issues_found.append({
                'index': idx,
                'q_num': q_num,
                'id': q['id'],
                'question_text': question_text,
                'choices': choices
            })

    print()
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   Total questions checked: {len(target_indices)}")
    print(f"   Corrupted questions found: {len(issues_found)}")

    if issues_found:
        print()
        print("⚠️  CORRUPTED QUESTIONS:")
        for issue in issues_found:
            print(f"   Q{issue['q_num']}: {issue['question_text']}...")
            print(f"      Choices: {issue['choices']}")

        print()
        print("🔍 Checking ALL questions for corruption pattern...")
        all_corrupted = []
        for idx, q in enumerate(questions):
            choices = q['choices']
            if isinstance(choices, str):
                try:
                    choices = json.loads(choices)
                except:
                    choices = []

            is_corrupted = all(
                isinstance(choice, str) and len(choice.strip()) <= 2
                for choice in choices
            )

            if is_corrupted:
                all_corrupted.append(idx + 1)

        print(f"   Total corrupted questions: {len(all_corrupted)}")
        print(f"   Question numbers: {all_corrupted}")

        if len(all_corrupted) > 0:
            print()
            print("📈 Corruption pattern:")
            if all_corrupted[0] > 40:
                print(f"   ⚠️  Corruption starts at Q{all_corrupted[0]}")
                print(f"   This suggests an issue during upload/parsing")
                print(f"   Questions 1-{all_corrupted[0]-1} are likely OK")
                print(f"   Questions {all_corrupted[0]}-{all_corrupted[-1]} need fixing")
    else:
        print()
        print("✅ No corruption detected in sampled questions")

    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(investigate_questions())
