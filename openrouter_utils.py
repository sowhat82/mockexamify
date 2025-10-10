"""
Enhanced OpenRouter API utilities for MockExamify
Comprehensive AI-powered content generation and explanations
"""
import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional
import logging
import config

logger = logging.getLogger(__name__)

class OpenRouterManager:
    """Enhanced manager for OpenRouter API interactions"""
    
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3-haiku"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mockexamify.streamlit.app",
            "X-Title": "MockExamify"
        }
    
    async def generate_explanation(self, question: str, choices: List[str], correct_index: int, 
                                 scenario: str = "", explanation_seed: str = "") -> str:
        """Generate detailed explanation for a single question"""
        try:
            prompt = self._create_explanation_prompt(
                question, choices, correct_index, scenario, explanation_seed
            )
            
            explanation = await self._generate_text(prompt)
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Explanation temporarily unavailable. Please try again later."
    
    async def generate_batch_explanations(self, questions: List[Dict[str, Any]], 
                                        user_answers: List[int]) -> List[str]:
        """Generate explanations for multiple questions in batch"""
        explanations = []
        
        # Process in smaller batches to avoid rate limits
        batch_size = 3
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            batch_answers = user_answers[i:i + batch_size]
            
            batch_explanations = await asyncio.gather(
                *[
                    self.generate_explanation(
                        q['question'],
                        q.get('choices', []),
                        q.get('correct_index', 0),
                        q.get('scenario', ''),
                        q.get('explanation_seed', '')
                    )
                    for q in batch
                ],
                return_exceptions=True
            )
            
            # Handle exceptions in batch results
            for exp in batch_explanations:
                if isinstance(exp, Exception):
                    explanations.append("Explanation temporarily unavailable.")
                else:
                    explanations.append(exp)
            
            # Add delay between batches to respect rate limits
            if i + batch_size < len(questions):
                await asyncio.sleep(1)
        
        return explanations
    
    async def generate_mock_exam(self, topic: str, difficulty: str, num_questions: int = 10,
                               include_scenarios: bool = False) -> Dict[str, Any]:
        """Generate a complete mock exam with metadata"""
        try:
            prompt = self._create_mock_generation_prompt(
                topic, difficulty, num_questions, include_scenarios
            )
            
            response = await self._generate_text(prompt, max_tokens=4000)
            questions = self._parse_mock_questions(response)
            
            # Create mock exam metadata
            mock_data = {
                "title": f"{topic} - {difficulty.title()} Level Mock Exam",
                "description": f"AI-generated {difficulty} level practice exam covering {topic}",
                "topic": topic,
                "difficulty": difficulty,
                "time_limit_minutes": min(num_questions * 2, 120),  # 2 min per question, max 2 hours
                "questions_json": questions,
                "total_questions": len(questions),
                "ai_generated": True,
                "explanation_enabled": True,
                "price_credits": max(1, len(questions) // 5)  # 1 credit per 5 questions
            }
            
            return mock_data
            
        except Exception as e:
            logger.error(f"Error generating mock exam: {e}")
            return {}
    
    async def enhance_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance an existing question with better explanations and metadata"""
        try:
            prompt = self._create_enhancement_prompt(question)
            response = await self._generate_text(prompt)
            
            enhanced_data = self._parse_question_enhancement(response)
            
            # Merge enhanced data with original
            enhanced_question = question.copy()
            enhanced_question.update(enhanced_data)
            
            return enhanced_question
            
        except Exception as e:
            logger.error(f"Error enhancing question: {e}")
            return question
    
    async def generate_study_tips(self, topic: str, user_performance: Dict[str, Any]) -> str:
        """Generate personalized study tips based on user performance"""
        try:
            prompt = self._create_study_tips_prompt(topic, user_performance)
            tips = await self._generate_text(prompt)
            return tips
            
        except Exception as e:
            logger.error(f"Error generating study tips: {e}")
            return "Keep practicing and reviewing the material. Focus on areas where you scored lower."
    
    async def validate_question_quality(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and rate the quality of a question"""
        try:
            prompt = self._create_validation_prompt(question)
            response = await self._generate_text(prompt)
            
            validation_result = self._parse_validation_result(response)
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating question: {e}")
            return {"score": 7, "feedback": "Unable to validate question quality"}
    
    async def _generate_text(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
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
                                "content": "You are an expert educational content creator and exam specialist. Provide clear, accurate, and helpful responses."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "frequency_penalty": 0.1,
                        "presence_penalty": 0.1
                    }
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
    
    def _create_explanation_prompt(self, question: str, choices: List[str], correct_index: int,
                                 scenario: str = "", explanation_seed: str = "") -> str:
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
    
    def _create_mock_generation_prompt(self, topic: str, difficulty: str, num_questions: int,
                                     include_scenarios: bool = False) -> str:
        """Create enhanced prompt for generating complete mock exams"""
        scenario_instruction = "Include brief scenarios for some questions when appropriate." if include_scenarios else ""
        
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
        avg_score = user_performance.get('average_score', 0)
        weak_areas = user_performance.get('weak_areas', [])
        strong_areas = user_performance.get('strong_areas', [])
        
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
    
    def _parse_mock_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract mock exam questions"""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
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
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
                
        except Exception as e:
            logger.error(f"Error parsing question enhancement: {e}")
        
        return {}
    
    def _parse_validation_result(self, response: str) -> Dict[str, Any]:
        """Parse AI response for validation result"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
                
        except Exception as e:
            logger.error(f"Error parsing validation result: {e}")
        
        return {"score": 5, "feedback": "Unable to validate"}
    
    def _validate_question_format(self, question: Dict[str, Any]) -> bool:
        """Validate question format and content"""
        required_fields = ['question', 'choices', 'correct_index']
        
        # Check required fields
        for field in required_fields:
            if field not in question:
                return False
        
        # Validate choices
        choices = question['choices']
        if not isinstance(choices, list) or len(choices) != 4:
            return False
        
        # Validate correct_index
        correct_index = question['correct_index']
        if not isinstance(correct_index, int) or not (0 <= correct_index < 4):
            return False
        
        # Check for empty content
        if not question['question'].strip():
            return False
        
        for choice in choices:
            if not choice.strip():
                return False
        
        return True
    
    def _clean_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize question data"""
        cleaned = {
            'question': question['question'].strip(),
            'choices': [choice.strip() for choice in question['choices']],
            'correct_index': int(question['correct_index']),
            'explanation_seed': question.get('explanation_seed', '').strip(),
            'scenario': question.get('scenario', '').strip(),
            'difficulty': question.get('difficulty', 'medium'),
            'topic_tags': question.get('topic_tags', [])
        }
        
        return cleaned

# Global instance
openrouter_manager = OpenRouterManager()

# Helper functions for easy access
async def generate_explanation(question: str, choices: List[str], correct_index: int, 
                             scenario: str = "", explanation_seed: str = "") -> str:
    """Generate explanation for a single question"""
    return await openrouter_manager.generate_explanation(
        question, choices, correct_index, scenario, explanation_seed
    )

async def generate_batch_explanations(questions: List[Dict[str, Any]], 
                                    user_answers: List[int]) -> List[str]:
    """Generate explanations for multiple questions"""
    return await openrouter_manager.generate_batch_explanations(questions, user_answers)

async def generate_mock_exam(topic: str, difficulty: str, num_questions: int = 10,
                           include_scenarios: bool = False) -> Dict[str, Any]:
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