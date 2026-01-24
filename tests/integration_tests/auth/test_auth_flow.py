"""Integration tests for complete authentication flow."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jea_meeting_web_scraper.auth.routes import router
from jea_meeting_web_scraper.auth.schemas import fake_users_db
from jea_meeting_web_scraper.auth.security import get_password_hash


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/auth")
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def test_user_credentials():
    """Provide test user credentials."""
    return {"username": "testuser", "password": "secret"}


@pytest.fixture(autouse=True)
def reset_fake_db():
    """Reset fake database before each test."""
    fake_users_db.clear()
    fake_users_db["testuser"] = {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    }


class TestLoginFlow:
    """Test complete login flow."""

    def test_successful_login(self, client, test_user_credentials):
        """Test successful login returns access token."""
        response = client.post("/auth/login", data=test_user_credentials)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_with_wrong_password(self, client):
        """Test login with incorrect password fails."""
        response = client.post(
            "/auth/login", data={"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_with_nonexistent_user(self, client):
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

    def test_login_missing_password(self, client):
        """Test login without password fails."""
        response = client.post("/auth/login", data={"username": "testuser"})

        assert response.status_code == 422  # Validation error


class TestRegistrationFlow:
    """Test user registration flow."""

    def test_successful_registration(self, client):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "hashed_password" not in data  # Should not expose password

    def test_register_duplicate_username(self, client):
        """Test that registering with existing username fails."""
        # testuser already exists from fixture
        user_data = {
            "username": "testuser",
            "email": "another@example.com",
            "password": "password123",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_then_login(self, client):
        """Test that newly registered user can immediately login."""
        # Register new user
        user_data = {
            "username": "freshuser",
            "email": "fresh@example.com",
            "password": "freshpass123",
        }
        client.post("/auth/register", json=user_data)

        # Try to login
        login_response = client.post(
            "/auth/login",
            data={"username": "freshuser", "password": "freshpass123"},
        )

        assert login_response.status_code == 200
        assert "access_token" in login_response.json()


class TestProtectedEndpoints:
    """Test protected endpoints requiring authentication."""

    def test_access_me_with_valid_token(self, client, test_user_credentials):
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

    def test_refresh_token_with_valid_token(self, client, test_user_credentials):
        """Test refreshing token with valid credentials."""
        # Login first
        login_response = client.post("/auth/login", data=test_user_credentials)
        old_token = login_response.json()["access_token"]

        # Refresh token
        refresh_response = client.post(
            "/auth/refresh", headers={"Authorization": f"Bearer {old_token}"}
        )

        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        assert new_token != old_token
        assert len(new_token) > 0

    def test_refresh_token_without_auth(self, client):
        """Test refreshing token without authentication fails."""
        response = client.post("/auth/refresh")

        assert response.status_code == 401


class TestDisabledUser:
    """Test behavior with disabled user accounts."""

    def test_disabled_user_cannot_access_protected_routes(self, client):
        """Test that disabled users cannot access protected routes."""
        # Create disabled user
        password = "password123"
        fake_users_db["disabled"] = {
            "username": "disabled",
            "email": "disabled@example.com",
            "hashed_password": get_password_hash(password),
            "disabled": True,
        }

        # Login (authentication succeeds)
        login_response = client.post(
            "/auth/login", data={"username": "disabled", "password": password}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Try to access protected endpoint
        me_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert me_response.status_code == 400
        assert "inactive" in me_response.json()["detail"].lower()
