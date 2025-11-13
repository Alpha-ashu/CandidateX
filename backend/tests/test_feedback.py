"""
Tests for feedback system.
"""
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import Feedback, UserRole


class TestFeedback:
    """Test feedback functionality."""

    @pytest.mark.asyncio
    async def test_submit_feedback_anonymous(self, client: AsyncClient, db: AsyncIOMotorDatabase):
        """Test submitting anonymous feedback."""
        feedback_data = {
            "feedback_type": "general",
            "subject": "Test feedback",
            "message": "This is a test feedback message",
            "rating": 4,
            "page_url": "/dashboard"
        }

        response = await client.post("/api/v1/feedback/", json=feedback_data)
        assert response.status_code == 201

        data = response.json()
        assert data["feedback_type"] == "general"
        assert data["subject"] == "Test feedback"
        assert data["message"] == "This is a test feedback message"
        assert data["rating"] == 4
        assert data["status"] == "pending"
        assert data["user_id"] is None  # Anonymous

    @pytest.mark.asyncio
    async def test_submit_feedback_authenticated(self, client: AsyncClient, db: AsyncIOMotorDatabase, test_user_token: str):
        """Test submitting feedback as authenticated user."""
        feedback_data = {
            "feedback_type": "bug",
            "subject": "Bug report",
            "message": "Found a bug in the interview system",
            "rating": 2
        }

        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await client.post("/api/v1/feedback/", json=feedback_data, headers=headers)
        assert response.status_code == 201

        data = response.json()
        assert data["feedback_type"] == "bug"
        assert data["subject"] == "Bug report"
        assert data["rating"] == 2
        assert data["user_id"] is not None

    @pytest.mark.asyncio
    async def test_get_feedback_list_authenticated(self, client: AsyncClient, db: AsyncIOMotorDatabase, test_user_token: str):
        """Test getting feedback list as authenticated user."""
        # First submit some feedback
        feedback_data = {
            "feedback_type": "feature",
            "subject": "Feature request",
            "message": "Please add dark mode"
        }

        headers = {"Authorization": f"Bearer {test_user_token}"}
        await client.post("/api/v1/feedback/", json=feedback_data, headers=headers)

        # Get feedback list
        response = await client.get("/api/v1/feedback/", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check that user's feedback is included
        user_feedback = [f for f in data if f["subject"] == "Feature request"]
        assert len(user_feedback) == 1

    @pytest.mark.asyncio
    async def test_get_feedback_by_id(self, client: AsyncClient, db: AsyncIOMotorDatabase, test_user_token: str):
        """Test getting specific feedback by ID."""
        # Submit feedback
        feedback_data = {
            "feedback_type": "general",
            "subject": "Specific feedback",
            "message": "Testing get by ID"
        }

        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await client.post("/api/v1/feedback/", json=feedback_data, headers=headers)
        feedback_id = response.json()["id"]

        # Get feedback by ID
        response = await client.get(f"/api/v1/feedback/{feedback_id}", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == feedback_id
        assert data["subject"] == "Specific feedback"

    @pytest.mark.asyncio
    async def test_update_feedback_status_admin(self, client: AsyncClient, db: AsyncIOMotorDatabase, admin_token: str):
        """Test updating feedback status as admin."""
        # Submit feedback
        feedback_data = {
            "feedback_type": "bug",
            "subject": "Status update test",
            "message": "Testing status update"
        }

        response = await client.post("/api/v1/feedback/", json=feedback_data)
        feedback_id = response.json()["id"]

        # Update status as admin
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(f"/api/v1/feedback/{feedback_id}/status", params={"status": "reviewed"}, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "reviewed"

    @pytest.mark.asyncio
    async def test_delete_feedback(self, client: AsyncClient, db: AsyncIOMotorDatabase, test_user_token: str):
        """Test deleting feedback."""
        # Submit feedback
        feedback_data = {
            "feedback_type": "general",
            "subject": "Delete test",
            "message": "Testing deletion"
        }

        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await client.post("/api/v1/feedback/", json=feedback_data, headers=headers)
        feedback_id = response.json()["id"]

        # Delete feedback
        response = await client.delete(f"/api/v1/feedback/{feedback_id}", headers=headers)
        assert response.status_code == 200

        # Verify deletion
        response = await client.get(f"/api/v1/feedback/{feedback_id}", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_feedback_validation(self, client: AsyncClient):
        """Test feedback input validation."""
        # Test missing required fields
        invalid_data = {
            "feedback_type": "general"
            # Missing subject and message
        }

        response = await client.post("/api/v1/feedback/", json=invalid_data)
        assert response.status_code == 422  # Validation error

        # Test invalid rating
        invalid_data = {
            "feedback_type": "general",
            "subject": "Test",
            "message": "Test message",
            "rating": 6  # Invalid rating > 5
        }

        response = await client.post("/api/v1/feedback/", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feedback_stats_admin(self, client: AsyncClient, db: AsyncIOMotorDatabase, admin_token: str):
        """Test getting feedback statistics as admin."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/v1/feedback/stats/summary", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_feedback" in data
        assert "feedback_by_type" in data
        assert "feedback_by_status" in data
        assert "average_rating" in data

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient, db: AsyncIOMotorDatabase, test_user_token: str):
        """Test unauthorized access to admin-only endpoints."""
        # Try to access stats as regular user
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await client.get("/api/v1/feedback/stats/summary", headers=headers)
        assert response.status_code == 403

        # Submit feedback first to get an ID
        feedback_data = {"feedback_type": "general", "subject": "Test", "message": "Test"}
        response = await client.post("/api/v1/feedback/", json=feedback_data)
        feedback_id = response.json()["id"]

        # Try to update status as regular user
        response = await client.put(f"/api/v1/feedback/{feedback_id}/status", params={"status": "reviewed"}, headers=headers)
        assert response.status_code == 403
