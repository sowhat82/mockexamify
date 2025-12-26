"""
Debug script to check a specific question's answer in the database
"""
import asyncio
from db import db

async def check_question():
    """Check the EAM question with complex structure"""

    # Search for the question by partial text match
    search_text = "EAM introduces a client with a complex multi-layered"

    print(f"Searching for question containing: '{search_text}'")

    # Query all questions in pool_questions
    response = db.admin_client.table("pool_questions").select("*").execute()

    matching_questions = []
    for q in response.data:
        if search_text.lower() in q.get('question_text', '').lower():
            matching_questions.append(q)

    print(f"\nFound {len(matching_questions)} matching question(s)\n")

    for q in matching_questions:
        import json

        # Parse choices if it's a JSON string
        choices = q['choices']
        if isinstance(choices, str):
            print(f"⚠️  Choices is stored as STRING, parsing JSON...")
            try:
                choices = json.loads(choices)
            except:
                print(f"❌ Failed to parse choices JSON")

        print("=" * 80)
        print(f"Question ID: {q['id']}")
        print(f"Question text: {q['question_text'][:100]}...")
        print(f"\nChoices (type: {type(choices).__name__}):")
        for i, choice in enumerate(choices):
            marker = "✅" if i == q['correct_answer'] else "◯"
            print(f"  {marker} {i}: {choice}")
        print(f"\nCorrect answer stored in DB: {q['correct_answer']}")
        print(f"Correct answer letter: {chr(65 + q['correct_answer'])}")
        print(f"Correct answer text: {choices[q['correct_answer']]}")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(check_question())
