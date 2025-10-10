"""
OpenRouter API utilities for MockExamify
Handles AI-powered content generation and explanations
"""
import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional
import logging
import config

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Client for OpenRouter API interactions"""
    
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3-haiku"
    
    async def generate_explanations(self, questions: List[Dict[str, Any]], user_answers: List[int], correct_answers: List[int]) -> List[str]:
        """Generate explanations for exam questions"""
        explanations = []
        
        for i, question in enumerate(questions):
            try:
                user_answer_idx = user_answers.get(i, -1)
                correct_idx = correct_answers[i]
                
                prompt = self._create_explanation_prompt(
                    question, user_answer_idx, correct_idx
                )
                
                explanation = await self._generate_text(prompt)
                explanations.append(explanation)
                
            except Exception as e:
                logger.error(f"Error generating explanation for question {i}: {e}")
                explanations.append("Explanation temporarily unavailable.")
        
        return explanations
    
    async def generate_question_variants(self, base_question: Dict[str, Any], num_variants: int = 3) -> List[Dict[str, Any]]:
        """Generate variants of a question for different difficulty levels"""
        variants = []
        
        try:
            prompt = self._create_variant_prompt(base_question, num_variants)
            response = await self._generate_text(prompt)
            
            # Parse the response to extract variants
            variants = self._parse_question_variants(response)
            
        except Exception as e:
            logger.error(f"Error generating question variants: {e}")
        
        return variants
    
    async def generate_mock_questions(self, topic: str, difficulty: str, num_questions: int = 10) -> List[Dict[str, Any]]:
        """Generate a complete set of mock questions for a topic"""
        questions = []
        
        try:
            prompt = self._create_mock_generation_prompt(topic, difficulty, num_questions)
            response = await self._generate_text(prompt)
            
            # Parse the response to extract questions
            questions = self._parse_mock_questions(response)
            
        except Exception as e:
            logger.error(f"Error generating mock questions: {e}")
        
        return questions
    
    async def _generate_text(self, prompt: str) -> str:
        """Generate text using OpenRouter API"""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return "Error generating content."
                    
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return "Error generating content."
    
    def _create_explanation_prompt(self, question: Dict[str, Any], user_answer_idx: int, correct_idx: int) -> str:
        """Create prompt for generating question explanations"""
        question_text = question.get("question", "")
        choices = question.get("choices", [])
        
        user_choice = choices[user_answer_idx] if 0 <= user_answer_idx < len(choices) else "No answer selected"
        correct_choice = choices[correct_idx] if 0 <= correct_idx < len(choices) else "Unknown"
        
        prompt = f"""
You are an expert exam tutor. Explain why the correct answer is right and help the student understand their mistake.

Question: {question_text}

Choices:
"""
        for i, choice in enumerate(choices):
            marker = "✓" if i == correct_idx else "✗" if i == user_answer_idx else " "
            prompt += f"{marker} {chr(65 + i)}. {choice}\n"
        
        prompt += f"""
Student's answer: {user_choice}
Correct answer: {correct_choice}

Please provide a clear, educational explanation that:
1. Explains why the correct answer is right
2. If the student chose incorrectly, explains what makes their choice wrong
3. Provides additional context or study tips
4. Uses simple, encouraging language

Keep the explanation under 200 words.
"""
        return prompt
    
    def _create_variant_prompt(self, base_question: Dict[str, Any], num_variants: int) -> str:
        """Create prompt for generating question variants"""
        return f"""
Create {num_variants} variants of this multiple-choice question with different difficulty levels:

Original Question: {base_question.get("question", "")}
Choices: {base_question.get("choices", [])}
Correct Answer: {base_question.get("correct_index", 0)}

Generate variants that:
1. Test the same concept but with different scenarios
2. Have varying difficulty levels (easy, medium, hard)
3. Maintain the same question format (4 multiple choice options)
4. Include clear correct answers

Format your response as JSON with this structure:
[
  {{
    "question": "variant question text",
    "choices": ["A", "B", "C", "D"],
    "correct_index": 0,
    "difficulty": "easy|medium|hard",
    "explanation_template": "brief explanation"
  }}
]
"""
    
    def _create_mock_generation_prompt(self, topic: str, difficulty: str, num_questions: int) -> str:
        """Create prompt for generating complete mock exams"""
        return f"""
Generate {num_questions} multiple-choice questions for a {difficulty} level exam on {topic}.

Requirements:
- Each question should have exactly 4 choices (A, B, C, D)
- Only one correct answer per question
- Questions should be realistic and exam-appropriate
- Cover different aspects of {topic}
- Maintain {difficulty} difficulty level throughout

Format your response as JSON with this structure:
[
  {{
    "question": "question text",
    "choices": ["choice A", "choice B", "choice C", "choice D"],
    "correct_index": 0,
    "explanation_template": "brief explanation of correct answer"
  }}
]

Generate practical, relevant questions that would appear in a professional exam.
"""
    
    def _parse_question_variants(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract question variants"""
        try:
            # Try to extract JSON from the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        return []
    
    def _parse_mock_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract mock exam questions"""
        try:
            # Try to extract JSON from the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                questions = json.loads(json_str)
                
                # Validate question format
                validated_questions = []
                for q in questions:
                    if (isinstance(q, dict) and 
                        'question' in q and 
                        'choices' in q and 
                        'correct_index' in q and
                        isinstance(q['choices'], list) and
                        len(q['choices']) == 4):
                        validated_questions.append(q)
                
                return validated_questions
        except Exception as e:
            logger.error(f"Error parsing mock questions: {e}")
        
        return []

# Helper functions for easy access
async def generate_explanations(questions: List[Dict[str, Any]], user_answers: List[int], correct_answers: List[int]) -> List[str]:
    """Generate explanations for exam questions"""
    client = OpenRouterClient()
    return await client.generate_explanations(questions, user_answers, correct_answers)

async def generate_question_variants(base_question: Dict[str, Any], num_variants: int = 3) -> List[Dict[str, Any]]:
    """Generate variants of a question"""
    client = OpenRouterClient()
    return await client.generate_question_variants(base_question, num_variants)

async def generate_mock_questions(topic: str, difficulty: str, num_questions: int = 10) -> List[Dict[str, Any]]:
    """Generate a complete mock exam"""
    client = OpenRouterClient()
    return await client.generate_mock_questions(topic, difficulty, num_questions)