"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from typing import Dict, Any


@pytest.mark.api
@pytest.mark.auth
class TestAuthentication:
    """Test authentication endpoints."""

    async def test_user_registration(self, client: AsyncClient):
        """Test user registration."""
        user_data = {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "securepassword123"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data

    async def test_user_registration_duplicate_email(self, client: AsyncClient, test_user: Dict[str, Any]):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user["email"],  # Existing email
            "full_name": "Duplicate User",
            "password": "securepassword123"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_user_login(self, client: AsyncClient, test_user: Dict[str, Any]):
        """Test user login."""
        login_data = {
            "username": test_user["email"],
            "password": "testpassword123"
        }

        response = await client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_user_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = await client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_get_current_user_profile(self, client: AsyncClient, auth_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test getting current user profile."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["full_name"] == test_user["full_name"]
        assert data["role"] == test_user["role"]

    async def test_get_current_user_profile_unauthorized(self, client: AsyncClient):
        """Test getting user profile without authentication."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    async def test_password_reset_request(self, client: AsyncClient, test_user: Dict[str, Any]):
        """Test password reset request."""
        reset_data = {"email": test_user["email"]}

        response = await client.post("/api/v1/auth/forgot-password", json=reset_data)

        # Should always return success for security (doesn't reveal if email exists)
        assert response.status_code == 200
        assert "password reset link" in response.json()["message"]

    async def test_refresh_token(self, client: AsyncClient, test_user: Dict[str, Any]):
        """Test token refresh."""
        # First login to get tokens
        login_data = {
            "username": test_user["email"],
            "password": "testpassword123"
        }

        login_response = await client.post("/api/v1/auth/login", data=login_data)
        refresh_token = login_response.json()["refresh_token"]

        # Now refresh the token
        refresh_data = {"refresh_token": refresh_token}
        response = await client.post("/api/v1/auth/refresh-token", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token  # Should be a new token


@pytest.mark.unit
@pytest.mark.auth
class TestAuthUtils:
    """Test authentication utility functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        from app.auth.utils import get_password_hash, verify_password

        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        from app.auth.utils import create_access_token, verify_token
        from app.models.user import UserRole

        token_data = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "candidate"
        }

        token = create_access_token(token_data)
        decoded = verify_token(token)

        assert decoded is not None
        assert decoded.user_id == "user123"
        assert decoded.email == "test@example.com"
        assert decoded.role == UserRole.CANDIDATE

    def test_password_strength_validation(self):
        """Test password strength validation."""
        from app.auth.utils import validate_password_strength

        # Strong password
        strong_result = validate_password_strength("StrongPass123!")
        assert strong_result["valid"]
        assert strong_result["length"]
        assert strong_result["uppercase"]
        assert strong_result["lowercase"]
        assert strong_result["digit"]
        assert strong_result["special"]

        # Weak password
        weak_result = validate_password_strength("weak")
        assert not weak_result["valid"]
        assert not weak_result["length"]
        assert not weak_result["uppercase"]
        assert not weak_result["digit"]
        assert not weak_result["special"]
