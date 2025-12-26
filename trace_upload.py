"""
Test Word document with JSON to verify answer stays as 2
"""
import asyncio
from docx import Document
from io import BytesIO
import sys

# Mock streamlit for testing
class MockSt:
    def info(self, msg):
        print(f"ℹ️  {msg}")

    def success(self, msg):
        print(f"✅ {msg}")

    def warning(self, msg):
        print(f"⚠️  {msg}")

    def error(self, msg):
        print(f"❌ {msg}")

sys.modules['streamlit'] = type(sys)('streamlit')
sys.modules['streamlit'].info = MockSt().info
sys.modules['streamlit'].success = MockSt().success
sys.modules['streamlit'].warning = MockSt().warning
sys.modules['streamlit'].error = MockSt().error

from document_parser import document_parser

# Create test Word document with user's exact JSON
def create_word_with_json():
    doc = Document()

    json_content = '''[{
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

    doc.add_paragraph(json_content)

    # Save to BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    buffer.name = "test.docx"

    return buffer

print("=" * 80)
print("CREATING TEST WORD DOCUMENT WITH JSON")
print("=" * 80)

uploaded_file = create_word_with_json()

print("\n" + "=" * 80)
print("PARSING WITH DOCUMENT PARSER")
print("=" * 80)

success, questions, error = document_parser.parse_document(uploaded_file)

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)

if not success:
    print(f"❌ Parse failed: {error}")
    sys.exit(1)

if not questions:
    print("❌ No questions extracted")
    sys.exit(1)

print(f"\n✅ Successfully extracted {len(questions)} question(s)")

for i, q in enumerate(questions, 1):
    print(f"\n--- Question {i} ---")
    print(f"Text: {q.get('question', '')[:100]}...")

    choices = q.get('choices', [])
    correct_answer = q.get('correct_answer')
    correct_index = q.get('correct_index')

    print(f"\nFields:")
    print(f"  correct_answer: {correct_answer}")
    print(f"  correct_index: {correct_index}")

    print(f"\nChoices:")
    for idx, choice in enumerate(choices):
        marker = "✅" if idx == (correct_answer or correct_index) else "◯"
        print(f"  {marker} {idx}: {choice}")

    print(f"\n🔍 VERIFICATION:")
    print(f"  Expected: 2")
    print(f"  Actual: {correct_answer or correct_index}")

    if (correct_answer or correct_index) == 2:
        print(f"  ✅ CORRECT - Answer preserved as 2")
    else:
        print(f"  ❌ WRONG - Answer changed from 2 to {correct_answer or correct_index}")
        sys.exit(1)

print("\n" + "=" * 80)
print("✅ TEST PASSED - JSON parsing works correctly!")
print("=" * 80)
