"""Functional tests for end-to-end authentication scenarios."""

import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI
from jea_meeting_web_scraper.auth.routes import (
    router,
    fake_users_db,
    get_password_hash,
    create_access_token,
)


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


@pytest.fixture(autouse=True)
def reset_fake_db():
    """Reset fake database before each test."""
    fake_users_db.clear()
    fake_users_db["testuser"] = {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }


class TestCompleteUserJourney:
    """Test complete user journey from registration to access."""

    def test_new_user_registration_and_full_access(self, client):
        """Test complete flow: register, login, access protected resource, refresh token."""
        # Step 1: Register new user
        registration_data = {
            "username": "journey_user",
            "email": "journey@example.com",
            "password": "secure_password_123",
            "full_name": "Journey Test User",
        }
        reg_response = client.post("/auth/register", json=registration_data)
        assert reg_response.status_code == 200
        assert reg_response.json()["username"] == "journey_user"

        # Step 2: Login with new credentials
        login_response = client.post(
            "/auth/login",
            data={"username": "journey_user", "password": "secure_password_123"},
        )
        assert login_response.status_code == 200
        token1 = login_response.json()["access_token"]

        # Step 3: Access protected resource
        me_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token1}"}
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["username"] == "journey_user"
        assert user_data["email"] == "journey@example.com"

        # Step 4: Refresh token
        refresh_response = client.post(
            "/auth/refresh", headers={"Authorization": f"Bearer {token1}"}
        )
        assert refresh_response.status_code == 200
        token2 = refresh_response.json()["access_token"]
        assert token2 != token1

        # Step 5: Use refreshed token to access resource again
        me_response2 = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token2}"}
        )
        assert me_response2.status_code == 200
        assert me_response2.json()["username"] == "journey_user"


class TestSecurityScenarios:
    """Test security-related scenarios."""

    def test_token_expires_and_cannot_be_reused(self, client):
        """Test that expired tokens cannot be used."""
        # Create user with short-lived token
        username = "expiry_test"
        password = "password123"
        fake_users_db[username] = {
            "username": username,
            "hashed_password": get_password_hash(password),
            "disabled": False,
        }

        # Create an immediately expired token
        expired_token = create_access_token(
            data={"sub": username}, expires_delta=timedelta(seconds=-1)
        )

        # Try to use expired token
        response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_token_from_one_user_cannot_access_another_user_data(self, client):
        """Test that tokens are user-specific."""
        # Create two users
        user1_password = "password1"
        user2_password = "password2"

        fake_users_db["user1"] = {
            "username": "user1",
            "email": "user1@example.com",
            "hashed_password": get_password_hash(user1_password),
            "disabled": False,
        }
        fake_users_db["user2"] = {
            "username": "user2",
            "email": "user2@example.com",
            "hashed_password": get_password_hash(user2_password),
            "disabled": False,
        }

        # Login as user1
        response1 = client.post(
            "/auth/login", data={"username": "user1", "password": user1_password}
        )
        token1 = response1.json()["access_token"]

        # Check that token1 returns user1's data
        me_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token1}"}
        )
        assert me_response.json()["username"] == "user1"
        assert me_response.json()["email"] == "user1@example.com"

    def test_cannot_register_with_existing_username(self, client):
        """Test that duplicate usernames are rejected."""
        # First registration
        user_data = {
            "username": "popular_name",
            "email": "first@example.com",
            "password": "password1",
        }
        response1 = client.post("/auth/register", json=user_data)
        assert response1.status_code == 200

        # Second registration with same username
        user_data2 = {
            "username": "popular_name",
            "email": "second@example.com",
            "password": "password2",
        }
        response2 = client.post("/auth/register", json=user_data2)
        assert response2.status_code == 400

    def test_password_change_workflow(self, client):
        """Test simulated password change (register with new password)."""
        # Register initial user
        initial_data = {
            "username": "changeme",
            "email": "change@example.com",
            "password": "old_password",
        }
        client.post("/auth/register", json=initial_data)

        # Login with old password
        login1 = client.post(
            "/auth/login", data={"username": "changeme", "password": "old_password"}
        )
        assert login1.status_code == 200

        # Simulate password change by updating the database
        fake_users_db["changeme"]["hashed_password"] = get_password_hash(
            "new_password"
        )

        # Old password should no longer work
        login2 = client.post(
            "/auth/login", data={"username": "changeme", "password": "old_password"}
        )
        assert login2.status_code == 401

        # New password should work
        login3 = client.post(
            "/auth/login", data={"username": "changeme", "password": "new_password"}
        )
        assert login3.status_code == 200


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_username_registration(self, client):
        """Test that empty username is rejected."""
        user_data = {"username": "", "email": "test@example.com", "password": "pass"}
        response = client.post("/auth/register", json=user_data)

        # Should fail validation
        assert response.status_code == 422

    def test_very_long_password(self, client):
        """Test registration and login with very long password."""
        long_password = "a" * 1000
        user_data = {
            "username": "longpass",
            "email": "long@example.com",
            "password": long_password,
        }

        # Register
        reg_response = client.post("/auth/register", json=user_data)
        assert reg_response.status_code == 200

        # Login with long password
        login_response = client.post(
            "/auth/login", data={"username": "longpass", "password": long_password}
        )
        assert login_response.status_code == 200

    def test_special_characters_in_credentials(self, client):
        """Test handling of special characters in username and password."""
        user_data = {
            "username": "user@#$%",
            "email": "special@example.com",
            "password": "p@$$w0rd!#$%^&*()",
        }

        # Register
        reg_response = client.post("/auth/register", json=user_data)
        assert reg_response.status_code == 200

        # Login
        login_response = client.post(
            "/auth/login",
            data={"username": "user@#$%", "password": "p@$$w0rd!#$%^&*()"},
        )
        assert login_response.status_code == 200

    def test_multiple_concurrent_logins_same_user(self, client):
        """Test that same user can have multiple active tokens."""
        credentials = {"username": "testuser", "password": "secret"}

        # Login multiple times
        response1 = client.post("/auth/login", data=credentials)
        token1 = response1.json()["access_token"]

        response2 = client.post("/auth/login", data=credentials)
        token2 = response2.json()["access_token"]

        # Both tokens should be valid and different
        assert token1 != token2

        me1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"})
        me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})

        assert me1.status_code == 200
        assert me2.status_code == 200
