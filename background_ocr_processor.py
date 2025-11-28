"""
Background OCR Processor
Processes scanned PDFs in the background to avoid UI timeouts
"""
import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_ocr_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Patterns that indicate missing context
INCOMPLETE_PATTERNS = [
    r'^The basis of which',
    r'^This product',
    r'^According to the case study',
    r'^Based on the scenario',
    r'^In the example',
    r'^The product described',
    r'^Under this arrangement',
    r'^For this investment',
    r'^In this case',
    r'^The structure outlined',
    r'^The instrument mentioned',
    r'basis.*mandatory\s*redemption.*determined',
    r'payout.*maturity.*determined by the\s*$',
    r'determined by the\s*Choices',
    r'^Referring to',
    r'^For the',
    r'^With reference to',
]


def detect_incomplete_question(question_text: str) -> Optional[str]:
    """
    Detect if a question references missing context.
    Returns the reason if incomplete, None if complete.
    """
    question_text = question_text.strip()

    # Check against patterns
    for pattern in INCOMPLETE_PATTERNS:
        if re.search(pattern, question_text, re.IGNORECASE):
            return f"Matches pattern: {pattern}"

    # Check if question starts with article + noun without context
    if re.match(r'^The\s+\w+\s+(of|for|in)\s+which', question_text, re.IGNORECASE):
        return "Starts with 'The X of/for/in which' pattern"

    # Check for references to "this/that product/fund/instrument" without context
    if re.search(r'\b(this|that)\s+(fund|product|instrument|security|option|structure)\b', question_text, re.IGNORECASE):
        return "References 'this/that fund/product/instrument' without context"

    return None


async def attempt_heal_question(question: Dict, full_text: str, question_index: int) -> Tuple[bool, Optional[Dict]]:
    """
    Attempt to heal an incomplete question by finding and merging context from the full OCR text.

    Returns:
        (success, healed_question) - success is True if healing worked, healed_question contains the updated question
    """
    try:
        from openrouter_utils import OpenRouterManager

        question_text = question.get("question", "")

        # Extract a window of text around where this question likely appears
        # This is a heuristic - we'll look for the question text in the full OCR output
        text_lower = full_text.lower()
        question_lower = question_text.lower()[:50]  # Use first 50 chars to find location

        position = text_lower.find(question_lower)

        if position == -1:
            logger.warning(f"Could not locate question in OCR text for healing")
            return False, None

        # Extract 1000 characters before the question as potential context
        start_pos = max(0, position - 1000)
        context_window = full_text[start_pos:position + len(question_text) + 200]

        # Use AI to heal the question
        prompt = f"""You are helping fix an incomplete exam question that references missing context.

The question text is:
"{question_text}"

The surrounding text from the document (which may contain case studies, product descriptions, or other context) is:
{context_window}

Task: If you can find relevant context (case study, product description, scenario) in the surrounding text that this question refers to, rewrite the question to be self-contained by incorporating that context. If no clear context exists, return "CANNOT_HEAL".

Return ONLY the rewritten question text, or "CANNOT_HEAL". Do not add explanations or commentary.

Example:
- Original: "What is the share of participation of this fund"
- If context mentions "Fund X with 80% participation", return: "What is the share of participation of Fund X that provides 80% equity exposure"

Rewritten question:"""

        manager = OpenRouterManager()
        response = await manager.generate_text(prompt, max_tokens=500)

        healed_text = response.strip()

        if healed_text == "CANNOT_HEAL" or len(healed_text) < 10:
            logger.info(f"Question {question_index}: Could not heal - no clear context found")
            return False, None

        # Create healed question
        healed_question = question.copy()
        healed_question["question"] = healed_text
        healed_question["was_healed"] = True
        healed_question["original_question"] = question_text

        logger.info(f"Question {question_index}: Successfully healed")
        logger.debug(f"  Original: {question_text[:80]}...")
        logger.debug(f"  Healed: {healed_text[:80]}...")

        return True, healed_question

    except Exception as e:
        logger.error(f"Error healing question: {e}")
        return False, None


async def process_scanned_pdf(file_path: str, pool_id: str, pool_name: str, source_filename: str):
    """
    Process a scanned PDF with OCR in the background

    Args:
        file_path: Path to the saved PDF file
        pool_id: ID of the pool to add questions to
        pool_name: Name of the pool
        source_filename: Original filename
    """
    from db import db
    from document_parser import DocumentParser

    logger.info(f"Starting background OCR processing for: {source_filename}")
    logger.info(f"Pool: {pool_name} (ID: {pool_id})")

    try:
        # Read the file
        with open(file_path, 'rb') as f:
            file_bytes = f.read()

        logger.info(f"File loaded: {len(file_bytes)} bytes")

        # Initialize parser
        parser = DocumentParser()

        # Extract text using OCR (no page limit for background processing)
        logger.info("Starting OCR extraction...")
        import fitz
        import easyocr
        import numpy as np
        from PIL import Image

        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = len(pdf_doc)
        logger.info(f"PDF has {total_pages} pages - processing all pages in background")

        # Initialize EasyOCR reader
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)

        all_text = []

        for i in range(total_pages):
            page = pdf_doc[i]

            logger.info(f"OCR processing page {i+1}/{total_pages}...")

            # Render page to image (150 DPI)
            mat = fitz.Matrix(150 / 72, 150 / 72)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image then numpy array
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_array = np.array(img)

            # Run OCR
            try:
                results = reader.readtext(
                    img_array,
                    paragraph=True,
                    batch_size=4
                )
                page_text = "\n".join([result[1] for result in results])
                all_text.append(page_text)

                # Log progress every 5 pages
                if (i + 1) % 5 == 0:
                    logger.info(f"Progress: {i+1}/{total_pages} pages completed")

            except Exception as e:
                logger.error(f"OCR failed on page {i+1}: {e}")
                continue

        pdf_doc.close()

        combined_text = "\n\n".join(all_text)
        logger.info(f"OCR completed: {len(combined_text)} characters extracted from {total_pages} pages")

        if not combined_text or len(combined_text) < 100:
            logger.error("OCR did not extract sufficient text")
            return

        # Parse questions from extracted text
        logger.info("Parsing questions from extracted text...")
        questions = parser._parse_questions_with_ai(combined_text)

        if not questions:
            logger.error("No questions could be extracted from OCR text")
            return

        logger.info(f"Extracted {len(questions)} questions")

        # Validate and filter questions
        valid_questions = []
        invalid_count = 0
        healed_count = 0
        incomplete_skipped = 0

        for idx, q in enumerate(questions, 1):
            # Check if question has all required fields
            if not q.get("question") or not isinstance(q.get("choices"), list):
                logger.warning(f"Question {idx} missing question text or choices - skipping")
                invalid_count += 1
                continue

            # Check if choices is not empty
            if len(q["choices"]) == 0:
                logger.warning(f"Question {idx} has empty choices array - skipping")
                invalid_count += 1
                continue

            # Check if correct_index is valid
            if not isinstance(q.get("correct_index"), int):
                logger.warning(f"Question {idx} missing or invalid correct_index - skipping")
                invalid_count += 1
                continue

            if q["correct_index"] < 0 or q["correct_index"] >= len(q["choices"]):
                logger.warning(f"Question {idx} has correct_index {q['correct_index']} out of range for {len(q['choices'])} choices - skipping")
                invalid_count += 1
                continue

            # Check for incomplete questions (missing context)
            question_text = q.get("question", "")
            incomplete_reason = detect_incomplete_question(question_text)

            if incomplete_reason:
                logger.info(f"Question {idx}: Detected incomplete - {incomplete_reason}")
                logger.info(f"  Attempting to heal question...")

                # Try to heal the question
                success, healed_q = await attempt_heal_question(q, combined_text, idx)

                if success and healed_q:
                    # Use the healed question
                    q = healed_q
                    healed_count += 1
                    logger.info(f"Question {idx}: ✅ Successfully healed")
                else:
                    # Could not heal - skip this question
                    logger.warning(f"Question {idx}: ❌ Could not heal - skipping")
                    incomplete_skipped += 1
                    continue

            # Question is valid (or was successfully healed)
            q["source_file"] = source_filename
            valid_questions.append(q)

        logger.info(f"Validation complete: {len(valid_questions)} valid, {invalid_count} invalid, {healed_count} healed, {incomplete_skipped} incomplete (skipped)")

        if not valid_questions:
            logger.error("No valid questions after validation")
            return

        # Add questions to pool
        logger.info(f"Adding {len(valid_questions)} valid questions to pool {pool_name}...")

        success = await db.add_questions_to_pool(
            pool_id=pool_id,
            questions=valid_questions,
            source_file=source_filename,
            batch_id=None
        )

        if success:
            logger.info(f"✅ Successfully added {len(valid_questions)} questions to pool {pool_name}")
        else:
            logger.error(f"❌ Failed to add questions to pool")

        # Clean up temporary file
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not delete temporary file: {e}")

        logger.info("Background OCR processing complete!")

    except Exception as e:
        logger.error(f"Fatal error in background OCR processing: {e}", exc_info=True)


async def main():
    """Main entry point for background OCR processor"""
    if len(sys.argv) < 5:
        logger.error("Usage: python background_ocr_processor.py <file_path> <pool_id> <pool_name> <source_filename>")
        sys.exit(1)

    file_path = sys.argv[1]
    pool_id = sys.argv[2]
    pool_name = sys.argv[3]
    source_filename = sys.argv[4]

    logger.info(f"Background OCR processor started")
    logger.info(f"File: {file_path}")
    logger.info(f"Pool: {pool_name} ({pool_id})")

    await process_scanned_pdf(file_path, pool_id, pool_name, source_filename)

    logger.info("Background OCR processor finished")


if __name__ == "__main__":
    asyncio.run(main())
