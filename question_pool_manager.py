"""
Question Pool Manager for MockExamify
Handles question bank storage, AI-powered duplicate detection, and pool management
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from openrouter_utils import OpenRouterManager

logger = logging.getLogger(__name__)


class QuestionPoolManager:
    """
    Manages question pools with automatic duplicate detection
    Admin can upload multiple files to same pool - system handles merging
    Uses AI to detect semantic duplicates beyond exact text matching
    """

    def __init__(self):
        self.ai = OpenRouterManager()
        self.similarity_threshold = 0.95  # 95% similarity = duplicate

    def calculate_question_hash(self, question: Dict[str, Any]) -> str:
        """
        Calculate unique hash for a question based on its content
        Used for exact duplicate detection
        """
        # Normalize question text (lowercase, strip whitespace)
        q_text = question.get("question", "").lower().strip()

        # Normalize choices (lowercase, strip whitespace, sort)
        choices = [c.lower().strip() for c in question.get("choices", [])]
        choices_str = "|".join(sorted(choices))

        # Create hash from question + choices
        hash_content = f"{q_text}|{choices_str}"
        return hashlib.md5(hash_content.encode(), usedforsecurity=False).hexdigest()

    def detect_exact_duplicates(
        self, new_questions: List[Dict[str, Any]], existing_questions: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Detect exact duplicates between new and existing questions

        Returns:
            (unique_questions, duplicate_questions)
        """
        # Build hash map of existing questions
        existing_hashes = {}
        for q in existing_questions:
            q_hash = self.calculate_question_hash(q)
            existing_hashes[q_hash] = q

        unique_questions = []
        duplicate_questions = []

        for new_q in new_questions:
            new_hash = self.calculate_question_hash(new_q)

            if new_hash in existing_hashes:
                # Exact duplicate found
                duplicate_questions.append(new_q)
            else:
                # Unique question
                unique_questions.append(new_q)
                # Add to existing hashes to check for duplicates within new batch
                existing_hashes[new_hash] = new_q

        return unique_questions, duplicate_questions

    async def detect_similar_questions_with_ai(
        self,
        new_question: Dict[str, Any],
        existing_questions: List[Dict[str, Any]],
        threshold: float = 0.90,
    ) -> Tuple[List[Tuple[Dict[str, Any], float]], Optional[str]]:
        """
        Use AI to detect semantically similar questions
        Returns (list of (question, similarity_score) tuples above threshold, error_message)
        error_message is None on success, or a string describing the error
        """
        try:
            similar_questions = []

            # For efficiency, only check against random sample if too many questions
            sample_size = min(len(existing_questions), 50)
            import random

            questions_to_check = (
                random.sample(existing_questions, sample_size)
                if len(existing_questions) > sample_size
                else existing_questions
            )

            for existing_q in questions_to_check:
                similarity, error = await self._calculate_semantic_similarity(
                    new_question, existing_q
                )

                # If we hit a rate limit or error, propagate it up
                if error:
                    if "rate limit" in error.lower() or "429" in error:
                        return [], error
                    # For other errors, log but continue
                    logger.warning(f"Error calculating similarity (continuing): {error}")
                    continue

                if similarity >= threshold:
                    similar_questions.append((existing_q, similarity))

            # Sort by similarity descending
            similar_questions.sort(key=lambda x: x[1], reverse=True)

            return similar_questions, None

        except Exception as e:
            error_msg = f"Error detecting similar questions with AI: {e}"
            logger.error(error_msg)
            return [], error_msg

    async def _calculate_semantic_similarity(
        self, q1: Dict[str, Any], q2: Dict[str, Any]
    ) -> Tuple[float, Optional[str]]:
        """
        Use AI to calculate semantic similarity between two questions
        Returns (score from 0.0 to 1.0, error_message)
        error_message is None on success, or a string describing the error
        """
        try:
            prompt = f"""Compare these two exam questions and rate their similarity from 0.0 to 1.0.

Consider:
- Same topic/concept being tested
- Similar question structure
- Overlapping answer choices
- Different wording but same intent

Question 1:
{q1.get('question')}
Choices: {', '.join(q1.get('choices', []))}

Question 2:
{q2.get('question')}
Choices: {', '.join(q2.get('choices', []))}

Respond with ONLY a number between 0.0 and 1.0, nothing else.
Examples:
- Exact same: 1.0
- Very similar (rewording): 0.9-0.95
- Same topic, different angle: 0.7-0.85
- Related topics: 0.5-0.7
- Unrelated: 0.0-0.3
"""

            # Use OpenRouterManager with cascading model fallback
            response = await self.ai._generate_text(prompt, max_tokens=10, temperature=0.1)

            if response and not response.startswith("Error:"):
                # Extract number from response
                try:
                    # Clean the response (remove any extra text)
                    content = response.strip()
                    similarity = float(content)
                    return max(0.0, min(1.0, similarity)), None  # Clamp between 0 and 1
                except ValueError:
                    logger.warning(f"Could not parse similarity score: {response}")
                    return 0.0, None
            else:
                # Check if it's a rate limit error
                if response and ("rate limit" in response.lower() or "429" in response):
                    return 0.0, response
                logger.warning(f"AI returned error: {response}")
                return 0.0, None

        except Exception as e:
            error_msg = f"Error calculating similarity: {e}"
            logger.error(error_msg)
            return 0.0, error_msg

    def merge_questions_to_pool(
        self,
        pool_name: str,
        new_questions: List[Dict[str, Any]],
        existing_pool: Optional[List[Dict[str, Any]]] = None,
        skip_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """
        Merge new questions into existing question pool

        Args:
            pool_name: Name of the question pool
            new_questions: New questions to add
            existing_pool: Existing questions in the pool (if any)
            skip_duplicates: If True, skip exact duplicates

        Returns:
            {
                'pool_name': str,
                'total_questions': int,
                'added_questions': int,
                'skipped_duplicates': int,
                'merged_pool': List[Dict],
                'duplicate_info': List[Dict]
            }
        """
        if existing_pool is None:
            existing_pool = []

        # Detect exact duplicates
        unique_questions, duplicate_questions = self.detect_exact_duplicates(
            new_questions, existing_pool
        )

        # Add metadata to new questions
        timestamp = datetime.now(timezone.utc).isoformat()
        for q in unique_questions:
            q["pool_name"] = pool_name
            q["added_at"] = timestamp
            q["question_hash"] = self.calculate_question_hash(q)

        # Merge pools
        merged_pool = existing_pool + unique_questions

        return {
            "pool_name": pool_name,
            "total_questions": len(merged_pool),
            "added_questions": len(unique_questions),
            "skipped_duplicates": len(duplicate_questions),
            "merged_pool": merged_pool,
            "duplicate_info": [
                {
                    "question": d.get("question", "")[:100] + "...",
                    "reason": "Exact duplicate (same question text and choices)",
                }
                for d in duplicate_questions
            ],
        }

    def get_pool_statistics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about a question pool"""
        if not questions:
            return {
                "total_questions": 0,
                "unique_questions": 0,
                "categories": {},
                "difficulties": {},
                "date_range": None,
            }

        # Count categories
        categories = {}
        for q in questions:
            cat = q.get("category", "Uncategorized")
            categories[cat] = categories.get(cat, 0) + 1

        # Count difficulties
        difficulties = {}
        for q in questions:
            diff = q.get("difficulty", "medium")
            difficulties[diff] = difficulties.get(diff, 0) + 1

        # Get date range
        dates = [q.get("added_at") for q in questions if q.get("added_at")]
        date_range = None
        if dates:
            dates.sort()
            date_range = {"earliest": dates[0], "latest": dates[-1]}

        return {
            "total_questions": len(questions),
            "unique_questions": len(set(self.calculate_question_hash(q) for q in questions)),
            "categories": categories,
            "difficulties": difficulties,
            "date_range": date_range,
        }

    def organize_by_upload_batch(
        self, questions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group questions by upload date/batch"""
        batches = {}

        for q in questions:
            added_at = q.get("added_at", "Unknown")
            if added_at not in batches:
                batches[added_at] = []
            batches[added_at].append(q)

        return batches

    def create_pool_name_from_filename(self, filename: str) -> str:
        """
        Extract pool name from filename
        Examples:
          "CACS2-Paper2-V1.pdf" -> "CACS2 Paper 2"
          "Python-Basics-2024.docx" -> "Python Basics"
          "math_exam_v3.pdf" -> "Math Exam"
        """
        import re

        # Remove extension
        name = filename.rsplit(".", 1)[0]

        # Remove version indicators
        name = re.sub(r"[_-]?[vV]\d+$", "", name)
        name = re.sub(r"[_-]?\d{4}$", "", name)  # Remove year

        # Replace separators with spaces
        name = name.replace("_", " ").replace("-", " ")

        # Capitalize words
        name = " ".join(word.capitalize() for word in name.split())

        return name.strip()


# Global instance
question_pool_manager = QuestionPoolManager()
