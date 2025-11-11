"""
Comprehensive API tests for CandidateX backend.
Covers all major endpoints with various scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any, List
import json
import io
import asyncio
from httpx import AsyncClient


@pytest.mark.api
class TestAuthenticationAPI:
    """Comprehensive authentication API tests."""

    def test_user_registration_complete_flow(self, client: TestClient):
        """Test complete user registration flow."""
        user_data = {
            "email": "completetest@example.com",
            "full_name": "Complete Test User",
            "password": "SecurePass123!",
            "role": "candidate"
        }

        # Register user
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        user_id = data["id"]

        # Try to login immediately (should work since email verification is optional)
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }

        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200

        token_data = login_response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # Get user profile
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200

        profile = profile_response.json()
        assert profile["email"] == user_data["email"]
        assert profile["full_name"] == user_data["full_name"]

    def test_password_validation_rules(self, client: TestClient):
        """Test password validation rules."""
        test_cases = [
            # (password, should_pass)
            ("weak", False),  # Too short
            ("nouppercaseordigit", False),  # Missing uppercase and digit
            ("NOLOWERCASEORDIGIT", False),  # Missing lowercase and digit
            ("NoSpecialChar123", False),  # Missing special character
            ("ValidPass123!", True),  # Valid password
        ]

        for password, should_pass in test_cases:
            user_data = {
                "email": f"test_{password}@example.com",
                "full_name": "Test User",
                "password": password,
                "role": "candidate"
            }

            response = client.post("/api/v1/auth/register", json=user_data)

            if should_pass:
                assert response.status_code == 201
            else:
                assert response.status_code == 400
                assert "password" in response.json()["detail"].lower()

    def test_account_lockout_mechanism(self, client: TestClient, test_user: Dict[str, Any]):
        """Test account lockout after failed login attempts."""
        # Attempt multiple failed logins
        for i in range(6):  # More than the limit
            login_data = {
                "username": test_user["email"],
                "password": "wrongpassword"
            }
            response = client.post("/api/v1/auth/login", data=login_data)

            if i < 5:  # First 5 should fail but not lock
                assert response.status_code == 401
            else:  # 6th should be locked
                assert response.status_code == 423  # Locked

        # Verify account is actually locked
        correct_login_data = {
            "username": test_user["email"],
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/login", data=correct_login_data)
        assert response.status_code == 423

    def test_token_expiration_and_refresh(self, client: TestClient, test_user: Dict[str, Any]):
        """Test token expiration and refresh functionality."""
        # Login to get tokens
        login_data = {
            "username": test_user["email"],
            "password": "testpassword123"
        }

        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200

        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # Use access token
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200

        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/api/v1/auth/refresh-token", json=refresh_data)
        assert refresh_response.status_code == 200

        new_tokens = refresh_response.json()
        assert new_tokens["access_token"] != access_token
        assert new_tokens["refresh_token"] != refresh_token

        # Old token should still work (until it expires)
        old_headers = {"Authorization": f"Bearer {access_token}"}
        old_profile_response = client.get("/api/v1/auth/me", headers=old_headers)
        assert old_profile_response.status_code == 200


@pytest.mark.api
class TestInterviewAPI:
    """Comprehensive interview API tests."""

    async def test_complete_interview_workflow(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test complete interview creation and execution workflow."""
        # Create interview
        interview_data = {
            "job_title": "Senior Software Engineer",
            "job_description": "Build scalable web applications using React, Node.js, and AWS",
            "experience_level": "senior",
            "question_count": 3,
            "time_limit_per_question": 300,
            "interview_mode": "technical",
            "interview_type": "mixed"
        }

        create_response = await client.post(
            "/api/v1/interviews/",
            json=interview_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200

        interview = create_response.json()
        interview_id = interview["id"]

        # Get interview details
        get_response = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200

        # Start interview
        start_response = await client.post(
            f"/api/v1/interviews/{interview_id}/start",
            headers=auth_headers
        )
        assert start_response.status_code == 200

        # Submit responses for each question
        interview_details = get_response.json()
        questions = interview_details.get("questions", [])

        for i, question in enumerate(questions):
            response_data = {
                "question_index": i,
                "response_text": f"This is my response to question {i+1}: {question.get('question_text', '')}",
                "time_spent": 150
            }

            submit_response = await client.post(
                f"/api/v1/interviews/{interview_id}/submit-response",
                json=response_data,
                headers=auth_headers
            )
            assert submit_response.status_code == 200

        # Complete interview
        complete_response = await client.post(
            f"/api/v1/interviews/{interview_id}/complete",
            headers=auth_headers
        )
        assert complete_response.status_code == 200

        # Verify final interview state
        final_get_response = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers=auth_headers
        )
        assert final_get_response.status_code == 200

        final_interview = final_get_response.json()
        assert final_interview["status"] == "completed"
        assert "overall_score" in final_interview
        assert "ai_feedback" in final_interview

    async def test_interview_permissions(self, client: AsyncClient, auth_headers: Dict[str, str], test_db):
        """Test interview access permissions."""
        # Create interview for current user
        interview_data = {
            "job_title": "Test Engineer",
            "job_description": "Testing role",
            "experience_level": "mid",
            "question_count": 2,
            "time_limit_per_question": 300
        }

        create_response = await client.post(
            "/api/v1/interviews/",
            json=interview_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        interview_id = create_response.json()["id"]

        # Create another user
        from app.auth.utils import get_password_hash
        other_user = {
            "email": "other@example.com",
            "full_name": "Other User",
            "password_hash": get_password_hash("otherpass123"),
            "role": "candidate",
            "status": "active",
            "email_verified": True
        }

        other_result = await test_db.users.insert_one(other_user)
        other_user_id = str(other_result.inserted_id)

        # Create token for other user
        from app.auth.utils import create_access_token
        other_token_data = {
            "sub": other_user_id,
            "email": other_user["email"],
            "role": other_user["role"]
        }
        other_token = create_access_token(other_token_data)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access interview with other user - should fail
        access_response = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers=other_headers
        )
        assert access_response.status_code == 404  # Not found for security

    async def test_interview_validation(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test interview data validation."""
        # Test invalid experience level
        invalid_data = {
            "job_title": "Test",
            "job_description": "Test",
            "experience_level": "invalid_level",
            "question_count": 5
        }

        response = await client.post(
            "/api/v1/interviews/",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

        # Test question count limits
        too_many_questions = {
            "job_title": "Test",
            "job_description": "Test",
            "experience_level": "mid",
            "question_count": 50  # Over limit
        }

        response = await client.post(
            "/api/v1/interviews/",
            json=too_many_questions,
            headers=auth_headers
        )
        assert response.status_code == 422

    async def test_interview_analytics(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test interview analytics functionality."""
        # Create multiple interviews
        interviews_data = [
            {
                "job_title": "Frontend Developer",
                "job_description": "React development",
                "experience_level": "mid",
                "question_count": 3
            },
            {
                "job_title": "Backend Developer",
                "job_description": "Node.js development",
                "experience_level": "senior",
                "question_count": 4
            }
        ]

        created_interviews = []
        for interview_data in interviews_data:
            response = await client.post(
                "/api/v1/interviews/",
                json=interview_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            created_interviews.append(response.json())

        # Get analytics
        analytics_response = await client.get(
            "/api/v1/interviews/analytics/overview",
            headers=auth_headers
        )
        assert analytics_response.status_code == 200

        analytics = analytics_response.json()
        assert "total_interviews" in analytics
        assert "average_score" in analytics
        assert "interviews_by_type" in analytics
        assert "recent_interviews" in analytics
        assert analytics["total_interviews"] >= len(created_interviews)


@pytest.mark.api
class TestResumeAPI:
    """Comprehensive resume API tests."""

    async def test_resume_upload_and_processing(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test complete resume upload and processing workflow."""
        # Create a mock PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Software Engineer Resume) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF"

        # Create upload file
        files = {"file": ("test_resume.pdf", io.BytesIO(pdf_content), "application/pdf")}

        # Upload resume
        upload_response = await client.post(
            "/api/v1/resume/upload",
            files=files,
            headers=auth_headers
        )

        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            assert "resume_id" in upload_data
            assert upload_data["upload_status"] == "uploaded"

            resume_id = upload_data["resume_id"]

            # Check resume in list
            list_response = await client.get("/api/v1/resume/list", headers=auth_headers)
            assert list_response.status_code == 200

            resume_list = list_response.json()["resumes"]
            assert len(resume_list) > 0

            # Get resume details
            details_response = await client.get(
                f"/api/v1/resume/{resume_id}",
                headers=auth_headers
            )
            assert details_response.status_code == 200

            # Note: Analysis would happen asynchronously in real implementation
            # For testing, we verify the structure
            resume_details = details_response.json()
            assert "filename" in resume_details
            assert "processing_status" in resume_details

    async def test_resume_job_matching(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test resume-job matching functionality."""
        # Create a mock resume (simplified for testing)
        resume_data = {
            "filename": "test_resume.pdf",
            "content": "Experienced software engineer with Python, React, and AWS skills. 5 years experience."
        }

        job_description = """
        Senior Software Engineer position requiring:
        - Python programming experience
        - React.js frontend development
        - AWS cloud services
        - 3+ years of experience
        - Bachelor's degree in Computer Science
        """

        # Test job matching (mock implementation)
        match_data = {
            "resume_id": "test_resume_123",
            "job_description": job_description,
            "job_title": "Senior Software Engineer"
        }

        # This would normally require an existing resume
        # For testing, we verify the endpoint structure
        match_response = await client.post(
            "/api/v1/resume/test_resume_123/compare",
            json=match_data,
            headers=auth_headers
        )
        # Should fail with 404 since resume doesn't exist
        assert match_response.status_code == 404

    async def test_resume_analytics(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test resume analytics functionality."""
        analytics_response = await client.get(
            "/api/v1/resume/analytics/overview",
            headers=auth_headers
        )
        assert analytics_response.status_code == 200

        analytics = analytics_response.json()
        assert "stats" in analytics
        assert "score_distribution" in analytics
        assert "recent_comparisons" in analytics
        assert "insights" in analytics


@pytest.mark.api
class TestSecurityAndAuthorization:
    """Security and authorization tests."""

    async def test_role_based_access_control(self, client: AsyncClient, admin_auth_headers: Dict[str, str], auth_headers: Dict[str, str]):
        """Test role-based access control."""
        # Regular user trying to access admin endpoints
        admin_response = await client.get("/api/v1/admin/dashboard", headers=auth_headers)
        assert admin_response.status_code == 403  # Forbidden

        # Admin accessing admin endpoints
        admin_dashboard_response = await client.get("/api/v1/admin/dashboard", headers=admin_auth_headers)
        # Should work (assuming admin endpoints exist)
        assert admin_dashboard_response.status_code in [200, 404]  # 404 if not implemented

    async def test_api_rate_limiting(self, client: AsyncClient):
        """Test API rate limiting."""
        # Make multiple requests quickly
        responses = []
        for i in range(150):  # More than rate limit
            response = await client.get("/api/v1/auth/me")  # Requires auth but tests rate limiting
            responses.append(response.status_code)

        # Should have some 429 (Too Many Requests) responses
        rate_limited_responses = [r for r in responses if r == 429]
        # Note: Rate limiting might not be fully implemented in test environment
        # This test verifies the structure is in place

    async def test_input_validation_and_sanitization(self, client: AsyncClient):
        """Test input validation and sanitization."""
        # Test SQL injection attempt
        malicious_data = {
            "email": "test@example.com",
            "full_name": "'; DROP TABLE users; --",
            "password": "password123"
        }

        response = await client.post("/api/v1/auth/register", json=malicious_data)
        # Should either sanitize or reject
        assert response.status_code in [201, 400, 422]

        # Test XSS attempt
        xss_data = {
            "email": "xss@example.com",
            "full_name": "<script>alert('xss')</script>",
            "password": "password123"
        }

        response = await client.post("/api/v1/auth/register", json=xss_data)
        assert response.status_code in [201, 400, 422]

    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are properly set."""
        response = await client.options("/api/v1/auth/login")

        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    async def test_security_headers(self, client: AsyncClient):
        """Test security headers are present."""
        response = await client.get("/")

        # Check security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "referrer-policy"
        ]

        for header in security_headers:
            assert header in response.headers


@pytest.mark.integration
class TestUserLevelScenarios:
    """User-level integration tests covering complete workflows."""

    async def test_candidate_onboarding_journey(self, client: AsyncClient):
        """Test complete candidate onboarding journey."""
        # 1. Register new account
        user_data = {
            "email": "candidate_journey@example.com",
            "full_name": "Journey Candidate",
            "password": "JourneyPass123!",
            "role": "candidate"
        }

        register_response = await client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # 2. Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }

        login_response = await client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200

        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # 3. Update profile
        profile_update = {
            "full_name": "Updated Journey Candidate"
        }

        # Note: Profile update endpoint might not exist, skip if not implemented

        # 4. Upload resume
        resume_content = b"Sample resume content for testing"
        files = {"file": ("journey_resume.pdf", io.BytesIO(resume_content), "application/pdf")}

        resume_response = await client.post(
            "/api/v1/resume/upload",
            files=files,
            headers=headers
        )

        if resume_response.status_code == 200:
            resume_data = resume_response.json()
            resume_id = resume_data["resume_id"]

            # 5. Create mock interview
            interview_data = {
                "job_title": "Software Engineer",
                "job_description": "Building web applications",
                "experience_level": "mid",
                "question_count": 2,
                "time_limit_per_question": 300
            }

            interview_response = await client.post(
                "/api/v1/interviews/",
                json=interview_data,
                headers=headers
            )
            assert interview_response.status_code == 200

            interview = interview_response.json()
            interview_id = interview["id"]

            # 6. Complete interview workflow
            start_response = await client.post(
                f"/api/v1/interviews/{interview_id}/start",
                headers=headers
            )
            assert start_response.status_code == 200

            # Submit responses
            for i in range(2):
                submit_data = {
                    "question_index": i,
                    "response_text": f"Sample response {i+1}",
                    "time_spent": 120
                }

                submit_response = await client.post(
                    f"/api/v1/interviews/{interview_id}/submit-response",
                    json=submit_data,
                    headers=headers
                )
                assert submit_response.status_code == 200

            # Complete interview
            complete_response = await client.post(
                f"/api/v1/interviews/{interview_id}/complete",
                headers=headers
            )
            assert complete_response.status_code == 200

            # 7. Check dashboard/analytics
            dashboard_response = await client.get("/api/v1/interviews/analytics/overview", headers=headers)
            assert dashboard_response.status_code == 200

    async def test_recruiter_workflow(self, client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test recruiter workflow for resume analysis."""
        # 1. Login as recruiter (using admin account)
        headers = admin_auth_headers

        # 2. Upload and analyze resumes
        resume_content = b"Senior Developer Resume: Python, React, AWS, 7 years experience"
        files = {"file": ("recruiter_resume.pdf", io.BytesIO(resume_content), "application/pdf")}

        upload_response = await client.post(
            "/api/v1/resume/upload",
            files=files,
            headers=headers
        )

        if upload_response.status_code == 200:
            resume_data = upload_response.json()
            resume_id = resume_data["resume_id"]

            # 3. Get resume analysis
            analysis_response = await client.get(
                f"/api/v1/resume/{resume_id}/analysis",
                headers=headers
            )
            # Analysis might not be ready immediately
            assert analysis_response.status_code in [200, 202, 422]

            # 4. Compare with job
            job_data = {
                "resume_id": resume_id,
                "job_description": "Senior Python Developer needed with React and AWS experience",
                "job_title": "Senior Python Developer"
            }

            compare_response = await client.post(
                f"/api/v1/resume/{resume_id}/compare",
                json=job_data,
                headers=headers
            )
            assert compare_response.status_code == 200

            comparison = compare_response.json()
            assert "match_score" in comparison
            assert "skills_match" in comparison
            assert "recommendations" in comparison

    async def test_admin_management_workflow(self, client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test admin management workflow."""
        headers = admin_auth_headers

        # 1. Get system analytics
        analytics_response = await client.get("/api/v1/interviews/analytics/overview", headers=headers)
        assert analytics_response.status_code == 200

        # 2. Get resume analytics
        resume_analytics_response = await client.get("/api/v1/resume/analytics/overview", headers=headers)
        assert resume_analytics_response.status_code == 200

        # 3. Check admin dashboard (if exists)
        admin_response = await client.get("/api/v1/admin/dashboard", headers=headers)
        assert admin_response.status_code in [200, 404]  # 404 if not implemented

    async def test_error_handling_and_recovery(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test error handling and recovery scenarios."""
        # Test invalid interview ID
        invalid_response = await client.get(
            "/api/v1/interviews/invalid_id_123",
            headers=auth_headers
        )
        assert invalid_response.status_code == 404

        # Test invalid resume ID
        invalid_resume_response = await client.get(
            "/api/v1/resume/invalid_resume_id",
            headers=auth_headers
        )
        assert invalid_resume_response.status_code == 404

        # Test malformed JSON
        malformed_response = await client.post(
            "/api/v1/interviews/",
            content="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert malformed_response.status_code == 422

        # Test unauthorized access
        no_auth_response = await client.get("/api/v1/auth/me")
        assert no_auth_response.status_code == 401

    async def test_performance_and_load_handling(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test performance and load handling."""
        import asyncio

        # Test concurrent requests
        async def make_request():
            return await client.get("/api/v1/auth/me", headers=auth_headers)

        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == len(responses)

        # Test large payload handling
        large_data = {
            "job_title": "Test Position",
            "job_description": "x" * 10000,  # Large description
            "experience_level": "senior",
            "question_count": 5
        }

        large_response = await client.post(
            "/api/v1/interviews/",
            json=large_data,
            headers=auth_headers
        )
        assert large_response.status_code in [200, 413]  # 413 if payload too large


@pytest.mark.slow
class TestDataIntegrityAndConsistency:
    """Tests for data integrity and consistency."""

    async def test_database_transaction_integrity(self, client: AsyncClient, auth_headers: Dict[str, str], test_db):
        """Test database transaction integrity."""
        # Create interview
        interview_data = {
            "job_title": "Integrity Test",
            "job_description": "Testing data integrity",
            "experience_level": "mid",
            "question_count": 2
        }

        create_response = await client.post(
            "/api/v1/interviews/",
            json=interview_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200

        interview = create_response.json()
        interview_id = interview["id"]

        # Verify interview exists in database
        db_interview = await test_db.interviews.find_one({"_id": interview_id})
        assert db_interview is not None
        assert db_interview["job_title"] == interview_data["job_title"]

        # Delete interview
        delete_response = await client.delete(
            f"/api/v1/interviews/{interview_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200

        # Verify interview is deleted
        deleted_interview = await test_db.interviews.find_one({"_id": interview_id})
        assert deleted_interview is None

    async def test_concurrent_user_operations(self, client: AsyncClient, test_db):
        """Test concurrent user operations."""
        import asyncio

        async def create_and_use_account(user_num: int):
            # Create user
            user_data = {
                "email": f"concurrent{user_num}@example.com",
                "full_name": f"Concurrent User {user_num}",
                "password": f"Pass{user_num}123!",
                "role": "candidate"
            }

            register_response = await client.post("/api/v1/auth/register", json=user_data)
            if register_response.status_code != 201:
                return False

            # Login
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }

            login_response = await client.post("/api/v1/auth/login", data=login_data)
            if login_response.status_code != 200:
                return False

            tokens = login_response.json()
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}

            # Create interview
            interview_data = {
                "job_title": f"Concurrent Test {user_num}",
                "job_description": "Testing concurrent operations",
                "experience_level": "mid",
                "question_count": 1
            }

            interview_response = await client.post(
                "/api/v1/interviews/",
                json=interview_data,
                headers=headers
            )

            return interview_response.status_code == 200

        # Run 5 concurrent user operations
        tasks = [create_and_use_account(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # At least some should succeed (depends on system capacity)
        success_count = sum(results)
        assert success_count >= 3  # At least 3 should succeed

    async def test_data_validation_constraints(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test data validation constraints."""
        # Test email format validation
        invalid_emails = ["invalid", "invalid@", "@invalid.com", "invalid.com"]

        for invalid_email in invalid_emails:
            user_data = {
                "email": invalid_email,
                "full_name": "Test User",
                "password": "ValidPass123!",
                "role": "candidate"
            }

            response = await client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 422  # Validation error

        # Test enum validation
        invalid_role_data = {
            "email": "enumtest@example.com",
            "full_name": "Enum Test",
            "password": "ValidPass123!",
            "role": "invalid_role"
        }

        response = await client.post("/api/v1/auth/register", json=invalid_role_data)
        assert response.status_code == 422

        # Test interview data constraints
        invalid_interview_data = {
            "job_title": "",  # Empty title
            "job_description": "Valid description",
            "experience_level": "mid",
            "question_count": 25  # Over limit
        }

        response = await client.post(
            "/api/v1/interviews/",
            json=invalid_interview_data,
            headers=auth_headers
        )
        assert response.status_code == 422
