"""Integration tests for complete authentication flow."""


class TestLoginFlow:
    """Test complete login flow."""

    def test_successful_login(self, client, test_user, test_user_credentials):
        """Test successful login returns access token."""
        response = client.post("/auth/login", data=test_user_credentials)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_with_wrong_password(self, client, test_user):
        """Test login with incorrect password fails."""
        response = client.post(
            "/auth/login", data={"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_with_nonexistent_user(self, client, clean_db):
        """Test login with non-existent username fails."""
        response = client.post(
            "/auth/login", data={"username": "ghostuser", "password": "anypassword"}
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_missing_username(self, client):
        """Test login without username fails."""
        response = client.post("/auth/login", data={"password": "secret"})

        assert response.status_code == 422  # Validation error

    def test_login_missing_password(self, client, test_user):
        """Test login without password fails."""
        response = client.post("/auth/login", data={"username": "testuser"})

        assert response.status_code == 422  # Validation error


class TestProtectedEndpoints:
    """Test protected endpoints requiring authentication."""

    def test_access_me_with_valid_token(self, client, test_user, test_user_credentials):
        """Test accessing /me endpoint with valid token."""
        # Login first
        login_response = client.post("/auth/login", data=test_user_credentials)
        token = login_response.json()["access_token"]

        # Access protected endpoint
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_access_me_without_token(self, client):
        """Test accessing /me endpoint without token fails."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_access_me_with_invalid_token(self, client):
        """Test accessing /me endpoint with invalid token fails."""
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401
