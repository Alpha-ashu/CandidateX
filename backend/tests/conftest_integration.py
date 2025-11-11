"""
Integration test configuration and fixtures.
Provides comprehensive setup for API integration testing.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from fastapi.testclient import TestClient
from httpx import AsyncClient
import httpx
import os
import tempfile
from unittest.mock import patch

from app.main import app
from app.models.user import UserRole, UserStatus
from app.utils.database import create_test_user, delete_user_data


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user_candidate():
    """Create a test candidate user for integration testing."""
    email = "test.candidate.integration@candidatex.com"
    user_id = await create_test_user(
        email=email,
        full_name="Test Candidate Integration",
        role=UserRole.CANDIDATE
    )
    yield {"id": user_id, "email": email, "role": UserRole.CANDIDATE}
    # Cleanup will be handled by the test cleanup fixture


@pytest.fixture
async def test_user_recruiter():
    """Create a test recruiter user for integration testing."""
    email = "test.recruiter.integration@candidatex.com"
    user_id = await create_test_user(
        email=email,
        full_name="Test Recruiter Integration",
        role=UserRole.RECRUITER
    )
    yield {"id": user_id, "email": email, "role": UserRole.RECRUITER}
    # Cleanup will be handled by the test cleanup fixture


@pytest.fixture
async def test_user_admin():
    """Create a test admin user for integration testing."""
    email = "test.admin.integration@candidatex.com"
    user_id = await create_test_user(
        email=email,
        full_name="Test Admin Integration",
        role=UserRole.ADMIN
    )
    yield {"id": user_id, "email": email, "role": UserRole.ADMIN}
    # Cleanup will be handled by the test cleanup fixture


@pytest.fixture
async def authenticated_client_candidate(test_user_candidate, async_client: httpx.AsyncClient):
    """Create an authenticated client for candidate user."""
    # Login to get tokens
    login_data = {
        "email": test_user_candidate["email"],
        "password": "Test123!"
    }
    
    response = await async_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    yield {
        "client": async_client,
        "headers": headers,
        "user": test_user_candidate,
        "tokens": tokens
    }


@pytest.fixture
async def authenticated_client_recruiter(test_user_recruiter, async_client: httpx.AsyncClient):
    """Create an authenticated client for recruiter user."""
    # Login to get tokens
    login_data = {
        "email": test_user_recruiter["email"],
        "password": "Test123!"
    }
    
    response = await async_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    yield {
        "client": async_client,
        "headers": headers,
        "user": test_user_recruiter,
        "tokens": tokens
    }


@pytest.fixture
async def authenticated_client_admin(test_user_admin, async_client: httpx.AsyncClient):
    """Create an authenticated client for admin user."""
    # Login to get tokens
    login_data = {
        "email": test_user_admin["email"],
        "password": "Test123!"
    }
    
    response = await async_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    yield {
        "client": async_client,
        "headers": headers,
        "user": test_user_admin,
        "tokens": tokens
    }


@pytest.fixture
def mock_ai_service():
    """Mock AI service for integration tests."""
    with patch("app.ai.service.ai_service") as mock_service:
        # Mock common AI service methods
        mock_service.generate_interview_questions.return_value = [
            {
                "question_id": "q1",
                "question_text": "What is your experience with Python?",
                "question_type": "technical",
                "expected_skills": ["Python", "Programming"]
            },
            {
                "question_id": "q2", 
                "question_text": "Tell me about a challenging project you worked on",
                "question_type": "behavioral",
                "expected_skills": ["Communication", "Problem Solving"]
            }
        ]
        
        mock_service.evaluate_response.return_value = {
            "score": 85,
            "feedback": "Good technical response with clear examples",
            "strengths": ["Technical knowledge", "Clear communication"],
            "improvements": ["Provide more specific examples"]
        }
        
        yield mock_service


@pytest.fixture
def mock_database():
    """Mock database for integration tests."""
    # This would typically involve setting up test database or using test collections
    # For now, we'll use in-memory mocking
    with patch("app.utils.database.db_manager") as mock_db_manager:
        yield mock_db_manager


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        "test_user_password": "Test123!",
        "test_interview_data": {
            "job_title": "Software Engineer",
            "job_description": "Full-stack development position",
            "experience_level": "mid",
            "question_count": 5,
            "interview_mode": "technical"
        },
        "api_endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users", 
            "interviews": "/api/v1/interviews",
            "dashboard": "/api/v1/dashboard",
            "admin": "/api/v1/admin",
            "ai": "/api/v1/ai"
        }
    }


@pytest.fixture
async def cleanup_test_users():
    """Cleanup fixture for test users."""
    test_users = []
    
    async def add_test_user(user_data):
        test_users.append(user_data)
    
    yield add_test_user
    
    # Cleanup all test users after test
    for user_data in test_users:
        try:
            await delete_user_data(user_data["id"], user_data["role"])
        except Exception as e:
            print(f"Warning: Failed to cleanup user {user_data.get('id', 'unknown')}: {e}")


@pytest.fixture
def test_data_factory():
    """Factory for creating test data."""
    class TestDataFactory:
        @staticmethod
        def create_user_registration_data(role: str = "candidate", email: str = None):
            """Create user registration test data."""
            import random
            import string
            
            if not email:
                email = f"test.{role}.{''.join(random.choices(string.ascii_lowercase, k=8))}@test.com"
                
            return {
                "email": email,
                "password": "TestPass123!",
                "full_name": f"Test {role.title()} User",
                "role": role
            }
        
        @staticmethod
        def create_interview_creation_data():
            """Create interview creation test data."""
            return {
                "job_title": "Test Software Engineer",
                "job_description": "Test job description for integration testing",
                "experience_level": "mid",
                "question_count": 3,
                "interview_mode": "technical",
                "target_skills": ["Python", "JavaScript", "Testing"]
            }
        
        @staticmethod
        def create_login_data(email: str, password: str = "Test123!"):
            """Create login test data."""
            return {
                "email": email,
                "password": password
            }
        
        @staticmethod
        def create_dashboard_stats_request():
            """Create dashboard stats request data."""
            return {
                "timeframe": "30days",
                "include_trends": True
            }
    
    return TestDataFactory()


@pytest.fixture
def temp_file_factory():
    """Factory for creating temporary files for testing."""
    class TempFileFactory:
        @staticmethod
        def create_test_file(content: str = "test content", suffix: str = ".txt"):
            """Create a temporary test file."""
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
                f.write(content)
                return f.name
        
        @staticmethod
        def create_test_pdf_file():
            """Create a minimal PDF file for testing."""
            # This is a minimal PDF content
            pdf_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj

xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
178
%%EOF"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
                f.write(pdf_content)
                return f.name
    
    return TempFileFactory()


# Mark all integration tests
def pytest_configure(config):
    """Configure pytest markers for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    )


# Custom assertions for integration tests
class IntegrationTestAssertions:
    """Custom assertions for integration testing."""
    
    @staticmethod
    def assert_response_success(response, expected_status_code=200):
        """Assert that response indicates success."""
        assert response.status_code == expected_status_code, f"Expected {expected_status_code}, got {response.status_code}: {response.text}"
    
    @staticmethod
    def assert_response_error(response, expected_status_code=None):
        """Assert that response indicates an error."""
        if expected_status_code:
            assert response.status_code == expected_status_code, f"Expected {expected_status_code}, got {response.status_code}"
        else:
            assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
    
    @staticmethod
    def assert_json_response(response, expected_keys=None):
        """Assert that response is valid JSON and contains expected keys."""
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)
        
        if expected_keys:
            for key in expected_keys:
                assert key in data, f"Expected key '{key}' not found in response: {data}"
        
        return data
    
    @staticmethod
    def assert_authenticated_response(response):
        """Assert that response indicates successful authentication."""
        data = IntegrationTestAssertions.assert_json_response(response, ["access_token", "refresh_token", "user"])
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert "id" in data["user"]
        assert "email" in data["user"]
        assert "role" in data["user"]
        
        return data


@pytest.fixture
def assertions():
    """Provide custom assertions for integration tests."""
    return IntegrationTestAssertions()