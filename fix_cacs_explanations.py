"""
Fix explanations for auto-corrected CACS Paper 1 questions.
Regenerates explanations to match the corrected answers.
"""
import asyncio
import re
from typing import List, Dict, Any
from openrouter_utils import openrouter_manager
from db import db

async def fix_explanations():
    """Fix explanations for all auto-corrected questions"""

    # Read the cleanup log to find auto-corrected question IDs
    with open('cacs_cleanup_log.txt', 'r') as f:
        log_lines = f.readlines()

    # Extract question IDs that had "Old Answer:" and "New Answer:" (these were auto-corrected)
    auto_corrected_ids = []
    for i, line in enumerate(log_lines):
        if 'Old Answer:' in line:
            # Look backwards for the question ID
            for j in range(i-1, max(i-10, 0), -1):
                if 'Question ID:' in log_lines[j]:
                    match = re.search(r'Question ID: ([a-f0-9-]+)', log_lines[j])
                    if match:
                        auto_corrected_ids.append(match.group(1))
                        break

    print(f"Found {len(auto_corrected_ids)} auto-corrected questions to fix")

    # Process each question
    fixed_count = 0
    error_count = 0

    for idx, question_id in enumerate(auto_corrected_ids, 1):
        try:
            print(f"\n[{idx}/{len(auto_corrected_ids)}] Processing question {question_id}...")

            # Fetch question from database
            response = db.admin_client.table("pool_questions").select("*").eq("id", question_id).execute()

            if not response.data:
                print(f"  ❌ Question not found in database")
                error_count += 1
                continue

            question = response.data[0]

            # Extract question data
            question_text = question['question_text']
            choices = question['choices']
            correct_index = question['correct_answer']
            scenario = question.get('scenario', '') or ''

            print(f"  Question: {question_text[:80]}...")
            print(f"  Correct answer: {chr(65 + correct_index)} - {choices[correct_index]}")

            # Generate new explanation with the corrected answer
            new_explanation = await openrouter_manager.generate_explanation(
                question=question_text,
                choices=choices,
                correct_index=correct_index,
                scenario=scenario
            )

            print(f"  ✅ Generated new explanation ({len(new_explanation)} chars)")

            # Update in database
            update_response = db.admin_client.table("pool_questions").update({
                'explanation': new_explanation
            }).eq('id', question_id).execute()

            if update_response.data:
                print(f"  ✅ Updated explanation in database")
                fixed_count += 1
            else:
                print(f"  ❌ Failed to update database")
                error_count += 1

            # Rate limiting - wait between API calls
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error processing question: {e}")
            error_count += 1
            continue

    print("\n" + "=" * 80)
    print("✅ EXPLANATION FIX COMPLETE")
    print("=" * 80)
    print(f"Total questions processed: {len(auto_corrected_ids)}")
    print(f"Successfully fixed: {fixed_count}")
    print(f"Errors: {error_count}")

if __name__ == "__main__":
    asyncio.run(fix_explanations())
