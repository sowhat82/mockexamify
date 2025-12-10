#!/usr/bin/env python3
"""
Check the cmfas M1b pool for questions without proper context
"""
import asyncio
from db import db

async def check_pool():
    """Check cmfas M1b pool questions"""
    # Find the pool
    pools = await db.get_all_question_pools()

    target_pool = None
    for pool in pools:
        if 'cmfas' in pool['pool_name'].lower() and 'm1b' in pool['pool_name'].lower():
            target_pool = pool
            break

    if not target_pool:
        print("❌ Pool 'cmfas M1b' not found")
        print("\nAvailable pools:")
        for pool in pools:
            print(f"  - {pool['pool_name']} (ID: {pool['id']})")
        return

    print(f"✅ Found pool: {target_pool['pool_name']} (ID: {target_pool['id']})")

    # Get questions from pool
    questions = await db.get_pool_questions(target_pool['id'])
    print(f"\n📊 Total questions in pool: {len(questions)}")

    # Analyze questions
    incomplete_questions = []

    for q in questions:
        question_text = q['question_text']
        scenario = q.get('scenario', '')

        # Check if question references names/people without context
        if any(name in question_text for name in ['Sally', 'Kelly', 'Denny', 'Mary', 'Bernard', 'Alfred', 'Harry', 'Jeff', 'Director Hong']):
            # These questions need a scenario explaining what each person did
            if not scenario or len(scenario.strip()) < 50:
                incomplete_questions.append({
                    'id': q['id'],
                    'question': question_text[:100],
                    'scenario': scenario if scenario else "(no scenario)",
                    'has_scenario': bool(scenario and len(scenario.strip()) >= 50)
                })

    print(f"\n⚠️ Found {len(incomplete_questions)} questions that reference people without adequate context:\n")

    for idx, q in enumerate(incomplete_questions, 1):
        print(f"{idx}. ID: {q['id']}")
        print(f"   Question: {q['question']}...")
        print(f"   Scenario: {q['scenario'][:100] if q['scenario'] != '(no scenario)' else '(no scenario)'}...")
        print(f"   Has adequate scenario: {q['has_scenario']}")
        print()

    # Save IDs to file for deletion
    if incomplete_questions:
        with open('cmfas_m1b_incomplete_ids.txt', 'w') as f:
            for q in incomplete_questions:
                f.write(f"{q['id']}\n")

        print(f"💾 Saved {len(incomplete_questions)} question IDs to cmfas_m1b_incomplete_ids.txt")
        print("\nTo delete these questions, run: python delete_cmfas_m1b_incomplete.py")

if __name__ == "__main__":
    asyncio.run(check_pool())
