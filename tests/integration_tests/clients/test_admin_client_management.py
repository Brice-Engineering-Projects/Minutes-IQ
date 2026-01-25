"""
Integration tests for admin client management endpoints.
"""

from fastapi.testclient import TestClient


class TestCreateClient:
    """Tests for POST /admin/clients endpoint."""

    def test_create_client_success(self, client: TestClient, admin_token: str):
        """Test successfully creating a client."""
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "City of Jacksonville",
                "description": "Municipal government of Jacksonville, FL",
                "website_url": "https://www.coj.net",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "City of Jacksonville"
        assert data["description"] == "Municipal government of Jacksonville, FL"
        assert data["website_url"] == "https://www.coj.net"
        assert data["is_active"] is True
        assert "client_id" in data
        assert "created_at" in data

    def test_create_client_minimal(self, client: TestClient, admin_token: str):
        """Test creating a client with only required fields."""
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "JEA"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "JEA"
        assert data["description"] is None
        assert data["website_url"] is None

    def test_create_client_duplicate_name(self, client: TestClient, admin_token: str):
        """Test creating a client with duplicate name fails."""
        # Create first client
        client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Duval County Schools"},
        )

        # Try to create duplicate
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Duval County Schools"},
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_client_invalid_name(self, client: TestClient, admin_token: str):
        """Test creating a client with invalid name."""
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "AB"},  # Too short
        )

        assert response.status_code == 400

    def test_create_client_requires_admin(self, client: TestClient, user_token: str):
        """Test that regular users cannot create clients."""
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"name": "Test Client"},
        )

        assert response.status_code == 403


class TestListClients:
    """Tests for GET /admin/clients endpoint."""

    def test_list_clients_empty(self, client: TestClient, admin_token: str):
        """Test listing clients when none exist."""
        response = client.get(
            "/admin/clients", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["clients"] == []
        assert data["total"] == 0
        assert data["limit"] == 100
        assert data["offset"] == 0

    def test_list_clients_with_data(self, client: TestClient, admin_token: str):
        """Test listing clients with data."""
        # Create some clients
        for i in range(3):
            client.post(
                "/admin/clients",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"name": f"Client {i}"},
            )

        response = client.get(
            "/admin/clients", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 3
        assert data["total"] == 3

    def test_list_clients_pagination(self, client: TestClient, admin_token: str):
        """Test listing clients with pagination."""
        # Create 5 clients
        for i in range(5):
            client.post(
                "/admin/clients",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"name": f"Client {i:02d}"},
            )

        # Get first page
        response = client.get(
            "/admin/clients?limit=2&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Get second page
        response = client.get(
            "/admin/clients?limit=2&offset=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 2
        assert data["total"] == 5

    def test_list_clients_filter_active(self, client: TestClient, admin_token: str):
        """Test filtering clients by active status."""
        # Create active client
        client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Active Client"},
        )

        # Create and deactivate another client
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Inactive Client"},
        )
        inactive_id = response.json()["client_id"]
        client.delete(
            f"/admin/clients/{inactive_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Filter for active only
        response = client.get(
            "/admin/clients?is_active=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["clients"][0]["name"] == "Active Client"


class TestGetClient:
    """Tests for GET /admin/clients/{client_id} endpoint."""

    def test_get_client_success(self, client: TestClient, admin_token: str):
        """Test getting a specific client."""
        # Create client
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Test Client", "description": "Test description"},
        )
        client_id = response.json()["client_id"]

        # Get client
        response = client.get(
            f"/admin/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Client"
        assert data["description"] == "Test description"
        assert "keywords" in data

    def test_get_client_not_found(self, client: TestClient, admin_token: str):
        """Test getting a non-existent client."""
        response = client.get(
            "/admin/clients/99999", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestUpdateClient:
    """Tests for PUT /admin/clients/{client_id} endpoint."""

    def test_update_client_name(self, client: TestClient, admin_token: str):
        """Test updating a client's name."""
        # Create client
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Original Name"},
        )
        client_id = response.json()["client_id"]

        # Update name
        response = client.put(
            f"/admin/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert "updated_at" in data

    def test_update_client_multiple_fields(self, client: TestClient, admin_token: str):
        """Test updating multiple client fields."""
        # Create client
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Test Client"},
        )
        client_id = response.json()["client_id"]

        # Update multiple fields
        response = client.put(
            f"/admin/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "description": "New description",
                "website_url": "https://example.com",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"
        assert data["website_url"] == "https://example.com"
        assert data["name"] == "Test Client"  # Unchanged

    def test_update_client_deactivate(self, client: TestClient, admin_token: str):
        """Test deactivating a client."""
        # Create client
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Test Client"},
        )
        client_id = response.json()["client_id"]

        # Deactivate
        response = client.put(
            f"/admin/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_client_not_found(self, client: TestClient, admin_token: str):
        """Test updating a non-existent client."""
        response = client.put(
            "/admin/clients/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Name"},
        )

        assert response.status_code == 404


class TestDeleteClient:
    """Tests for DELETE /admin/clients/{client_id} endpoint."""

    def test_delete_client_success(self, client: TestClient, admin_token: str):
        """Test successfully deleting a client (soft delete)."""
        # Create client
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Test Client"},
        )
        client_id = response.json()["client_id"]

        # Delete client
        response = client.delete(
            f"/admin/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 204

        # Verify client is deactivated, not deleted
        response = client.get(
            f"/admin/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_delete_client_not_found(self, client: TestClient, admin_token: str):
        """Test deleting a non-existent client."""
        response = client.delete(
            "/admin/clients/99999", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestClientKeywordAssociations:
    """Tests for client-keyword association endpoints."""

    def test_add_keyword_to_client(self, client: TestClient, admin_token: str):
        """Test adding a keyword to a client."""
        # Create client
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Test Client"},
        )
        client_id = response.json()["client_id"]

        # Create keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "infrastructure"},
        )
        keyword_id = response.json()["keyword_id"]

        # Associate keyword with client
        response = client.post(
            f"/admin/clients/{client_id}/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword_id": keyword_id},
        )

        assert response.status_code == 201
        assert "success" in response.json()["message"].lower()

    def test_add_keyword_to_client_duplicate(
        self, client: TestClient, admin_token: str
    ):
        """Test adding the same keyword twice fails gracefully."""
        # Create client and keyword
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Test Client"},
        )
        client_id = response.json()["client_id"]

        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "budget"},
        )
        keyword_id = response.json()["keyword_id"]

        # Add keyword first time
        client.post(
            f"/admin/clients/{client_id}/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword_id": keyword_id},
        )

        # Try to add again
        response = client.post(
            f"/admin/clients/{client_id}/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword_id": keyword_id},
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_remove_keyword_from_client(self, client: TestClient, admin_token: str):
        """Test removing a keyword from a client."""
        # Create client and keyword
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Test Client"},
        )
        client_id = response.json()["client_id"]

        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "transportation"},
        )
        keyword_id = response.json()["keyword_id"]

        # Add keyword
        client.post(
            f"/admin/clients/{client_id}/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword_id": keyword_id},
        )

        # Remove keyword
        response = client.delete(
            f"/admin/clients/{client_id}/keywords/{keyword_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 204

    def test_get_client_keywords(self, client: TestClient, admin_token: str):
        """Test getting all keywords for a client."""
        # Create client
        response = client.post(
            "/admin/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Test Client"},
        )
        client_id = response.json()["client_id"]

        # Create and add keywords
        keywords = ["water", "utilities", "rates"]
        for kw in keywords:
            response = client.post(
                "/admin/keywords",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"keyword": kw},
            )
            keyword_id = response.json()["keyword_id"]
            client.post(
                f"/admin/clients/{client_id}/keywords",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"keyword_id": keyword_id},
            )

        # Get client keywords
        response = client.get(
            f"/admin/clients/{client_id}/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["keywords"]) == 3
        keyword_texts = [k["keyword"] for k in data["keywords"]]
        assert set(keyword_texts) == set(keywords)
