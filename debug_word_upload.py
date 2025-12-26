"""
Debug Word document upload to trace where answer changes from 2 to 1
"""
import asyncio
from db import db
from document_parser import document_parser
from docx import Document
from io import BytesIO

# Create a test Word document with JSON
def create_test_word_doc():
    """Create a Word document containing JSON"""
    doc = Document()

    json_text = '''[{
  "id": 7,
  "chapter": "Private Banking Code of Conduct",
  "question": "An EAM introduces a client with a complex multi-layered corporate structure. The beneficial owner is identified but intermediate entities are unclear. What should you do?",
  "options": [
    "Proceed with account opening as the beneficial owner is clear",
    "Immediately file a suspicious transaction report",
    "Understand the purpose of the structure and the account before proceeding",
    "Decline the relationship due to structural complexity"
  ],
  "correct_answer": 2
}]'''

    doc.add_paragraph(json_text)

    # Save to BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Create a file-like object with name attribute
    class FakeFile:
        def __init__(self, buffer, name):
            self.buffer = buffer
            self.name = name

        def read(self):
            return self.buffer.read()

        def seek(self, pos):
            return self.buffer.seek(pos)

    return FakeFile(buffer, "test_document.docx")

async def test_upload():
    """Test the upload process"""
    print("=" * 80)
    print("CREATING TEST WORD DOCUMENT WITH JSON")
    print("=" * 80)

    uploaded_file = create_test_word_doc()

    print("\n" + "=" * 80)
    print("PARSING DOCUMENT")
    print("=" * 80)

    success, questions, error = document_parser.parse_document(uploaded_file)

    if not success:
        print(f"❌ Parse failed: {error}")
        return

    if not questions:
        print("❌ No questions extracted")
        return

    print(f"\n✅ Extracted {len(questions)} question(s)")

    for i, q in enumerate(questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Question text: {q.get('question', '')[:80]}...")
        print(f"Choices: {len(q.get('choices', []))} options")
        print(f"correct_index: {q.get('correct_index')}")
        print(f"correct_answer: {q.get('correct_answer')}")

        choices = q.get('choices', [])
        correct_idx = q.get('correct_answer') or q.get('correct_index', 0)

        if correct_idx < len(choices):
            print(f"Correct choice: {chr(65 + correct_idx)} - {choices[correct_idx]}")

        print(f"\nAll choices:")
        for idx, choice in enumerate(choices):
            marker = "✅" if idx == correct_idx else "◯"
            print(f"  {marker} {idx}: {choice}")

    print("\n" + "=" * 80)
    print("CHECKING WHAT WOULD BE STORED IN DATABASE")
    print("=" * 80)

    q = questions[0]
    print(f"Field 'correct_index': {q.get('correct_index')}")
    print(f"Field 'correct_answer': {q.get('correct_answer')}")
    print(f"Expected in DB: 2")
    print(f"Actual would be: {q.get('correct_answer') or q.get('correct_index')}")

    if (q.get('correct_answer') or q.get('correct_index')) != 2:
        print("\n❌ BUG CONFIRMED: Answer changed from 2 to something else!")
        print("Debugging where the change happens...")
    else:
        print("\n✅ Answer is correct (2)")

if __name__ == "__main__":
    import streamlit as st
    # Mock streamlit functions for testing
    st.info = print
    st.success = print
    st.warning = print
    st.error = print

    asyncio.run(test_upload())
