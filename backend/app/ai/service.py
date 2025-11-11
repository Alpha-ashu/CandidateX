"""
AI service integration for question generation and response evaluation.
"""
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# AI service imports
import google.generativeai as genai
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """AI service for interview question generation and evaluation."""

    def __init__(self):
        self.google_client = None
        self.openai_client = None

        # Initialize Google AI if API key is available
        if settings.GOOGLE_AI_API_KEY:
            try:
                genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
                self.google_client = genai.GenerativeModel(settings.AI_MODEL)
                logger.info("Google AI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google AI: {e}")

        # Initialize OpenAI if API key is available
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key":
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")

    async def generate_interview_questions(
        self,
        job_title: str,
        job_description: Optional[str],
        experience_level: str,
        question_count: int,
        interview_mode: str,
        interview_type: str
    ) -> List[Dict[str, Any]]:
        """
        Generate interview questions using AI.
        """
        prompt = self._build_question_generation_prompt(
            job_title, job_description, experience_level,
            question_count, interview_mode, interview_type
        )

        try:
            if self.google_client:
                return await self._generate_with_google(prompt, question_count)
            elif self.openai_client:
                return await self._generate_with_openai(prompt, question_count)
            else:
                logger.warning("No AI client available, using fallback questions")
                return self._generate_fallback_questions(question_count, interview_mode)
        except Exception as e:
            logger.error(f"AI question generation failed: {e}")
            return self._generate_fallback_questions(question_count, interview_mode)

    async def evaluate_response(
        self,
        question: str,
        response: str,
        question_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's response using AI.
        """
        prompt = self._build_evaluation_prompt(question, response, question_type)

        try:
            if self.google_client:
                return await self._evaluate_with_google(prompt)
            elif self.openai_client:
                return await self._evaluate_with_openai(prompt)
            else:
                logger.warning("No AI client available, using basic evaluation")
                return self._basic_evaluation(response)
        except Exception as e:
            logger.error(f"AI response evaluation failed: {e}")
            return self._basic_evaluation(response)

    async def generate_overall_feedback(
        self,
        responses: List[Dict[str, Any]],
        job_title: str,
        experience_level: str
    ) -> Dict[str, Any]:
        """
        Generate overall interview feedback.
        """
        prompt = self._build_feedback_prompt(responses, job_title, experience_level)

        try:
            if self.google_client:
                return await self._generate_feedback_with_google(prompt)
            elif self.openai_client:
                return await self._generate_feedback_with_openai(prompt)
            else:
                logger.warning("No AI client available, using basic feedback")
                return self._basic_feedback(responses)
        except Exception as e:
            logger.error(f"AI feedback generation failed: {e}")
            return self._basic_feedback(responses)

    def _build_question_generation_prompt(
        self,
        job_title: str,
        job_description: Optional[str],
        experience_level: str,
        question_count: int,
        interview_mode: str,
        interview_type: str
    ) -> str:
        """Build prompt for question generation."""
        experience_map = {
            "entry": "junior or entry-level",
            "mid": "mid-level",
            "senior": "senior or experienced"
        }

        mode_instructions = {
            "behavioral": "Focus on behavioral questions that assess past experiences, problem-solving, and soft skills.",
            "technical": "Focus on technical questions related to the job requirements and industry knowledge.",
            "mixed": "Mix of behavioral and technical questions appropriate for the role."
        }

        prompt = f"""
        Generate {question_count} interview questions for a {experience_map.get(experience_level, 'mid-level')} {job_title} position.

        Job Description: {job_description or 'Not provided'}

        Interview Mode: {interview_mode}
        Instructions: {mode_instructions.get(interview_mode, mode_instructions['mixed'])}

        Requirements:
        1. Questions should be appropriate for the experience level
        2. Include a mix of question types (situational, problem-solving, technical knowledge)
        3. Each question should assess relevant skills for the role
        4. Provide clear, concise questions
        5. Include context or follow-up prompts where helpful

        Return the questions as a JSON array of objects with this format:
        [
            {{
                "question_text": "Question here?",
                "type": "text",
                "category": "behavioral|technical|mixed",
                "difficulty_level": "easy|medium|hard",
                "skills_assessed": ["skill1", "skill2"],
                "time_limit": 300
            }}
        ]
        """

        return prompt

    def _build_evaluation_prompt(self, question: str, response: str, question_type: str) -> str:
        """Build prompt for response evaluation."""
        prompt = f"""
        Evaluate this interview response:

        Question: {question}
        Response: {response}

        Provide a detailed evaluation including:
        1. Score (0-10 scale)
        2. Key strengths
        3. Areas for improvement
        4. Specific feedback
        5. Communication effectiveness
        6. Content relevance

        Return as JSON with this structure:
        {{
            "score": 7.5,
            "feedback": "Detailed feedback here",
            "strengths": ["Strength 1", "Strength 2"],
            "improvements": ["Improvement 1", "Improvement 2"],
            "communication_score": 8,
            "content_score": 7
        }}
        """

        return prompt

    def _build_feedback_prompt(
        self,
        responses: List[Dict[str, Any]],
        job_title: str,
        experience_level: str
    ) -> str:
        """Build prompt for overall feedback generation."""
        # Summarize responses for the prompt
        response_summary = "\n".join([
            f"Q{i+1}: {r.get('question', 'N/A')}\nA: {r.get('response', 'N/A')[:200]}..."
            for i, r in enumerate(responses[:5])  # Limit to first 5 for prompt length
        ])

        prompt = f"""
        Generate comprehensive feedback for a {experience_level} {job_title} interview.

        Interview Responses Summary:
        {response_summary}

        Provide overall feedback including:
        1. Overall score (0-100)
        2. Summary of performance
        3. Key strengths
        4. Areas needing improvement
        5. Specific recommendations
        6. Detailed scores for different competencies

        Return as JSON with this structure:
        {{
            "overall_score": 75,
            "overall_feedback": "Summary here",
            "strengths": ["Strength 1", "Strength 2"],
            "weaknesses": ["Weakness 1", "Weakness 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"],
            "communication_score": 8,
            "technical_score": 7,
            "problem_solving_score": 6,
            "behavioral_score": 8
        }}
        """

        return prompt

    async def _generate_with_google(self, prompt: str, question_count: int) -> List[Dict[str, Any]]:
        """Generate questions using Google AI."""
        try:
            response = self.google_client.generate_content(prompt)
            # Extract the JSON response from the AI
            response_text = response.text.strip()

            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                if isinstance(result, list) and len(result) > 0:
                    return result
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if isinstance(result, list) and len(result) > 0:
                        return result

            # If JSON parsing fails, create structured questions from text
            logger.warning("Failed to parse JSON from Google AI response, using fallback")
            return self._generate_fallback_questions(question_count, "mixed")

        except Exception as e:
            logger.error(f"Google AI generation failed: {e}")
            raise

    async def _generate_with_openai(self, prompt: str, question_count: int) -> List[Dict[str, Any]]:
        """Generate questions using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )

            response_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                if isinstance(result, list) and len(result) > 0:
                    return result
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if isinstance(result, list) and len(result) > 0:
                        return result

            # If JSON parsing fails, create structured questions from text
            logger.warning("Failed to parse JSON from OpenAI response, using fallback")
            return self._generate_fallback_questions(question_count, "mixed")

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    def _generate_fallback_questions(self, question_count: int, interview_mode: str) -> List[Dict[str, Any]]:
        """Generate fallback questions when AI is unavailable."""
        fallback_questions = [
            {
                "question_text": "Tell me about yourself and your background.",
                "type": "text",
                "category": "behavioral",
                "difficulty_level": "easy",
                "skills_assessed": ["communication"],
                "time_limit": 300
            },
            {
                "question_text": "What are your greatest strengths?",
                "type": "text",
                "category": "behavioral",
                "difficulty_level": "easy",
                "skills_assessed": ["self-awareness"],
                "time_limit": 300
            },
            {
                "question_text": "Describe a challenging situation you faced and how you handled it.",
                "type": "text",
                "category": "behavioral",
                "difficulty_level": "medium",
                "skills_assessed": ["problem-solving", "communication"],
                "time_limit": 300
            },
            {
                "question_text": "Where do you see yourself in 5 years?",
                "type": "text",
                "category": "behavioral",
                "difficulty_level": "medium",
                "skills_assessed": ["planning", "career-goals"],
                "time_limit": 300
            },
            {
                "question_text": "Why are you interested in this position?",
                "type": "text",
                "category": "behavioral",
                "difficulty_level": "easy",
                "skills_assessed": ["motivation"],
                "time_limit": 300
            }
        ]

        # Return requested number of questions, cycling through available ones
        result = []
        for i in range(question_count):
            question = fallback_questions[i % len(fallback_questions)].copy()
            question["question_text"] = f"{question['question_text']} (Question {i+1})"
            result.append(question)

        return result

    async def _evaluate_with_google(self, prompt: str) -> Dict[str, Any]:
        """Evaluate response using Google AI."""
        try:
            response = self.google_client.generate_content(prompt)
            response_text = response.text.strip()

            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                if isinstance(result, dict) and "score" in result:
                    return result
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if isinstance(result, dict) and "score" in result:
                        return result

            # If JSON parsing fails, return basic evaluation
            logger.warning("Failed to parse JSON from Google AI evaluation response")
            return self._basic_evaluation("Response text")

        except Exception as e:
            logger.error(f"Google AI evaluation failed: {e}")
            raise

    async def _evaluate_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Evaluate response using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )

            response_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                if isinstance(result, dict) and "score" in result:
                    return result
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if isinstance(result, dict) and "score" in result:
                        return result

            # If JSON parsing fails, return basic evaluation
            logger.warning("Failed to parse JSON from OpenAI evaluation response")
            return self._basic_evaluation("Response text")

        except Exception as e:
            logger.error(f"OpenAI evaluation failed: {e}")
            raise

    def _basic_evaluation(self, response: str) -> Dict[str, Any]:
        """Basic evaluation when AI is unavailable."""
        length_score = min(len(response.split()) / 50, 1.0)  # Basic length check
        score = 5.0 + (length_score * 3.0)  # 5-8 range

        return {
            "score": round(score, 1),
            "feedback": "Response recorded. AI evaluation not available.",
            "strengths": ["Completed response"],
            "improvements": ["AI analysis not available"],
            "communication_score": 5,
            "content_score": 5
        }

    async def _generate_feedback_with_google(self, prompt: str) -> Dict[str, Any]:
        """Generate feedback using Google AI."""
        try:
            response = self.google_client.generate_content(prompt)
            response_text = response.text.strip()

            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                if isinstance(result, dict) and "overall_score" in result:
                    return result
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if isinstance(result, dict) and "overall_score" in result:
                        return result

            # If JSON parsing fails, return basic feedback
            logger.warning("Failed to parse JSON from Google AI feedback response")
            return self._basic_feedback([])

        except Exception as e:
            logger.error(f"Google AI feedback failed: {e}")
            raise

    async def _generate_feedback_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Generate feedback using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )

            response_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                if isinstance(result, dict) and "overall_score" in result:
                    return result
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if isinstance(result, dict) and "overall_score" in result:
                        return result

            # If JSON parsing fails, return basic feedback
            logger.warning("Failed to parse JSON from OpenAI feedback response")
            return self._basic_feedback([])

        except Exception as e:
            logger.error(f"OpenAI feedback failed: {e}")
            raise

    def _basic_feedback(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Basic feedback when AI is unavailable."""
        completed_responses = len([r for r in responses if r.get('response')])
        score = (completed_responses / len(responses)) * 100 if responses else 0

        return {
            "overall_score": round(score, 1),
            "overall_feedback": f"Completed {completed_responses} out of {len(responses)} questions. AI analysis not available.",
            "strengths": ["Completed interview"],
            "weaknesses": ["AI analysis not available"],
            "recommendations": ["Complete more practice interviews"],
            "communication_score": 5,
            "technical_score": 5,
            "problem_solving_score": 5,
            "behavioral_score": 5
        }

# Global AI service instance
ai_service = AIService()
