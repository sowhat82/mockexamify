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

        # Check required fields
        required_fields = ['question_text', 'choices', 'correct_answer']
        for field in required_fields:
            if field not in normalized or normalized[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, errors

        # Validate choices
        choices = question['choices']
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
        correct_index = question['correct_answer']
        if not isinstance(correct_index, int):
            errors.append(f"correct_answer must be an integer, got {type(correct_index)}")
        elif correct_index < 0 or correct_index >= len(choices):
            errors.append(f"correct_answer index {correct_index} out of range (0-{len(choices)-1})")

        # Validate explanation if present
        if 'explanation' in question and question['explanation']:
            explanation_errors = QuestionValidator._validate_explanation(
                question['explanation'],
                choices,
                correct_index
            )
            errors.extend(explanation_errors)

        return len(errors) == 0, errors

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
