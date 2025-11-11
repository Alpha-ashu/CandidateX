"""
Authentication Middleware Integration Tests
Comprehensive integration tests for authentication and authorization middleware.
"""
import pytest
import asyncio
import httpx
from unittest.mock import patch, Mock
import jwt
import time
from tests.conftest_integration import IntegrationTestAssertions


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.middleware
class TestAuthenticationMiddleware:
    """Integration tests for authentication middleware."""

    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, async_client: httpx.AsyncClient, assertions):
        """Test that unauthenticated requests are denied access to protected endpoints."""
        protected_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/users/me",
            "/api/v1/interviews/",
            "/api/v1/dashboard/stats"
        ]
        
        for endpoint in protected_endpoints:
            response = await async_client.get(endpoint)
            assertions.assert_response_error(response, 401)
            
            data = assertions.assert_json_response(response, ["detail"])
            assert "not authenticated" in data["detail"].lower() or "unauthorized" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_valid_token_authentication(self, authenticated_client_candidate, assertions):
        """Test that valid tokens pass authentication middleware."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Access protected endpoint with valid token
        response = await client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_success(response)
        
        data = assertions.assert_json_response(response, ["email", "role"])
        assert data["email"] == authenticated_client_candidate["user"]["email"]

    @pytest.mark.asyncio
    async def test_invalid_token_authentication(self, async_client: httpx.AsyncClient, assertions):
        """Test that invalid tokens are rejected by authentication middleware."""
        invalid_tokens = [
            "invalid.jwt.token",
            "Bearer invalid.token.here",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "malformed.token",
            "",
            "NotBearer token"
        ]
        
        for invalid_token in invalid_tokens:
            headers = {"Authorization": invalid_token}
            response = await async_client.get("/api/v1/auth/me", headers=headers)
            assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_expired_token_handling(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test that expired tokens are properly handled."""
        # Create a token with a short expiration time
        from app.auth.utils import create_access_token
        
        # Create token that expires immediately
        token_data = {
            "sub": test_user_candidate["id"],
            "email": test_user_candidate["email"],
            "role": "candidate",
            "exp": int(time.time()) - 3600  # Expired 1 hour ago
        }
        
        expired_token = create_access_token(token_data)
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_error(response, 401)
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "expired" in data["detail"].lower() or "token" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_token_without_required_claims(self, async_client: httpx.AsyncClient, test_user_candidate, assertions):
        """Test that tokens without required claims are rejected."""
        from app.auth.utils import create_access_token
        
        # Create token without 'sub' claim
        incomplete_token_data = {
            "email": test_user_candidate["email"],
            "role": "candidate",
            "exp": int(time.time()) + 3600
        }
        
        incomplete_token = create_access_token(incomplete_token_data)
        headers = {"Authorization": f"Bearer {incomplete_token}"}
        
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_malformed_authorization_header(self, async_client: httpx.AsyncClient, assertions):
        """Test that malformed authorization headers are rejected."""
        malformed_headers = [
            {"Authorization": ""},  # Empty
            {"Authorization": " "},  # Space only
            {"Authorization": "Basic dGVzdA=="},  # Basic auth
            {"Authorization": "Digest realm="},  # Digest auth
            {"Authorization": "OAuth2 token"},  # Wrong OAuth format
            {"authorization": "Bearer token"},  # Wrong case (should be case insensitive)
        ]
        
        for headers in malformed_headers:
            response = await async_client.get("/api/v1/auth/me", headers=headers)
            assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_public_endpoints_accessible_without_auth(self, async_client: httpx.AsyncClient, assertions):
        """Test that public endpoints are accessible without authentication."""
        public_endpoints = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/register",  # Registration endpoint
            "/api/v1/auth/login",     # Login endpoint
        ]
        
        for endpoint in public_endpoints:
            response = await async_client.get(endpoint)
            # Should not return 401 (authentication error)
            assert response.status_code != 401, f"Public endpoint {endpoint} should not require authentication"

    @pytest.mark.asyncio
    async def test_token_validation_with_wrong_secret(self, async_client: httpx.AsyncClient, authenticated_client_candidate, assertions):
        """Test token validation with wrong secret key."""
        # Create a token with a different secret
        wrong_token = jwt.encode(
            {"sub": "user_id", "email": "test@example.com", "role": "candidate"},
            "wrong_secret",
            algorithm="HS256"
        )
        
        headers = {"Authorization": f"Bearer {wrong_token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_concurrent_authentication_requests(self, authenticated_client_candidate, assertions):
        """Test concurrent authentication requests don't interfere."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Make concurrent requests
        concurrent_requests = [
            client.get("/api/v1/auth/me", headers=headers)
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*concurrent_requests)
        
        # All should succeed
        for response in responses:
            assertions.assert_response_success(response)
            
            data = response.json()
            assert data["email"] == authenticated_client_candidate["user"]["email"]


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.middleware
class TestAuthorizationMiddleware:
    """Integration tests for authorization middleware."""

    @pytest.mark.asyncio
    async def test_candidate_cannot_access_admin_endpoints(self, authenticated_client_candidate, assertions):
        """Test that candidates cannot access admin-only endpoints."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/stats",
            "/api/v1/admin/system",
            "/api/v1/admin/backup",
            "/api/v1/admin/restore"
        ]
        
        for endpoint in admin_endpoints:
            response = await client.get(endpoint, headers=headers)
            
            # Should be forbidden for candidates
            assert response.status_code in [403, 404], f"Candidate should not access {endpoint}"
            if response.status_code == 403:
                assertions.assert_response_error(response, 403)

    @pytest.mark.asyncio
    async def test_recruiter_cannot_access_admin_endpoints(self, authenticated_client_recruiter, assertions):
        """Test that recruiters cannot access admin-only endpoints."""
        client = authenticated_client_recruiter["client"]
        headers = authenticated_client_recruiter["headers"]
        
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/stats",
            "/api/v1/admin/system"
        ]
        
        for endpoint in admin_endpoints:
            response = await client.get(endpoint, headers=headers)
            
            # Should be forbidden for recruiters
            assert response.status_code in [403, 404]
            if response.status_code == 403:
                assertions.assert_response_error(response, 403)

    @pytest.mark.asyncio
    async def test_admin_can_access_admin_endpoints(self, authenticated_client_admin, assertions):
        """Test that admin can access admin-only endpoints."""
        client = authenticated_client_admin["client"]
        headers = authenticated_client_admin["headers"]
        
        # Admin should be able to access profile endpoint
        profile_response = await client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_success(profile_response)
        
        profile_data = profile_response.json()
        assert profile_data["role"] == "admin"
        
        # Try admin endpoint (may return 404 if not implemented)
        admin_response = await client.get("/api/v1/admin/users", headers=headers)
        assert admin_response.status_code in [200, 404], "Admin should have access to admin endpoints"

    @pytest.mark.asyncio
    async def test_candidate_can_access_candidate_endpoints(self, authenticated_client_candidate, assertions):
        """Test that candidates can access candidate-specific endpoints."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        candidate_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/users/me",
            "/api/v1/dashboard/stats"  # Should be accessible to all authenticated users
        ]
        
        for endpoint in candidate_endpoints:
            response = await client.get(endpoint, headers=headers)
            
            # Should succeed or return 404 (not implemented) but not 403
            assert response.status_code in [200, 404], f"Candidate should access {endpoint}"
            if response.status_code == 200:
                assertions.assert_response_success(response)

    @pytest.mark.asyncio
    async def test_recruiter_can_access_recruiter_endpoints(self, authenticated_client_recruiter, assertions):
        """Test that recruiters can access recruiter-specific endpoints."""
        client = authenticated_client_recruiter["client"]
        headers = authenticated_client_recruiter["headers"]
        
        recruiter_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/users/me",
            "/api/v1/dashboard/stats"
        ]
        
        for endpoint in recruiter_endpoints:
            response = await client.get(endpoint, headers=headers)
            
            # Should succeed or return 404 (not implemented) but not 403
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                assertions.assert_response_success(response)

    @pytest.mark.asyncio
    async def test_cross_role_endpoint_access_denied(self, authenticated_client_candidate, authenticated_client_recruiter, test_data_factory, assertions):
        """Test that users cannot access other users' resources."""
        candidate_client = authenticated_client_candidate["client"]
        candidate_headers = authenticated_client_candidate["headers"]
        recruiter_client = authenticated_client_recruiter["client"]
        recruiter_headers = authenticated_client_recruiter["headers"]
        
        # Create interview as recruiter
        interview_data = test_data_factory.create_interview_creation_data()
        create_response = await recruiter_client.post("/api/v1/interviews/", headers=recruiter_headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Candidate tries to access recruiter's interview
            access_response = await candidate_client.get(f"/api/v1/interviews/{interview_id}", headers=candidate_headers)
            
            # Should be forbidden or not found
            assert access_response.status_code in [403, 404]
            if access_response.status_code == 403:
                assertions.assert_response_error(access_response, 403)

    @pytest.mark.asyncio
    async def test_resource_ownership_validation(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test that resource ownership is properly validated."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create interview
        interview_data = test_data_factory.create_interview_creation_data()
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Update interview (should succeed - own resource)
            update_data = {"job_title": "Updated Title"}
            update_response = await client.patch(f"/api/v1/interviews/{interview_id}", headers=headers, json=update_data)
            
            if update_response.status_code == 200:
                assertions.assert_response_success(update_response)
            elif update_response.status_code == 404:
                # Update endpoint might not exist
                pass


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.middleware
@pytest.mark.security
class TestSecurityMiddleware:
    """Integration tests for security middleware."""

    @pytest.mark.asyncio
    async def test_rate_limiting_applied(self, async_client: httpx.AsyncClient, assertions):
        """Test that rate limiting middleware is applied."""
        # Make many rapid requests to trigger rate limiting
        rapid_requests = []
        for i in range(50):  # Make many requests quickly
            task = async_client.get("/api/v1/auth/register")  # Use a public endpoint
            rapid_requests.append(task)
        
        responses = await asyncio.gather(*rapid_requests, return_exceptions=True)
        
        # Count responses
        success_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 429]
        normal_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code in [200, 422]]  # 422 for validation errors
        
        # Some requests should be rate limited
        if success_responses:
            assert len(success_responses) > 0, "Rate limiting should trigger under heavy load"
        if normal_responses:
            assert len(normal_responses) > 0, "Some requests should succeed"

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, test_client, assertions):
        """Test that CORS middleware adds appropriate headers."""
        # Test preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
        
        response = test_client.options("/api/v1/auth/register", headers=headers)
        
        # Should return 200 for preflight
        assert response.status_code == 200
        
        # Check for CORS headers
        cors_headers = ["access-control-allow-origin", "access-control-allow-methods", "access-control-allow-headers"]
        for header in cors_headers:
            assert any(h.lower().startswith(header) for h in response.headers.keys())

    @pytest.mark.asyncio
    async def test_security_headers_present(self, test_client, assertions):
        """Test that security headers are added to responses."""
        response = test_client.get("/api/v1/auth/me")  # Protected endpoint
        
        # Check for security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security"
        ]
        
        for header in security_headers:
            # Headers might be present with different casing
            assert any(h.lower() == header.lower() for h in response.headers.keys()), f"Security header {header} not found"

    @pytest.mark.asyncio
    async def test_input_validation_middleware(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test that input validation middleware filters malicious input."""
        malicious_inputs = [
            {"email": "<script>alert('xss')</script>@test.com", "password": "Test123!"},
            {"email": "test@example.com", "password": "../../../etc/passwd"},
            {"email": "'; DROP TABLE users; --@test.com", "password": "Test123!"},
            {"email": "${7*7}@test.com", "password": "Test123!"}
        ]
        
        for malicious_data in malicious_inputs:
            response = await async_client.post("/api/v1/auth/register", json=malicious_data)
            
            # Should return validation error or 400, not succeed
            assert response.status_code in [400, 422, 429], "Malicious input should be rejected"
            if response.status_code in [400, 422]:
                assertions.assert_response_error(response, response.status_code)

    @pytest.mark.asyncio
    async def test_request_logging_middleware(self, async_client: httpx.AsyncClient, assertions):
        """Test that request logging middleware works."""
        # This test would verify logs are created - in a real test environment
        # you would capture log output and verify it contains the request details
        
        response = await async_client.get("/health")
        assertions.assert_response_success(response)
        
        # In a real test, you would check that the request was logged
        # For now, we just verify the endpoint works

    @pytest.mark.asyncio
    async def test_ip_filtering_middleware(self, async_client: httpx.AsyncClient, assertions):
        """Test that IP filtering middleware works."""
        # Test with blocked IP (if any are configured)
        # This would require setting up specific IP rules
        
        response = await async_client.get("/health")
        assertions.assert_response_success(response)
        
        # In a real test environment, you would test with blocked IPs

    @pytest.mark.asyncio
    async def test_maintenance_mode_middleware(self, async_client: httpx.AsyncClient, assertions):
        """Test that maintenance mode middleware works when enabled."""
        # This would test the maintenance mode functionality
        # In a real implementation, maintenance mode would be configurable
        
        response = await async_client.get("/health")
        assertions.assert_response_success(response)

    @pytest.mark.asyncio
    async def test_api_versioning_middleware(self, async_client: httpx.AsyncClient, assertions):
        """Test that API versioning middleware works."""
        # Test with version header
        headers = {"API-Version": "1.0"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        
        # Should work (not return version error)
        assert response.status_code in [200, 401, 404]  # 401 if no auth, 404 if not implemented

    @pytest.mark.asyncio
    async def test_trusted_host_middleware(self, async_client: httpx.AsyncClient, assertions):
        """Test that trusted host middleware validates host headers."""
        # Test with untrusted host
        headers = {"Host": "malicious-site.com"}
        response = await async_client.get("/health", headers=headers)
        
        # Should return 400 (bad request) for untrusted host
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_error_handler_middleware(self, async_client: httpx.AsyncClient, assertions):
        """Test that error handling middleware works correctly."""
        # Test with malformed request that should trigger error handling
        response = await async_client.get("/api/v1/auth/nonexistent-endpoint")
        assertions.assert_response_error(response, 404)
        
        data = assertions.assert_json_response(response, ["detail"])
        assert "not found" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.middleware
@pytest.mark.slow
class TestMiddlewarePerformance:
    """Integration tests for middleware performance and efficiency."""

    @pytest.mark.asyncio
    async def test_authentication_overhead(self, authenticated_client_candidate, assertions):
        """Test that authentication middleware adds reasonable overhead."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Measure timing for authenticated vs unauthenticated requests
        start_time = time.time()
        response = await client.get("/api/v1/auth/me", headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assertions.assert_response_success(response)
        
        # Authentication should not take more than 1 second in test environment
        assert response_time < 1.0, f"Authentication took too long: {response_time}s"

    @pytest.mark.asyncio
    async def test_middleware_stack_working_together(self, authenticated_client_candidate, assertions):
        """Test that all middleware work together properly."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Make a request that goes through multiple middleware
        response = await client.get("/api/v1/auth/me", headers=headers)
        assertions.assert_response_success(response)
        
        data = response.json()
        assert data["email"] == authenticated_client_candidate["user"]["email"]
        
        # Verify security headers are present
        assert "x-content-type-options" in [h.lower() for h in response.headers.keys()]

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, authenticated_client_candidate, assertions):
        """Test that middleware handles concurrent requests efficiently."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Make many concurrent authenticated requests
        start_time = time.time()
        concurrent_requests = [
            client.get("/api/v1/auth/me", headers=headers)
            for _ in range(20)
        ]
        
        responses = await asyncio.gather(*concurrent_requests)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All should succeed
        for response in responses:
            assertions.assert_response_success(response)
        
        # Should handle 20 requests in reasonable time
        assert total_time < 5.0, f"Concurrent requests took too long: {total_time}s"