#!/usr/bin/env python3
"""
One-time cleanup script to validate and fix answer errors in CACS Paper 1 pool.
Uses AI to detect and auto-correct questions with wrong answers (≥90% confidence).
"""

import asyncio
import json
import sys
from typing import List, Dict, Any

from db import db
from openrouter_utils import validate_answer_correctness
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_cacs_paper1_answers():
    """Validate and fix answers in CACS Paper 1 pool"""

    print("=" * 80)
    print("CACS Paper 1 - Answer Validation & Cleanup")
    print("=" * 80)
    print()

    # Get CACS Paper 1 pool
    print("🔍 Finding CACS Paper 1 pool...")
    pools_response = db.admin_client.table("question_pools").select("*").eq("pool_name", "CACS Paper 1").execute()

    if not pools_response.data:
        print("❌ CACS Paper 1 pool not found")
        return

    pool = pools_response.data[0]
    pool_id = pool['id']
    print(f"✅ Found pool: {pool['pool_name']} (ID: {pool_id})")
    print()

    # Get all questions from pool
    print("📚 Loading all questions from pool...")
    questions_response = db.admin_client.table("pool_questions").select("*").eq("pool_id", pool_id).execute()

    if not questions_response.data:
        print("❌ No questions found in pool")
        return

    questions = questions_response.data
    print(f"✅ Loaded {len(questions)} questions")
    print()

    # Validate each question
    print("🤖 Starting AI answer validation...")
    print("=" * 80)
    print()

    auto_corrected = []
    low_confidence_warnings = []
    no_issues = []
    errors = []

    for idx, q in enumerate(questions, 1):
        question_id = q['id']
        question_text = q['question_text']
        choices = json.loads(q['choices']) if isinstance(q['choices'], str) else q['choices']
        correct_index = q['correct_answer']
        scenario = q.get('scenario', '')

        print(f"[{idx}/{len(questions)}] Validating question {question_id[:8]}...")
        print(f"  Question: {question_text[:80]}...")
        print(f"  Current answer: {chr(65 + correct_index)} - {choices[correct_index][:60]}...")

        try:
            # Call AI to validate answer
            validation = await validate_answer_correctness(
                question_text, choices, correct_index, scenario
            )

            if validation['should_auto_correct'] and not validation['is_valid']:
                # Auto-correct
                old_index = correct_index
                new_index = validation['ai_suggested_index']

                print(f"  ❌ WRONG ANSWER DETECTED (Confidence: {validation['confidence']:.0%})")
                print(f"     Old: {chr(65 + old_index)} - {choices[old_index][:60]}...")
                print(f"     New: {chr(65 + new_index)} - {choices[new_index][:60]}...")
                print(f"     Reasoning: {validation['reasoning'][:100]}...")

                # Update in database
                update_response = db.admin_client.table("pool_questions").update({
                    'correct_answer': new_index
                }).eq('id', question_id).execute()

                if update_response.data:
                    print(f"  ✅ CORRECTED in database")
                    auto_corrected.append({
                        'question_id': question_id,
                        'question_text': question_text[:100],
                        'old_answer': f"{chr(65 + old_index)} - {choices[old_index]}",
                        'new_answer': f"{chr(65 + new_index)} - {choices[new_index]}",
                        'confidence': validation['confidence'],
                        'reasoning': validation['reasoning']
                    })
                else:
                    print(f"  ❌ FAILED to update database")

            elif not validation['is_valid'] and validation['confidence'] < 0.90:
                # Low confidence warning
                print(f"  ⚠️  POTENTIAL ISSUE (Confidence: {validation['confidence']:.0%} - too low to auto-correct)")
                print(f"     Suggests: {chr(65 + validation['ai_suggested_index'])} - {choices[validation['ai_suggested_index']][:60]}...")
                print(f"     Reasoning: {validation['reasoning'][:100]}...")

                low_confidence_warnings.append({
                    'question_id': question_id,
                    'question_text': question_text[:100],
                    'current_answer': f"{chr(65 + correct_index)} - {choices[correct_index]}",
                    'suggested_answer': f"{chr(65 + validation['ai_suggested_index'])} - {choices[validation['ai_suggested_index']]}",
                    'confidence': validation['confidence'],
                    'reasoning': validation['reasoning']
                })
            else:
                # No issues
                print(f"  ✅ Answer is correct")
                no_issues.append(question_id)

            print()

            # Rate limiting
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Error validating question {question_id}: {e}")
            print(f"  ❌ ERROR: {e}")
            errors.append({
                'question_id': question_id,
                'error': str(e)
            })
            print()

    # Final Report
    print()
    print("=" * 80)
    print("FINAL REPORT")
    print("=" * 80)
    print()

    print(f"📊 SUMMARY:")
    print(f"  Total questions validated: {len(questions)}")
    print(f"  ✅ Correct answers: {len(no_issues)}")
    print(f"  🔧 Auto-corrected: {len(auto_corrected)}")
    print(f"  ⚠️  Low confidence warnings: {len(low_confidence_warnings)}")
    print(f"  ❌ Errors: {len(errors)}")
    print()

    if auto_corrected:
        print("=" * 80)
        print(f"🔧 AUTO-CORRECTED ({len(auto_corrected)} questions)")
        print("=" * 80)
        for idx, correction in enumerate(auto_corrected, 1):
            print(f"\n{idx}. Question ID: {correction['question_id']}")
            print(f"   Text: {correction['question_text']}")
            print(f"   Old Answer: {correction['old_answer']}")
            print(f"   New Answer: {correction['new_answer']}")
            print(f"   Confidence: {correction['confidence']:.0%}")
            print(f"   Reasoning: {correction['reasoning']}")

    if low_confidence_warnings:
        print()
        print("=" * 80)
        print(f"⚠️  LOW CONFIDENCE WARNINGS ({len(low_confidence_warnings)} questions)")
        print("=" * 80)
        print("These questions may have wrong answers but AI is not confident enough to auto-correct.")
        print("Manual review recommended.")
        for idx, warning in enumerate(low_confidence_warnings, 1):
            print(f"\n{idx}. Question ID: {warning['question_id']}")
            print(f"   Text: {warning['question_text']}")
            print(f"   Current Answer: {warning['current_answer']}")
            print(f"   AI Suggests: {warning['suggested_answer']}")
            print(f"   Confidence: {warning['confidence']:.0%}")
            print(f"   Reasoning: {warning['reasoning']}")

    if errors:
        print()
        print("=" * 80)
        print(f"❌ ERRORS ({len(errors)} questions)")
        print("=" * 80)
        for idx, error in enumerate(errors, 1):
            print(f"\n{idx}. Question ID: {error['question_id']}")
            print(f"   Error: {error['error']}")

    print()
    print("=" * 80)
    print("✅ CLEANUP COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(cleanup_cacs_paper1_answers())
