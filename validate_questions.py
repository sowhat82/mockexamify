#!/usr/bin/env python3
"""
Script to validate questions in the database and find potential issues:
1. Explanations that contradict the marked correct answer
2. Mathematical inconsistencies
3. Missing or malformed data
"""

import json
import re
from typing import List, Dict, Any
from db import db


def check_explanation_contradiction(question: Dict[str, Any]) -> List[str]:
    """Check if explanation contradicts the marked correct answer"""
    issues = []
    explanation = question.get('explanation', '')
    correct_index = question.get('correct_answer')

    if not explanation:
        return issues

    choices = question.get('choices', [])
    if isinstance(choices, str):
        choices = json.loads(choices)

    if correct_index is None or correct_index >= len(choices):
        issues.append("Invalid correct_answer index")
        return issues

    correct_choice = choices[correct_index]

    # Check for phrases that admit the answer is wrong
    warning_phrases = [
        "does not lead to this answer",
        "doesn't lead to this answer",
        "seems there was an oversight",
        "however, the direct calculation",
        "suggests a need for understanding",
        "might involve a different interpretation"
    ]

    for phrase in warning_phrases:
        if phrase.lower() in explanation.lower():
            issues.append(f"Explanation contains warning phrase: '{phrase}'")

    # Check if explanation mentions a different answer as correct
    # Look for patterns like "The correct answer is X" where X != marked answer
    pattern = r"(?:correct answer|right answer)(?:\s+is|\s*:)\s*([A-D]|[0-9]+X?)"
    matches = re.findall(pattern, explanation, re.IGNORECASE)

    for match in matches:
        # Convert letter to index
        if match.upper() in ['A', 'B', 'C', 'D']:
            mentioned_index = ord(match.upper()) - ord('A')
            if mentioned_index != correct_index:
                issues.append(f"Explanation says answer is {match.upper()} but marked as {chr(65 + correct_index)}")
        # Check for answer values mentioned
        elif match.upper() in correct_choice.upper():
            # This is okay - explanation mentions the correct value
            pass
        elif len(matches) > 0 and match not in correct_choice:
            # Mentioned answer doesn't match marked answer
            issues.append(f"Explanation mentions '{match}' which may contradict marked answer '{correct_choice}'")

    return issues


def check_mathematical_consistency(question: Dict[str, Any]) -> List[str]:
    """Check for basic mathematical consistency"""
    issues = []
    explanation = question.get('explanation', '')

    if not explanation:
        return issues

    # Look for calculations that are admitted to be wrong
    if "however" in explanation.lower() and "calculation" in explanation.lower():
        if "does not" in explanation.lower() or "doesn't" in explanation.lower():
            issues.append("Explanation admits calculation issues")

    # Look for multiple contradictory formulas
    formula_count = len(re.findall(r"formula[:\s]+", explanation, re.IGNORECASE))
    if formula_count > 2:
        issues.append(f"Multiple formulas mentioned ({formula_count}) - may indicate confusion")

    return issues


def check_data_quality(question: Dict[str, Any]) -> List[str]:
    """Check basic data quality"""
    issues = []

    # Check required fields
    if not question.get('question_text'):
        issues.append("Missing question text")

    if not question.get('choices'):
        issues.append("Missing choices")

    if question.get('correct_answer') is None:
        issues.append("Missing correct_answer")

    # Check choices format
    choices = question.get('choices', [])
    if isinstance(choices, str):
        try:
            choices = json.loads(choices)
        except:
            issues.append("Invalid JSON in choices")
            return issues

    if len(choices) < 2:
        issues.append(f"Only {len(choices)} choices (expected at least 2)")

    # Check if correct_answer is valid index
    correct_index = question.get('correct_answer')
    if correct_index is not None and correct_index >= len(choices):
        issues.append(f"correct_answer index {correct_index} out of range (only {len(choices)} choices)")

    return issues


def validate_all_questions():
    """Validate all questions in the database"""
    print("=" * 80)
    print("QUESTION VALIDATION REPORT")
    print("=" * 80)
    print()

    # Get all questions
    response = db.admin_client.table("pool_questions").select("*").execute()
    questions = response.data

    print(f"Total questions to validate: {len(questions)}\n")

    # Track statistics
    total_issues = 0
    questions_with_issues = 0
    issue_types = {
        'explanation_contradiction': 0,
        'math_inconsistency': 0,
        'data_quality': 0
    }

    problematic_questions = []

    for q in questions:
        question_issues = []

        # Run all checks
        contradiction_issues = check_explanation_contradiction(q)
        math_issues = check_mathematical_consistency(q)
        quality_issues = check_data_quality(q)

        if contradiction_issues:
            question_issues.extend([("CONTRADICTION", issue) for issue in contradiction_issues])
            issue_types['explanation_contradiction'] += len(contradiction_issues)

        if math_issues:
            question_issues.extend([("MATH", issue) for issue in math_issues])
            issue_types['math_inconsistency'] += len(math_issues)

        if quality_issues:
            question_issues.extend([("QUALITY", issue) for issue in quality_issues])
            issue_types['data_quality'] += len(quality_issues)

        if question_issues:
            questions_with_issues += 1
            total_issues += len(question_issues)
            problematic_questions.append((q, question_issues))

    # Print summary
    print("SUMMARY")
    print("-" * 80)
    print(f"Questions with issues: {questions_with_issues} / {len(questions)} ({questions_with_issues/len(questions)*100:.1f}%)")
    print(f"Total issues found: {total_issues}")
    print(f"\nIssue breakdown:")
    print(f"  - Explanation contradictions: {issue_types['explanation_contradiction']}")
    print(f"  - Math inconsistencies: {issue_types['math_inconsistency']}")
    print(f"  - Data quality issues: {issue_types['data_quality']}")
    print()

    # Print detailed report for problematic questions
    if problematic_questions:
        print("\nDETAILED REPORT")
        print("=" * 80)

        for q, issues in problematic_questions[:20]:  # Show first 20
            choices = q.get('choices', [])
            if isinstance(choices, str):
                choices = json.loads(choices)

            correct_index = q.get('correct_answer')
            correct_answer = choices[correct_index] if correct_index is not None and correct_index < len(choices) else "UNKNOWN"

            print(f"\nQuestion ID: {q['id']}")
            print(f"Pool ID: {q['pool_id']}")
            print(f"Question: {q['question_text'][:100]}...")
            print(f"Marked Answer: {chr(65 + correct_index) if correct_index is not None else 'NONE'}. {correct_answer}")
            print(f"Issues found: {len(issues)}")
            for issue_type, issue_desc in issues:
                print(f"  [{issue_type}] {issue_desc}")
            print("-" * 80)

        if len(problematic_questions) > 20:
            print(f"\n... and {len(problematic_questions) - 20} more questions with issues")

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)

    return problematic_questions


if __name__ == "__main__":
    validate_all_questions()
