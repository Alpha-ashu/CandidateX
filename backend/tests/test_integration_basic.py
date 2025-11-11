"""
Basic Integration Test - Framework Verification
Simple test to verify integration test framework is working.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_framework_basic_health_check():
    """Basic test to verify framework and app are working."""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_framework_basic_root():
    """Basic test to verify root endpoint."""
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "CandidateX" in data["message"]
    assert data["version"] == "1.0.0"


def test_framework_basic_auth_register():
    """Basic test to verify auth registration endpoint exists."""
    client = TestClient(app)
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "role": "candidate"
    })
    
    # Should either succeed (201) or fail with specific error (400 for duplicate, 422 for validation)
    assert response.status_code in [200, 201, 400, 422]


def test_framework_basic_auth_login():
    """Basic test to verify auth login endpoint exists."""
    client = TestClient(app)
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "Test123!"
    })
    
    # Should fail with 401 for invalid credentials
    assert response.status_code == 401


def test_framework_basic_protected_endpoint():
    """Basic test to verify protected endpoint requires auth."""
    client = TestClient(app)
    response = client.get("/api/v1/auth/me")
    
    # Should fail with 401 (unauthorized)
    assert response.status_code == 401


def test_framework_basic_api_docs():
    """Basic test to verify API documentation is accessible."""
    client = TestClient(app)
    response = client.get("/docs")
    
    # Should return HTML for Swagger UI
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_framework_basic_openapi_spec():
    """Basic test to verify OpenAPI specification."""
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"].startswith("3.")
    assert "CandidateX" in data["info"]["title"]