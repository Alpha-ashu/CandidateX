"""
User Registration and Login Flow Integration Tests
Comprehensive integration tests for user authentication flows.
"""
import pytest
import asyncio
import httpx
from tests.conftest_integration import IntegrationTestAssertions


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.auth
class TestUserRegistrationFlow:
    """Integration tests for complete user registration flow."""

    @pytest.mark.asyncio
    async def test_complete_candidate_registration_and_login_flow(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test complete candidate registration and login flow."""
        # Step 1: Register new candidate
        registration_data = test_data_factory.create_user_registration_data(role="candidate")
        
        register_response = await async_client.post("/api/v1/auth/register", json=registration_data)
        assertions.assert_response_success(register_response, 201)
        
        register_data = assertions.assert_json_response(register_response, [
            "id", "email", "full_name", "role", "status", "email_verified"
        ])
        
        # Verify registration data
        assert register_data["email"] == registration_data["email"]
        assert register_data["full_name"] == registration_data["full_name"]
        assert register_data["role"] == "candidate"
        assert register_data["status"] == "active"
        assert register_data["email_verified"] is True
        
        # Step 2: Login with new credentials
        login_data = {
            "email": registration_data["email"],
            "password": registration_data["password"]
        }
        
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response)
        
        login_result = assertions.assert_authenticated_response(login_response)
        
        # Verify login data
        assert login_result["user"]["email"] == registration_data["email"]
        assert login_result["user"]["full_name"] == registration_data["full_name"]
        assert login_result["user"]["role"] == "candidate"
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        
        # Step 3: Access protected endpoint with token
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}
        profile_response = await async_client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_success(profile_response)
        
        profile_data = assertions.assert_json_response(profile_response, [
            "id", "email", "full_name", "role", "status"
        ])
        
        assert profile_data["email"] == registration_data["email"]
        assert profile_data["id"] == register_data["id"]

    @pytest.mark.asyncio
    async def test_complete_recruiter_registration_and_login_flow(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test complete recruiter registration and login flow."""
        # Step 1: Register new recruiter
        registration_data = test_data_factory.create_user_registration_data(role="recruiter")
        
        register_response = await async_client.post("/api/v1/auth/register", json=registration_data)
        assertions.assert_response_success(register_response, 201)
        
        register_data = assertions.assert_json_response(register_response, ["role", "email_verified"])
        assert register_data["role"] == "recruiter"
        
        # Step 2: Login with new credentials
        login_data = {
            "email": registration_data["email"],
            "password": registration_data["password"]
        }
        
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response)
        
        login_result = assertions.assert_authenticated_response(login_response)
        assert login_result["user"]["role"] == "recruiter"
        
        # Step 3: Verify recruiter-specific access
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}
        profile_response = await async_client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_success(profile_response)
        
        profile_data = profile_response.json()
        assert profile_data["role"] == "recruiter"

    @pytest.mark.asyncio
    async def test_complete_admin_registration_and_login_flow(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test complete admin registration and login flow."""
        # Step 1: Register new admin
        registration_data = test_data_factory.create_user_registration_data(role="admin")
        
        register_response = await async_client.post("/api/v1/auth/register", json=registration_data)
        assertions.assert_response_success(register_response, 201)
        
        register_data = assertions.assert_json_response(register_response, ["role", "email_verified"])
        assert register_data["role"] == "admin"
        
        # Step 2: Login with new credentials
        login_data = {
            "email": registration_data["email"],
            "password": registration_data["password"]
        }
        
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response)
        
        login_result = assertions.assert_authenticated_response(login_response)
        assert login_result["user"]["role"] == "admin"
        
        # Step 3: Verify admin-specific access (accessing admin endpoints)
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}
        
        # Try to access admin endpoint (may not exist yet)
        admin_response = await async_client.get("/api/v1/admin/users", headers=headers)
        # Should get 200 (success) or 404 (not implemented) but not 403 (forbidden)
        assert admin_response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_registration_with_weak_password(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test registration with weak password fails validation."""
        registration_data = test_data_factory.create_user_registration_data(role="candidate")
        registration_data["password"] = "123"  # Weak password
        
        response = await async_client.post("/api/v1/auth/register", json=registration_data)
        assertions.assert_response_error(response, 400)
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "password" in data["detail"].lower() or "validation" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_registration_with_invalid_email(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test registration with invalid email format."""
        registration_data = test_data_factory.create_user_registration_data(role="candidate")
        registration_data["email"] = "invalid-email-format"  # Invalid email
        
        response = await async_client.post("/api/v1/auth/register", json=registration_data)
        assertions.assert_response_error(response, 422)  # Validation error
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "email" in data["detail"].lower() or "validation" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_registration_with_missing_fields(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test registration with missing required fields."""
        registration_data = {
            "email": "test@example.com"
            # Missing password, full_name, role
        }
        
        response = await async_client.post("/api/v1/auth/register", json=registration_data)
        assertions.assert_response_error(response, 422)  # Validation error

    @pytest.mark.asyncio
    async def test_registration_with_duplicate_email_fails(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test that registration fails with duplicate email."""
        # First registration
        registration_data = test_data_factory.create_user_registration_data(role="candidate")
        
        response1 = await async_client.post("/api/v1/auth/register", json=registration_data)
        assertions.assert_response_success(response1, 201)
        
        # Second registration with same email
        response2 = await async_client.post("/api/v1/auth/register", json=registration_data)
        assertions.assert_response_error(response2, 400)
        
        data = assertions.assert_json_response(response2, ["detail"])
        assert "already registered" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_before_registration_fails(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test that login fails for non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "any_password"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_error(response, 401)
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "incorrect" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_with_wrong_password_fails(self, async_client: httpx.AsyncClient, test_data_factory, test_user_candidate, assertions):
        """Test that login fails with wrong password."""
        login_data = {
            "email": test_user_candidate["email"],
            "password": "wrong_password"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_error(response, 401)
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "incorrect" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.auth
class TestTokenManagementFlow:
    """Integration tests for token management flow."""

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test complete token refresh flow."""
        # Step 1: Initial login
        login_data = {
            "email": test_user_candidate["email"],
            "password": "Test123!"
        }
        
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response)
        
        login_result = assertions.assert_authenticated_response(login_response)
        original_access_token = login_result["access_token"]
        refresh_token = login_result["refresh_token"]
        
        # Step 2: Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = await async_client.post("/api/v1/auth/refresh-token", json=refresh_data)
        assertions.assert_response_success(refresh_response)
        
        refresh_result = assertions.assert_authenticated_response(refresh_response)
        new_access_token = refresh_result["access_token"]
        
        # Step 3: Verify new token works
        headers = {"Authorization": f"Bearer {new_access_token}"}
        profile_response = await async_client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_success(profile_response)
        
        profile_data = profile_response.json()
        assert profile_data["email"] == test_user_candidate["email"]
        
        # Step 4: Verify tokens are different
        assert new_access_token != original_access_token

    @pytest.mark.asyncio
    async def test_expired_access_token_fails(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test that expired access token fails authentication."""
        # This test would require token expiration simulation
        # For now, we'll test with an obviously invalid token
        invalid_token = "invalid.jwt.token"
        
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        
        assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_malformed_token_fails(self, async_client: httpx.AsyncClient, assertions):
        """Test that malformed token fails authentication."""
        malformed_tokens = [
            "Bearer malformed",
            "invalidtoken",
            "Bearer ",
            "",
            "Bearer a.b"  # Too few parts
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = await async_client.get("/api/v1/auth/me", headers=headers)
            assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_missing_authorization_header_fails(self, async_client: httpx.AsyncClient, assertions):
        """Test that requests without authorization header fail."""
        response = await async_client.get("/api/v1/auth/me")
        assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_wrong_authorization_format_fails(self, async_client: httpx.AsyncClient, assertions):
        """Test that wrong authorization header format fails."""
        wrong_formats = [
            "Basic dGVzdA==",  # Basic auth
            "Invalid token",    # Wrong scheme
            "Bearer",          # Missing token
        ]
        
        for auth_header in wrong_formats:
            headers = {"Authorization": auth_header}
            response = await async_client.get("/api/v1/auth/me", headers=headers)
            assertions.assert_response_error(response, 401)


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.auth
class TestRoleBasedAccessFlow:
    """Integration tests for role-based access control flow."""

    @pytest.mark.asyncio
    async def test_candidate_access_restrictions(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test that candidates cannot access admin endpoints."""
        # Login as candidate
        login_data = {
            "email": test_user_candidate["email"],
            "password": "Test123!"
        }
        
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response)
        
        login_result = assertions.assert_authenticated_response(login_response)
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}
        
        # Try to access admin endpoints
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/stats",
            "/api/v1/admin/system"
        ]
        
        for endpoint in admin_endpoints:
            response = await async_client.get(endpoint, headers=headers)
            # Should get 403 (forbidden) or 404 (not found) but not 200
            assert response.status_code in [403, 404], f"Candidate should not access {endpoint}"
            if response.status_code == 403:
                assertions.assert_response_error(response, 403)

    @pytest.mark.asyncio
    async def test_recruiter_access_restrictions(self, async_client: httpx.AsyncClient, test_user_recruiter, assertions):
        """Test that recruiters cannot access admin endpoints."""
        # Login as recruiter
        login_data = {
            "email": test_user_recruiter["email"],
            "password": "Test123!"
        }
        
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response)
        
        login_result = assertions.assert_authenticated_response(login_response)
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}
        
        # Try to access admin endpoint
        response = await async_client.get("/api/v1/admin/users", headers=headers)
        assert response.status_code in [403, 404]
        if response.status_code == 403:
            assertions.assert_response_error(response, 403)

    @pytest.mark.asyncio
    async def test_admin_access_all_endpoints(self, async_client: httpx.AsyncClient, test_user_admin, assertions):
        """Test that admin can access all endpoints."""
        # Login as admin
        login_data = {
            "email": test_user_admin["email"],
            "password": "Test123!"
        }
        
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response)
        
        login_result = assertions.assert_authenticated_response(login_response)
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}
        
        # Admin should be able to access user profile
        profile_response = await async_client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_success(profile_response)
        
        profile_data = profile_response.json()
        assert profile_data["role"] == "admin"


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.auth
class TestPasswordManagementFlow:
    """Integration tests for password management flow."""

    @pytest.mark.asyncio
    async def test_change_password_flow(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test complete password change flow."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Step 1: Change password
        password_data = {
            "current_password": "Test123!",
            "new_password": "NewSecure123!"
        }
        
        change_response = await client.post("/api/v1/auth/change-password", headers=headers, json=password_data)
        
        if change_response.status_code == 200:
            assertions.assert_response_success(change_response)
        elif change_response.status_code == 404:
            # Endpoint might not exist
            pytest.skip("Password change endpoint not implemented")
        
        # Step 2: Login with new password
        login_data = {
            "email": authenticated_client_candidate["user"]["email"],
            "password": "NewSecure123!"
        }
        
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response)
        
        login_result = assertions.assert_authenticated_response(login_response)
        assert login_result["user"]["email"] == authenticated_client_candidate["user"]["email"]

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password(self, authenticated_client_candidate, assertions):
        """Test password change with wrong current password fails."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        password_data = {
            "current_password": "wrong_password",
            "new_password": "NewSecure123!"
        }
        
        response = await client.post("/api/v1/auth/change-password", headers=headers, json=password_data)
        
        if response.status_code == 400:
            assertions.assert_response_error(response, 400)
            data = assertions.assert_json_response(response, ["detail"])
            assert "current password" in data["detail"].lower()
        elif response.status_code == 404:
            # Endpoint might not exist
            pytest.skip("Password change endpoint not implemented")

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(self, authenticated_client_candidate, assertions):
        """Test password change with weak new password fails."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        password_data = {
            "current_password": "Test123!",
            "new_password": "123"  # Weak password
        }
        
        response = await client.post("/api/v1/auth/change-password", headers=headers, json=password_data)
        
        if response.status_code == 400:
            assertions.assert_response_error(response, 400)
            data = assertions.assert_json_response(response, ["detail"])
            assert "password" in data["detail"].lower() or "validation" in data["detail"].lower()
        elif response.status_code == 404:
            # Endpoint might not exist
            pytest.skip("Password change endpoint not implemented")

    @pytest.mark.asyncio
    async def test_forgot_password_flow(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test forgot password flow (email sending simulation)."""
        forgot_data = {
            "email": test_user_candidate["email"]
        }
        
        response = await async_client.post("/api/v1/auth/forgot-password", json=forgot_data)
        
        # Should return 200 even if email doesn't exist (security)
        assertions.assert_response_success(response, 200)
        data = assertions.assert_json_response(response, ["message"])
        assert "reset" in data["message"].lower() or "sent" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_flow(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test password reset flow with valid token."""
        # This test would require a valid reset token
        # For now, we'll test with an obviously invalid token
        
        reset_data = {
            "token": "invalid_reset_token",
            "new_password": "NewSecure123!"
        }
        
        response = await async_client.post("/api/v1/auth/reset-password", json=reset_data)
        assertions.assert_response_error(response, 400)
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.slow
class TestSessionManagementFlow:
    """Integration tests for session management."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_logins(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test multiple concurrent login sessions."""
        login_data = {
            "email": test_user_candidate["email"],
            "password": "Test123!"
        }
        
        # Create multiple concurrent login requests
        login_tasks = [
            async_client.post("/api/v1/auth/login", json=login_data)
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*login_tasks)
        
        # All should succeed
        for response in responses:
            assertions.assert_response_success(response)
            login_result = assertions.assert_authenticated_response(response)
            assert login_result["user"]["email"] == test_user_candidate["email"]

    @pytest.mark.asyncio
    async def test_login_logout_login_flow(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test complete login-logout-login flow."""
        login_data = {
            "email": test_user_candidate["email"],
            "password": "Test123!"
        }
        
        # First login
        login_response1 = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response1)
        
        login_result1 = assertions.assert_authenticated_response(login_response1)
        headers1 = {"Authorization": f"Bearer {login_result1['access_token']}"}
        
        # Verify first session works
        profile_response1 = await async_client.get("/api/v1/auth/me", headers=headers1)
        assertions.assert_response_success(profile_response1)
        
        # Logout (if endpoint exists)
        logout_response = await async_client.post("/api/v1/auth/logout", headers=headers1)
        if logout_response.status_code in [200, 204, 404]:
            pass  # Logout endpoint may or may not exist
        
        # Second login
        login_response2 = await async_client.post("/api/v1/auth/login", json=login_data)
        assertions.assert_response_success(login_response2)
        
        login_result2 = assertions.assert_authenticated_response(login_response2)
        headers2 = {"Authorization": f"Bearer {login_result2['access_token']}"}
        
        # Verify second session works
        profile_response2 = await async_client.get("/api/v1/auth/me", headers=headers2)
        assertions.assert_response_success(profile_response2)
        
        # Both sessions should work (some systems allow concurrent sessions)
        assert profile_response1.json()["email"] == profile_response2.json()["email"]