#!/usr/bin/env python3
"""Find and analyze the complaint question in CACS Paper 1 pool."""

import asyncio
from db import DatabaseManager

async def main():
    db = DatabaseManager()

    # Search for questions with "complaint" in CACS Paper 1
    pools = await db.get_all_question_pools()
    cacs1_pool = None
    print(f"Found {len(pools)} pools")
    for pool in pools:
        pool_name = pool.get('pool_name') or pool.get('name', '')
        print(f"Pool: {pool_name} - Keys: {pool.keys()}")
        if 'CACS' in pool_name and '1' in pool_name:
            cacs1_pool = pool
            break

    if not cacs1_pool:
        print("CACS Paper 1 pool not found")
        return

    print(f"Found pool: {cacs1_pool['pool_name']} (ID: {cacs1_pool['id']})")

    # Get all questions from the pool
    questions = await db.get_pool_questions(cacs1_pool['id'])

    # Search for questions with "complaint"
    found = 0
    for q in questions:
        if 'complaint' in q['question_text'].lower():
            found += 1
            print(f"\n{'='*80}")
            print(f"Question ID: {q['id']}")
            print(f"Question Keys: {q.keys()}")
            print(f"Question: {q['question_text']}")
            print(f"\nRaw question data:")
            for key, value in q.items():
                if key != 'question_text':
                    print(f"  {key}: {value}")
            print(f"{'='*80}")

    print(f"\nTotal questions with 'complaint': {found}")

if __name__ == '__main__':
    asyncio.run(main())
