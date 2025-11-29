"""
Health endpoint tests - Verify API is running and responding.
"""

import pytest


def test_health_endpoint_exists(client):
    """Test that health endpoint returns 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_api_docs_accessible(client):
    """Test that OpenAPI docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_unauthorized_endpoint_returns_401(client):
    """Test that protected endpoints return 401 without auth."""
    response = client.get("/api/projects")
    assert response.status_code == 401
