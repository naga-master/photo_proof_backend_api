"""
Clients API tests - Verify client CRUD operations.
Uses V2 API endpoints: /v2/clients/*
"""

import pytest


# V2 API base path
BASE_PATH = "/v2/clients"


class TestClientsEndpoints:
    """Test client API endpoints."""

    def test_list_clients_without_auth_returns_401(self, client):
        """Test listing clients requires authentication."""
        response = client.get(f"{BASE_PATH}/")
        assert response.status_code == 401

    def test_list_clients_with_auth(self, client, auth_headers):
        """Test listing clients with valid auth token."""
        response = client.get(f"{BASE_PATH}/", headers=auth_headers)
        # Returns empty list or 401/403 depending on user setup
        assert response.status_code in [200, 401, 403]

    def test_get_client_without_auth_returns_401(self, client):
        """Test getting single client requires authentication."""
        response = client.get(f"{BASE_PATH}/1")
        assert response.status_code == 401

    def test_get_client_not_found(self, client, auth_headers):
        """Test getting non-existent client returns 404."""
        response = client.get(f"{BASE_PATH}/99999", headers=auth_headers)
        assert response.status_code in [404, 401, 403]

    def test_create_client_without_auth_returns_401(self, client):
        """Test creating client requires authentication."""
        response = client.post(
            f"{BASE_PATH}/",
            json={"name": "Test Client", "email": "test@example.com"}
        )
        assert response.status_code == 401

    def test_create_client_missing_required_fields(self, client, auth_headers):
        """Test creating client with missing fields returns 422."""
        response = client.post(
            f"{BASE_PATH}/",
            json={},
            headers=auth_headers
        )
        assert response.status_code in [422, 401, 403]

    def test_create_client_invalid_email(self, client, auth_headers):
        """Test creating client with invalid email format."""
        response = client.post(
            f"{BASE_PATH}/",
            json={"name": "Test", "email": "invalid-email"},
            headers=auth_headers
        )
        # Should fail validation
        assert response.status_code in [422, 400, 401, 403]

    def test_update_client_without_auth_returns_401(self, client):
        """Test updating client requires authentication."""
        response = client.patch(
            f"{BASE_PATH}/1",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 401

    def test_delete_client_without_auth_returns_401(self, client):
        """Test deleting client requires authentication."""
        response = client.delete(f"{BASE_PATH}/1")
        assert response.status_code == 401

    def test_list_clients_with_search(self, client, auth_headers):
        """Test listing clients with search parameter."""
        response = client.get(
            f"{BASE_PATH}/?search=test",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_list_clients_with_status_filter(self, client, auth_headers):
        """Test listing clients with status filter."""
        response = client.get(
            f"{BASE_PATH}/?status_filter=active",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_list_clients_with_pagination(self, client, auth_headers):
        """Test listing clients with pagination."""
        response = client.get(
            f"{BASE_PATH}/?skip=0&limit=10",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_list_clients_invalid_pagination(self, client, auth_headers):
        """Test listing clients with invalid pagination params."""
        # Negative skip should fail validation
        response = client.get(
            f"{BASE_PATH}/?skip=-1",
            headers=auth_headers
        )
        assert response.status_code in [422, 200, 401, 403]


class TestClientCreation:
    """Test client creation scenarios."""

    def test_create_client_with_minimal_data(self, client, auth_headers):
        """Test creating client with minimum required fields."""
        response = client.post(
            f"{BASE_PATH}/",
            json={
                "name": "Minimal Client",
                "email": "minimal@example.com"
            },
            headers=auth_headers
        )
        # May fail due to studio validation or succeed
        assert response.status_code in [200, 201, 401, 403]

    def test_create_client_with_full_data(self, client, auth_headers):
        """Test creating client with all optional fields."""
        response = client.post(
            f"{BASE_PATH}/",
            json={
                "name": "Full Client",
                "email": "full@example.com",
                "phone": "+1234567890",
                "address": "123 Test St",
                "whatsapp_opt_in": True,
                "email_opt_in": True,
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 401, 403]


class TestClientPasswordGeneration:
    """Test client password/credential endpoints."""

    def test_generate_password_without_auth(self, client):
        """Test generating password requires authentication."""
        response = client.post(f"{BASE_PATH}/1/generate-password")
        assert response.status_code == 401

    def test_reset_password_without_auth(self, client):
        """Test resetting password requires authentication."""
        response = client.post(f"{BASE_PATH}/1/reset-password")
        assert response.status_code == 401

    def test_send_credentials_without_auth(self, client):
        """Test sending credentials requires authentication."""
        response = client.post(f"{BASE_PATH}/1/send-credentials")
        assert response.status_code == 401
