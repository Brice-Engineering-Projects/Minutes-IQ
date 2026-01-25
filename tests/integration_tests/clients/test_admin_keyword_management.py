"""
Integration tests for admin keyword management endpoints.
"""

from fastapi.testclient import TestClient


class TestCreateKeyword:
    """Tests for POST /admin/keywords endpoint."""

    def test_create_keyword_success(self, client: TestClient, admin_token: str):
        """Test successfully creating a keyword."""
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "keyword": "infrastructure",
                "category": "Public Works",
                "description": "Related to roads, bridges, and public facilities",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["keyword"] == "infrastructure"
        assert data["category"] == "Public Works"
        assert data["description"] == "Related to roads, bridges, and public facilities"
        assert data["is_active"] is True
        assert "keyword_id" in data
        assert "created_at" in data

    def test_create_keyword_minimal(self, client: TestClient, admin_token: str):
        """Test creating a keyword with only required fields."""
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "budget"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["keyword"] == "budget"
        assert data["category"] is None
        assert data["description"] is None

    def test_create_keyword_duplicate(self, client: TestClient, admin_token: str):
        """Test creating a duplicate keyword fails."""
        # Create first keyword
        client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "water"},
        )

        # Try to create duplicate
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "water"},
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_keyword_too_short(self, client: TestClient, admin_token: str):
        """Test creating a keyword that's too short."""
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "a"},  # Only 1 character
        )

        assert response.status_code == 400

    def test_create_keyword_requires_admin(self, client: TestClient, user_token: str):
        """Test that regular users cannot create keywords."""
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"keyword": "test"},
        )

        assert response.status_code == 403


class TestListKeywords:
    """Tests for GET /admin/keywords endpoint."""

    def test_list_keywords_empty(self, client: TestClient, admin_token: str):
        """Test listing keywords when none exist."""
        response = client.get(
            "/admin/keywords", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["keywords"] == []
        assert data["total"] == 0

    def test_list_keywords_with_data(self, client: TestClient, admin_token: str):
        """Test listing keywords with data."""
        # Create some keywords
        keywords = ["budget", "infrastructure", "utilities"]
        for kw in keywords:
            client.post(
                "/admin/keywords",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"keyword": kw},
            )

        response = client.get(
            "/admin/keywords", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["keywords"]) == 3
        assert data["total"] == 3

    def test_list_keywords_pagination(self, client: TestClient, admin_token: str):
        """Test listing keywords with pagination."""
        # Create 5 keywords
        for i in range(5):
            client.post(
                "/admin/keywords",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"keyword": f"keyword{i:02d}"},
            )

        # Get first page
        response = client.get(
            "/admin/keywords?limit=2&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["keywords"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_list_keywords_filter_category(self, client: TestClient, admin_token: str):
        """Test filtering keywords by category."""
        # Create keywords with different categories
        client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "roads", "category": "Infrastructure"},
        )
        client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "revenue", "category": "Finance"},
        )
        client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "bridges", "category": "Infrastructure"},
        )

        # Filter by Infrastructure category
        response = client.get(
            "/admin/keywords?category=Infrastructure",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for kw in data["keywords"]:
            assert kw["category"] == "Infrastructure"

    def test_list_keywords_filter_active(self, client: TestClient, admin_token: str):
        """Test filtering keywords by active status."""
        # Create active keyword
        client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "active_keyword"},
        )

        # Create and deactivate another keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "inactive_keyword"},
        )
        inactive_id = response.json()["keyword_id"]
        client.delete(
            f"/admin/keywords/{inactive_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Filter for active only
        response = client.get(
            "/admin/keywords?is_active=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["keywords"][0]["keyword"] == "active_keyword"


class TestGetKeyword:
    """Tests for GET /admin/keywords/{keyword_id} endpoint."""

    def test_get_keyword_success(self, client: TestClient, admin_token: str):
        """Test getting a specific keyword."""
        # Create keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "test_keyword", "category": "Test"},
        )
        keyword_id = response.json()["keyword_id"]

        # Get keyword
        response = client.get(
            f"/admin/keywords/{keyword_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["keyword"] == "test_keyword"
        assert data["category"] == "Test"

    def test_get_keyword_not_found(self, client: TestClient, admin_token: str):
        """Test getting a non-existent keyword."""
        response = client.get(
            "/admin/keywords/99999", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestUpdateKeyword:
    """Tests for PUT /admin/keywords/{keyword_id} endpoint."""

    def test_update_keyword_text(self, client: TestClient, admin_token: str):
        """Test updating a keyword's text."""
        # Create keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "original"},
        )
        keyword_id = response.json()["keyword_id"]

        # Update keyword text
        response = client.put(
            f"/admin/keywords/{keyword_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "updated"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["keyword"] == "updated"

    def test_update_keyword_category(self, client: TestClient, admin_token: str):
        """Test updating a keyword's category."""
        # Create keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "test"},
        )
        keyword_id = response.json()["keyword_id"]

        # Update category
        response = client.put(
            f"/admin/keywords/{keyword_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category": "New Category", "description": "New description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "New Category"
        assert data["description"] == "New description"
        assert data["keyword"] == "test"  # Unchanged

    def test_update_keyword_deactivate(self, client: TestClient, admin_token: str):
        """Test deactivating a keyword."""
        # Create keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "test"},
        )
        keyword_id = response.json()["keyword_id"]

        # Deactivate
        response = client.put(
            f"/admin/keywords/{keyword_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_keyword_not_found(self, client: TestClient, admin_token: str):
        """Test updating a non-existent keyword."""
        response = client.put(
            "/admin/keywords/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "updated"},
        )

        assert response.status_code == 404


class TestDeleteKeyword:
    """Tests for DELETE /admin/keywords/{keyword_id} endpoint."""

    def test_delete_keyword_success(self, client: TestClient, admin_token: str):
        """Test successfully deleting a keyword (soft delete)."""
        # Create keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "test"},
        )
        keyword_id = response.json()["keyword_id"]

        # Delete keyword
        response = client.delete(
            f"/admin/keywords/{keyword_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 204

        # Verify keyword is deactivated
        response = client.get(
            f"/admin/keywords/{keyword_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_delete_keyword_not_found(self, client: TestClient, admin_token: str):
        """Test deleting a non-existent keyword."""
        response = client.delete(
            "/admin/keywords/99999", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestSearchKeywords:
    """Tests for GET /admin/keywords/search endpoint."""

    def test_search_keywords(self, client: TestClient, admin_token: str):
        """Test searching for keywords."""
        # Create keywords
        keywords = ["water", "wastewater", "water_quality", "air_quality"]
        for kw in keywords:
            client.post(
                "/admin/keywords",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"keyword": kw},
            )

        # Search for "water"
        response = client.get(
            "/admin/keywords/search?q=water",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3  # water, wastewater, water_quality
        result_keywords = [k["keyword"] for k in data["results"]]
        assert "water" in result_keywords
        assert "wastewater" in result_keywords
        assert "water_quality" in result_keywords

    def test_search_keywords_no_results(self, client: TestClient, admin_token: str):
        """Test searching with no matches."""
        response = client.get(
            "/admin/keywords/search?q=nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 0


class TestGetCategories:
    """Tests for GET /admin/keywords/categories endpoint."""

    def test_get_categories(self, client: TestClient, admin_token: str):
        """Test getting all keyword categories."""
        # Create keywords with categories
        client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "roads", "category": "Infrastructure"},
        )
        client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "budget", "category": "Finance"},
        )
        client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "bridges", "category": "Infrastructure"},
        )

        response = client.get(
            "/admin/keywords/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert set(data["categories"]) == {"Infrastructure", "Finance"}

    def test_get_categories_empty(self, client: TestClient, admin_token: str):
        """Test getting categories when none exist."""
        response = client.get(
            "/admin/keywords/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["categories"] == []


class TestSuggestKeywords:
    """Tests for GET /admin/keywords/suggest endpoint."""

    def test_suggest_keywords(self, client: TestClient, admin_token: str):
        """Test getting keyword suggestions (autocomplete)."""
        # Create keywords
        keywords = ["infrastructure", "infrastructure_bond", "internet", "internal"]
        for kw in keywords:
            client.post(
                "/admin/keywords",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"keyword": kw},
            )

        # Get suggestions for "infra"
        response = client.get(
            "/admin/keywords/suggest?q=infra",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        # Should prioritize keywords that start with "infra"
        suggestions = [s["keyword"] for s in data["suggestions"]]
        assert "infrastructure" in suggestions
        assert "infrastructure_bond" in suggestions

    def test_suggest_keywords_limit(self, client: TestClient, admin_token: str):
        """Test suggestion limit."""
        # Create many keywords
        for i in range(15):
            client.post(
                "/admin/keywords",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"keyword": f"test{i:02d}"},
            )

        # Get suggestions with limit
        response = client.get(
            "/admin/keywords/suggest?q=test&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) <= 5


class TestKeywordUsage:
    """Tests for GET /admin/keywords/{keyword_id}/usage endpoint."""

    def test_get_keyword_usage(self, client: TestClient, admin_token: str):
        """Test getting clients that use a keyword."""
        # Create keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "water"},
        )
        keyword_id = response.json()["keyword_id"]

        # Create clients
        client_ids = []
        for i in range(3):
            response = client.post(
                "/admin/clients",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"name": f"Client {i}"},
            )
            client_ids.append(response.json()["client_id"])

        # Associate keyword with clients
        for cid in client_ids[:2]:  # Only first 2 clients
            client.post(
                f"/admin/clients/{cid}/keywords",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"keyword_id": keyword_id},
            )

        # Get keyword usage
        response = client.get(
            f"/admin/keywords/{keyword_id}/usage",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["keyword"] == "water"
        assert len(data["clients"]) == 2

    def test_get_keyword_usage_none(self, client: TestClient, admin_token: str):
        """Test getting usage for keyword with no clients."""
        # Create keyword
        response = client.post(
            "/admin/keywords",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"keyword": "unused"},
        )
        keyword_id = response.json()["keyword_id"]

        # Get keyword usage
        response = client.get(
            f"/admin/keywords/{keyword_id}/usage",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 0
