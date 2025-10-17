# Document Upload Feature Guide

## Overview

The MockExamify admin panel now supports **automatic question extraction** from PDF and Word documents using AI. This makes it easy to upload entire mock exams without manually formatting CSV or JSON files.

## Supported File Formats

### 1. **PDF Documents (.pdf)**
- Upload PDF files containing multiple-choice questions
- AI automatically extracts questions, choices, and correct answers
- Works with various PDF formats and layouts

### 2. **Word Documents (.docx, .doc)**
- Upload Microsoft Word documents
- Extracts from both paragraph text and tables
- Maintains question structure and formatting

### 3. **CSV Files (.csv)** *(Traditional method)*
- Manual structured format
- Requires specific column headers
- Best for programmatically generated data

### 4. **JSON Files (.json)** *(Traditional method)*
- Array of question objects
- Precise control over question structure
- Good for API integrations

## How It Works

### AI-Powered Extraction (PDF/Word)

1. **Text Extraction**: The system reads all text from your document
2. **AI Analysis**: Uses Claude AI (via OpenRouter) to identify questions
3. **Structured Parsing**: Converts questions into database format
4. **Validation**: Ensures all questions have valid choices and answers
5. **Preview**: Shows you extracted questions before saving

### Document Format Guidelines

For best AI extraction results, structure your documents like this:

```
Question 1: What is the capital of France?
A) London
B) Paris *
C) Berlin
D) Madrid

Answer: B
Explanation: Paris is the capital and largest city of France.

Question 2: Which programming language is used for web development?
A) Python
B) JavaScript *
C) C++
D) Assembly

Scenario: In modern web applications
Answer: JavaScript
```

### Key Tips for Good Results

1. **Number your questions**: Use Q1, Question 1, 1., etc.
2. **Label choices clearly**: A/B/C/D or 1/2/3/4
3. **Mark correct answers**:
   - Use asterisk (*) next to correct choice
   - Or write "Answer: B" after choices
   - Or bold/highlight the correct answer
4. **Add context**: Include scenarios before questions (optional)
5. **Provide explanations**: These help generate better AI explanations later

## Configuration

### OpenRouter API Setup

To use AI document parsing, configure your OpenRouter API key:

1. Get API key from: https://openrouter.ai/
2. Add to your `.env` file:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```
3. Or add to Streamlit secrets (for deployment)

### Demo Mode Fallback

If no API key is configured:
- System runs in demo mode
- Basic pattern matching used (limited capability)
- Consider adding API key for production use

## Usage Instructions

### Admin Upload Process

1. **Login as Admin**
   - Email: `admin@mockexamify.com`
   - Password: `admin123`

2. **Navigate to Upload Page**
   - Click "📤 Upload Mock" from admin panel

3. **Fill Exam Details**
   - Title: Descriptive exam name
   - Category: Programming, Math, Science, etc.
   - Price: Credits required (1-50)
   - Description: What the exam covers
   - Enable AI Explanations: Checkbox

4. **Upload Document**
   - Click file uploader
   - Select PDF or Word document
   - Wait for AI extraction (may take 10-30 seconds)

5. **Preview Questions**
   - Review extracted questions
   - Check choices and correct answers
   - Verify question count

6. **Create Exam**
   - Click "🚀 Create Mock Exam"
   - System saves to database
   - Ready for students!

## Example Document Structure

### Simple Format
```
1. What is 2 + 2?
   a. 3
   b. 4 ✓
   c. 5
   d. 6

2. What is the capital of Japan?
   A. Seoul
   B. Beijing
   C. Tokyo ✓
   D. Bangkok
```

### Detailed Format
```
SCENARIO: Basic Python Programming

Question 1: What is the output of print("Hello" + "World")?
Choices:
A. Hello World
B. HelloWorld ← CORRECT
C. Hello+World
D. Error

Explanation Hint: String concatenation in Python joins strings without spaces.

---

SCENARIO: Database Concepts

Question 2: Which SQL command retrieves data?
A. INSERT
B. UPDATE
C. DELETE
D. SELECT ← CORRECT

Note: SELECT is used to query and retrieve data from database tables.
```

### Complex Format with Context
```
EXAM SECTION: Object-Oriented Programming

Background: Consider the following Python class definition:

class Vehicle:
    def __init__(self, wheels):
        self.wheels = wheels

Q1. How many parameters does __init__ accept?
(A) 0
(B) 1
(C) 2 ← Answer
(D) 3

Reasoning: __init__ receives 'self' (implicit) and 'wheels' (explicit) = 2 total

---

Q2. What attribute does Vehicle have?
1. name
2. wheels ← Correct
3. speed
4. color
```

## Error Handling

### Common Issues

**"Could not extract sufficient text"**
- Document may be scanned image-based
- Try OCR tool first to convert to text
- Or manually create CSV/JSON

**"No questions could be extracted"**
- AI couldn't identify clear questions
- Check document formatting
- Ensure questions are clearly labeled

**"Questions did not pass validation"**
- Missing choices or correct answers
- Check each question has 2+ choices
- Verify correct answer is marked

### Troubleshooting

1. **Check file format**: Ensure it's .pdf, .docx, or .doc
2. **Review document structure**: Questions should be clearly formatted
3. **Verify API key**: Make sure OpenRouter key is configured
4. **Try traditional upload**: Use CSV/JSON if AI extraction fails

## API Costs

### OpenRouter Pricing

- Model used: `anthropic/claude-3-haiku`
- Cost: ~$0.00025 per question extracted
- Example: 50-question exam ≈ $0.01
- Very affordable for occasional use

### Rate Limits

- OpenRouter: 100 requests/minute (default)
- Sufficient for typical admin usage
- Contact OpenRouter to increase if needed

## Advanced Features

### Batch Upload

To upload multiple exams:
1. Create separate documents for each exam
2. Upload one at a time through admin panel
3. Or use CSV/JSON for bulk uploads

### Custom Extraction

For specialized formats:
1. Modify `document_parser.py`
2. Adjust AI prompt in `_create_extraction_prompt()`
3. Add custom parsing logic if needed

### Integration

The document parser can be used programmatically:

```python
from document_parser import document_parser

# Parse a file
success, questions, error = document_parser.parse_document(file)

if success:
    print(f"Extracted {len(questions)} questions")
    for q in questions:
        print(q['question'])
```

## Security Notes

- Files are processed in memory only
- No permanent storage of uploaded documents
- API calls go through HTTPS
- API key stored securely in environment variables

## Future Enhancements

Planned features:
- [ ] Support for image-based PDFs (OCR)
- [ ] Excel/spreadsheet upload
- [ ] Bulk document upload
- [ ] Question editing after extraction
- [ ] Custom extraction templates
- [ ] Multi-language support

## Support

For issues or questions:
- Check error messages in the UI
- Review logs for detailed error info
- Contact: support@mockexamify.com

---

**Last Updated**: 2025-10-15
**Version**: 1.0.0
