"""
Question validation module for validating questions before uploading to database.
Can be imported and used by upload scripts.
"""

import json
import re
from typing import List, Dict, Any, Tuple


class QuestionValidator:
    """Validates question data before database insertion"""

    @staticmethod
    def validate_question(question: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single question.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Normalize field names - support both upload format and database format
        normalized = {}
        if 'question' in question:
            normalized['question_text'] = question['question']
        elif 'question_text' in question:
            normalized['question_text'] = question['question_text']

        if 'correct_index' in question:
            normalized['correct_answer'] = question['correct_index']
        elif 'correct_answer' in question:
            normalized['correct_answer'] = question['correct_answer']

        normalized['choices'] = question.get('choices')
        normalized['explanation'] = question.get('explanation')
        normalized['scenario'] = question.get('scenario', '')

        # Check required fields
        required_fields = ['question_text', 'choices', 'correct_answer']
        for field in required_fields:
            if field not in normalized or normalized[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, errors

        # Validate choices
        choices = normalized['choices']
        if isinstance(choices, str):
            try:
                choices = json.loads(choices)
            except json.JSONDecodeError:
                errors.append("Invalid JSON in choices field")
                return False, errors

        if not isinstance(choices, list):
            errors.append("Choices must be a list")
            return False, errors

        if len(choices) < 2:
            errors.append(f"Must have at least 2 choices, found {len(choices)}")

        # Validate correct_answer index
        correct_index = normalized['correct_answer']
        if not isinstance(correct_index, int):
            errors.append(f"correct_answer must be an integer, got {type(correct_index)}")
        elif correct_index < 0 or correct_index >= len(choices):
            errors.append(f"correct_answer index {correct_index} out of range (0-{len(choices)-1})")

        # Validate question text for missing context
        question_text_errors = QuestionValidator._validate_question_text(
            normalized['question_text'],
            normalized['scenario']
        )
        errors.extend(question_text_errors)

        # Validate explanation if present
        if 'explanation' in question and question['explanation']:
            explanation_errors = QuestionValidator._validate_explanation(
                question['explanation'],
                choices,
                correct_index
            )
            errors.extend(explanation_errors)

        # Only fail if there are CRITICAL errors (not just warnings)
        has_critical_errors = any('CRITICAL' in err for err in errors)
        return not has_critical_errors, errors

    @staticmethod
    def _validate_question_text(question_text: str, scenario: str = '') -> List[str]:
        """
        Validate the question text for missing context issues

        Args:
            question_text: The question text to validate
            scenario: Optional scenario/context. If provided and substantial, some checks are skipped.
        """
        errors = []

        q_lower = question_text.lower()
        has_adequate_scenario = scenario and len(scenario.strip()) >= 50

        # Pattern 1: "Given the following information/details" without actual data
        if 'given the following' in q_lower or 'using the following' in q_lower:
            # Check if question is too short and lacks numbers/data
            has_numbers = any(c.isdigit() for c in question_text)
            if not has_numbers or len(question_text) < 100:
                errors.append(
                    "CRITICAL: Question says 'given the following' but doesn't provide the data. "
                    "Either include the data or rephrase the question."
                )

        # Pattern 2: "Evaluate/Consider the following statements" without statements
        if ('evaluate the following' in q_lower or 'consider the following' in q_lower) and 'statement' in q_lower:
            # Real statements would have numbers like "Statement 1" or "1." or "i."
            has_statements = any(pattern in question_text for pattern in [
                'Statement 1', 'statement 1', '1.', '2.', 'i.', 'ii.', 'iii.', 'I.', 'II.'
            ])
            if not has_statements:
                errors.append(
                    "CRITICAL: Question asks to evaluate statements but doesn't list them. "
                    "Include the actual statements in the question text."
                )

        # Pattern 3: "Based on the following" without context
        if 'based on the following' in q_lower and len(question_text) < 120:
            has_context = any(pattern in question_text for pattern in [':', ';', '\n', '•', '-'])
            if not has_context:
                errors.append(
                    "CRITICAL: Question says 'based on the following' but doesn't provide context. "
                    "Include the required information."
                )

        # Pattern 4: Removed - Questions ending with ':' are valid (e.g., "Which of the following:")

        # Pattern 5: Questions that reference specific people without adequate scenario
        # Look for questions asking "who did/didn't contravene/violate" or "who is/isn't guilty"
        if not has_adequate_scenario:
            # Common patterns in case study questions
            case_study_patterns = [
                (r'\b(?:contravened?|violat(?:ed?|ing))\s+(?:the\s+)?(?:insider\s+trading\s+act|sfa|securities\s+act)',
                 'references violations without case study'),
                (r'\b(?:is|are|was|were)\s+guilty\s+of\s+(?:insider\s+trading|market\s+manipulation)',
                 'references guilt determination without case study'),
                (r'\b(?:had|has)\s+(?:contravened?|violat(?:ed?|ing))',
                 'references past violations without context'),
            ]

            for pattern, reason in case_study_patterns:
                if re.search(pattern, q_lower):
                    # Check if the question also mentions multiple specific people (proper names)
                    # Common test names: Sally, Kelly, Denny, Mary, Bernard, Alfred, Harry, Jeff
                    # Also match "Director X" or "Mr/Ms X" patterns
                    name_pattern = r'\b(?:Sally|Kelly|Denny|Mary|Bernard|Alfred|Harry|Jeff|Director\s+\w+|Mr\.?\s+\w+|Ms\.?\s+\w+|TR\s+\w+)\b'
                    names_found = re.findall(name_pattern, question_text, re.IGNORECASE)

                    if len(names_found) >= 1:  # At least one person mentioned
                        errors.append(
                            f"CRITICAL: Question {reason} describing what each person did. "
                            f"Found references to: {', '.join(set(names_found))}. "
                            f"Either include a detailed scenario/case study in the 'scenario' field, "
                            f"or rewrite the question to be self-contained."
                        )
                        break  # Only report once

        return errors

    @staticmethod
    def _validate_explanation(explanation: str, choices: List[str], correct_index: int) -> List[str]:
        """Validate the explanation text for common issues"""
        errors = []

        # Check for red flag phrases that indicate the AI got confused
        warning_phrases = [
            ("does not lead to this answer", "Explanation admits answer doesn't match calculation"),
            ("doesn't lead to this answer", "Explanation admits answer doesn't match calculation"),
            ("seems there was an oversight", "Explanation indicates possible error"),
            ("however, the direct calculation", "Explanation contradicts itself"),
            ("suggests a need for understanding", "Vague explanation suggesting confusion"),
            ("might involve a different interpretation", "Explanation is uncertain about answer")
        ]

        for phrase, error_msg in warning_phrases:
            if phrase.lower() in explanation.lower():
                errors.append(f"CRITICAL: {error_msg}")

        # Check if explanation explicitly states a different answer
        # Look for "The correct answer is X" where X doesn't match
        pattern = r"(?:correct answer|right answer)(?:\s+is|\s*:)\s*([A-D])"
        matches = re.findall(pattern, explanation, re.IGNORECASE)

        for match in matches:
            mentioned_index = ord(match.upper()) - ord('A')
            if mentioned_index != correct_index:
                errors.append(
                    f"CRITICAL: Explanation says answer is {match.upper()} "
                    f"but correct_answer is set to {chr(65 + correct_index)}"
                )

        # Warn if explanation is suspiciously short or missing
        if len(explanation.strip()) < 50:
            errors.append("WARNING: Explanation is very short (< 50 chars)")

        return errors

    @staticmethod
    def validate_batch(questions: List[Dict[str, Any]], strict: bool = True) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate a batch of questions.

        Args:
            questions: List of question dictionaries
            strict: If True, reject questions with any errors. If False, only reject critical errors.

        Returns:
            Tuple of (valid_questions, rejected_questions_with_errors)
        """
        valid = []
        rejected = []

        for i, question in enumerate(questions):
            is_valid, errors = QuestionValidator.validate_question(question)

            if is_valid:
                valid.append(question)
            else:
                # Check if errors are critical
                has_critical = any('CRITICAL' in str(error) for error in errors)

                if strict or has_critical:
                    rejected.append({
                        'question': question,
                        'index': i,
                        'errors': errors
                    })
                else:
                    # Non-critical warnings - still accept
                    valid.append(question)

        return valid, rejected

    @staticmethod
    def print_validation_report(rejected: List[Dict]):
        """Print a formatted validation report for rejected questions"""
        if not rejected:
            print("✅ All questions passed validation!")
            return

        print(f"\n❌ {len(rejected)} question(s) failed validation:\n")
        print("=" * 80)

        for item in rejected:
            question = item['question']
            errors = item['errors']
            index = item['index']

            print(f"\nQuestion #{index + 1}")
            print(f"Text: {question.get('question_text', 'N/A')[:100]}...")
            print(f"Errors ({len(errors)}):")
            for error in errors:
                print(f"  • {error}")
            print("-" * 80)


def validate_question_file(filepath: str, strict: bool = True) -> bool:
    """
    Validate questions from a JSON file.

    Args:
        filepath: Path to JSON file containing questions
        strict: If True, reject questions with any errors

    Returns:
        True if all questions are valid, False otherwise
    """
    with open(filepath, 'r') as f:
        questions = json.load(f)

    if not isinstance(questions, list):
        print("❌ File must contain a JSON array of questions")
        return False

    print(f"Validating {len(questions)} questions from {filepath}...\n")

    valid, rejected = QuestionValidator.validate_batch(questions, strict=strict)

    print(f"✅ Valid questions: {len(valid)}")
    print(f"❌ Rejected questions: {len(rejected)}")

    if rejected:
        QuestionValidator.print_validation_report(rejected)
        return False

    print("\n✅ All questions passed validation!")
    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python question_validator.py <questions_file.json> [--strict]")
        sys.exit(1)

    filepath = sys.argv[1]
    strict = '--strict' in sys.argv

    success = validate_question_file(filepath, strict=strict)
    sys.exit(0 if success else 1)
