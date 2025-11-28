"""
Background OCR Processor
Processes scanned PDFs in the background to avoid UI timeouts
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

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

            # Question is valid
            q["source_file"] = source_filename
            valid_questions.append(q)

        logger.info(f"Validation complete: {len(valid_questions)} valid, {invalid_count} invalid (skipped)")

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
