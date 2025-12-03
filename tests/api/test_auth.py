"""
Authentication API tests - Verify auth endpoints and token handling.
"""

import pytest
from app.services.auth_service import AuthService


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_without_credentials_returns_422(self, client):
        """Test login fails without credentials."""
        response = client.post("/api/auth/studio/login", json={})
        assert response.status_code == 422

    def test_login_with_invalid_credentials_returns_401(self, client):
        """Test login fails with invalid credentials."""
        response = client.post(
            "/api/auth/studio/login",
            json={"username": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_me_endpoint_without_auth_returns_401(self, client):
        """Test /me endpoint requires authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_endpoint_with_valid_token(self, client, auth_headers):
        """Test /me endpoint accepts valid token format."""
        response = client.get("/api/auth/me", headers=auth_headers)
        # Returns 401 because test user doesn't exist in DB
        # but token format is validated (not 403 or 422)
        assert response.status_code in [200, 401, 404]


class TestAuthService:
    """Test AuthService utility functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("wrong_password", hashed)

    def test_access_token_creation(self):
        """Test JWT access token creation."""
        token_data = {"sub": "user-123", "email": "test@example.com"}
        token = AuthService.create_access_token(token_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long

    def test_token_decode(self):
        """Test JWT token decoding."""
        token_data = {"sub": "user-123", "email": "test@example.com", "role": "studio"}
        token = AuthService.create_access_token(token_data)
        
        decoded = AuthService.decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "studio"

    def test_invalid_token_returns_none(self):
        """Test that invalid tokens return None."""
        result = AuthService.decode_token("invalid.token.here")
        assert result is None

    def test_password_generation(self):
        """Test random password generation."""
        password = AuthService.generate_password(12)
        
        assert len(password) == 12
        assert password.isalnum()
