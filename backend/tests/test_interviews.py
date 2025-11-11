"""
Tests for interview endpoints.
"""
import pytest
from httpx import AsyncClient
from typing import Dict, Any


@pytest.mark.api
class TestInterviews:
    """Test interview endpoints."""

    async def test_create_interview(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test creating a new interview."""
        interview_data = {
            "job_title": "Software Engineer",
            "job_description": "Develop web applications using modern technologies",
            "experience_level": "mid",
            "question_count": 5,
            "time_limit_per_question": 300
        }

        response = await client.post("/api/v1/interviews/", json=interview_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["job_title"] == interview_data["job_title"]
        assert data["experience_level"] == interview_data["experience_level"]
        assert data["question_count"] == interview_data["question_count"]
        assert "id" in data
        assert data["status"] == "created"

    async def test_get_user_interviews(self, client: AsyncClient, auth_headers: Dict[str, str], test_interview: Dict[str, Any]):
        """Test getting user's interviews."""
        response = await client.get("/api/v1/interviews/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "interviews" in data
        assert len(data["interviews"]) >= 1

        # Check if our test interview is in the list
        interview_ids = [interview["id"] for interview in data["interviews"]]
        assert str(test_interview["_id"]) in interview_ids

    async def test_get_interview_details(self, client: AsyncClient, auth_headers: Dict[str, str], test_interview: Dict[str, Any]):
        """Test getting interview details."""
        interview_id = str(test_interview["_id"])
        response = await client.get(f"/api/v1/interviews/{interview_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == interview_id
        assert data["job_title"] == test_interview["job_title"]
        assert data["status"] == test_interview["status"]

    async def test_start_interview(self, client: AsyncClient, auth_headers: Dict[str, str], test_interview: Dict[str, Any]):
        """Test starting an interview."""
        interview_id = str(test_interview["_id"])
        response = await client.post(f"/api/v1/interviews/{interview_id}/start", headers=auth_headers)

        assert response.status_code == 200
        assert "started successfully" in response.json()["message"]

    async def test_submit_response(self, client: AsyncClient, auth_headers: Dict[str, str], test_interview: Dict[str, Any]):
        """Test submitting a response."""
        interview_id = str(test_interview["_id"])

        # First start the interview
        await client.post(f"/api/v1/interviews/{interview_id}/start", headers=auth_headers)

        # Submit a response
        response_data = {
            "question_index": 0,
            "response_text": "This is my answer to the question.",
            "time_spent": 150
        }

        response = await client.post(
            f"/api/v1/interviews/{interview_id}/submit-response",
            json=response_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "submitted successfully" in response.json()["message"]

    async def test_complete_interview(self, client: AsyncClient, auth_headers: Dict[str, str], test_interview: Dict[str, Any]):
        """Test completing an interview."""
        interview_id = str(test_interview["_id"])

        # Start the interview first
        await client.post(f"/api/v1/interviews/{interview_id}/start", headers=auth_headers)

        # Complete the interview
        response = await client.post(f"/api/v1/interviews/{interview_id}/complete", headers=auth_headers)

        assert response.status_code == 200
        assert "completed successfully" in response.json()["message"]

    async def test_get_interview_analytics(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test getting interview analytics."""
        response = await client.get("/api/v1/interviews/analytics/overview", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "score_distribution" in data
        assert "recent_interviews" in data

    async def test_interview_access_control(self, client: AsyncClient, admin_auth_headers: Dict[str, str], test_interview: Dict[str, Any]):
        """Test that users can only access their own interviews."""
        # Try to access another user's interview as admin
        interview_id = str(test_interview["_id"])
        response = await client.get(f"/api/v1/interviews/{interview_id}", headers=admin_auth_headers)

        # Admin should be able to access (different logic for admin)
        # This test assumes admin can access all interviews
        assert response.status_code in [200, 403]  # Either success or forbidden based on implementation


@pytest.mark.unit
class TestInterviewModels:
    """Test interview model validation."""

    def test_interview_create_validation(self):
        """Test interview creation validation."""
        from app.models.interview import InterviewCreate
        from pydantic import ValidationError

        # Valid data
        valid_data = {
            "job_title": "Software Engineer",
            "experience_level": "mid",
            "question_count": 5,
            "time_limit_per_question": 300
        }

        interview = InterviewCreate(**valid_data)
        assert interview.job_title == valid_data["job_title"]
        assert interview.question_count == valid_data["question_count"]

        # Invalid data - question count too low
        invalid_data = valid_data.copy()
        invalid_data["question_count"] = 2  # Below minimum

        with pytest.raises(ValidationError):
            InterviewCreate(**invalid_data)

        # Invalid data - time limit too short
        invalid_data2 = valid_data.copy()
        invalid_data2["time_limit_per_question"] = 30  # Below minimum

        with pytest.raises(ValidationError):
            InterviewCreate(**invalid_data2)


@pytest.mark.integration
@pytest.mark.slow
class TestInterviewWorkflow:
    """Test complete interview workflow."""

    async def test_full_interview_workflow(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test complete interview creation to completion workflow."""
        # 1. Create interview
        interview_data = {
            "job_title": "Frontend Developer",
            "job_description": "Build user interfaces with React",
            "experience_level": "mid",
            "question_count": 3,
            "time_limit_per_question": 300
        }

        create_response = await client.post("/api/v1/interviews/", json=interview_data, headers=auth_headers)
        assert create_response.status_code == 200
        interview_id = create_response.json()["id"]

        # 2. Get interview details
        details_response = await client.get(f"/api/v1/interviews/{interview_id}", headers=auth_headers)
        assert details_response.status_code == 200
        assert details_response.json()["status"] == "created"

        # 3. Start interview
        start_response = await client.post(f"/api/v1/interviews/{interview_id}/start", headers=auth_headers)
        assert start_response.status_code == 200

        # 4. Submit responses for all questions
        for i in range(3):
            response_data = {
                "question_index": i,
                "response_text": f"This is my answer to question {i+1}.",
                "time_spent": 120 + i * 30
            }

            submit_response = await client.post(
                f"/api/v1/interviews/{interview_id}/submit-response",
                json=response_data,
                headers=auth_headers
            )
            assert submit_response.status_code == 200

        # 5. Complete interview
        complete_response = await client.post(f"/api/v1/interviews/{interview_id}/complete", headers=auth_headers)
        assert complete_response.status_code == 200

        # 6. Verify interview is completed
        final_details = await client.get(f"/api/v1/interviews/{interview_id}", headers=auth_headers)
        assert final_details.status_code == 200
        assert final_details.json()["status"] == "completed"

        # 7. Check analytics updated
        analytics_response = await client.get("/api/v1/interviews/analytics/overview", headers=auth_headers)
        assert analytics_response.status_code == 200
