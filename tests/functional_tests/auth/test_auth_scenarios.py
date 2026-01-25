"""Functional tests for end-to-end authentication scenarios."""

from datetime import timedelta

from jea_meeting_web_scraper.auth.security import create_access_token, get_password_hash


class TestCompleteUserJourney:
    """Test complete user journey from login to access."""

    def test_login_and_access_protected_resource(
        self, client, test_user, test_user_credentials
    ):
        """Test complete flow: login, access protected resource."""
        # Step 1: Login
        login_response = client.post("/auth/login", data=test_user_credentials)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Step 2: Access protected resource
        me_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "testuser"


class TestTokenManagement:
    """Test token lifecycle and management."""

    def test_token_expiration_respected(self, client, db_connection, test_user):
        """Test that expired tokens are rejected."""
        # Create an expired token (negative expiration)
        expired_token = create_access_token(
            data={"sub": str(test_user["user_id"])},
            expires_delta=timedelta(seconds=-10),
        )

        # Try to use expired token
        response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_malformed_token_rejected(self, client):
        """Test that malformed tokens are rejected."""
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"}
        )

        assert response.status_code == 401

    def test_token_with_invalid_user_id(self, client):
        """Test that token with non-existent user ID is rejected."""
        # Create token for user that doesn't exist
        fake_token = create_access_token(data={"sub": "99999"})

        response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {fake_token}"}
        )

        assert response.status_code == 401


class TestSecurityBehavior:
    """Test security-related behavior."""

    def test_password_not_exposed_in_responses(
        self, client, test_user, test_user_credentials
    ):
        """Test that hashed passwords are never exposed."""
        # Login
        login_response = client.post("/auth/login", data=test_user_credentials)
        assert "hashed_password" not in login_response.json()
        assert "password" not in login_response.json()

        # Get user info
        token = login_response.json()["access_token"]
        me_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert "hashed_password" not in me_response.json()
        assert "password" not in me_response.json()

    def test_case_sensitive_username(self, client, test_user):
        """Test that usernames are case-sensitive."""
        # Try login with uppercase username
        response = client.post(
            "/auth/login",
            data={"username": "TESTUSER", "password": "secret"},
        )

        assert response.status_code == 401

    def test_sql_injection_attempt_in_username(self, client):
        """Test that SQL injection attempts in username are safely handled."""
        response = client.post(
            "/auth/login",
            data={
                "username": "admin' OR '1'='1",
                "password": "anything",
            },
        )

        # Should fail with 401, not crash
        assert response.status_code == 401


class TestConcurrentAccess:
    """Test concurrent access scenarios."""

    def test_multiple_concurrent_logins_same_user(
        self, client, test_user, test_user_credentials
    ):
        """Test that same user can have multiple valid tokens."""
        # Login twice
        response1 = client.post("/auth/login", data=test_user_credentials)
        token1 = response1.json()["access_token"]

        response2 = client.post("/auth/login", data=test_user_credentials)
        token2 = response2.json()["access_token"]

        # Both tokens should work
        me_response1 = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token1}"}
        )
        assert me_response1.status_code == 200

        me_response2 = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token2}"}
        )
        assert me_response2.status_code == 200

    def test_multiple_users_different_sessions(self, client, db_connection, clean_db):
        """Test that multiple users can have active sessions simultaneously."""
        # Create two users
        for i in [1, 2]:
            hashed_password = get_password_hash(f"password{i}")
            cursor = db_connection.execute(
                "INSERT INTO users (username, email, role_id) VALUES (?, ?, ?) RETURNING user_id;",
                (f"user{i}", f"user{i}@example.com", 2),
            )
            user_id = cursor.fetchone()[0]
            cursor.close()  # Close cursor before next statement

            cursor2 = db_connection.execute(
                "INSERT INTO auth_credentials (user_id, provider_id, hashed_password, is_active) VALUES (?, ?, ?, ?);",
                (user_id, 1, hashed_password, 1),
            )
            cursor2.close()  # Close cursor before commit
        db_connection.commit()

        # Login as both users
        token1 = client.post(
            "/auth/login", data={"username": "user1", "password": "password1"}
        ).json()["access_token"]

        token2 = client.post(
            "/auth/login", data={"username": "user2", "password": "password2"}
        ).json()["access_token"]

        # Both should be able to access their own info
        me1 = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token1}"}
        ).json()
        me2 = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token2}"}
        ).json()

        assert me1["username"] == "user1"
        assert me2["username"] == "user2"


class TestInactiveCredentials:
    """Test behavior with inactive credentials."""

    def test_inactive_credentials_cannot_login(self, client, db_connection, clean_db):
        """Test that users with inactive credentials cannot login."""
        # Create user with inactive credentials
        hashed_password = get_password_hash("testpass")
        cursor = db_connection.execute(
            "INSERT INTO users (username, email, role_id) VALUES (?, ?, ?) RETURNING user_id;",
            ("inactive_user", "inactive@example.com", 2),
        )
        user_id = cursor.fetchone()[0]
        cursor.close()  # Close cursor before next statement

        cursor2 = db_connection.execute(
            "INSERT INTO auth_credentials (user_id, provider_id, hashed_password, is_active) VALUES (?, ?, ?, ?);",
            (user_id, 1, hashed_password, 0),  # is_active = 0
        )
        cursor2.close()  # Close cursor before commit
        db_connection.commit()

        # Try to login
        response = client.post(
            "/auth/login",
            data={"username": "inactive_user", "password": "testpass"},
        )

        assert response.status_code == 401
