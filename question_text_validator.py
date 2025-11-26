"""
Question Text Validator and Auto-Fixer
Detects and automatically fixes common corruption issues in question text
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class QuestionTextValidator:
    """Validates and fixes corrupted question text"""

    # Auto-fix patterns: (pattern, replacement, description)
    AUTO_FIX_PATTERNS = [
        # Common OCR/parsing errors
        (r'\ba\*', 'at', 'Fixed: a* → at'),
        (r'\bir\s+trading\b', 'is trading', 'Fixed: ir trading → is trading'),
        (r'\bir\s+', 'is ', 'Fixed: ir → is'),
        (r'\b(a|the|is|are)\s+r\s+(strategy|spread|option|fund|investment|portfolio|market|risk|return|account|security)', r'\1 \2', 'Fixed: removed single letter corruption'),

        # Multiple spaces
        (r'  +', ' ', 'Fixed: multiple spaces'),

        # Missing space after punctuation
        (r'([.!?])([A-Z])', r'\1 \2', 'Fixed: missing space after punctuation'),

        # Double punctuation (but not ellipsis ...)
        (r'([.!?])\1+', r'\1', 'Fixed: double punctuation'),
    ]

    # Warning patterns: (pattern, warning_message)
    WARNING_PATTERNS = [
        # Very short questions
        (lambda text: len(text.strip()) < 15, 'Question text is very short (< 15 chars)'),

        # Contains unusual characters (but exclude common ones)
        (lambda text: bool(re.search(r'[^\w\s.,!?;:()\[\]{}\'-‑%$€£¥]', text)),
         'Contains unusual characters'),
    ]

    @staticmethod
    def validate_and_fix_question(question_text: str) -> Tuple[str, List[str], List[str]]:
        """
        Validate and auto-fix question text

        Args:
            question_text: Original question text

        Returns:
            Tuple of (fixed_text, fixes_applied, warnings)
        """
        if not question_text or not isinstance(question_text, str):
            return question_text, [], ['Question text is empty or invalid']

        fixed_text = question_text
        fixes_applied = []
        warnings = []

        # Apply auto-fixes
        for pattern, replacement, description in QuestionTextValidator.AUTO_FIX_PATTERNS:
            new_text = re.sub(pattern, replacement, fixed_text)
            if new_text != fixed_text:
                fixes_applied.append(description)
                fixed_text = new_text

        # Check for warnings
        for check, warning_message in QuestionTextValidator.WARNING_PATTERNS:
            if callable(check):
                if check(fixed_text):
                    warnings.append(warning_message)
            else:
                if re.search(check, fixed_text):
                    warnings.append(warning_message)

        return fixed_text, fixes_applied, warnings

    @staticmethod
    def validate_and_fix_questions_batch(questions: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Validate and fix a batch of questions

        Args:
            questions: List of question dictionaries

        Returns:
            Tuple of (fixed_questions, stats)
        """
        stats = {
            'total': len(questions),
            'fixed': 0,
            'warnings': 0,
            'fixes_by_type': {},
            'questions_with_warnings': []
        }

        fixed_questions = []

        for q in questions:
            question_text = q.get('question', '') or q.get('question_text', '')

            if not question_text:
                warnings.append('Empty question text')
                stats['warnings'] += 1
                fixed_questions.append(q)
                continue

            # Validate and fix
            fixed_text, fixes_applied, warnings = QuestionTextValidator.validate_and_fix_question(
                question_text
            )

            # Update question with fixed text
            q_fixed = q.copy()
            if 'question' in q_fixed:
                q_fixed['question'] = fixed_text
            if 'question_text' in q_fixed:
                q_fixed['question_text'] = fixed_text

            # Track stats
            if fixes_applied:
                stats['fixed'] += 1
                for fix in fixes_applied:
                    stats['fixes_by_type'][fix] = stats['fixes_by_type'].get(fix, 0) + 1

            if warnings:
                stats['warnings'] += 1
                stats['questions_with_warnings'].append({
                    'text': fixed_text[:100] + '...' if len(fixed_text) > 100 else fixed_text,
                    'warnings': warnings
                })

            fixed_questions.append(q_fixed)

        return fixed_questions, stats

    @staticmethod
    def validate_choices(choices: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate and clean answer choices

        Args:
            choices: List of answer choice strings

        Returns:
            Tuple of (cleaned_choices, warnings)
        """
        if not choices or not isinstance(choices, list):
            return choices, ['Choices are empty or invalid']

        cleaned_choices = []
        warnings = []

        for i, choice in enumerate(choices):
            if not choice or (isinstance(choice, str) and not choice.strip()):
                warnings.append(f'Choice {i+1} is empty')
                cleaned_choices.append(choice)
                continue

            # Clean the choice
            cleaned = str(choice).strip()

            # Check for very short choices (possible truncation)
            if len(cleaned) < 2 and not cleaned.isdigit():
                warnings.append(f'Choice {i+1} is very short: "{cleaned}"')

            cleaned_choices.append(cleaned)

        # Check for duplicates
        non_empty = [c for c in cleaned_choices if c and c.strip()]
        if len(non_empty) != len(set(non_empty)):
            warnings.append('Duplicate choices detected')

        return cleaned_choices, warnings


def validate_question_batch(questions: List[Dict]) -> Dict:
    """
    Main entry point for validating a batch of questions

    Args:
        questions: List of question dictionaries with 'question' or 'question_text' and 'choices'

    Returns:
        Dictionary with validation results and statistics
    """
    validator = QuestionTextValidator()

    # Validate and fix question text
    fixed_questions, text_stats = validator.validate_and_fix_questions_batch(questions)

    # Validate choices for each question
    choice_warnings_count = 0
    for q in fixed_questions:
        choices = q.get('choices', [])
        if choices:
            cleaned_choices, choice_warnings = validator.validate_choices(choices)
            q['choices'] = cleaned_choices
            if choice_warnings:
                choice_warnings_count += 1

    return {
        'questions': fixed_questions,
        'stats': {
            **text_stats,
            'questions_with_choice_warnings': choice_warnings_count
        }
    }
