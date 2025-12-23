"""
Fix questions with missing sub-items (a, b, c, d) by extracting them from source PDF
"""
import asyncio
import json
import re
from typing import Dict, List, Optional

import PyPDF2
from db import db
from openrouter_utils import openrouter_manager


async def extract_question_with_context_from_pdf(pdf_path: str, question_num: int) -> Optional[Dict]:
    """Extract a specific question with its full context including sub-items"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

        # Find the question in the PDF
        # Pattern: "31. Which of the following..." followed by lettered items
        pattern = rf"{question_num}\.\s+(.*?)(?=\d+\.|$)"
        match = re.search(pattern, text, re.DOTALL)

        if not match:
            print(f"Could not find question {question_num} in PDF")
            return None

        full_text = match.group(1)

        # Now parse this section using AI
        prompt = f"""Extract the complete question including all sub-items from this text:

{full_text}

This question has TWO parts:
1. A main question text
2. Lettered sub-items (a, b, c, d) that define what the answer choices refer to
3. Answer choices that reference the sub-items (e.g., "(a) and (b)")

CRITICAL: The lettered items (a, b, c, d) are NOT the answer choices. They are part of the question context.
The actual answer choices are the options that combine these letters like "(a), (c) and (d)".

Return JSON:
{{
  "question_text": "The main question including all sub-items (a, b, c, d)",
  "choices": ["Array of the actual answer choices that reference the sub-items"],
  "correct_index": 0
}}

Example output format:
{{
  "question_text": "Which of the following are elements of best execution?\\n\\na. Speed of execution\\nb. Price confidentiality\\nc. Likelihood of execution\\nd. Client instructions",
  "choices": ["(a), (c) and (d)", "(a), (b) and (d)", "(b), (c) and (d)", "(a), (b), (c) and (d)"],
  "correct_index": 3
}}

Extract now:"""

        # Call AI to parse
        response = await openrouter_manager.call_api(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1000
        )

        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response: {e}")
            print(f"Response was: {response}")
            return None

    except Exception as e:
        print(f"Error extracting question {question_num}: {e}")
        return None


async def find_questions_with_missing_subitems(pool_id: str) -> List[Dict]:
    """Find all questions in pool that have missing sub-items"""
    questions = await db.get_pool_questions(pool_id)

    missing_subitems = []

    for q in questions:
        question_text = q.get('question_text', '')
        choices = q.get('choices', [])

        if isinstance(choices, str):
            try:
                choices = json.loads(choices)
            except:
                pass

        # Check if choices reference (a), (b), (c), (d) but question doesn't list them
        has_sub_refs = any('(a)' in str(choice) or '(b)' in str(choice) for choice in choices if choice)
        has_sub_list = '(a)' in question_text or '\na.' in question_text or '\na)' in question_text

        if has_sub_refs and not has_sub_list:
            missing_subitems.append({
                'id': q.get('id'),
                'question': question_text,
                'choices': choices,
                'correct_answer': q.get('correct_answer')
            })

    return missing_subitems


async def fix_question_subitems(pdf_path: str, pool_id: str):
    """Fix all questions with missing sub-items"""

    # Find questions that need fixing
    print(f"\n🔍 Scanning pool for questions with missing sub-items...")
    questions_to_fix = await find_questions_with_missing_subitems(pool_id)

    print(f"📊 Found {len(questions_to_fix)} questions with missing sub-items\n")

    if not questions_to_fix:
        print("✅ No questions need fixing!")
        return

    # Try to match each question to its number in the PDF
    # This is tricky - we'll use the question text to search
    fixed_count = 0
    failed_count = 0

    for idx, q_data in enumerate(questions_to_fix, 1):
        question_id = q_data['id']
        question_text = q_data['question']

        print(f"\n[{idx}/{len(questions_to_fix)}] Processing question ID: {question_id}")
        print(f"Current question: {question_text[:100]}...")

        # Extract first few words to search in PDF
        search_words = ' '.join(question_text.split()[:8])

        # Search PDF for this question
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                for page in pdf_reader.pages:
                    full_text += page.extract_text() + "\n"

            # Find question number by searching for the text
            # Pattern: Look for question number before our search words
            pattern = rf"(\d+)\.\s+{re.escape(search_words[:50])}"
            match = re.search(pattern, full_text, re.IGNORECASE)

            if match:
                question_num = int(match.group(1))
                print(f"📍 Found as question #{question_num} in PDF")

                # Extract full question with context
                extracted = await extract_question_with_context_from_pdf(pdf_path, question_num)

                if extracted and extracted.get('question_text'):
                    # Update in database
                    updated_data = {
                        'question_text': extracted['question_text'],
                        'choices': json.dumps(extracted['choices']),
                        'correct_answer': extracted['correct_index']
                    }

                    success = await db.update_question(question_id, updated_data)

                    if success:
                        print(f"✅ Fixed question ID: {question_id}")
                        print(f"   New question text: {extracted['question_text'][:150]}...")
                        fixed_count += 1
                    else:
                        print(f"❌ Failed to update database for question ID: {question_id}")
                        failed_count += 1
                else:
                    print(f"❌ Failed to extract question content")
                    failed_count += 1
            else:
                print(f"❌ Could not find question in PDF")
                failed_count += 1

        except Exception as e:
            print(f"❌ Error processing question: {e}")
            failed_count += 1

    print(f"\n" + "="*50)
    print(f"📊 Summary:")
    print(f"   ✅ Fixed: {fixed_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📝 Total: {len(questions_to_fix)}")


async def main():
    """Main entry point"""
    # Get CACS Paper 1 pool
    pools = db.admin_client.table("question_pools").select("*").ilike("pool_name", "%CACS%Paper%1%").execute()

    if not pools.data:
        print("❌ No CACS Paper 1 pool found")
        return

    pool_id = pools.data[0]['id']
    pool_name = pools.data[0]['pool_name']

    print(f"🎯 Target pool: {pool_name}")
    print(f"   Pool ID: {pool_id}")

    # Path to uploaded PDF
    pdf_path = "/tmp/CACS Paper 1 practise questions.PDF"

    # Check if PDF exists
    import os
    if not os.path.exists(pdf_path):
        print(f"\n❌ PDF not found at: {pdf_path}")
        print("Please provide the path to the PDF file:")
        pdf_path = input("> ").strip()

        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return

    # Fix questions
    await fix_question_subitems(pdf_path, pool_id)

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
