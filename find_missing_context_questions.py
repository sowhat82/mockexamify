#!/usr/bin/env python3
"""
Find questions with MISSING context - specifically ones that say
"given the following" or "evaluate the following" but don't provide the actual information
"""

import json
from db import DatabaseManager

def main():
    db = DatabaseManager()

    # Get all questions
    result = db.admin_client.table("pool_questions").select("*").execute()
    all_questions = result.data

    print(f"Scanning {len(all_questions)} questions...\n")

    missing_context = []

    for q in all_questions:
        q_text = q['question_text']
        q_lower = q_text.lower()

        # Specific patterns from user's screenshots
        is_missing = False

        # Pattern 1: "Given the following information" but no information provided
        # Real info would include numbers, or the question would be longer
        if 'given the following information' in q_lower:
            # If no numbers and question is short, it's missing context
            has_numbers = any(c.isdigit() for c in q_text)
            if not has_numbers or len(q_text) < 100:
                is_missing = True

        # Pattern 2: "given the following details" but no details
        if 'given the following details' in q_lower:
            has_numbers = any(c.isdigit() for c in q_text)
            if not has_numbers or len(q_text) < 100:
                is_missing = True

        # Pattern 3: "evaluate the following statements" but no statements
        if 'evaluate the following' in q_lower and 'statement' in q_lower:
            # Real statements would have numbers like "Statement 1" or "1."
            has_statements = 'statement 1' in q_lower or 'statement 2' in q_lower or '1.' in q_text or 'i.' in q_lower
            if not has_statements:
                is_missing = True

        # Pattern 4: "given the following exchange rates" but no rates
        if 'given the following exchange rate' in q_lower:
            # Real rates would have format like USD/SGD or EUR/JPY
            has_rates = '/' in q_text and any(c.isdigit() for c in q_text)
            if not has_rates:
                is_missing = True

        if is_missing:
            missing_context.append(q)

    print(f"{'='*80}")
    print(f"FOUND {len(missing_context)} QUESTIONS WITH MISSING CONTEXT")
    print(f"{'='*80}\n")

    # Get pool names
    pools_result = db.admin_client.table("question_pools").select("*").execute()
    pool_map = {p['id']: p['pool_name'] for p in pools_result.data}

    for i, q in enumerate(missing_context, 1):
        pool_name = pool_map.get(q['pool_id'], 'Unknown')
        choices = json.loads(q['choices']) if isinstance(q['choices'], str) else q['choices']

        print(f"\nQuestion {i}:")
        print(f"  ID: {q['id']}")
        print(f"  Pool: {pool_name}")
        print(f"  Question: {q['question_text']}")
        print(f"  Correct answer: {chr(65 + q['correct_answer'])}. {choices[q['correct_answer']]}")

    # Save IDs to file for deletion
    if missing_context:
        ids = [q['id'] for q in missing_context]
        with open('missing_context_ids.txt', 'w') as f:
            f.write('\n'.join(ids))
        print(f"\n{'='*80}")
        print(f"Saved {len(ids)} question IDs to missing_context_ids.txt")
        print(f"\nThese questions are IMPOSSIBLE to answer and should be DELETED")

if __name__ == "__main__":
    main()
