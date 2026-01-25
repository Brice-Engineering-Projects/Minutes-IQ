"""
Integration tests for password reset flow.

Tests the complete password reset functionality including:
- Reset token generation and validation
- Token expiration
- Single-use token enforcement
- Password update
- Email enumeration protection
"""

import time

import pytest
from fastapi.testclient import TestClient

from jea_meeting_web_scraper.auth.security import get_password_hash, verify_password
from jea_meeting_web_scraper.db.client import get_db_connection
from jea_meeting_web_scraper.db.password_reset_repository import (
    PasswordResetRepository,
)
from jea_meeting_web_scraper.db.password_reset_service import PasswordResetService
from jea_meeting_web_scraper.db.user_repository import UserRepository
from jea_meeting_web_scraper.main import app

client = TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user for password reset testing."""
    with get_db_connection() as conn:
        user_repo = UserRepository(conn)

        # Create test user
        user = user_repo.create_user(
            username="testuser", email="testuser@example.com", role_id=2
        )

        # Create password credentials
        hashed_password = get_password_hash("originalpassword")
        cursor = conn.execute(
            """
            INSERT INTO auth_credentials (user_id, provider_id, hashed_password, is_active)
            VALUES (?, 1, ?, 1);
            """,
            (user["user_id"], hashed_password),
        )
        cursor.close()
        conn.commit()

        return user


class TestPasswordResetRequest:
    """Tests for initiating password reset."""

    def test_request_reset_with_valid_email(self, test_user):
        """Test that reset request succeeds with a valid email."""
        response = client.post(
            "/auth/reset-request",
            json={"email": test_user["email"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "password reset link has been sent" in data["message"].lower()

        # Verify token was created in database
        with get_db_connection() as conn:
            repo = PasswordResetRepository(conn)
            tokens = repo.get_user_tokens(test_user["user_id"], valid_only=True)
            assert len(tokens) == 1
            assert tokens[0]["is_valid"] == 1

    def test_request_reset_with_nonexistent_email(self):
        """Test that reset request returns success even with non-existent email (security)."""
        response = client.post(
            "/auth/reset-request",
            json={"email": "nonexistent@example.com"},
        )

        # Should return success to prevent email enumeration
        assert response.status_code == 200
        data = response.json()
        assert "password reset link has been sent" in data["message"].lower()

    def test_request_reset_invalidates_previous_tokens(self, test_user):
        """Test that requesting a new reset invalidates previous tokens."""
        # First request
        response1 = client.post(
            "/auth/reset-request",
            json={"email": test_user["email"]},
        )
        assert response1.status_code == 200

        # Second request
        response2 = client.post(
            "/auth/reset-request",
            json={"email": test_user["email"]},
        )
        assert response2.status_code == 200

        # Verify only one valid token exists
        with get_db_connection() as conn:
            repo = PasswordResetRepository(conn)
            tokens = repo.get_user_tokens(test_user["user_id"], valid_only=True)
            assert len(tokens) == 1

    def test_request_reset_with_invalid_email_format(self):
        """Test that reset request rejects invalid email format."""
        response = client.post(
            "/auth/reset-request",
            json={"email": "notanemail"},
        )

        assert response.status_code == 422  # Validation error


class TestPasswordResetConfirm:
    """Tests for completing password reset with token."""

    def test_confirm_reset_with_valid_token(self, test_user):
        """Test that password reset succeeds with a valid token."""
        # Create a reset token
        with get_db_connection() as conn:
            reset_repo = PasswordResetRepository(conn)
            user_repo = UserRepository(conn)
            service = PasswordResetService(reset_repo, user_repo)

            success, error, token = service.create_reset_token(test_user["email"])
            assert success
            assert token is not None

        # Confirm reset with the token
        new_password = "newSecurePassword123"
        response = client.post(
            "/auth/reset-confirm",
            json={"token": token, "new_password": new_password},
        )

        assert response.status_code == 200
        data = response.json()
        assert "password has been reset successfully" in data["message"].lower()

        # Verify password was updated
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT hashed_password
                FROM auth_credentials
                WHERE user_id = ? AND provider_id = 1;
                """,
                (test_user["user_id"],),
            )
            row = cursor.fetchone()
            cursor.close()

            assert row is not None
            assert verify_password(new_password, row[0])

    def test_confirm_reset_with_invalid_token(self):
        """Test that password reset fails with an invalid token."""
        response = client.post(
            "/auth/reset-confirm",
            json={"token": "invalid-token-12345", "new_password": "newPassword123"},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_confirm_reset_with_used_token(self, test_user):
        """Test that password reset fails with an already-used token."""
        # Create and use a reset token
        with get_db_connection() as conn:
            reset_repo = PasswordResetRepository(conn)
            user_repo = UserRepository(conn)
            service = PasswordResetService(reset_repo, user_repo)

            success, error, token = service.create_reset_token(test_user["email"])
            assert success

            # Use the token once
            success, error = service.reset_password(token, "firstNewPassword")
            assert success

        # Try to use the same token again
        response = client.post(
            "/auth/reset-confirm",
            json={"token": token, "new_password": "secondNewPassword"},
        )

        assert response.status_code == 400
        assert "already been used" in response.json()["detail"].lower()

    def test_confirm_reset_with_expired_token(self, test_user):
        """Test that password reset fails with an expired token."""
        # Create a token that expires immediately
        with get_db_connection() as conn:
            reset_repo = PasswordResetRepository(conn)
            user_repo = UserRepository(conn)
            service = PasswordResetService(reset_repo, user_repo)

            # Generate token
            token = service.generate_token()
            token_hash = service.hash_token(token)

            # Create token with past expiration
            current_time = int(time.time())
            reset_repo.create_token(
                user_id=test_user["user_id"],
                token_hash=token_hash,
                created_at=current_time - 3600,  # Created 1 hour ago
                expires_at=current_time - 1,  # Expired 1 second ago
            )
            conn.commit()

        # Try to use expired token
        response = client.post(
            "/auth/reset-confirm",
            json={"token": token, "new_password": "newPassword123"},
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_confirm_reset_rejects_weak_password(self, test_user):
        """Test that password reset rejects weak passwords."""
        # Create a reset token
        with get_db_connection() as conn:
            reset_repo = PasswordResetRepository(conn)
            user_repo = UserRepository(conn)
            service = PasswordResetService(reset_repo, user_repo)

            success, error, token = service.create_reset_token(test_user["email"])
            assert success

        # Try to set a weak password
        response = client.post(
            "/auth/reset-confirm",
            json={"token": token, "new_password": "weak"},  # Too short
        )

        assert response.status_code == 422  # Validation error
        assert "at least 8 characters" in str(response.json()).lower()


class TestPasswordResetTokenSecurity:
    """Tests for password reset token security features."""

    def test_token_is_hashed_in_database(self, test_user):
        """Test that tokens are stored as hashes, not plaintext."""
        with get_db_connection() as conn:
            reset_repo = PasswordResetRepository(conn)
            user_repo = UserRepository(conn)
            service = PasswordResetService(reset_repo, user_repo)

            # Create a token
            success, error, token = service.create_reset_token(test_user["email"])
            assert success
            assert token is not None

            # Get token from database
            tokens = reset_repo.get_user_tokens(test_user["user_id"])
            assert len(tokens) == 1

            # Verify stored token is a hash, not the plaintext
            stored_token_hash = tokens[0]["token_hash"]
            assert stored_token_hash != token
            assert len(stored_token_hash) == 64  # SHA-256 hex length

    def test_multiple_users_can_have_concurrent_resets(self):
        """Test that multiple users can request resets simultaneously."""
        # Create two users
        with get_db_connection() as conn:
            user_repo = UserRepository(conn)

            user1 = user_repo.create_user(
                username="user1", email="user1@example.com", role_id=2
            )
            user2 = user_repo.create_user(
                username="user2", email="user2@example.com", role_id=2
            )

            # Add password credentials for both
            for user in [user1, user2]:
                hashed = get_password_hash("password123")
                conn.execute(
                    """
                    INSERT INTO auth_credentials (user_id, provider_id, hashed_password, is_active)
                    VALUES (?, 1, ?, 1);
                    """,
                    (user["user_id"], hashed),
                )
            conn.commit()

        # Both users request resets
        response1 = client.post(
            "/auth/reset-request", json={"email": "user1@example.com"}
        )
        response2 = client.post(
            "/auth/reset-request", json={"email": "user2@example.com"}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify both have valid tokens
        with get_db_connection() as conn:
            repo = PasswordResetRepository(conn)
            user1_tokens = repo.get_user_tokens(user1["user_id"], valid_only=True)
            user2_tokens = repo.get_user_tokens(user2["user_id"], valid_only=True)

            assert len(user1_tokens) == 1
            assert len(user2_tokens) == 1

    def test_successful_reset_invalidates_all_user_tokens(self, test_user):
        """Test that successful password reset invalidates all tokens for the user."""
        # Create multiple tokens
        with get_db_connection() as conn:
            reset_repo = PasswordResetRepository(conn)
            user_repo = UserRepository(conn)
            service = PasswordResetService(reset_repo, user_repo)

            # Create first token
            success1, _, token1 = service.create_reset_token(test_user["email"])
            assert success1

            # Manually create another token (simulating multiple requests)
            token2 = service.generate_token()
            token2_hash = service.hash_token(token2)
            current_time = int(time.time())
            reset_repo.create_token(
                user_id=test_user["user_id"],
                token_hash=token2_hash,
                created_at=current_time,
                expires_at=current_time + 1800,
            )
            conn.commit()

        # Use the first token to reset password
        response = client.post(
            "/auth/reset-confirm",
            json={"token": token1, "new_password": "newPassword123"},
        )
        assert response.status_code == 200

        # Verify all tokens are invalidated
        with get_db_connection() as conn:
            repo = PasswordResetRepository(conn)
            valid_tokens = repo.get_user_tokens(test_user["user_id"], valid_only=True)
            assert len(valid_tokens) == 0


class TestPasswordResetTokenExpiration:
    """Tests for token expiration behavior."""

    def test_token_expires_after_30_minutes(self, test_user):
        """Test that tokens are created with 30-minute expiration."""
        with get_db_connection() as conn:
            reset_repo = PasswordResetRepository(conn)
            user_repo = UserRepository(conn)
            service = PasswordResetService(reset_repo, user_repo)

            # Create token
            before_time = int(time.time())
            success, error, token = service.create_reset_token(test_user["email"])
            after_time = int(time.time())

            assert success

            # Get token from database
            tokens = reset_repo.get_user_tokens(test_user["user_id"])
            assert len(tokens) == 1

            created_at = tokens[0]["created_at"]
            expires_at = tokens[0]["expires_at"]

            # Verify creation time is recent
            assert before_time <= created_at <= after_time

            # Verify expiration is 30 minutes (1800 seconds) after creation
            expected_expiration = created_at + 1800
            assert expires_at == expected_expiration
