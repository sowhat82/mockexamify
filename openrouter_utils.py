"""
Enhanced OpenRouter API utilities for MockExamify
Comprehensive AI-powered content generation and explanations with caching and production features
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

import config
from models import DifficultyLevel, Question

logger = logging.getLogger(__name__)

# Simple in-memory cache for explanations and generation
_explanation_cache = {}
_generation_cache = {}
_cache_expiry = {}
CACHE_DURATION_HOURS = 24


class OpenRouterManager:
    """Enhanced manager for OpenRouter API interactions with advanced AI features"""

    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"

        # Load model cascade from models_config.json
        self.models = self._load_model_cascade()
        self.model = self.models[0] if self.models else "openai/gpt-4o-mini"
        self.fallback_model = self.models[1] if len(self.models) > 1 else "openai/gpt-4o-mini"
        self.budget_model = self.models[-1] if self.models else "openai/gpt-4o-mini"

        logger.info(f"Model cascade loaded: {len(self.models)} models")
        logger.info(f"Primary model: {self.model}")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mockexamify.streamlit.app",
            "X-Title": "MockExamify Production",
        }
        self.rate_limit_delay = 0.5  # Faster for production
        self.max_retries = len(self.models)  # Try all models in cascade
        self.batch_size = 5  # For bulk operations

    def _load_model_cascade(self) -> List[str]:
        """Load model priority list from models_config.json"""
        try:
            with open("models_config.json", "r") as f:
                config_data = json.load(f)
                models = config_data.get("models", [])
                if models:
                    logger.info(f"Loaded {len(models)} models from models_config.json")
                    return models
                else:
                    logger.warning("No models found in models_config.json, using defaults")
                    return ["openai/gpt-4o-mini"]
        except FileNotFoundError:
            logger.warning("models_config.json not found, using default model")
            return ["openai/gpt-4o-mini"]
        except Exception as e:
            logger.error(f"Error loading models_config.json: {e}")
            return ["openai/gpt-4o-mini"]

    async def generate_explanation(
        self,
        question: str,
        choices: List[str],
        correct_index: int,
        scenario: str = "",
        explanation_seed: str = "",
    ) -> str:
        """Generate detailed explanation for a single question with caching"""
        try:
            # Create cache key
            cache_key = self._create_cache_key(
                question, choices, correct_index, scenario, explanation_seed
            )

            # Check cache first
            cached_explanation = self._get_cached_explanation(cache_key)
            if cached_explanation:
                logger.info("Using cached explanation")
                return cached_explanation

            # Generate new explanation
            prompt = self._create_explanation_prompt(
                question, choices, correct_index, scenario, explanation_seed
            )

            explanation = await self._generate_text_with_retry(prompt)

            # Cache the result
            self._cache_explanation(cache_key, explanation)

            return explanation

        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return self._get_fallback_explanation(question, choices, correct_index)

    async def generate_batch_explanations(
        self, questions: List[Dict[str, Any]], user_answers: List[int]
    ) -> List[str]:
        """Generate explanations for multiple questions in batch with improved error handling"""
        explanations = []

        # Process in smaller batches to avoid rate limits
        batch_size = 2  # Reduced batch size for better reliability
        total_batches = (len(questions) + batch_size - 1) // batch_size

        for batch_num, i in enumerate(range(0, len(questions), batch_size)):
            batch = questions[i : i + batch_size]
            batch_answers = user_answers[i : i + batch_size]

            logger.info(f"Processing explanation batch {batch_num + 1}/{total_batches}")

            try:
                batch_explanations = await asyncio.gather(
                    *[
                        self.generate_explanation(
                            q["question"],
                            q.get("choices", []),
                            q.get("correct_index", 0),
                            q.get("scenario", ""),
                            q.get("explanation_seed", ""),
                        )
                        for q in batch
                    ],
                    return_exceptions=True,
                )

                # Handle exceptions in batch results
                for j, exp in enumerate(batch_explanations):
                    if isinstance(exp, Exception):
                        logger.error(f"Error generating explanation for question {i + j}: {exp}")
                        question = batch[j]
                        fallback = self._get_fallback_explanation(
                            question["question"],
                            question.get("choices", []),
                            question.get("correct_index", 0),
                        )
                        explanations.append(fallback)
                    else:
                        explanations.append(exp)

                # Add delay between batches to respect rate limits
                if i + batch_size < len(questions):
                    await asyncio.sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                # Add fallback explanations for the entire batch
                for q in batch:
                    fallback = self._get_fallback_explanation(
                        q["question"], q.get("choices", []), q.get("correct_index", 0)
                    )
                    explanations.append(fallback)

        return explanations

    async def generate_mock_exam(
        self, topic: str, difficulty: str, num_questions: int = 10, include_scenarios: bool = False
    ) -> Dict[str, Any]:
        """Generate a complete mock exam with metadata and improved error handling"""
        try:
            prompt = self._create_mock_generation_prompt(
                topic, difficulty, num_questions, include_scenarios
            )

            response = await self._generate_text_with_retry(prompt, max_tokens=4000)
            questions = self._parse_mock_questions(response)

            # Validate questions
            valid_questions = []
            for i, question in enumerate(questions):
                if self._validate_question_format(question):
                    valid_questions.append(self._clean_question(question))
                else:
                    logger.warning(f"Generated question {i+1} failed validation, skipping")

            if not valid_questions:
                logger.error("No valid questions generated")
                return {}

            # Create mock exam metadata
            mock_data = {
                "title": f"{topic} - {difficulty.title()} Level Mock Exam",
                "description": f"AI-generated {difficulty} level practice exam covering {topic}",
                "topic": topic,
                "difficulty": difficulty,
                "time_limit_minutes": min(
                    len(valid_questions) * 2, 120
                ),  # 2 min per question, max 2 hours
                "questions_json": valid_questions,
                "total_questions": len(valid_questions),
                "ai_generated": True,
                "explanation_enabled": True,
                "price_credits": max(1, len(valid_questions) // 5),  # 1 credit per 5 questions
                "category": "AI Generated",
                "is_active": True,
            }

            return mock_data

        except Exception as e:
            logger.error(f"Error generating mock exam: {e}")
            return {}

    async def enhance_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance an existing question with better explanations and metadata"""
        try:
            prompt = self._create_enhancement_prompt(question)
            response = await self._generate_text_with_retry(prompt)

            enhanced_data = self._parse_question_enhancement(response)

            # Merge enhanced data with original
            enhanced_question = question.copy()
            enhanced_question.update(enhanced_data)

            return enhanced_question

        except Exception as e:
            logger.error(f"Error enhancing question: {e}")
            return question

    async def fix_question_errors(
        self,
        question_text: str,
        choices: List[str],
        correct_answer: Optional[int] = None,
        validate_answer: bool = True,
        scenario: str = ""
    ) -> Dict[str, Any]:
        """
        Conservative AI fix for OCR errors, typos, grammar issues, and incorrect answers.

        Args:
            question_text: The question text to fix
            choices: List of answer choices to fix
            correct_answer: Index of claimed correct answer (for validation)
            validate_answer: Whether to validate and potentially fix the correct answer
            scenario: Optional scenario/context for answer validation

        Returns:
            Dict with keys:
                - fixed_question: Corrected question text
                - fixed_choices: List of corrected choices
                - changes_made: Dict of changes
                - has_changes: Boolean indicating if any fixes were made
                - answer_validation: Dict with answer validation results (if validate_answer=True)
                - original_correct_answer: Original correct answer index
                - suggested_correct_answer: AI's suggested correct answer index (if different)
                - answer_changed: Boolean indicating if answer was corrected
        """
        try:
            # Step 1: Fix text errors (OCR, spelling, grammar)
            prompt = self._create_fix_errors_prompt(question_text, choices)
            response = await self._generate_text_with_retry(
                prompt, max_tokens=3000, temperature=0.3  # Low temperature for conservative fixes
            )

            # Parse the AI response
            fix_result = self._parse_fix_errors_response(response, question_text, choices)

            # Step 2: Validate answer correctness if requested
            if validate_answer and correct_answer is not None:
                validation_result = await self.validate_answer_correctness(
                    question_text, choices, correct_answer, scenario
                )

                fix_result["answer_validation"] = validation_result
                fix_result["original_correct_answer"] = correct_answer
                fix_result["suggested_correct_answer"] = validation_result["ai_suggested_index"]
                fix_result["answer_changed"] = (
                    validation_result["ai_suggested_index"] != correct_answer
                )
                fix_result["answer_confidence"] = validation_result["confidence"]

                # Update has_changes if answer needs correction
                if fix_result["answer_changed"]:
                    fix_result["has_changes"] = True
                    if "answer" not in fix_result["changes_made"]:
                        fix_result["changes_made"]["answer"] = []

                    fix_result["changes_made"]["answer"].append(
                        f"Correct answer changed from {chr(65 + correct_answer)} to "
                        f"{chr(65 + validation_result['ai_suggested_index'])} "
                        f"(confidence: {validation_result['confidence']:.0%})"
                    )

                    # Step 3: Regenerate explanation for the corrected answer
                    logger.info("Answer was changed - regenerating explanation for corrected answer")
                    try:
                        new_explanation = await self.generate_explanation(
                            question=question_text,
                            choices=choices,
                            correct_index=validation_result["ai_suggested_index"],
                            scenario=scenario
                        )
                        fix_result["new_explanation"] = new_explanation
                        fix_result["explanation_regenerated"] = True

                        if "explanation" not in fix_result["changes_made"]:
                            fix_result["changes_made"]["explanation"] = []
                        fix_result["changes_made"]["explanation"].append(
                            "Explanation regenerated for corrected answer"
                        )
                    except Exception as e:
                        logger.error(f"Failed to regenerate explanation: {e}")
                        fix_result["new_explanation"] = None
                        fix_result["explanation_regenerated"] = False
                else:
                    fix_result["new_explanation"] = None
                    fix_result["explanation_regenerated"] = False
            else:
                fix_result["answer_validation"] = None
                fix_result["original_correct_answer"] = correct_answer
                fix_result["suggested_correct_answer"] = correct_answer
                fix_result["answer_changed"] = False
                fix_result["new_explanation"] = None
                fix_result["explanation_regenerated"] = False

            return fix_result

        except Exception as e:
            logger.error(f"Error fixing question errors: {e}")
            # Return original content unchanged on error
            return {
                "fixed_question": question_text,
                "fixed_choices": choices,
                "changes_made": {"question": [], "choices": {}},
                "has_changes": False,
                "answer_validation": None,
                "original_correct_answer": correct_answer,
                "suggested_correct_answer": correct_answer,
                "answer_changed": False,
                "new_explanation": None,
                "explanation_regenerated": False,
                "error": str(e)
            }

    async def detect_error_patterns(
        self,
        fix_result: Dict[str, Any],
        question_text: str,
        choices: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Detect error patterns from a fixed question that might appear in other questions.

        Args:
            fix_result: The result from fix_question_errors
            question_text: Original question text
            choices: Original choices

        Returns:
            List of error patterns found, each with:
                - pattern_type: 'ocr_space', 'misspelling', 'grammar', 'wrong_answer'
                - search_pattern: Pattern to search for in other questions
                - description: Human-readable description
                - example_fix: Example of the fix applied
        """
        patterns = []

        # Pattern 1: OCR spacing errors (words with spaces in middle)
        if fix_result.get('changes_made', {}).get('question'):
            for change in fix_result['changes_made']['question']:
                # Look for patterns like "word1 word2" → "word1word2"
                if 'Fixed:' in change and '→' in change:
                    before_after = change.replace('Fixed:', '').strip().split('→')
                    if len(before_after) == 2:
                        before = before_after[0].strip()
                        after = before_after[1].strip()

                        # Check if this is a space removal (OCR error)
                        if ' ' in before and before.replace(' ', '') == after:
                            patterns.append({
                                'pattern_type': 'ocr_space',
                                'search_pattern': before,
                                'fixed_pattern': after,
                                'description': f'OCR spacing error: "{before}" should be "{after}"',
                                'example_fix': change
                            })

        # Pattern 2: Consistent misspellings
        if fix_result.get('changes_made', {}).get('question'):
            for change in fix_result['changes_made']['question']:
                if 'spelling' in change.lower() or 'typo' in change.lower():
                    # Extract the misspelling pattern
                    if 'Fixed:' in change and '→' in change:
                        before_after = change.replace('Fixed:', '').strip().split('→')
                        if len(before_after) == 2:
                            before = before_after[0].strip()
                            after = before_after[1].strip()
                            patterns.append({
                                'pattern_type': 'misspelling',
                                'search_pattern': before,
                                'fixed_pattern': after,
                                'description': f'Spelling error: "{before}" should be "{after}"',
                                'example_fix': change
                            })

        # Pattern 3: Wrong answer pattern
        if fix_result.get('answer_changed'):
            validation = fix_result.get('answer_validation', {})
            reasoning = validation.get('reasoning', '')

            # Extract keywords from the question to identify similar questions
            keywords = self._extract_keywords(question_text)

            patterns.append({
                'pattern_type': 'wrong_answer',
                'keywords': keywords,
                'original_answer_index': fix_result['original_correct_answer'],
                'correct_answer_index': fix_result['suggested_correct_answer'],
                'description': f'Similar questions may have wrong answer (confidence: {validation.get("confidence", 0):.0%})',
                'reasoning': reasoning,
                'example_fix': f"Changed answer from {chr(65 + fix_result['original_correct_answer'])} to {chr(65 + fix_result['suggested_correct_answer'])}"
            })

        return patterns

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key phrases from question text for pattern matching"""
        # Simple keyword extraction - can be enhanced with NLP
        keywords = []

        # Common important phrases in financial/regulatory questions
        key_phrases = [
            'complex.*structure', 'beneficial owner', 'suspicious transaction',
            'customer due diligence', 'enhanced due diligence', 'know your customer',
            'AML', 'KYC', 'STR', 'SAR', 'politically exposed person', 'PEP',
            'risk assessment', 'money laundering', 'terrorist financing'
        ]

        import re
        text_lower = text.lower()

        for phrase in key_phrases:
            if re.search(phrase, text_lower):
                keywords.append(phrase)

        return keywords

    async def validate_answer_correctness(
        self, question_text: str, choices: List[str], claimed_correct_index: int, scenario: str = ""
    ) -> Dict[str, Any]:
        """
        Validate if the claimed correct answer is actually correct.

        Args:
            question_text: The question text
            choices: List of answer choices
            claimed_correct_index: Index of the claimed correct answer
            scenario: Optional scenario/context for the question

        Returns:
            Dict with keys:
                - is_valid: True if claimed answer seems correct
                - confidence: 0.0-1.0 confidence score
                - ai_suggested_index: AI's suggested correct answer index
                - ai_suggested_choice: AI's suggested correct answer text
                - reasoning: Explanation for AI's determination
                - should_auto_correct: True if confidence >= 0.90 and answer is wrong
        """
        try:
            prompt = self._create_answer_validation_prompt(
                question_text, choices, claimed_correct_index, scenario
            )
            response = await self._generate_text_with_retry(
                prompt, max_tokens=1000, temperature=0.3  # Low temperature for consistent answers
            )

            # Parse the AI response
            validation_result = self._parse_answer_validation_response(
                response, claimed_correct_index, choices
            )

            return validation_result

        except Exception as e:
            logger.error(f"Error validating answer correctness: {e}")
            # Safe fallback: assume answer is correct
            return {
                "is_valid": True,
                "confidence": 0.0,
                "ai_suggested_index": claimed_correct_index,
                "ai_suggested_choice": choices[claimed_correct_index] if claimed_correct_index < len(choices) else "",
                "reasoning": f"Unable to validate due to error: {str(e)}",
                "should_auto_correct": False,
                "error": str(e)
            }

    async def generate_study_tips(self, topic: str, user_performance: Dict[str, Any]) -> str:
        """Generate personalized study tips based on user performance"""
        try:
            prompt = self._create_study_tips_prompt(topic, user_performance)
            tips = await self._generate_text_with_retry(prompt)
            return tips

        except Exception as e:
            logger.error(f"Error generating study tips: {e}")
            # Return more helpful fallback
            score = user_performance.get("score", 0)
            if score >= 80:
                return "Great work! Continue practicing to maintain your high performance. Focus on advanced concepts and edge cases."
            elif score >= 60:
                return "Good progress! Review areas where you scored lower and practice more questions in those topics."
            else:
                return "Keep studying and practicing. Focus on fundamental concepts and take more practice exams to improve."

    async def validate_question_quality(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and rate the quality of a question"""
        try:
            prompt = self._create_validation_prompt(question)
            response = await self._generate_text_with_retry(prompt)

            validation_result = self._parse_validation_result(response)
            return validation_result

        except Exception as e:
            logger.error(f"Error validating question: {e}")
            return {
                "score": 7,
                "feedback": "Unable to validate question quality due to service unavailability",
                "suggestions": [
                    "Ensure question is clear and specific",
                    "Verify all answer choices are plausible",
                ],
            }

    async def _generate_text(
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7
    ) -> str:
        """Generate text using OpenRouter API with enhanced error handling"""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert educational content creator and exam specialist. Provide clear, accurate, and helpful responses.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "frequency_penalty": 0.1,
                        "presence_penalty": 0.1,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return "Error: Unable to generate content at this time."

        except httpx.TimeoutException:
            logger.error("OpenRouter API timeout")
            return "Error: Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return "Error: Unable to connect to AI service."

    async def _generate_text_with_retry(
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7, model: str = None
    ) -> str:
        """Generate text with model cascade fallback - tries free models first, paid as backup"""

        # Use specified model or cascade through all models
        models_to_try = [model] if model else self.models

        for model_index, current_model in enumerate(models_to_try):
            try:
                # Add rate limiting delay between attempts
                if model_index > 0:
                    await asyncio.sleep(self.rate_limit_delay * model_index)

                # Temporarily set the model
                old_model = self.model
                self.model = current_model

                try:
                    logger.info(
                        f"Trying model {model_index + 1}/{len(models_to_try)}: {current_model}"
                    )
                    result = await self._generate_text(prompt, max_tokens, temperature)

                    # Check if result indicates an error
                    if not result.startswith("Error:"):
                        logger.info(f"✅ Success with model: {current_model}")
                        return result
                    else:
                        logger.warning(f"❌ Model {current_model} returned error: {result}")

                finally:
                    self.model = old_model

            except Exception as e:
                logger.error(f"❌ Model {current_model} failed with exception: {e}")
                # Continue to next model in cascade
                if model_index < len(models_to_try) - 1:
                    logger.info(f"Falling back to next model...")
                    continue
                else:
                    logger.error(f"All {len(models_to_try)} models failed")
                    raise

        return "Error: Unable to generate content after trying all models in cascade."

    def _create_cache_key(
        self,
        question: str,
        choices: List[str],
        correct_index: int,
        scenario: str = "",
        explanation_seed: str = "",
    ) -> str:
        """Create a unique cache key for the explanation"""
        content = f"{question}|{','.join(choices)}|{correct_index}|{scenario}|{explanation_seed}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached_explanation(self, cache_key: str) -> Optional[str]:
        """Get explanation from cache if not expired"""
        if cache_key in _explanation_cache:
            expiry_time = _cache_expiry.get(cache_key)
            if expiry_time and datetime.now() < expiry_time:
                return _explanation_cache[cache_key]
            else:
                # Remove expired entry
                _explanation_cache.pop(cache_key, None)
                _cache_expiry.pop(cache_key, None)
        return None

    def _cache_explanation(self, cache_key: str, explanation: str):
        """Cache an explanation with expiry"""
        _explanation_cache[cache_key] = explanation
        _cache_expiry[cache_key] = datetime.now() + timedelta(hours=CACHE_DURATION_HOURS)

        # Cleanup old entries (simple strategy)
        if len(_explanation_cache) > 1000:
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = [key for key, expiry in _cache_expiry.items() if expiry <= now]

        for key in expired_keys:
            _explanation_cache.pop(key, None)
            _cache_expiry.pop(key, None)

    def _get_fallback_explanation(
        self, question: str, choices: List[str], correct_index: int
    ) -> str:
        """Generate a basic fallback explanation when AI is unavailable"""
        if 0 <= correct_index < len(choices):
            correct_choice = choices[correct_index]
            return f"""
**Correct Answer:** {chr(65 + correct_index)}. {correct_choice}

This is the correct answer for this question. For a detailed explanation of why this answer is correct and why the other options are incorrect, please try again later when our AI explanation service is available.

**Study Tip:** Review the relevant course material and practice similar questions to reinforce your understanding of this concept.
"""
        else:
            return "Explanation temporarily unavailable. Please try again later."

    def _create_explanation_prompt(
        self,
        question: str,
        choices: List[str],
        correct_index: int,
        scenario: str = "",
        explanation_seed: str = "",
    ) -> str:
        """Create enhanced prompt for generating question explanations"""
        correct_choice = choices[correct_index] if 0 <= correct_index < len(choices) else "Unknown"

        prompt = f"""
Create a clear, educational explanation for this exam question.

{f"SCENARIO: {scenario}" if scenario else ""}

QUESTION: {question}

CHOICES:
"""
        for i, choice in enumerate(choices):
            marker = "✓ CORRECT" if i == correct_index else ""
            prompt += f"{chr(65 + i)}. {choice} {marker}\n"

        prompt += f"""
CORRECT ANSWER: {chr(65 + correct_index)}. {correct_choice}

{f"EXPLANATION HINT: {explanation_seed}" if explanation_seed else ""}

Please provide a comprehensive explanation that:
1. **Why it's correct**: Clearly explain why the correct answer is right
2. **Common mistakes**: Explain why other options are incorrect
3. **Key concept**: Identify the main concept being tested
4. **Study tip**: Provide a brief tip for remembering this concept

Keep the explanation informative but concise (under 300 words).
Use clear, encouraging language suitable for exam preparation.
"""
        return prompt

    def _create_mock_generation_prompt(
        self, topic: str, difficulty: str, num_questions: int, include_scenarios: bool = False
    ) -> str:
        """Create enhanced prompt for generating complete mock exams"""
        scenario_instruction = (
            "Include brief scenarios for some questions when appropriate."
            if include_scenarios
            else ""
        )

        return f"""
Generate {num_questions} high-quality multiple-choice questions for a {difficulty.upper()} level exam on: {topic}

REQUIREMENTS:
- Each question must have exactly 4 choices (A, B, C, D)
- Only one correct answer per question
- Questions should be realistic and exam-appropriate
- Cover diverse aspects of {topic}
- Maintain consistent {difficulty} difficulty level
- {scenario_instruction}

DIFFICULTY GUIDELINES:
- EASY: Basic concepts, straightforward application
- MEDIUM: Applied knowledge, some analysis required
- HARD: Complex scenarios, critical thinking, multiple concepts

FORMAT your response as valid JSON:
```json
[
  {{
    "question": "Clear, specific question text",
    "choices": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation_seed": "Brief hint for explanation generation",
    "scenario": "Optional background context",
    "difficulty": "{difficulty}",
    "topic_tags": ["tag1", "tag2"]
  }}
]
```

Generate practical, relevant questions that would appear in a professional {topic} examination.
Ensure questions test understanding, not just memorization.
"""

    def _create_enhancement_prompt(self, question: Dict[str, Any]) -> str:
        """Create prompt for enhancing existing questions"""
        return f"""
Enhance this exam question to improve its quality and educational value:

CURRENT QUESTION:
Question: {question.get('question', '')}
Choices: {question.get('choices', [])}
Correct Answer: Index {question.get('correct_index', 0)}

Please provide enhancements in JSON format:
```json
{{
  "improved_question": "Enhanced question text if needed",
  "explanation_seed": "Hint for generating explanations",
  "difficulty_level": "easy|medium|hard",
  "topic_tags": ["relevant", "tags"],
  "quality_score": 8,
  "enhancement_notes": "What was improved"
}}
```

Focus on:
1. Clarity and precision of question wording
2. Realistic and plausible distractors
3. Appropriate difficulty level
4. Educational value
"""

    def _create_study_tips_prompt(self, topic: str, user_performance: Dict[str, Any]) -> str:
        """Create prompt for generating personalized study tips"""
        avg_score = user_performance.get("average_score", 0)
        weak_areas = user_performance.get("weak_areas", [])
        strong_areas = user_performance.get("strong_areas", [])

        return f"""
Generate personalized study tips for a student studying {topic}.

STUDENT PERFORMANCE:
- Average Score: {avg_score}%
- Weak Areas: {', '.join(weak_areas) if weak_areas else 'None identified'}
- Strong Areas: {', '.join(strong_areas) if strong_areas else 'None identified'}

Provide 5-7 specific, actionable study tips that:
1. Address identified weak areas
2. Build on existing strengths
3. Are practical and implementable
4. Include specific study techniques
5. Encourage continued learning

Format as a clear, motivating response with numbered tips.
"""

    def _create_validation_prompt(self, question: Dict[str, Any]) -> str:
        """Create prompt for validating question quality"""
        return f"""
Evaluate the quality of this exam question and provide a rating:

QUESTION: {question.get('question', '')}
CHOICES: {question.get('choices', [])}
CORRECT ANSWER: Index {question.get('correct_index', 0)}

Rate this question on a scale of 1-10 and provide feedback.

Respond in JSON format:
```json
{{
  "score": 8,
  "feedback": "Detailed feedback on question quality",
  "strengths": ["Clear wording", "Good distractors"],
  "improvements": ["Could be more specific", "Add scenario"],
  "difficulty_assessment": "medium"
}}
```

Consider:
1. Question clarity and precision
2. Answer choice quality
3. Difficulty appropriateness
4. Educational value
5. Absence of ambiguity
"""

    def _create_fix_errors_prompt(self, question_text: str, choices: List[str]) -> str:
        """Create prompt for conservative error fixing"""
        choices_formatted = "\n".join([f"{i}: {choice}" for i, choice in enumerate(choices)])

        return f"""You are a conservative text correction assistant. Your ONLY job is to fix obvious errors without changing meaning.

STRICT RULES:
1. Fix ONLY these types of errors:
   - OCR errors (spaces in middle of words: "Charli e" → "Charlie", "pa rt" → "part", "reimburse ment" → "reimbursement")
   - Spelling mistakes ("recieve" → "receive", "seperate" → "separate")
   - Grammar errors ("He suspect" → "He suspects", "they was" → "they were")
   - Subject-verb agreement ("The company have" → "The company has")
   - Multiple spaces or punctuation errors

2. DO NOT:
   - Change question meaning or intent
   - Rewrite for "clarity" or "better phrasing"
   - Add or remove content
   - Change technical terms or financial terminology
   - Simplify complex sentences
   - Change numbers, dates, or proper nouns
   - Fix things that are not clearly errors

3. If you're unsure whether something is an error, DO NOT change it.

QUESTION TEXT:
{question_text}

ANSWER CHOICES:
{choices_formatted}

Respond with JSON ONLY. No extra text before or after the JSON:
{{{{
  "fixed_question": "corrected question text (or original if no errors)",
  "fixed_choices": ["corrected choice 0", "corrected choice 1", "corrected choice 2", "corrected choice 3"],
  "changes_made": {{{{
    "question": ["Fixed: Charli e → Charlie", "Fixed: He suspect → He suspects"],
    "choices": {{{{
      "0": ["Fixed: reimburse ment → reimbursement"],
      "1": []
    }}}}
  }}}},
  "has_changes": true
}}}}

If NO errors are found at all, return:
{{{{
  "fixed_question": "{question_text}",
  "fixed_choices": {json.dumps(choices)},
  "changes_made": {{{{"question": [], "choices": {{}}}}}},
  "has_changes": false
}}}}

Be extremely conservative. Only fix OBVIOUS errors."""

    def _create_answer_validation_prompt(
        self, question_text: str, choices: List[str], claimed_correct_index: int, scenario: str = ""
    ) -> str:
        """Create prompt for validating answer correctness"""
        choices_formatted = "\n".join([f"{chr(65 + i)}. {choice}" for i, choice in enumerate(choices)])
        scenario_text = f"\n\nSCENARIO/CONTEXT:\n{scenario}" if scenario else ""

        return f"""You are an expert in finance, banking, and regulatory exams (CACS, CMFAS, Securities, MAS regulations).

Analyze this multiple-choice question and determine the BEST correct answer.

QUESTION: {question_text}{scenario_text}

ANSWER CHOICES:
{choices_formatted}

CLAIMED CORRECT ANSWER: {chr(65 + claimed_correct_index)}. {choices[claimed_correct_index]}

TASK:
1. Determine which choice is ACTUALLY the most defensible correct answer based on financial regulations and best practices
2. Rate your confidence (0.0-1.0) in your determination
3. Explain your reasoning clearly

IMPORTANT:
- Only choose a different answer if you are VERY confident (≥0.90) the claimed answer is wrong
- If confidence < 0.90, you are uncertain - be conservative
- For "EXCEPT" questions, the correct answer is the one that does NOT belong
- Consider regulatory requirements (MAS, SFA, FAA) for finance-related questions

Respond in JSON ONLY (no preamble or explanation before the JSON):
{{{{
  "best_answer_letter": "B",
  "best_answer_index": 1,
  "confidence": 0.95,
  "reasoning": "Detailed explanation of why this is the correct answer and why the claimed answer is wrong if applicable...",
  "is_claimed_answer_correct": false,
  "issues_with_claimed_answer": "Specific issues with the claimed correct answer if any..."
}}}}

Be thorough in your reasoning. If unsure, lower your confidence score."""

    def _parse_fix_errors_response(
        self, response: str, original_question: str, original_choices: List[str]
    ) -> Dict[str, Any]:
        """Parse AI response for error fixes"""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)

                # Validate the response structure
                if not all(key in result for key in ["fixed_question", "fixed_choices", "changes_made"]):
                    logger.warning("Invalid response structure from AI, using original content")
                    return {
                        "fixed_question": original_question,
                        "fixed_choices": original_choices,
                        "changes_made": {"question": [], "choices": {}},
                        "has_changes": False
                    }

                # Ensure has_changes is present
                if "has_changes" not in result:
                    # Determine if there are any changes
                    result["has_changes"] = bool(
                        result.get("changes_made", {}).get("question", []) or
                        result.get("changes_made", {}).get("choices", {})
                    )

                return result

        except Exception as e:
            logger.error(f"Error parsing fix errors response: {e}")

        # Fallback: return original content unchanged
        return {
            "fixed_question": original_question,
            "fixed_choices": original_choices,
            "changes_made": {"question": [], "choices": {}},
            "has_changes": False
        }

    def _parse_answer_validation_response(
        self, response: str, claimed_index: int, choices: List[str]
    ) -> Dict[str, Any]:
        """Parse AI response for answer validation"""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)

                # Validate the response structure
                required_keys = ["best_answer_index", "confidence", "reasoning"]
                if not all(key in result for key in required_keys):
                    logger.warning("Invalid response structure from AI, using safe fallback")
                    return self._get_validation_fallback(claimed_index, choices)

                # Extract values with defaults
                ai_index = int(result.get("best_answer_index", claimed_index))
                confidence = float(result.get("confidence", 0.0))
                reasoning = result.get("reasoning", "")
                is_claimed_correct = result.get("is_claimed_answer_correct", True)

                # Bounds check
                if ai_index < 0 or ai_index >= len(choices):
                    logger.warning(f"AI suggested invalid index {ai_index}, using claimed index")
                    ai_index = claimed_index

                # Determine if should auto-correct
                is_valid = (ai_index == claimed_index) or is_claimed_correct
                should_auto_correct = (confidence >= 0.90) and not is_valid

                return {
                    "is_valid": is_valid,
                    "confidence": min(1.0, max(0.0, confidence)),  # Clamp to 0.0-1.0
                    "ai_suggested_index": ai_index,
                    "ai_suggested_choice": choices[ai_index],
                    "reasoning": reasoning,
                    "should_auto_correct": should_auto_correct
                }

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in answer validation: {e}")
        except Exception as e:
            logger.error(f"Error parsing answer validation response: {e}")

        # Fallback: assume answer is correct
        return self._get_validation_fallback(claimed_index, choices)

    def _get_validation_fallback(self, claimed_index: int, choices: List[str]) -> Dict[str, Any]:
        """Get safe fallback validation result"""
        return {
            "is_valid": True,
            "confidence": 0.0,
            "ai_suggested_index": claimed_index,
            "ai_suggested_choice": choices[claimed_index] if claimed_index < len(choices) else "",
            "reasoning": "Unable to validate - assuming claimed answer is correct",
            "should_auto_correct": False
        }

    def _parse_mock_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract mock exam questions"""
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                questions = json.loads(json_str)

                # Validate and clean questions
                validated_questions = []
                for q in questions:
                    if self._validate_question_format(q):
                        validated_questions.append(self._clean_question(q))

                return validated_questions

        except Exception as e:
            logger.error(f"Error parsing mock questions: {e}")

        return []

    def _parse_question_enhancement(self, response: str) -> Dict[str, Any]:
        """Parse AI response for question enhancement"""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error parsing question enhancement: {e}")

        return {}

    def _parse_validation_result(self, response: str) -> Dict[str, Any]:
        """Parse AI response for validation result"""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error parsing validation result: {e}")

        return {"score": 5, "feedback": "Unable to validate"}

    def _validate_question_format(self, question: Dict[str, Any]) -> bool:
        """Validate question format and content"""
        required_fields = ["question", "choices", "correct_index"]

        # Check required fields
        for field in required_fields:
            if field not in question:
                return False

        # Validate choices
        choices = question["choices"]
        if not isinstance(choices, list) or len(choices) != 4:
            return False

        # Validate correct_index
        correct_index = question["correct_index"]
        if not isinstance(correct_index, int) or not (0 <= correct_index < 4):
            return False

        # Check for empty content
        if not question["question"].strip():
            return False

        for choice in choices:
            if not choice.strip():
                return False

        return True

    # Advanced AI Generation Methods for Production MVP

    async def tag_question_topics(
        self, question_text: str, choices: List[str], exam_category: str
    ) -> List[str]:
        """Use AI to automatically tag questions with relevant topics"""
        try:
            prompt = f"""
            Analyze this {exam_category} exam question and identify the specific topics it covers.

            Question: {question_text}
            Choices: {', '.join(choices)}
            Exam Category: {exam_category}

            Return a JSON list of 2-5 specific topic tags that best categorize this question.
            Topics should be specific (e.g., "Capital Adequacy Ratio", "Risk Management Framework")
            rather than general (e.g., "Banking", "Finance").

            Return format: ["topic1", "topic2", "topic3"]
            """

            response = await self._generate_text_with_retry(prompt, model=self.budget_model)

            # Parse JSON response
            try:
                tags = json.loads(response.strip())
                return [tag.strip() for tag in tags if isinstance(tag, str)][:5]
            except json.JSONDecodeError:
                # Fallback: extract topics from response text
                lines = response.strip().split("\n")
                tags = []
                for line in lines:
                    if '"' in line:
                        parts = line.split('"')
                        for part in parts[1::2]:  # Every second part is inside quotes
                            if part.strip():
                                tags.append(part.strip())
                return tags[:5]

        except Exception as e:
            logger.error(f"Error tagging question topics: {e}")
            return []

    async def generate_question_variants(
        self, base_question: Dict[str, Any], num_variants: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate variants of an existing question with different scenarios/numbers"""
        try:
            prompt = f"""
            Create {num_variants} variants of this exam question. Each variant should:
            - Test the same concept but with different scenarios, numbers, or contexts
            - Maintain the same difficulty level and question structure
            - Have 4 plausible answer choices with only one correct answer
            - Include a brief explanation for the correct answer

            Original Question: {base_question['question']}
            Original Choices: {json.dumps(base_question['choices'])}
            Original Correct Answer: {base_question['choices'][base_question['correct_index']]}
            Original Explanation: {base_question.get('explanation_seed', '')}

            Return as JSON array with this structure:
            [{{
                "question": "variant question text",
                "choices": ["A", "B", "C", "D"],
                "correct_index": 0,
                "explanation_seed": "brief explanation",
                "scenario": "optional scenario context"
            }}]
            """

            response = await self._generate_text_with_retry(prompt)

            try:
                variants = json.loads(response.strip())
                validated_variants = []

                for variant in variants:
                    if self._validate_question_structure(variant):
                        validated_variants.append(variant)

                return validated_variants

            except json.JSONDecodeError:
                logger.error("Failed to parse question variants JSON")
                return []

        except Exception as e:
            logger.error(f"Error generating question variants: {e}")
            return []

    async def generate_adaptive_questions(
        self,
        user_weak_areas: List[str],
        difficulty_level: str,
        exam_category: str,
        num_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Generate questions targeted at user's weak areas for adaptive practice"""
        try:
            weak_areas_text = ", ".join(user_weak_areas)

            prompt = f"""
            Generate {num_questions} {difficulty_level} level practice questions for {exam_category}
            specifically targeting these weak areas: {weak_areas_text}

            Requirements:
            - Each question should focus on one of the weak areas
            - Difficulty: {difficulty_level}
            - Include practical scenarios where applicable
            - 4 answer choices each with clear explanations
            - Progressive difficulty within the set

            Return as JSON array with this structure:
            [{{
                "question": "question text",
                "choices": ["A", "B", "C", "D"],
                "correct_index": 0,
                "explanation_seed": "detailed explanation",
                "scenario": "scenario context if applicable",
                "target_topic": "specific weak area being addressed",
                "difficulty": "{difficulty_level}"
            }}]
            """

            response = await self._generate_text_with_retry(prompt)

            try:
                questions = json.loads(response.strip())
                validated_questions = []

                for q in questions:
                    if self._validate_question_structure(q):
                        validated_questions.append(q)

                return validated_questions

            except json.JSONDecodeError:
                logger.error("Failed to parse adaptive questions JSON")
                return []

        except Exception as e:
            logger.error(f"Error generating adaptive questions: {e}")
            return []

    async def enhance_explanation_quality(
        self,
        question: str,
        basic_explanation: str,
        user_answer: int,
        correct_answer: int,
        choices: List[str],
    ) -> str:
        """Enhance a basic explanation with more detailed reasoning"""
        try:
            user_choice = choices[user_answer] if 0 <= user_answer < len(choices) else "No answer"
            correct_choice = (
                choices[correct_answer] if 0 <= correct_answer < len(choices) else "Unknown"
            )

            prompt = f"""
            Enhance this explanation for an exam question to make it more educational and comprehensive.

            Question: {question}
            Choices: {json.dumps(choices)}
            User selected: {user_choice}
            Correct answer: {correct_choice}
            Basic explanation: {basic_explanation}

            Create an enhanced explanation that:
            1. Explains why the correct answer is right (with reasoning)
            2. Explains why the incorrect answers are wrong
            3. Provides additional context or learning tips
            4. Uses clear, educational language
            5. Keeps it concise but comprehensive

            Return only the enhanced explanation text.
            """

            enhanced = await self._generate_text_with_retry(prompt, model=self.budget_model)
            return enhanced.strip()

        except Exception as e:
            logger.error(f"Error enhancing explanation: {e}")
            return basic_explanation

    async def generate_syllabus_coverage_questions(
        self,
        syllabus_section: str,
        learning_objectives: List[str],
        exam_category: str,
        num_questions: int = 10,
    ) -> List[Dict[str, Any]]:
        """Generate questions that comprehensively cover a syllabus section"""
        try:
            objectives_text = "\n".join([f"- {obj}" for obj in learning_objectives])

            prompt = f"""
            Generate {num_questions} exam questions for {exam_category} that comprehensively cover
            this syllabus section:

            Section: {syllabus_section}
            Learning Objectives:
            {objectives_text}

            Requirements:
            - Cover each learning objective with at least one question
            - Mix of difficulty levels (easy, medium, hard)
            - Practical application scenarios where relevant
            - Clear, unambiguous questions
            - 4 plausible answer choices
            - Detailed explanations

            Return as JSON array with this structure:
            [{{
                "question": "question text",
                "choices": ["A", "B", "C", "D"],
                "correct_index": 0,
                "explanation_seed": "detailed explanation",
                "scenario": "practical scenario if applicable",
                "learning_objective": "which objective this addresses",
                "difficulty": "easy|medium|hard",
                "syllabus_section": "{syllabus_section}"
            }}]
            """

            response = await self._generate_text_with_retry(prompt)

            try:
                questions = json.loads(response.strip())
                validated_questions = []

                for q in questions:
                    if self._validate_question_structure(q):
                        validated_questions.append(q)

                return validated_questions

            except json.JSONDecodeError:
                logger.error("Failed to parse syllabus coverage questions JSON")
                return []

        except Exception as e:
            logger.error(f"Error generating syllabus coverage questions: {e}")
            return []

    async def analyze_question_difficulty(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and suggest appropriate difficulty level for a question"""
        try:
            prompt = f"""
            Analyze this exam question and determine its appropriate difficulty level and characteristics.

            Question: {question['question']}
            Choices: {json.dumps(question['choices'])}
            Correct Answer: {question['choices'][question['correct_index']]}

            Analyze and return JSON with:
            {{
                "suggested_difficulty": "easy|medium|hard",
                "complexity_factors": ["factor1", "factor2"],
                "cognitive_level": "recall|comprehension|application|analysis",
                "time_estimate_seconds": 60,
                "requires_calculation": true/false,
                "requires_memorization": true/false,
                "scenario_based": true/false,
                "explanation": "reasoning for difficulty assessment"
            }}
            """

            response = await self._generate_text_with_retry(prompt, model=self.budget_model)

            try:
                analysis = json.loads(response.strip())
                return analysis
            except json.JSONDecodeError:
                logger.error("Failed to parse difficulty analysis JSON")
                return {"suggested_difficulty": "medium", "explanation": "Analysis failed"}

        except Exception as e:
            logger.error(f"Error analyzing question difficulty: {e}")
            return {"suggested_difficulty": "medium", "explanation": "Analysis error"}

    def _clean_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize question data"""
        cleaned = {
            "question": question["question"].strip(),
            "choices": [choice.strip() for choice in question["choices"]],
            "correct_index": int(question["correct_index"]),
            "explanation_seed": question.get("explanation_seed", "").strip(),
            "scenario": question.get("scenario", "").strip(),
            "difficulty": question.get("difficulty", "medium"),
            "topic_tags": question.get("topic_tags", []),
        }

        return cleaned


# Global instance
openrouter_manager = OpenRouterManager()


# Helper functions for easy access
async def generate_explanation(
    question: str,
    choices: List[str],
    correct_index: int,
    scenario: str = "",
    explanation_seed: str = "",
) -> str:
    """Generate explanation for a single question"""
    return await openrouter_manager.generate_explanation(
        question, choices, correct_index, scenario, explanation_seed
    )


async def generate_batch_explanations(
    questions: List[Dict[str, Any]], user_answers: List[int]
) -> List[str]:
    """Generate explanations for multiple questions"""
    return await openrouter_manager.generate_batch_explanations(questions, user_answers)


async def generate_mock_exam(
    topic: str, difficulty: str, num_questions: int = 10, include_scenarios: bool = False
) -> Dict[str, Any]:
    """Generate a complete mock exam"""
    return await openrouter_manager.generate_mock_exam(
        topic, difficulty, num_questions, include_scenarios
    )


async def enhance_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance an existing question"""
    return await openrouter_manager.enhance_question(question)


async def generate_study_tips(topic: str, user_performance: Dict[str, Any]) -> str:
    """Generate personalized study tips"""
    return await openrouter_manager.generate_study_tips(topic, user_performance)


async def validate_question_quality(question: Dict[str, Any]) -> Dict[str, Any]:
    """Validate question quality"""
    return await openrouter_manager.validate_question_quality(question)


# New AI-powered helper functions for production MVP
async def tag_question_topics(
    question_text: str, choices: List[str], exam_category: str
) -> List[str]:
    """Auto-tag questions with relevant topics"""
    return await openrouter_manager.tag_question_topics(question_text, choices, exam_category)


async def generate_question_variants(
    base_question: Dict[str, Any], num_variants: int = 3
) -> List[Dict[str, Any]]:
    """Generate variants of an existing question"""
    return await openrouter_manager.generate_question_variants(base_question, num_variants)


async def generate_adaptive_questions(
    user_weak_areas: List[str], difficulty_level: str, exam_category: str, num_questions: int = 5
) -> List[Dict[str, Any]]:
    """Generate questions for user's weak areas"""
    return await openrouter_manager.generate_adaptive_questions(
        user_weak_areas, difficulty_level, exam_category, num_questions
    )


async def enhance_explanation_quality(
    question: str, basic_explanation: str, user_answer: int, correct_answer: int, choices: List[str]
) -> str:
    """Enhance explanation with detailed reasoning"""
    return await openrouter_manager.enhance_explanation_quality(
        question, basic_explanation, user_answer, correct_answer, choices
    )


async def generate_syllabus_coverage_questions(
    syllabus_section: str,
    learning_objectives: List[str],
    exam_category: str,
    num_questions: int = 10,
) -> List[Dict[str, Any]]:
    """Generate questions covering syllabus section"""
    return await openrouter_manager.generate_syllabus_coverage_questions(
        syllabus_section, learning_objectives, exam_category, num_questions
    )


async def analyze_question_difficulty(question: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze question difficulty and characteristics"""
    return await openrouter_manager.analyze_question_difficulty(question)


async def fix_question_errors(
    question_text: str,
    choices: List[str],
    correct_answer: Optional[int] = None,
    validate_answer: bool = True,
    scenario: str = ""
) -> Dict[str, Any]:
    """
    Conservative AI fix for OCR errors, typos, grammar issues, and incorrect answers.

    Args:
        question_text: The question text to fix
        choices: List of answer choices to fix
        correct_answer: Index of claimed correct answer (for validation)
        validate_answer: Whether to validate and potentially fix the correct answer
        scenario: Optional scenario/context for answer validation

    Returns:
        Dict with keys:
            - fixed_question: Corrected question text
            - fixed_choices: List of corrected choices
            - changes_made: Dict of changes
            - has_changes: Boolean indicating if any fixes were made
            - answer_validation: Dict with answer validation results (if validate_answer=True)
            - original_correct_answer: Original correct answer index
            - suggested_correct_answer: AI's suggested correct answer index (if different)
            - answer_changed: Boolean indicating if answer was corrected
    """
    return await openrouter_manager.fix_question_errors(
        question_text=question_text,
        choices=choices,
        correct_answer=correct_answer,
        validate_answer=validate_answer,
        scenario=scenario
    )


async def validate_answer_correctness(
    question_text: str,
    choices: List[str],
    claimed_correct_index: int,
    scenario: str = ""
) -> Dict[str, Any]:
    """
    Validate if the claimed correct answer is actually correct.

    Args:
        question_text: The question text
        choices: List of answer choices
        claimed_correct_index: Index of the claimed correct answer
        scenario: Optional scenario/context for the question

    Returns:
        Dict with keys:
            - is_valid: True if claimed answer seems correct
            - confidence: 0.0-1.0 confidence score
            - ai_suggested_index: AI's suggested correct answer index
            - ai_suggested_choice: AI's suggested correct answer text
            - reasoning: Explanation for AI's determination
            - should_auto_correct: True if confidence >= 0.90 and answer is wrong
    """
    return await openrouter_manager.validate_answer_correctness(
        question_text, choices, claimed_correct_index, scenario
    )
