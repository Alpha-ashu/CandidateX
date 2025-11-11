"""
Pytest configuration and fixtures for CandidateX backend tests.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import Dict, Any, AsyncGenerator
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from fastapi import FastAPI
from typing import Generator

from app.main import app
from app.config import settings
from app.models import init_database, init_redis


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Create a test MongoDB database."""
    # Use test database
    test_db_name = "candidatex_test"
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[test_db_name]

    # Clean up before tests
    await client.drop_database(test_db_name)

    init_database(client)

    yield db

    # Clean up after tests
    await client.drop_database(test_db_name)
    client.close()


@pytest_asyncio.fixture(scope="session")
async def test_redis():
    """Create a test Redis connection."""
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB + 1,  # Use different DB for tests
        decode_responses=True
    )

    # Clean up before tests
    await redis_client.flushdb()

    init_redis(redis_client)

    yield redis_client

    # Clean up after tests
    await redis_client.flushdb()
    await redis_client.close()


@pytest.fixture
def client(test_db, test_redis):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def test_user(test_db) -> Dict[str, Any]:
    """Create a test user."""
    from app.models.user import UserCreate
    from app.auth.utils import get_password_hash

    user_data = UserCreate(
        email="test@example.com",
        full_name="Test User",
        password="testpassword123"
    )

    user_doc = {
        "email": user_data.email,
        "full_name": user_data.full_name,
        "password_hash": get_password_hash(user_data.password),
        "role": "candidate",
        "status": "active",
        "email_verified": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }

    result = await test_db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    return user_doc


@pytest.fixture
async def auth_headers(client, test_user) -> Dict[str, str]:
    """Get authentication headers for test user."""
    from app.auth.utils import create_access_token

    token_data = {
        "sub": str(test_user["_id"]),
        "email": test_user["email"],
        "role": test_user["role"]
    }

    access_token = create_access_token(token_data)

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_interview(test_db, test_user) -> Dict[str, Any]:
    """Create a test interview."""
    from app.models.interview import InterviewCreate

    interview_data = InterviewCreate(
        job_title="Software Engineer",
        job_description="Develop web applications",
        experience_level="mid",
        question_count=5,
        time_limit_per_question=300
    )

    interview_doc = interview_data.dict()
    interview_doc["user_id"] = str(test_user["_id"])
    interview_doc["status"] = "created"
    interview_doc["questions"] = [
        {
            "id": f"q{i}",
            "question_text": f"Test question {i}?",
            "type": "text",
            "category": "technical",
            "difficulty_level": "medium",
            "skills_assessed": ["communication"],
            "time_limit": 300
        }
        for i in range(1, 6)
    ]
    interview_doc["responses"] = []
    interview_doc["created_at"] = "2025-01-01T00:00:00Z"
    interview_doc["updated_at"] = "2025-01-01T00:00:00Z"

    result = await test_db.interviews.insert_one(interview_doc)
    interview_doc["_id"] = result.inserted_id

    return interview_doc


@pytest.fixture
async def admin_user(test_db) -> Dict[str, Any]:
    """Create a test admin user."""
    from app.auth.utils import get_password_hash

    admin_doc = {
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password_hash": get_password_hash("adminpassword123"),
        "role": "admin",
        "status": "active",
        "email_verified": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }

    result = await test_db.users.insert_one(admin_doc)
    admin_doc["_id"] = result.inserted_id

    return admin_doc


@pytest.fixture
async def admin_auth_headers(client, admin_user) -> Dict[str, str]:
    """Get authentication headers for admin user."""
    from app.auth.utils import create_access_token

    token_data = {
        "sub": str(admin_user["_id"]),
        "email": admin_user["email"],
        "role": admin_user["role"]
    }

    access_token = create_access_token(token_data)

    return {"Authorization": f"Bearer {access_token}"}


# Custom test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "ai: AI service tests")


# Test utilities
class TestUtils:
    """Utility functions for tests."""

    @staticmethod
    def create_test_user_data(email: str = "test@example.com", role: str = "candidate") -> Dict[str, Any]:
        """Create test user data."""
        from app.auth.utils import get_password_hash

        return {
            "email": email,
            "full_name": "Test User",
            "password_hash": get_password_hash("testpassword123"),
            "role": role,
            "status": "active",
            "email_verified": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

    @staticmethod
    def create_test_interview_data(user_id: str) -> Dict[str, Any]:
        """Create test interview data."""
        return {
            "user_id": user_id,
            "job_title": "Software Engineer",
            "job_description": "Develop web applications",
            "experience_level": "mid",
            "question_count": 5,
            "time_limit_per_question": 300,
            "status": "created",
            "questions": [],
            "responses": [],
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

    @staticmethod
    def authenticate_user(client, email: str, password: str) -> Dict[str, str]:
        """Authenticate a user and return auth headers."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password}
        )

        if response.status_code == 200:
            token_data = response.json()
            return {"Authorization": f"Bearer {token_data['access_token']}"}

        return {}


# Make TestUtils available as a fixture
@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtils()
