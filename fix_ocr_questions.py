"""
Fix OCR errors in existing database questions
This script will fetch all questions from the database and fix OCR formatting issues
"""

import asyncio
import json
import re
from typing import Any, Dict, List

import httpx

import config
from db import db


def fix_ocr_text(text: str) -> str:
    """
    Fix common OCR errors in text using regex patterns

    Common issues:
    - Single letters separated by spaces (e.g., "p e r s h a r e" → "per share")
    - Conjoined words (e.g., "pershareand" → needs AI to fix)
    """
    if not text:
        return text

    # Pattern 1: Fix single letters separated by spaces (e.g., "p e r")
    # Look for sequences of single letters separated by spaces
    pattern = r"\b([a-z])\s+([a-z])(?:\s+([a-z]))*\b"

    def collapse_letters(match):
        # Get all matched groups and join them without spaces
        return "".join(filter(None, match.groups()))

    # Apply the pattern multiple times to catch all sequences
    prev_text = ""
    while prev_text != text:
        prev_text = text
        text = re.sub(pattern, collapse_letters, text, flags=re.IGNORECASE)

    return text


async def fix_question_with_ai(question_text: str, choices: List[str]) -> Dict[str, Any]:
    """
    Use AI to fix OCR errors in question text and choices
    """
    api_key = config.OPENROUTER_API_KEY

    if not api_key or api_key == "demo" or api_key == "your_openrouter_api_key":
        # Fall back to regex-only fix
        return {
            "question": fix_ocr_text(question_text),
            "choices": [fix_ocr_text(c) for c in choices],
        }

    # Use AI to fix OCR errors
    prompt = f"""Fix OCR errors in the following exam question. The text has OCR errors where:
- Words are split into individual letters with spaces (e.g., "p e r s h a r e" should be "per share")
- Words may be conjoined (e.g., "pershareand" should be "per share and")
- Mathematical symbols and numbers should be preserved

QUESTION:
{question_text}

CHOICES:
{json.dumps(choices, indent=2)}

Return a JSON object with the corrected text:
{{
  "question": "corrected question text",
  "choices": ["choice 1", "choice 2", "choice 3", "choice 4"]
}}

Return ONLY the JSON, no other text."""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mockexamify.com",
            "X-Title": "MockExamify",
        }

        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{config.OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload
            )

        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Extract JSON from response
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            fixed_data = json.loads(json_match.group())
            return fixed_data
        else:
            # Fall back to regex fix
            return {
                "question": fix_ocr_text(question_text),
                "choices": [fix_ocr_text(c) for c in choices],
            }

    except Exception as e:
        print(f"AI fix error: {e}, falling back to regex")
        # Fall back to regex-only fix
        return {
            "question": fix_ocr_text(question_text),
            "choices": [fix_ocr_text(c) for c in choices],
        }


async def fix_all_questions():
    """Fix OCR errors in all questions in the database"""
    print("Fetching all question pools...")

    # Get all question pools
    pools = await db.get_all_question_pools()

    if not pools:
        print("ERROR: No question pools found")
        return

    print(f"SUCCESS: Found {len(pools)} question pools")

    total_fixed = 0

    for pool in pools:
        pool_id = pool.get("id")
        pool_name = pool.get("pool_name", "Unknown")

        print(f"\nProcessing pool: {pool_name}")

        # Get all questions in this pool
        questions = await db.get_pool_questions(pool_id)

        if not questions:
            print(f"  WARNING: No questions found in pool")
            continue

        print(f"  Found {len(questions)} questions")

        # Scan ALL questions for OCR errors (newlines between single chars)
        print(f"\n  Scanning all questions for OCR errors...")
        questions_with_errors = []
        for i, q in enumerate(questions, 1):
            q_text = q.get("question_text", "")

            # Check for pattern: numbers/text followed by newlines with single chars
            # Pattern: look for sequences like "\n5\n0\n0" or "\nA\nt\nt\nh\ne"
            has_newline_ocr = bool(re.search(r"\n[0-9a-zA-Z]\n[0-9a-zA-Z]\n[0-9a-zA-Z]", q_text))

            if has_newline_ocr:
                questions_with_errors.append((i, q_text[:200], "newline-separated chars"))

        if questions_with_errors:
            print(f"  FOUND {len(questions_with_errors)} questions with newline OCR errors:")
            for q_num, q_preview, error_type in questions_with_errors[:10]:  # Show first 10
                # Show with newlines visible
                print(f"\n  Q{q_num}: {repr(q_preview)}")
                print(f"    Error type: {error_type}")
        else:
            print(f"  No newline OCR errors detected")
        print("")

        for idx, question in enumerate(questions, 1):
            question_id = question.get("id")
            question_text = question.get("question_text", "")

            # Parse choices
            choices = question.get("choices", [])
            if isinstance(choices, str):
                try:
                    choices = json.loads(choices)
                except:
                    choices = []

            # Check if question has OCR errors
            # Pattern: Newlines between single characters (e.g., "\n5\n0\n0" or "\nA\nt\nh\ne")
            has_ocr_errors = bool(
                re.search(r"\n[0-9a-zA-Z]\n[0-9a-zA-Z]\n[0-9a-zA-Z]", question_text)
            )

            if has_ocr_errors:
                print(f"  FIXING question {idx}/{len(questions)}: {question_text[:50]}...")

                # Fix with AI
                fixed = await fix_question_with_ai(question_text, choices)

                # Update in database
                try:
                    response = (
                        db.client.table("pool_questions")
                        .update(
                            {
                                "question_text": fixed["question"],
                                "choices": json.dumps(fixed["choices"]),
                            }
                        )
                        .eq("id", question_id)
                        .execute()
                    )

                    if response.data:
                        total_fixed += 1
                        print(f"    SUCCESS: Fixed: {fixed['question'][:60]}...")
                    else:
                        print(f"    ERROR: Failed to update question {question_id}")

                except Exception as e:
                    print(f"    ERROR: Error updating question: {e}")
            else:
                print(f"  OK: Question {idx}/{len(questions)} looks good")

    print(f"\nComplete! Fixed {total_fixed} questions with OCR errors")


if __name__ == "__main__":
    print("=" * 60)
    print("OCR ERROR FIX SCRIPT")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Fetch all questions from all pools")
    print("2. Detect OCR errors (split letters, formatting issues)")
    print("3. Fix them using AI (or regex fallback)")
    print("4. Update the database")
    print("\nWARNING: Make sure you have a backup of your database first!")
    print("=" * 60)

    # Check if running in demo mode
    if config.DEMO_MODE:
        print("\nWARNING: Running in DEMO_MODE!")
        print("The database operations will use the real Supabase database.")
        print("This is expected for hybrid mode (demo auth + real database).")
        print("")

    response = input("\nContinue? (yes/no): ")

    if response.lower() in ["yes", "y"]:
        asyncio.run(fix_all_questions())
    else:
        print("Cancelled")
