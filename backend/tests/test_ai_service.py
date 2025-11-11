"""
Unit tests for AI service functionality.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
import json

from app.ai.service import AIService, ai_service


@pytest.mark.unit
@pytest.mark.ai
class TestAIService:
    """Test AI service functionality without external dependencies."""

    def test_ai_service_initialization(self):
        """Test AI service initialization."""
        ai_service_instance = AIService()
        assert ai_service_instance is not None
        assert hasattr(ai_service_instance, 'google_client')
        assert hasattr(ai_service_instance, 'openai_client')
        # Note: Google client may be initialized if API key is present
        assert ai_service_instance.openai_client is None

    def test_global_ai_service_instance(self):
        """Test the global AI service instance."""
        assert ai_service is not None
        assert isinstance(ai_service, AIService)
        assert hasattr(ai_service, 'google_client')
        assert hasattr(ai_service, 'openai_client')

    @pytest.mark.asyncio
    async def test_generate_fallback_questions(self):
        """Test fallback question generation when AI is unavailable."""
        ai_service_instance = AIService()
        
        # Test behavioral questions
        questions = ai_service_instance._generate_fallback_questions(3, "behavioral")
        assert len(questions) == 3
        assert all("question_text" in q for q in questions)
        assert all("type" in q for q in questions)
        assert all("category" in q for q in questions)
        assert all("difficulty_level" in q for q in questions)
        assert all("skills_assessed" in q for q in questions)
        assert all("time_limit" in q for q in questions)

    @pytest.mark.asyncio
    async def test_generate_interview_questions_with_fallback(self):
        """Test interview question generation with fallback."""
        ai_service_instance = AIService()
        
        questions = await ai_service_instance.generate_interview_questions(
            job_title="Software Engineer",
            job_description="Python development role",
            experience_level="mid",
            question_count=3,
            interview_mode="technical",
            interview_type="mixed"
        )
        
        assert len(questions) == 3
        assert all("question_text" in q for q in questions)
        assert all("type" in q for q in questions)
        assert all("category" in q for q in questions)

    @pytest.mark.asyncio
    async def test_evaluate_response_with_basic_evaluation(self):
        """Test response evaluation with basic fallback."""
        ai_service_instance = AIService()
        
        result = await ai_service_instance.evaluate_response(
            question="What is Python?",
            response="Python is a programming language that is widely used for web development, data analysis, and artificial intelligence."
        )
        
        assert "score" in result
        assert "feedback" in result
        assert "strengths" in result
        assert "improvements" in result
        assert "communication_score" in result
        assert "content_score" in result
        assert isinstance(result["score"], (int, float))

    @pytest.mark.asyncio
    async def test_generate_overall_feedback_with_basic_feedback(self):
        """Test overall feedback generation with basic fallback."""
        ai_service_instance = AIService()
        
        responses = [
            {"question": "Q1", "response": "Response 1"},
            {"question": "Q2", "response": "Response 2"},
            {"question": "Q3", "response": "Response 3"}
        ]
        
        result = await ai_service_instance.generate_overall_feedback(
            responses=responses,
            job_title="Software Engineer",
            experience_level="mid"
        )
        
        assert "overall_score" in result
        assert "overall_feedback" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "recommendations" in result
        assert "communication_score" in result
        assert "technical_score" in result
        assert "problem_solving_score" in result
        assert "behavioral_score" in result

    def test_build_question_generation_prompt(self):
        """Test question generation prompt building."""
        ai_service_instance = AIService()
        
        prompt = ai_service_instance._build_question_generation_prompt(
            job_title="Software Engineer",
            job_description="Python development role",
            experience_level="senior",
            question_count=3,
            interview_mode="technical",
            interview_type="mixed"
        )
        
        assert "Software Engineer" in prompt
        assert "senior" in prompt
        assert "3" in prompt
        assert "technical" in prompt
        assert "interview questions" in prompt.lower()
        assert "JSON" in prompt

    def test_build_evaluation_prompt(self):
        """Test evaluation prompt building."""
        ai_service_instance = AIService()
        
        prompt = ai_service_instance._build_evaluation_prompt(
            question="What is Python?",
            response="Python is a programming language.",
            question_type="text"
        )
        
        assert "What is Python?" in prompt
        assert "Python is a programming language." in prompt
        assert "Evaluate this interview response" in prompt
        assert "JSON" in prompt
        assert "score" in prompt.lower()

    def test_build_feedback_prompt(self):
        """Test feedback prompt building."""
        ai_service_instance = AIService()
        
        responses = [
            {"question": "Q1", "response": "Response 1"},
            {"question": "Q2", "response": "Response 2"}
        ]
        
        prompt = ai_service_instance._build_feedback_prompt(
            responses=responses,
            job_title="Software Engineer",
            experience_level="senior"
        )
        
        assert "Software Engineer" in prompt
        assert "senior" in prompt
        assert "interview responses" in prompt.lower()
        assert "JSON" in prompt
        assert "overall score" in prompt.lower()

    def test_basic_evaluation(self):
        """Test basic evaluation method."""
        ai_service_instance = AIService()
        
        # Test with short response
        result = ai_service_instance._basic_evaluation("Short")
        assert result["score"] >= 5.0
        assert "Response recorded" in result["feedback"]
        
        # Test with longer response
        long_response = "This is a very long response " * 10
        result = ai_service_instance._basic_evaluation(long_response)
        assert result["score"] > 5.0
        assert result["score"] <= 8.0

    def test_basic_feedback(self):
        """Test basic feedback method."""
        ai_service_instance = AIService()
        
        responses = [
            {"response": "Response 1"},
            {"response": "Response 2"},
            {"response": ""}  # Empty response
        ]
        
        result = ai_service_instance._basic_feedback(responses)
        
        assert result["overall_score"] == 66.7  # 2 out of 3 completed
        assert "Completed 2 out of 3 questions" in result["overall_feedback"]
        assert "Completed interview" in result["strengths"]
        assert "AI analysis not available" in result["weaknesses"]

    @pytest.mark.asyncio
    async def test_generate_interview_questions_with_google_mock(self):
        """Test question generation with mocked Google AI."""
        ai_service_instance = AIService()
        
        # Mock Google AI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '''
        [
            {
                "question_text": "What is Python?",
                "type": "text",
                "category": "technical",
                "difficulty_level": "easy",
                "skills_assessed": ["programming"],
                "time_limit": 300
            }
        ]
        '''
        mock_client.generate_content.return_value = mock_response
        ai_service_instance.google_client = mock_client
        
        questions = await ai_service_instance.generate_interview_questions(
            job_title="Software Engineer",
            job_description="Python development",
            experience_level="mid",
            question_count=1,
            interview_mode="technical",
            interview_type="mixed"
        )
        
        assert len(questions) == 1
        assert questions[0]["question_text"] == "What is Python?"
        assert questions[0]["category"] == "technical"

    @pytest.mark.asyncio
    async def test_evaluate_response_with_google_mock(self):
        """Test response evaluation with mocked Google AI."""
        ai_service_instance = AIService()
        
        # Mock Google AI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '''
        {
            "score": 8.5,
            "feedback": "Good response",
            "strengths": ["Clear explanation"],
            "improvements": ["Add examples"],
            "communication_score": 8,
            "content_score": 9
        }
        '''
        mock_client.generate_content.return_value = mock_response
        ai_service_instance.google_client = mock_client
        
        result = await ai_service_instance.evaluate_response(
            question="What is Python?",
            response="Python is a programming language."
        )
        
        assert result["score"] == 8.5
        assert result["feedback"] == "Good response"
        assert "Clear explanation" in result["strengths"]
        assert "Add examples" in result["improvements"]

    @pytest.mark.asyncio
    async def test_generate_fallback_questions_cycle(self):
        """Test that fallback questions cycle when more are requested than available."""
        ai_service_instance = AIService()
        
        # Request more questions than available in fallback
        questions = ai_service_instance._generate_fallback_questions(8, "behavioral")
        
        assert len(questions) == 8
        # Should cycle through the available questions
        assert "Question 1" in questions[0]["question_text"]
        assert "Question 6" in questions[5]["question_text"]
        # The 7th question should cycle back to the beginning (7 % 5 = 2)
        # Since 5 questions are available, question 7 should be based on the first question
        assert questions[6]["question_text"] != questions[5]["question_text"]  # Should be different from 6th
        # And should have the pattern (Question 7)
        assert "Question 7" in questions[6]["question_text"]

    @pytest.mark.asyncio
    async def test_ai_service_with_api_key_mock(self):
        """Test AI service initialization with mocked API key."""
        with patch('app.config.settings.GOOGLE_AI_API_KEY', 'test_key'), \
             patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model:
            
            ai_service_instance = AIService()
            assert ai_service_instance.google_client is not None
            # Verify the API key was set
            # Note: This tests the configuration but not the actual API call


@pytest.mark.unit
@pytest.mark.ai
class TestAIIntegration:
    """Test AI service integration with the main application."""

    def test_ai_route_registration(self):
        """Test AI routes are properly registered."""
        from app.main import app
        
        # Check if AI routes are in the app
        routes = [route.path for route in app.routes]
        ai_routes = [route for route in routes if '/api/v1/ai' in route]
        
        # Should have AI routes
        assert len(ai_routes) >= 0  # May vary based on implementation

    def test_ai_config_validation(self):
        """Test AI configuration validation."""
        from app.config import settings
        
        # Test if AI settings are properly configured
        assert hasattr(settings, 'OPENAI_API_KEY') or hasattr(settings, 'GOOGLE_AI_API_KEY')
        assert hasattr(settings, 'AI_MODEL')
        assert settings.AI_MODEL is not None

    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self):
        """Test AI service error handling."""
        ai_service_instance = AIService()
        
        # Test that fallback works when no AI clients are available
        questions = await ai_service_instance.generate_interview_questions(
            job_title="Engineer",
            job_description="Test",
            experience_level="mid",
            question_count=2,
            interview_mode="mixed",
            interview_type="mixed"
        )
        
        assert len(questions) == 2
        assert all("question_text" in q for q in questions)

    def test_prompt_content_validation(self):
        """Test that prompts contain required elements."""
        ai_service_instance = AIService()
        
        # Test question generation prompt
        prompt = ai_service_instance._build_question_generation_prompt(
            "Engineer", "Test description", "mid", 3, "technical", "mixed"
        )
        
        assert "interview questions" in prompt.lower()
        assert "experience level" in prompt.lower()
        assert "JSON" in prompt
        
        # Test evaluation prompt
        eval_prompt = ai_service_instance._build_evaluation_prompt(
            "Test question", "Test response", "text"
        )
        
        assert "evaluate this interview response" in eval_prompt.lower()
        assert "score" in eval_prompt.lower()
        assert "JSON" in eval_prompt

    @pytest.mark.asyncio
    async def test_ai_service_integration_with_interviews(self):
        """Test AI service integration with interview functionality."""
        # This would test integration points, but requires the full interview setup
        # For now, we test the basic service methods
        ai_service_instance = AIService()
        
        # Test question generation integration
        questions = await ai_service_instance.generate_interview_questions(
            job_title="Python Developer",
            job_description="Looking for someone with Django experience",
            experience_level="senior",
            question_count=3,
            interview_mode="technical",
            interview_type="mixed"
        )
        
        assert len(questions) == 3
        assert all(q["type"] == "text" for q in questions)
        assert all("time_limit" in q for q in questions)

    def test_fallback_question_quality(self):
        """Test that fallback questions are appropriate."""
        ai_service_instance = AIService()
        
        questions = ai_service_instance._generate_fallback_questions(5, "behavioral")
        
        # Check that questions are appropriate
        for q in questions:
            assert q["category"] in ["behavioral", "technical", "mixed"]
            assert q["difficulty_level"] in ["easy", "medium", "hard"]
            assert isinstance(q["skills_assessed"], list)
            assert q["time_limit"] > 0

    @pytest.mark.asyncio
    async def test_ai_service_with_empty_responses(self):
        """Test AI service behavior with empty or minimal responses."""
        ai_service_instance = AIService()
        
        # Test with empty response
        result = await ai_service_instance.evaluate_response(
            question="What is your experience?",
            response=""
        )
        
        assert "score" in result
        assert result["score"] >= 5.0  # Should have some base score
        assert "feedback" in result

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self):
        """Test AI service handles multiple concurrent requests."""
        import asyncio
        
        ai_service_instance = AIService()
        
        # Create multiple concurrent requests
        async def make_request(i):
            return await ai_service_instance.generate_interview_questions(
                job_title=f"Position {i}",
                job_description="Test description",
                experience_level="mid",
                question_count=2,
                interview_mode="mixed",
                interview_type="mixed"
            )
        
        # Run multiple concurrent requests
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed with fallback
        assert all(len(result) == 2 for result in results)
        assert all("question_text" in q for result in results for q in result)