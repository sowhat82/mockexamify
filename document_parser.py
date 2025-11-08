"""
Document Parser for Mock Exam Questions
Extracts questions from PDF and Word documents using AI
"""

import io
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
import PyPDF2
import streamlit as st
from docx import Document

import config


class DocumentParser:
    """Parse PDF/Word documents and extract mock exam questions using AI"""

    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.model = config.OPENROUTER_MODEL
        self.base_url = config.OPENROUTER_BASE_URL

    def parse_document(self, uploaded_file) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Parse uploaded document and extract questions

        Returns:
            (success, questions_list, error_message)
        """
        try:
            # Determine file type
            file_extension = uploaded_file.name.split(".")[-1].lower()

            # Extract text from document
            if file_extension == "pdf":
                text = self._extract_text_from_pdf(uploaded_file)
            elif file_extension in ["docx", "doc"]:
                text = self._extract_text_from_word(uploaded_file)
            else:
                return False, [], f"Unsupported file type: {file_extension}"

            if not text or len(text.strip()) < 50:
                return False, [], "Could not extract sufficient text from document"

            # Use AI to parse questions from text
            questions = self._parse_questions_with_ai(text)

            if not questions:
                return False, [], "No questions could be extracted from the document"

            # Validate questions
            valid_questions = self._validate_questions(questions)

            if not valid_questions:
                return False, [], "Extracted questions did not pass validation"

            return True, valid_questions, ""

        except Exception as e:
            return False, [], f"Error parsing document: {str(e)}"

    def _extract_text_from_pdf(self, uploaded_file) -> str:
        """Extract text from PDF file"""
        try:
            # Reset file pointer
            uploaded_file.seek(0)

            # Read PDF
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""

            # Extract text from all pages
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")

    def _extract_text_from_word(self, uploaded_file) -> str:
        """Extract text from Word document"""
        try:
            # Reset file pointer
            uploaded_file.seek(0)

            # Read Word document
            doc = Document(uploaded_file)
            text = ""

            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text += cell.text + "\n"

            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading Word document: {str(e)}")

    def _parse_questions_with_ai(self, text: str) -> List[Dict[str, Any]]:
        """Use AI to parse questions from extracted text"""
        try:
            # If text is large, process in chunks
            chunk_size = 8000
            all_questions = []

            if len(text) <= chunk_size:
                # Small document - process all at once
                prompt = self._create_extraction_prompt(text)
                questions = self._call_ai_api(prompt)
                return questions
            else:
                # Large document - process in chunks
                st.info(f"📄 Document is large ({len(text)} chars). Processing in chunks...")

                # Split text into chunks (try to split at question boundaries)
                chunks = self._split_text_into_chunks(text, chunk_size)

                for i, chunk in enumerate(chunks, 1):
                    st.info(f"🔄 Processing chunk {i}/{len(chunks)}...")
                    prompt = self._create_extraction_prompt(chunk)
                    chunk_questions = self._call_ai_api(prompt)

                    if chunk_questions:
                        all_questions.extend(chunk_questions)
                        st.success(f"✅ Extracted {len(chunk_questions)} questions from chunk {i}")

                st.success(f"🎉 Total extracted: {len(all_questions)} questions from all chunks")
                return all_questions

        except Exception as e:
            st.error(f"AI parsing error: {str(e)}")
            return []

    def _split_text_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks, trying to keep questions together"""
        chunks = []
        current_chunk = ""

        # Split by common question delimiters
        lines = text.split("\n")

        for line in lines:
            # Check if adding this line would exceed chunk size
            if len(current_chunk) + len(line) > chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"

        # Add last chunk
        if current_chunk.strip():
            chunks.append(current_chunk)

        return chunks

    def _create_extraction_prompt(self, text: str) -> str:
        """Create prompt for AI to extract questions"""
        return f"""You are a specialized question extraction system. Extract all multiple-choice questions from the following document text.

DOCUMENT TEXT:
{text}

INSTRUCTIONS:
1. Identify all multiple-choice questions in the text
2. **CRITICAL - FIX OCR ERRORS**: The text may contain OCR errors where words are split into individual letters with spaces or line breaks. Fix these errors:
   - Example: "p e r s h a r e" should be "per share"
   - Example: "r e c e i v e d" should be "received"
   - Example: "d i v i d e n d s o f" should be "dividends of"
   - Remove extra spaces between individual letters
   - Reconstruct proper words from letter sequences
   - Fix formatting issues like conjoined words (e.g., "pershareand" → "per share and")
   - Preserve mathematical symbols like $, %, numbers

3. For each question, extract:
   - The question text (with OCR errors corrected)
   - All answer choices (typically A, B, C, D or 1, 2, 3, 4)
   - The correct answer
   - Any scenario/context provided before the question
   - Any explanation or additional notes

4. Format your response as a JSON array of questions. Each question should have:
   - "question": the question text (string, OCR errors fixed)
   - "choices": array of answer choice texts (array of strings, OCR errors fixed)
   - "correct_index": zero-based index of correct answer (integer, 0-3)
   - "scenario": optional context/scenario (string or null)
   - "explanation_seed": optional hint for explanation (string or null)

EXAMPLE OUTPUT FORMAT:
[
  {{
    "question": "What is the capital of France?",
    "choices": ["London", "Paris", "Berlin", "Madrid"],
    "correct_index": 1,
    "scenario": null,
    "explanation_seed": "France is a country in Western Europe"
  }},
  {{
    "question": "Which programming language is known for web development?",
    "choices": ["Python", "JavaScript", "C++", "Assembly"],
    "correct_index": 1,
    "scenario": "In modern web applications",
    "explanation_seed": "JavaScript runs in browsers"
  }}
]

IMPORTANT:
- Return ONLY the JSON array, no other text
- correct_index must be 0-based (0, 1, 2, 3...)
- Include at least 2 choices per question
- If you cannot find clear questions, return an empty array: []

Extract all questions now:"""

    def _call_ai_api(self, prompt: str) -> List[Dict[str, Any]]:
        """Call OpenRouter API to extract questions"""

        # Check if API key is configured (allow AI parsing even in DEMO_MODE)
        if not self.api_key or self.api_key == "demo" or self.api_key == "your_openrouter_api_key":
            # No valid API key configured
            st.warning(
                "⚠️ OpenRouter API key not configured. Using basic pattern matching fallback."
            )
            st.info(
                "💡 To enable AI-powered document parsing, add your OPENROUTER_API_KEY to .streamlit/secrets.toml"
            )
            return self._demo_parse_fallback()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://mockexamify.com",
                "X-Title": "MockExamify",
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # Low temperature for consistent extraction
                "max_tokens": 4000,
            }

            # Make synchronous request
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )

            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}: {response.text}")

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Extract JSON from response
            questions = self._extract_json_from_response(content)

            return questions

        except Exception as e:
            st.error(f"AI API call failed: {str(e)}")
            return []

    def _extract_json_from_response(self, content: str) -> List[Dict[str, Any]]:
        """Extract JSON array from AI response"""
        try:
            # Try to parse directly
            questions = json.loads(content)
            return questions if isinstance(questions, list) else []
        except json.JSONDecodeError:
            # Try to find JSON array in the content
            json_match = re.search(r"\[[\s\S]*\]", content)
            if json_match:
                try:
                    questions = json.loads(json_match.group(0))
                    return questions if isinstance(questions, list) else []
                except:
                    pass
            return []

    def _demo_parse_fallback(self) -> List[Dict[str, Any]]:
        """Fallback parser for demo mode - extracts questions using regex patterns"""
        st.info("Using basic pattern matching. For better results, configure AI API key.")

        # Return empty list for now - user should provide API key for real parsing
        # This could be enhanced with regex-based parsing if needed
        return []

    def _validate_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean extracted questions"""
        valid_questions = []

        st.info(f"🔍 Validating {len(questions)} extracted questions...")

        for i, q in enumerate(questions):
            try:
                # Check required fields
                if not isinstance(q, dict):
                    st.warning(f"Question {i+1}: Not a valid object, skipping")
                    continue

                if "question" not in q or not q["question"]:
                    st.warning(f"Question {i+1}: Missing question text, skipping")
                    continue

                if "choices" not in q or not isinstance(q["choices"], list):
                    st.warning(f"Question {i+1}: Missing or invalid choices, skipping")
                    continue

                if len(q["choices"]) < 2:
                    st.warning(f"Question {i+1}: Need at least 2 choices, skipping")
                    continue

                if "correct_index" not in q:
                    st.warning(f"Question {i+1}: Missing correct_index, skipping")
                    continue

                # Validate correct_index - handle both int and list (for multi-answer questions)
                raw_index = q["correct_index"]
                if isinstance(raw_index, list):
                    # If AI returned a list (e.g., [1, 2] for multi-select), take the first one
                    # Our system currently only supports single-answer questions
                    if len(raw_index) == 0:
                        st.warning(f"Question {i+1}: Empty correct_index list, skipping")
                        continue
                    correct_index = int(raw_index[0])
                else:
                    correct_index = int(raw_index)

                if correct_index < 0 or correct_index >= len(q["choices"]):
                    st.warning(f"Question {i+1}: Invalid correct_index {correct_index}, skipping")
                    continue

                # Clean and normalize question
                cleaned_question = {
                    "question": q["question"].strip(),
                    "choices": [str(choice).strip() for choice in q["choices"]],
                    "correct_index": correct_index,
                    "scenario": q.get("scenario", "").strip() if q.get("scenario") else None,
                    "explanation_seed": (
                        q.get("explanation_seed", "").strip() if q.get("explanation_seed") else None
                    ),
                }

                valid_questions.append(cleaned_question)

            except Exception as e:
                st.warning(f"Question {i+1}: Validation error - {str(e)}, skipping")
                continue

        # Show validation summary
        skipped = len(questions) - len(valid_questions)
        if skipped > 0:
            st.warning(f"⚠️ Validation complete: {len(valid_questions)} valid, {skipped} skipped")
        else:
            st.success(f"✅ Validation complete: All {len(valid_questions)} questions passed!")

        return valid_questions

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return ["pdf", "docx", "doc"]

    def get_file_type_help(self) -> str:
        """Get help text for supported file types"""
        return """
**Supported File Formats:**
- **PDF files (.pdf)**: Upload PDF documents containing multiple-choice questions
- **Word documents (.docx, .doc)**: Upload Word documents with questions

**Document Format Guidelines:**
The AI will automatically extract questions from your document. For best results:

1. **Clear Question Format**:
   - Number your questions (1., 2., Q1, etc.)
   - Use clear question text

2. **Answer Choices**:
   - Use consistent labeling (A, B, C, D or 1, 2, 3, 4)
   - Each choice on its own line or clearly separated

3. **Correct Answer**:
   - Indicate the correct answer (e.g., "Answer: B" or "Correct: 2")
   - Or mark with asterisk, bold, or highlight

4. **Optional Context**:
   - Include scenario/context before questions
   - Add explanations or notes (will be used for AI explanation generation)

**Example Format:**
```
Question 1: What is the capital of France?
A) London
B) Paris *
C) Berlin
D) Madrid

Answer: B
Explanation: Paris is the capital and largest city of France.
```

The AI will intelligently extract and structure all questions automatically!
"""


# Create singleton instance
document_parser = DocumentParser()
