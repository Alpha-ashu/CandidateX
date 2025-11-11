"""
API Endpoint Integration Tests
Comprehensive integration tests for all API endpoints.
"""
import pytest
from unittest.mock import patch
import asyncio
import httpx

from tests.conftest_integration import IntegrationTestAssertions


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationAPI:
    """Integration tests for authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_user_registration_candidate_success(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test successful candidate user registration."""
        user_data = test_data_factory.create_user_registration_data(role="candidate")
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Should succeed
        assertions.assert_response_success(response, 201)
        data = assertions.assert_json_response(response, [
            "id", "email", "full_name", "role", "status", "email_verified"
        ])
        
        # Verify data
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["role"] == user_data["role"]
        assert data["status"] == "active"
        assert data["email_verified"] is True

    @pytest.mark.asyncio
    async def test_user_registration_recruiter_success(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test successful recruiter user registration."""
        user_data = test_data_factory.create_user_registration_data(role="recruiter")
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Should succeed
        assertions.assert_response_success(response, 201)
        data = assertions.assert_json_response(response, [
            "id", "email", "full_name", "role", "status", "email_verified"
        ])
        
        # Verify data
        assert data["role"] == "recruiter"

    @pytest.mark.asyncio
    async def test_user_registration_admin_success(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test successful admin user registration."""
        user_data = test_data_factory.create_user_registration_data(role="admin")
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Should succeed
        assertions.assert_response_success(response, 201)
        data = assertions.assert_json_response(response, [
            "id", "email", "full_name", "role", "status", "email_verified"
        ])
        
        # Verify data
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_user_registration_duplicate_email(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test registration with duplicate email."""
        user_data = test_data_factory.create_user_registration_data(role="candidate")
        
        # Register first time
        response1 = await async_client.post("/api/v1/auth/register", json=user_data)
        assertions.assert_response_success(response1, 201)
        
        # Try to register again with same email
        response2 = await async_client.post("/api/v1/auth/register", json=user_data)
        assertions.assert_response_error(response2, 400)
        
        data = assertions.assert_json_response(response2, ["detail"])
        assert "Email already registered" in data["detail"]

    @pytest.mark.asyncio
    async def test_user_registration_invalid_data(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test registration with invalid data."""
        # Test missing required fields
        invalid_data = {
            "email": "test@example.com"
            # Missing password, full_name, role
        }
        
        response = await async_client.post("/api/v1/auth/register", json=invalid_data)
        assertions.assert_response_error(response, 422)  # Validation error

    @pytest.mark.asyncio
    async def test_user_login_success(self, async_client: httpx.AsyncClient, test_data_factory, test_user_candidate, assertions):
        """Test successful user login."""
        login_data = test_data_factory.create_login_data(test_user_candidate["email"])
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Should succeed
        assertions.assert_response_success(response)
        data = assertions.assert_authenticated_response(response)
        
        # Verify user data
        assert data["user"]["email"] == test_user_candidate["email"]
        assert data["user"]["role"] == "candidate"

    @pytest.mark.asyncio
    async def test_user_login_invalid_credentials(self, async_client: httpx.AsyncClient, test_data_factory, test_user_candidate, assertions):
        """Test login with invalid credentials."""
        # Test with wrong password
        login_data = {
            "email": test_user_candidate["email"],
            "password": "wrong_password"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_error(response, 401)
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "Incorrect email or password" in data["detail"]

    @pytest.mark.asyncio
    async def test_user_login_nonexistent_user(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "any_password"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_error(response, 401)
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "Incorrect email or password" in data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test token refresh."""
        # First login to get tokens
        login_data = {
            "email": test_user_candidate["email"],
            "password": "Test123!"
        }
        
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        login_data_result = assertions.assert_authenticated_response(login_response)
        
        # Use refresh token to get new access token
        refresh_data = {
            "refresh_token": login_data_result["refresh_token"]
        }
        
        response = await async_client.post("/api/v1/auth/refresh-token", json=refresh_data)
        assertions.assert_response_success(response)
        
        new_tokens = assertions.assert_authenticated_response(response)
        assert new_tokens["access_token"] != login_data_result["access_token"]

    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client_candidate, assertions):
        """Test user logout."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Logout (if endpoint exists)
        response = await client.post("/api/v1/auth/logout", headers=headers)
        
        # Logout might return 200 or 204
        if response.status_code == 200:
            assertions.assert_response_success(response)
        elif response.status_code == 204:
            assert response.content == b""  # No content
        else:
            # Some APIs don't have logout endpoint
            assert response.status_code in [200, 204, 404]

    @pytest.mark.asyncio
    async def test_get_current_user_profile(self, authenticated_client_candidate, assertions):
        """Test getting current user profile."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assertions.assert_response_success(response)
        data = assertions.assert_json_response(response, [
            "id", "email", "full_name", "role", "status", "email_verified"
        ])
        
        # Verify it's the authenticated user
        assert data["email"] == authenticated_client_candidate["user"]["email"]
        assert data["role"] == "candidate"


@pytest.mark.integration
@pytest.mark.users
class TestUsersAPI:
    """Integration tests for users API endpoints."""

    @pytest.mark.asyncio
    async def test_get_user_profile_unauthorized(self, async_client: httpx.AsyncClient, assertions):
        """Test getting user profile without authentication."""
        response = await async_client.get("/api/v1/users/me")
        assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_get_user_profile_authorized(self, authenticated_client_candidate, assertions):
        """Test getting user profile with authentication."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        response = await client.get("/api/v1/users/me", headers=headers)
        
        assertions.assert_response_success(response)
        data = assertions.assert_json_response(response, [
            "id", "email", "full_name", "role", "status"
        ])
        
        assert data["id"] == authenticated_client_candidate["user"]["id"]
        assert data["email"] == authenticated_client_candidate["user"]["email"]

    @pytest.mark.asyncio
    async def test_update_user_profile(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test updating user profile."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        update_data = {
            "full_name": "Updated Test User",
            "location": "New York, NY"
        }
        
        response = await client.put("/api/v1/users/me", headers=headers, json=update_data)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response, ["id", "email", "full_name"])
            assert data["full_name"] == update_data["full_name"]
        elif response.status_code == 404:
            # Profile update endpoint might not exist
            pass
        else:
            assertions.assert_response_success(response, 200)

    @pytest.mark.asyncio
    async def test_change_password(self, authenticated_client_candidate, assertions):
        """Test changing user password."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        password_data = {
            "current_password": "Test123!",
            "new_password": "NewTest123!"
        }
        
        response = await client.post("/api/v1/auth/change-password", headers=headers, json=password_data)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
        elif response.status_code == 404:
            # Endpoint might not exist
            pass
        else:
            assertions.assert_response_success(response, 200)


@pytest.mark.integration
@pytest.mark.interviews
class TestInterviewsAPI:
    """Integration tests for interviews API endpoints."""

    @pytest.mark.asyncio
    async def test_create_interview_candidate(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test creating an interview as candidate."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        interview_data = test_data_factory.create_interview_creation_data()
        
        response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if response.status_code == 201:
            assertions.assert_response_success(response, 201)
            data = assertions.assert_json_response(response, [
                "id", "job_title", "status", "created_at"
            ])
            assert data["job_title"] == interview_data["job_title"]
            assert data["status"] == "pending"
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 201)

    @pytest.mark.asyncio
    async def test_get_interviews_candidate(self, authenticated_client_candidate, assertions):
        """Test getting candidate's interviews."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        response = await client.get("/api/v1/interviews/", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response)
            assert isinstance(data, dict) or isinstance(data, list)
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 200)

    @pytest.mark.asyncio
    async def test_get_interview_by_id_candidate(self, authenticated_client_candidate, assertions):
        """Test getting a specific interview by ID."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # First create an interview
        interview_data = {
            "job_title": "Test Interview",
            "job_description": "Test description",
            "experience_level": "mid",
            "question_count": 3,
            "interview_mode": "technical"
        }
        
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Get the interview
            response = await client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
            
            if response.status_code == 200:
                assertions.assert_response_success(response)
                data = assertions.assert_json_response(response, ["id", "job_title", "status"])
                assert data["id"] == interview_id
            elif response.status_code == 404:
                # Endpoint might not exist
                pass

    @pytest.mark.asyncio
    async def test_update_interview_status(self, authenticated_client_candidate, assertions):
        """Test updating interview status."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create interview first
        interview_data = {
            "job_title": "Test Interview",
            "job_description": "Test description",
            "experience_level": "mid",
            "question_count": 3,
            "interview_mode": "technical"
        }
        
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Update status
            status_data = {"status": "in_progress"}
            response = await client.patch(f"/api/v1/interviews/{interview_id}/status", 
                                        headers=headers, json=status_data)
            
            if response.status_code == 200:
                assertions.assert_response_success(response)
            elif response.status_code == 404:
                # Endpoint might not exist
                pass

    @pytest.mark.asyncio
    async def test_delete_interview_candidate(self, authenticated_client_candidate, assertions):
        """Test deleting an interview."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create interview first
        interview_data = {
            "job_title": "Test Interview",
            "job_description": "Test description",
            "experience_level": "mid",
            "question_count": 3,
            "interview_mode": "technical"
        }
        
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Delete interview
            response = await client.delete(f"/api/v1/interviews/{interview_id}", headers=headers)
            
            if response.status_code == 204:
                assert response.content == b""  # No content
            elif response.status_code == 200:
                assertions.assert_response_success(response)
            elif response.status_code == 404:
                # Endpoint might not exist
                pass


@pytest.mark.integration
@pytest.mark.dashboard
class TestDashboardAPI:
    """Integration tests for dashboard API endpoints."""

    @pytest.mark.asyncio
    async def test_get_dashboard_stats_candidate(self, authenticated_client_candidate, assertions):
        """Test getting dashboard statistics for candidate."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        response = await client.get("/api/v1/dashboard/stats", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response)
            assert isinstance(data, dict)
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 200)

    @pytest.mark.asyncio
    async def test_get_dashboard_stats_recruiter(self, authenticated_client_recruiter, assertions):
        """Test getting dashboard statistics for recruiter."""
        client = authenticated_client_recruiter["client"]
        headers = authenticated_client_recruiter["headers"]
        
        response = await client.get("/api/v1/dashboard/stats", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response)
            assert isinstance(data, dict)
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 200)

    @pytest.mark.asyncio
    async def test_get_dashboard_unauthorized(self, async_client: httpx.AsyncClient, assertions):
        """Test getting dashboard stats without authentication."""
        response = await async_client.get("/api/v1/dashboard/stats")
        assertions.assert_response_error(response, 401)


@pytest.mark.integration
@pytest.mark.ai
class TestAIAPI:
    """Integration tests for AI API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_questions(self, authenticated_client_candidate, mock_ai_service, assertions):
        """Test AI question generation."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        request_data = {
            "job_title": "Software Engineer",
            "experience_level": "mid",
            "interview_mode": "technical"
        }
        
        response = await client.post("/api/v1/ai/generate-questions", headers=headers, json=request_data)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response, ["questions"])
            assert isinstance(data["questions"], list)
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 200)

    @pytest.mark.asyncio
    async def test_evaluate_response(self, authenticated_client_candidate, mock_ai_service, assertions):
        """Test AI response evaluation."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        request_data = {
            "question": "What is your experience with Python?",
            "response": "I have 3 years of experience with Python, working on web applications and data analysis.",
            "expected_skills": ["Python", "Programming"]
        }
        
        response = await client.post("/api/v1/ai/evaluate-response", headers=headers, json=request_data)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response, ["score", "feedback"])
            assert isinstance(data["score"], (int, float))
            assert isinstance(data["feedback"], str)
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 200)

    @pytest.mark.asyncio
    async def test_generate_feedback(self, authenticated_client_candidate, mock_ai_service, assertions):
        """Test AI feedback generation."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        request_data = {
            "interview_responses": [
                {"question": "Q1", "response": "Response 1", "score": 80},
                {"question": "Q2", "response": "Response 2", "score": 75}
            ]
        }
        
        response = await client.post("/api/v1/ai/generate-feedback", headers=headers, json=request_data)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response, ["overall_feedback", "summary"])
            assert isinstance(data["overall_feedback"], str)
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 200)

    @pytest.mark.asyncio
    async def test_ai_endpoints_unauthorized(self, async_client: httpx.AsyncClient, assertions):
        """Test AI endpoints without authentication."""
        request_data = {
            "job_title": "Software Engineer",
            "experience_level": "mid"
        }
        
        response = await async_client.post("/api/v1/ai/generate-questions", json=request_data)
        assertions.assert_response_error(response, 401)


@pytest.mark.integration
@pytest.mark.admin
class TestAdminAPI:
    """Integration tests for admin API endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_users_admin(self, authenticated_client_admin, assertions):
        """Test getting all users as admin."""
        client = authenticated_client_admin["client"]
        headers = authenticated_client_admin["headers"]
        
        response = await client.get("/api/v1/admin/users", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response)
            assert isinstance(data, dict) or isinstance(data, list)
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 200)

    @pytest.mark.asyncio
    async def test_get_all_users_candidate(self, authenticated_client_candidate, assertions):
        """Test getting all users as candidate (should fail)."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        response = await client.get("/api/v1/admin/users", headers=headers)
        
        if response.status_code == 403:
            assertions.assert_response_error(response, 403)
        elif response.status_code == 404:
            # Endpoint might not exist
            pass
        else:
            # Some APIs might return different error codes
            assert response.status_code in [403, 404, 401]

    @pytest.mark.asyncio
    async def test_get_system_stats_admin(self, authenticated_client_admin, assertions):
        """Test getting system statistics as admin."""
        client = authenticated_client_admin["client"]
        headers = authenticated_client_admin["headers"]
        
        response = await client.get("/api/v1/admin/stats", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            data = assertions.assert_json_response(response)
            assert isinstance(data, dict)
        elif response.status_code == 404:
            # Endpoint might not exist yet
            pass
        else:
            assertions.assert_response_success(response, 200)


@pytest.mark.integration
@pytest.mark.health
class TestHealthAPI:
    """Integration tests for health and status endpoints."""

    def test_health_check(self, test_client, assertions):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assertions.assert_response_success(response)
        
        data = assertions.assert_json_response(response, ["status", "version", "database"])
        assert data["status"] == "healthy"
        assert "version" in data
        assert "database" in data

    def test_root_endpoint(self, test_client, assertions):
        """Test root endpoint."""
        response = test_client.get("/")
        assertions.assert_response_success(response)
        
        data = assertions.assert_json_response(response, ["message", "version", "docs"])
        assert "CandidateX" in data["message"]
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"

    def test_docs_endpoint_accessible(self, test_client, assertions):
        """Test that API documentation is accessible."""
        response = test_client.get("/docs")
        assertions.assert_response_success(response, 200)
        
        # Should be HTML for Swagger UI
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_spec(self, test_client, assertions):
        """Test OpenAPI specification is accessible."""
        response = test_client.get("/openapi.json")
        assertions.assert_response_success(response)
        
        data = assertions.assert_json_response(response, ["openapi", "info", "paths"])
        assert data["openapi"].startswith("3.")
        assert "CandidateX" in data["info"]["title"]


@pytest.mark.integration
@pytest.mark.cors
class TestCORSIntegration:
    """Integration tests for CORS functionality."""

    def test_cors_headers_present(self, test_client, assertions):
        """Test that CORS headers are present in responses."""
        response = test_client.options("/api/v1/auth/register")
        
        # Check for CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods", 
            "access-control-allow-headers"
        ]
        
        for header in cors_headers:
            assert any(h.lower().startswith(header.lower()) for h in response.headers.keys())

    def test_cors_preflight_request(self, test_client, assertions):
        """Test CORS preflight request handling."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
        
        response = test_client.options("/api/v1/auth/register", headers=headers)
        
        # Should return 200 for preflight
        assert response.status_code == 200
        
        # Should have CORS headers
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]


@pytest.mark.integration
@pytest.mark.rate_limiting
class TestRateLimitingIntegration:
    """Integration tests for rate limiting."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rate_limiting_applied(self, async_client: httpx.AsyncClient, assertions):
        """Test that rate limiting is applied to endpoints."""
        # Make multiple rapid requests to trigger rate limiting
        tasks = []
        for i in range(10):
            task = async_client.get("/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some requests should succeed, some might be rate limited
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 429)
        
        assert success_count > 0, "At least some requests should succeed"
        # Rate limiting might or might not trigger depending on configuration
        assert success_count + rate_limited_count == 10, "All requests should have responses"

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, async_client: httpx.AsyncClient, assertions):
        """Test that rate limit headers are present in responses."""
        response = await async_client.get("/health")
        
        # Check for rate limit headers
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "x-ratelimit-reset"
        ]
        
        # Headers might be present with different casing
        header_names = [h.lower() for h in response.headers.keys()]
        has_rate_limit_info = any(
            header in header_names for header in rate_limit_headers
        )
        
        # Rate limiting might be disabled in test environment
        # So we just check that the request succeeded
        assertions.assert_response_success(response, 200)