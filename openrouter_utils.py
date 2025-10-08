"""
OpenRouter AI integration for MockExamify
"""
import httpx
import json
import logging
from typing import Optional, List, Dict, Any
from models import OpenRouterRequest, OpenRouterResponse, QuestionSchema
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenRouterManager:
    """Handles OpenRouter AI operations"""
    
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.base_url = config.OPENROUTER_BASE_URL
        self.model = config.OPENROUTER_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mockexamify.com",  # Optional: your site URL
            "X-Title": "MockExamify"  # Optional: your app name
        }
    
    async def generate_explanation(self, question: str, choices: List[str], correct_answer: str, context: Optional[str] = None) -> Optional[str]:
        """Generate explanation for a question using OpenRouter"""
        try:
            # Format choices for the prompt
            choices_text = "\n".join([f"{chr(65 + i)}. {choice}" for i, choice in enumerate(choices)])
            
            prompt = f"""You are an expert educator creating detailed explanations for exam questions.

Question: {question}

Answer Choices:
{choices_text}

Correct Answer: {correct_answer}

Please provide a clear, educational explanation that:
1. Explains why the correct answer is right
2. Briefly explains why the other options are incorrect
3. Provides relevant context or additional learning points
4. Uses simple, clear language suitable for students

Keep the explanation concise but comprehensive (2-4 paragraphs)."""

            if context:
                prompt += f"\n\nAdditional Context: {context}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    explanation = result['choices'][0]['message']['content'].strip()
                    logger.info(f"Generated explanation for question: {question[:50]}...")
                    return explanation
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return None
    
    async def generate_question_variants(self, base_question: QuestionSchema, num_variants: int = 3) -> List[QuestionSchema]:
        """Generate variants of a base question"""
        try:
            choices_text = "\n".join([f"{chr(65 + i)}. {choice}" for i, choice in enumerate(base_question.choices)])
            correct_choice = base_question.choices[base_question.correct_index]
            
            prompt = f"""You are an expert test creator. Generate {num_variants} variants of the following question while maintaining the same difficulty level and learning objective.

Original Question: {base_question.question}

Original Choices:
{choices_text}

Correct Answer: {correct_choice}

For each variant, provide:
1. A modified question that tests the same concept
2. Modified answer choices (keep the same structure)
3. Maintain the same correct answer position when possible
4. Ensure all variants are of similar difficulty

Return the response as a JSON array where each object has:
- "question": the variant question text
- "choices": array of choice texts
- "correct_index": index of correct choice (0-based)
- "explanation_template": brief explanation template

Example format:
[
  {{
    "question": "variant question text",
    "choices": ["choice A", "choice B", "choice C", "choice D"],
    "correct_index": 2,
    "explanation_template": "explanation template"
  }}
]"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.8
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    
                    # Try to parse JSON response
                    try:
                        variants_data = json.loads(content)
                        variants = []
                        
                        for variant_data in variants_data:
                            variants.append(QuestionSchema(
                                question=variant_data['question'],
                                choices=variant_data['choices'],
                                correct_index=variant_data['correct_index'],
                                explanation_template=variant_data.get('explanation_template'),
                                category=base_question.category,
                                difficulty=base_question.difficulty
                            ))
                        
                        logger.info(f"Generated {len(variants)} question variants")
                        return variants
                        
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON response from OpenRouter")
                        return []
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error generating question variants: {e}")
            return []
    
    async def enhance_question_bank(self, questions: List[QuestionSchema]) -> List[QuestionSchema]:
        """Enhance a question bank by generating explanations and improving quality"""
        try:
            enhanced_questions = []
            
            for question in questions:
                # Generate explanation if not present
                if not question.explanation_template:
                    correct_answer = question.choices[question.correct_index]
                    explanation = await self.generate_explanation(
                        question.question,
                        question.choices,
                        correct_answer
                    )
                    
                    if explanation:
                        question.explanation_template = explanation
                
                enhanced_questions.append(question)
            
            logger.info(f"Enhanced {len(enhanced_questions)} questions")
            return enhanced_questions
            
        except Exception as e:
            logger.error(f"Error enhancing question bank: {e}")
            return questions
    
    async def generate_mock_from_topic(self, topic: str, num_questions: int = 10, difficulty: str = "medium") -> List[QuestionSchema]:
        """Generate a complete mock exam from a topic"""
        try:
            prompt = f"""You are an expert test creator. Create {num_questions} multiple-choice questions about "{topic}" at {difficulty} difficulty level.

Requirements for each question:
- Clear, unambiguous question text
- 4 answer choices (A, B, C, D)
- Only one clearly correct answer
- Plausible but incorrect distractors
- Appropriate for {difficulty} difficulty level
- Cover different aspects of the topic

Return the response as a JSON array where each object has:
- "question": the question text
- "choices": array of 4 choice texts
- "correct_index": index of correct choice (0-based)
- "explanation_template": brief explanation
- "category": "{topic}"
- "difficulty": "{difficulty}"

Ensure questions test understanding, not just memorization."""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 3000,
                        "temperature": 0.8
                    },
                    timeout=90.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    
                    try:
                        questions_data = json.loads(content)
                        questions = []
                        
                        for q_data in questions_data:
                            questions.append(QuestionSchema(
                                question=q_data['question'],
                                choices=q_data['choices'],
                                correct_index=q_data['correct_index'],
                                explanation_template=q_data.get('explanation_template'),
                                category=q_data.get('category', topic),
                                difficulty=q_data.get('difficulty', difficulty)
                            ))
                        
                        logger.info(f"Generated {len(questions)} questions for topic: {topic}")
                        return questions
                        
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON response from OpenRouter")
                        return []
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error generating mock from topic: {e}")
            return []
    
    def is_configured(self) -> bool:
        """Check if OpenRouter is properly configured"""
        return bool(self.api_key and self.api_key != "your_openrouter_api_key")


# Global OpenRouter manager instance
openrouter_manager = OpenRouterManager()