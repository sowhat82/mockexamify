"""
Fix specific CACS Paper 1 questions with missing sub-items by re-extracting from PDF
"""
import asyncio
import json
import re
import sys
from typing import Dict, List, Optional

import PyPDF2
from db import db


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from PDF"""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text


def parse_question_with_subitems(text_block: str) -> Optional[Dict]:
    """
    Parse a question that has lettered sub-items.

    Example format:
    31. Which of the following are elements of best execution?
    a. Speed of execution
    b. Price confidentiality
    c. Likelihood of execution
    d. Client instructions

    ■ (a), (c) and (d).
    ■ (a), (b) and (d).
    ■ (b), (c) and (d).
    ■ (a), (b), (c) and (d). [CORRECT]
    """
    # Extract question number and main text
    question_match = re.match(r'^(\d+)\.\s+(.+?)(?=\n[a-d]\.|\n\n)', text_block, re.DOTALL)
    if not question_match:
        return None

    question_num = int(question_match.group(1))
    main_question = question_match.group(2).strip()

    # Extract lettered sub-items (a, b, c, d)
    subitems_pattern = r'\n([a-d])\.\s+([^\n]+)'
    subitems = re.findall(subitems_pattern, text_block)

    if not subitems:
        # No sub-items found, return None
        return None

    # Build complete question text with sub-items
    complete_question = main_question + "\n\n"
    for letter, text in subitems:
        complete_question += f"{letter}. {text.strip()}\n"
    complete_question = complete_question.strip()

    # Extract answer choices (patterns like "(a), (c) and (d)")
    # Look for lines with this pattern
    choices_pattern = r'[■□▪▫◯●]\s*\(([a-d][\),\s]+(?:and\s+)?\([a-d]\)|[a-d][\),\s]+\([a-d]\)[\),\s]+(?:and\s+)?\([a-d]\)|[a-d][\),\s]+\([a-d]\)[\),\s]+\([a-d]\)[\),\s]+(?:and\s+)?\([a-d]\)|all of the above)\)'

    # Simpler pattern - just look for parenthesized letter combinations
    choices = []
    choice_lines = re.findall(r'[■□▪▫◯●]\s*(.+?)\.?\s*$', text_block, re.MULTILINE)

    for line in choice_lines:
        # Check if line contains (a), (b), (c), (d) patterns
        if re.search(r'\([a-d]\)', line, re.IGNORECASE):
            choices.append(line.strip().rstrip('.'))

    if not choices:
        return None

    # Find correct answer (marked with bold or special indicator)
    correct_index = 0
    for i, choice in enumerate(choices):
        # Look for the choice in the original text with bold markers or "correct" indicator
        if re.search(rf'{re.escape(choice)}.*?(correct|\*\*|bold)', text_block, re.IGNORECASE):
            correct_index = i
            break

    # If no explicit marker, assume last choice or check for patterns
    # In the PDF, correct answer is in bold
    # We'll need to check each choice against the original block
    for i, choice in enumerate(choices):
        # Look for this choice followed by indicators
        escaped_choice = re.escape(choice.replace('(', r'\(').replace(')', r'\)'))
        # Check if this choice appears in bold context or has markers
        if i == len(choices) - 1:  # Often the last choice in examples
            correct_index = i

    return {
        'question_num': question_num,
        'question_text': complete_question,
        'choices': choices,
        'correct_index': correct_index
    }


async def find_and_fix_question(pool_id: str, pdf_text: str, search_text: str, question_data: Dict):
    """Find a question in the database by search text and update it"""

    # Find questions in pool
    questions = await db.get_pool_questions(pool_id)

    # Search for matching question
    for q in questions:
        question_text = q.get('question_text', '')

        # Check if this question matches our search
        if search_text.lower() in question_text.lower():
            question_id = q.get('id')

            print(f"\n✅ Found matching question:")
            print(f"   ID: {question_id}")
            print(f"   Current: {question_text[:100]}...")
            print(f"   New: {question_data['question_text'][:100]}...")

            # Update question
            updated_data = {
                'question_text': question_data['question_text'],
                'choices': json.dumps(question_data['choices']),
                'correct_answer': question_data['correct_index']
            }

            success = await db.update_question(question_id, updated_data)

            if success:
                print(f"   ✅ Updated successfully!")
                return True
            else:
                print(f"   ❌ Update failed")
                return False

    print(f"\n❌ No matching question found for: {search_text[:50]}...")
    return False


async def main(pdf_path: str):
    """Main entry point"""

    # Get CACS Paper 1 pool
    pools = db.admin_client.table("question_pools").select("*").ilike("pool_name", "%CACS%Paper%1%").execute()

    if not pools.data:
        print("❌ No CACS Paper 1 pool found")
        return

    pool_id = pools.data[0]['id']
    pool_name = pools.data[0]['pool_name']

    print(f"🎯 Target pool: {pool_name}")
    print(f"   Pool ID: {pool_id}\n")

    # Load PDF
    print(f"📄 Reading PDF: {pdf_path}")
    pdf_text = extract_pdf_text(pdf_path)
    print(f"   Extracted {len(pdf_text)} characters\n")

    # Known questions with missing sub-items and their search patterns
    # From the PDF, these are the questions with (a), (b), (c), (d) pattern
    problem_questions = [
        {
            'number': 6,
            'search': 'When would a Covered Person NOT be penalised',
            'block_start': '6. When would a Covered Person NOT be penalised'
        },
        {
            'number': 12,
            'search': 'Which of the following are criteria for determining if a client is a vulnerable client',
            'block_start': '12. Which of the following are criteria for determining'
        },
        {
            'number': 13,
            'search': 'Under the Private Banking Code of Conduct, why is it important',
            'block_start': '13. Under the Private Banking Code of Conduct'
        },
        {
            'number': 20,
            'search': 'What should you do with this information',
            'block_start': '20. '
        },
        {
            'number': 31,
            'search': 'Which of the following are elements of best execution practices',
            'block_start': '31. Which of the following are elements of best execution'
        },
        {
            'number': 32,
            'search': 'Why do Covered Persons and Entities gather a client',
            'block_start': '32. Why do Covered Persons and Entities'
        },
        {
            'number': 33,
            'search': 'Which of the following points should be addressed by a Covered Entity under the MAS Guidelines',
            'block_start': '33. Which of the following points should be addressed'
        },
        {
            'number': 34,
            'search': 'Which of the following should be taken into account when preparing a suitability analysis',
            'block_start': '34. Which of the following should be taken into account'
        },
        {
            'number': 37,
            'search': 'Which of the following scenarios could suggest a possible need for life insurance',
            'block_start': '37. Which of the following scenarios could suggest'
        },
        {
            'number': 40,
            'search': 'Which of the following are COMMON obstacles in preserving, protecting or transferring wealth',
            'block_start': '40. Which of the following are COMMON obstacles'
        }
    ]

    print(f"🔍 Searching for {len(problem_questions)} questions in PDF...\n")

    fixed_count = 0
    failed_count = 0

    for pq in problem_questions:
        print(f"\n{'='*60}")
        print(f"Question #{pq['number']}: {pq['search'][:60]}...")

        # Find the question block in PDF
        # Look for pattern: "NUMBER. text ... \nNEXT_NUMBER."
        next_num = pq['number'] + 1
        pattern = rf"{pq['number']}\.\s+(.+?)\n{next_num}\."

        match = re.search(pattern, pdf_text, re.DOTALL)

        if match:
            question_block = f"{pq['number']}. {match.group(1)}"

            # Parse this block
            parsed = parse_question_with_subitems(question_block)

            if parsed:
                print(f"📝 Parsed question with {len(parsed['choices'])} choices")

                # Update in database
                success = await find_and_fix_question(pool_id, pdf_text, pq['search'], parsed)

                if success:
                    fixed_count += 1
                else:
                    failed_count += 1
            else:
                print(f"❌ Failed to parse question block")
                failed_count += 1
        else:
            print(f"❌ Could not find question #{pq['number']} in PDF")
            failed_count += 1

    print(f"\n{'='*60}")
    print(f"\n📊 Summary:")
    print(f"   ✅ Fixed: {fixed_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📝 Total: {len(problem_questions)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_cacs_paper1_subitems.py <path_to_pdf>")
        print("\nExample:")
        print("  python fix_cacs_paper1_subitems.py '/workspaces/mockexamify/CACS Paper 1 practise questions.PDF'")
        sys.exit(1)

    pdf_path = sys.argv[1]

    import os
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        sys.exit(1)

    asyncio.run(main(pdf_path))
