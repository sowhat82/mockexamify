"""
Direct fix for CACS Paper 1 questions using AI to reconstruct from PDF
"""
import asyncio
import json
import re
import PyPDF2
from db import db
from openrouter_utils import openrouter_manager


async def fix_question_with_ai(pdf_text: str, question_num: int, search_text: str) -> dict:
    """Use AI to extract and fix a specific question from PDF text"""

    # Extract section around this question number
    pattern = rf"({question_num}\..+?)(?={question_num+1}\.|$)"
    match = re.search(pattern, pdf_text, re.DOTALL)

    if not match:
        print(f"Could not find question {question_num} in PDF")
        return None

    question_block = match.group(1).strip()

    # Use AI to parse this specific question
    prompt = f"""Extract this exam question and format it correctly.

QUESTION TEXT FROM PDF:
{question_block}

This question follows this pattern:
- Main question text
- Lettered sub-items (a, b, c, d) that are PART OF THE QUESTION
- Answer choices that reference the sub-items like "(a), (c) and (d)"

CRITICAL: The lettered items (a, b, c, d) should be included in the question text, NOT treated as answer choices.

Return JSON with this exact format:
{{
  "question_text": "Main question with all sub-items included",
  "choices": ["Choice 1", "Choice 2", "Choice 3", "Choice 4"],
  "correct_index": 0
}}

The question_text should include the sub-items like:
"Which of the following...?\\n\\na. First item\\nb. Second item\\nc. Third item\\nd. Fourth item"

The choices are the combinations like: ["(a), (c) and (d)", "(a), (b) and (d)", ...]

For the correct_index, the correct answer in the PDF is typically in BOLD. The last choice is often correct, but check the context.

Return ONLY the JSON, nothing else."""

    try:
        response = await openrouter_manager._generate_text(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.1
        )

        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            result = json.loads(json_match.group(0))
            print(f"✅ AI parsed question {question_num}")
            return result
        else:
            print(f"❌ No JSON found in AI response")
            return None

    except Exception as e:
        print(f"❌ AI parsing error: {e}")
        return None


async def update_question_in_db(pool_id: str, search_text: str, fixed_data: dict) -> bool:
    """Find and update question in database"""

    questions = await db.get_pool_questions(pool_id)

    # Find matching question
    for q in questions:
        question_text = q.get('question_text', '')

        # Check if this matches
        if search_text.lower() in question_text.lower()[:150]:
            question_id = q.get('id')

            print(f"   Found question ID: {question_id}")
            print(f"   Old: {question_text[:80]}...")
            print(f"   New: {fixed_data['question_text'][:80]}...")

            # Update
            updated_data = {
                'question_text': fixed_data['question_text'],
                'choices': json.dumps(fixed_data['choices']),
                'correct_answer': fixed_data['correct_index']
            }

            # Update directly with Supabase
            result = db.admin_client.table("pool_questions").update(updated_data).eq("id", question_id).execute()

            if result.data:
                print(f"   ✅ Updated in database")
                return True
            else:
                print(f"   ❌ Database update failed")
                return False

    print(f"   ❌ No matching question found in database")
    return False


async def main():
    # Get pool
    pools = db.admin_client.table("question_pools").select("*").ilike("pool_name", "%CACS%Paper%1%").execute()

    if not pools.data:
        print("❌ CACS Paper 1 pool not found")
        return

    pool_id = pools.data[0]['id']
    pool_name = pools.data[0]['pool_name']

    print(f"🎯 Pool: {pool_name}")
    print(f"   ID: {pool_id}\n")

    # Load PDF
    pdf_path = "/workspaces/mockexamify/CACS Paper 1 practise questions.PDF"
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        pdf_text = ""
        for page in pdf.pages:
            pdf_text += page.extract_text() + "\n"

    print(f"📄 Loaded PDF: {len(pdf_text)} characters\n")

    # Questions to fix
    questions_to_fix = [
        (6, "When would a Covered Person NOT be penalised"),
        (12, "Which of the following are criteria for determining if a client is a vulnerable client"),
        (13, "Under the Private Banking Code of Conduct, why is it important"),
        (20, "What should you do with this information"),
        (31, "Which of the following are elements of best execution practices"),
        (32, "Why do Covered Persons and Entities gather a client"),
        (33, "Which of the following points should be addressed by a Covered Entity"),
        (34, "Which of the following should be taken into account when preparing a suitability analysis"),
        (37, "Which of the following scenarios could suggest a possible need for life insurance"),
        (40, "Which of the following are COMMON obstacles in preserving, protecting or transferring wealth"),
    ]

    print(f"🔧 Fixing {len(questions_to_fix)} questions...\n")

    fixed = 0
    failed = 0

    for q_num, search_text in questions_to_fix:
        print(f"{'='*60}")
        print(f"Question #{q_num}: {search_text[:50]}...")

        # Parse with AI
        fixed_data = await fix_question_with_ai(pdf_text, q_num, search_text)

        if fixed_data:
            # Update in database
            success = await update_question_in_db(pool_id, search_text, fixed_data)
            if success:
                fixed += 1
            else:
                failed += 1
        else:
            print(f"   ❌ Failed to parse")
            failed += 1

        print()

        # Small delay to avoid rate limiting
        await asyncio.sleep(1)

    print(f"{'='*60}")
    print(f"\n📊 Summary:")
    print(f"   ✅ Fixed: {fixed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📝 Total: {len(questions_to_fix)}")


if __name__ == "__main__":
    asyncio.run(main())
