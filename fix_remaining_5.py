"""Fix the remaining 5 questions with missing sub-items"""
import asyncio
import json
import re
import PyPDF2
from db import db
from openrouter_utils import openrouter_manager


async def fix_by_id(pdf_text: str, question_id: str, question_text_snippet: str):
    """Fix a specific question by finding it in the PDF"""

    print(f"\n{'='*60}")
    print(f"Fixing: {question_text_snippet[:60]}...")
    print(f"ID: {question_id}")

    # Search for this question in PDF
    # Extract first few words to search
    search_words = ' '.join(question_text_snippet.split()[:6])

    # Find in PDF
    pattern = rf"(\d+)\..{{0,50}}{re.escape(search_words[:40])}"
    match = re.search(pattern, pdf_text, re.IGNORECASE | re.DOTALL)

    if not match:
        print(f"❌ Could not find question in PDF")
        return False

    question_num = int(match.group(1))
    print(f"📍 Found as question #{question_num} in PDF")

    # Extract full question block
    pattern2 = rf"({question_num}\..+?)(?={question_num+1}\.|$)"
    match2 = re.search(pattern2, pdf_text, re.DOTALL)

    if not match2:
        print(f"❌ Could not extract question block")
        return False

    question_block = match2.group(1).strip()

    # Use AI to parse
    prompt = f"""Extract this exam question and format it correctly.

QUESTION TEXT FROM PDF:
{question_block}

This question has:
- Main question text
- Lettered sub-items (a, b, c, d) that are PART OF THE QUESTION
- Answer choices that reference the sub-items

CRITICAL: Include the lettered items (a, b, c, d) in the question text.

Return JSON:
{{
  "question_text": "Question with sub-items",
  "choices": ["Choice 1", "Choice 2", "Choice 3", "Choice 4"],
  "correct_index": 0
}}

Return ONLY the JSON."""

    try:
        response = await openrouter_manager._generate_text(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.1
        )

        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            result = json.loads(json_match.group(0))

            print(f"✅ AI parsed successfully")
            print(f"   New question: {result['question_text'][:80]}...")

            # Update in database
            updated_data = {
                'question_text': result['question_text'],
                'choices': json.dumps(result['choices']),
                'correct_answer': result['correct_index']
            }

            db_result = db.admin_client.table("pool_questions").update(updated_data).eq("id", question_id).execute()

            if db_result.data:
                print(f"   ✅ Updated in database")
                return True
            else:
                print(f"   ❌ Database update failed")
                return False
        else:
            print(f"❌ No JSON in AI response")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    # Load PDF
    pdf_path = "/workspaces/mockexamify/CACS Paper 1 practise questions.PDF"
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        pdf_text = ""
        for page in pdf.pages:
            pdf_text += page.extract_text() + "\n"

    print(f"📄 Loaded PDF: {len(pdf_text)} characters")

    # Questions to fix (ID, snippet)
    questions = [
        ("b8ea0a45-a057-4e69-8f9e-b9c225dc7bb2", "Before AI securities lending arrangement, provide:"),
        ("6103e9fc-8847-4385-a31c-6f4fa48c4fc9", "When can a Covered Person act for multiple principals simultaneously"),
        ("9f05252d-57e7-46fd-ae97-3c727bfe5e12", "An AI client wants to withdraw their AI status"),
        ("c3e55ab1-8772-4ea1-a0be-7ea47587ce6a", "Why must Covered Entities practice good market conduct"),
        ("ae08404b-a009-459a-b0e2-87239ef458eb", "Payment messages showing only a company name"),
    ]

    fixed = 0
    failed = 0

    for qid, snippet in questions:
        success = await fix_by_id(pdf_text, qid, snippet)
        if success:
            fixed += 1
        else:
            failed += 1

        # Small delay
        await asyncio.sleep(1)

    print(f"\n{'='*60}")
    print(f"\n📊 Summary:")
    print(f"   ✅ Fixed: {fixed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📝 Total: {len(questions)}")


if __name__ == "__main__":
    asyncio.run(main())
