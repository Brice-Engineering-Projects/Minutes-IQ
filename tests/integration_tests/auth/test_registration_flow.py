"""
Integration tests for user registration with authorization codes.

Tests the complete registration flow including:
- Authorization code validation
- User account creation
- Code usage tracking
"""

import pytest
from fastapi.testclient import TestClient

from jea_meeting_web_scraper.auth.security import get_password_hash
from jea_meeting_web_scraper.db.auth_code_repository import AuthCodeRepository
from jea_meeting_web_scraper.db.auth_code_service import AuthCodeService
from jea_meeting_web_scraper.db.client import get_db_connection
from jea_meeting_web_scraper.db.user_repository import UserRepository
from jea_meeting_web_scraper.main import app

client = TestClient(app)


@pytest.fixture
def admin_user():
    """Create an admin user for testing (needed for creating auth codes)."""
    with get_db_connection() as conn:
        user_repo = UserRepository(conn)

        # Create admin user
        user = user_repo.create_user(
            username="admin", email="admin@test.com", role_id=1
        )

        # Create password credentials for admin
        hashed_password = get_password_hash("adminpassword")
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


@pytest.fixture
def valid_auth_code(admin_user):
    """Create a valid authorization code for testing."""
    with get_db_connection() as conn:
        repo = AuthCodeRepository(conn)
        service = AuthCodeService(repo)

        # Create a code with 1 use allowed
        code = service.create_code(
            created_by=admin_user["user_id"],
            max_uses=1,
            notes="Test registration code",
        )
        yield code["code_formatted"]


@pytest.fixture
def multi_use_auth_code(admin_user):
    """Create a multi-use authorization code for testing."""
    with get_db_connection() as conn:
        repo = AuthCodeRepository(conn)
        service = AuthCodeService(repo)

        # Create a code with 3 uses allowed
        code = service.create_code(
            created_by=admin_user["user_id"],
            max_uses=3,
            notes="Test multi-use code",
        )
        yield code["code_formatted"]


class TestSuccessfulRegistration:
    """Tests for successful user registration."""

    def test_register_with_valid_code(self, valid_auth_code):
        """Test successful registration with a valid authorization code."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securePassword123",
                "auth_code": valid_auth_code,
            },
        )

        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["role_id"] == 2  # Regular user
        assert "user_id" in data["user"]

        # Verify user was created in database
        with get_db_connection() as conn:
            user_repo = UserRepository(conn)
            user = user_repo.get_user_by_username("newuser")
            assert user is not None
            assert user["email"] == "newuser@example.com"

    def test_register_normalizes_auth_code_format(self, valid_auth_code):
        """Test that registration accepts codes with or without hyphens."""
        # Remove hyphens from the code
        code_without_hyphens = valid_auth_code.replace("-", "")

        response = client.post(
            "/auth/register",
            json={
                "username": "testuser2",
                "email": "testuser2@example.com",
                "password": "securePassword123",
                "auth_code": code_without_hyphens,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"

    def test_register_with_lowercase_code(self, valid_auth_code):
        """Test that registration accepts lowercase codes."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser3",
                "email": "testuser3@example.com",
                "password": "securePassword123",
                "auth_code": valid_auth_code.lower(),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"

    def test_multi_use_code_allows_multiple_registrations(self, multi_use_auth_code):
        """Test that a multi-use code can be used multiple times."""
        # First registration
        response1 = client.post(
            "/auth/register",
            json={
                "username": "multiuser1",
                "email": "multiuser1@example.com",
                "password": "securePassword123",
                "auth_code": multi_use_auth_code,
            },
        )
        assert response1.status_code == 201

        # Second registration with same code
        response2 = client.post(
            "/auth/register",
            json={
                "username": "multiuser2",
                "email": "multiuser2@example.com",
                "password": "securePassword123",
                "auth_code": multi_use_auth_code,
            },
        )
        assert response2.status_code == 201

        # Third registration with same code
        response3 = client.post(
            "/auth/register",
            json={
                "username": "multiuser3",
                "email": "multiuser3@example.com",
                "password": "securePassword123",
                "auth_code": multi_use_auth_code,
            },
        )
        assert response3.status_code == 201

        # Fourth registration should fail (max 3 uses)
        response4 = client.post(
            "/auth/register",
            json={
                "username": "multiuser4",
                "email": "multiuser4@example.com",
                "password": "securePassword123",
                "auth_code": multi_use_auth_code,
            },
        )
        assert response4.status_code == 400
        assert "fully used" in response4.json()["detail"].lower()


class TestRegistrationValidation:
    """Tests for registration input validation."""

    def test_register_rejects_short_password(self, valid_auth_code):
        """Test that registration rejects passwords shorter than 8 characters."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "short",  # Too short
                "auth_code": valid_auth_code,
            },
        )

        assert response.status_code == 422  # Validation error
        assert "at least 8 characters" in str(response.json()).lower()

    def test_register_rejects_invalid_email(self, valid_auth_code):
        """Test that registration rejects invalid email addresses."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "notanemail",  # No @ symbol
                "password": "securePassword123",
                "auth_code": valid_auth_code,
            },
        )

        assert response.status_code == 422  # Validation error
        assert "email" in str(response.json()).lower()

    def test_register_rejects_empty_username(self, valid_auth_code):
        """Test that registration rejects empty usernames."""
        response = client.post(
            "/auth/register",
            json={
                "username": "  ",  # Empty/whitespace
                "email": "testuser@example.com",
                "password": "securePassword123",
                "auth_code": valid_auth_code,
            },
        )

        assert response.status_code == 422  # Validation error
        assert "username" in str(response.json()).lower()

    def test_register_rejects_empty_auth_code(self):
        """Test that registration rejects empty authorization codes."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "securePassword123",
                "auth_code": "  ",  # Empty/whitespace
            },
        )

        assert response.status_code == 422  # Validation error


class TestRegistrationWithInvalidCode:
    """Tests for registration with invalid authorization codes."""

    def test_register_with_nonexistent_code(self):
        """Test that registration fails with a code that doesn't exist."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "securePassword123",
                "auth_code": "FAKE-CODE-1234",
            },
        )

        assert response.status_code == 400
        assert "invalid authorization code" in response.json()["detail"].lower()

    def test_register_with_used_code(self, valid_auth_code):
        """Test that registration fails with a code that has been fully used."""
        # First registration uses the code
        response1 = client.post(
            "/auth/register",
            json={
                "username": "firstuser",
                "email": "firstuser@example.com",
                "password": "securePassword123",
                "auth_code": valid_auth_code,
            },
        )
        assert response1.status_code == 201

        # Second registration should fail (single-use code)
        response2 = client.post(
            "/auth/register",
            json={
                "username": "seconduser",
                "email": "seconduser@example.com",
                "password": "securePassword123",
                "auth_code": valid_auth_code,
            },
        )
        assert response2.status_code == 400
        assert "fully used" in response2.json()["detail"].lower()

    def test_register_with_expired_code(self, admin_user):
        """Test that registration fails with an expired code."""
        import time

        # Create a code that expires in 1 second
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)

            # Create code directly with repository to set specific expiration
            code_string = "TESTEXPIRED1"
            repo.create_code(
                code=code_string,
                created_by=admin_user["user_id"],
                expires_at=int(time.time()) + 1,  # Expires in 1 second
                max_uses=1,
                notes="Test expired code",
            )
            conn.commit()

            # Format for display
            code = {
                "code_formatted": f"{code_string[:4]}-{code_string[4:8]}-{code_string[8:12]}"
            }

        # Wait for code to expire
        time.sleep(2)

        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "securePassword123",
                "auth_code": code["code_formatted"],
            },
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_register_with_revoked_code(self, admin_user):
        """Test that registration fails with a revoked code."""
        # Create and immediately revoke a code
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            code = service.create_code(
                created_by=admin_user["user_id"],
                max_uses=1,
                notes="Test revoked code",
            )
            service.revoke_code(code["code_id"])

        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "securePassword123",
                "auth_code": code["code_formatted"],
            },
        )

        assert response.status_code == 400
        assert "revoked" in response.json()["detail"].lower()


class TestRegistrationDuplicateHandling:
    """Tests for handling duplicate usernames and emails."""

    def test_register_with_duplicate_username(
        self, valid_auth_code, multi_use_auth_code
    ):
        """Test that registration fails if username already exists."""
        # First registration
        response1 = client.post(
            "/auth/register",
            json={
                "username": "duplicateuser",
                "email": "user1@example.com",
                "password": "securePassword123",
                "auth_code": valid_auth_code,
            },
        )
        assert response1.status_code == 201

        # Second registration with same username but different email and code
        response2 = client.post(
            "/auth/register",
            json={
                "username": "duplicateuser",  # Same username
                "email": "user2@example.com",  # Different email
                "password": "securePassword123",
                "auth_code": multi_use_auth_code,  # Different code
            },
        )
        assert response2.status_code == 409  # Conflict
        assert "username" in response2.json()["detail"].lower()
        assert "already exists" in response2.json()["detail"].lower()

    def test_register_with_duplicate_email(self, valid_auth_code, multi_use_auth_code):
        """Test that registration fails if email already exists."""
        # First registration
        response1 = client.post(
            "/auth/register",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "securePassword123",
                "auth_code": valid_auth_code,
            },
        )
        assert response1.status_code == 201

        # Second registration with different username but same email
        response2 = client.post(
            "/auth/register",
            json={
                "username": "user2",  # Different username
                "email": "duplicate@example.com",  # Same email
                "password": "securePassword123",
                "auth_code": multi_use_auth_code,  # Different code
            },
        )
        assert response2.status_code == 409  # Conflict
        assert "email" in response2.json()["detail"].lower()
        assert "already exists" in response2.json()["detail"].lower()


class TestCodeUsageTracking:
    """Tests for verifying code usage is properly tracked."""

    def test_registration_creates_usage_record(self, valid_auth_code):
        """Test that successful registration creates a usage record."""
        # Register a user
        response = client.post(
            "/auth/register",
            json={
                "username": "trackeduser",
                "email": "trackeduser@example.com",
                "password": "securePassword123",
                "auth_code": valid_auth_code,
            },
        )
        assert response.status_code == 201
        user_id = response.json()["user"]["user_id"]

        # Verify usage record was created
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            # Get code by string to find code_id
            normalized_code = valid_auth_code.replace("-", "").upper()
            code_data = repo.get_code_by_string(normalized_code)
            assert code_data is not None

            # Get usage history
            usage = repo.get_usage_history(code_data["code_id"])
            assert len(usage) == 1
            assert usage[0]["user_id"] == user_id

    def test_code_current_uses_increments(self, multi_use_auth_code):
        """Test that current_uses increments with each registration."""
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)

            # Get initial state
            normalized_code = multi_use_auth_code.replace("-", "").upper()
            code_data = repo.get_code_by_string(normalized_code)
            initial_uses = code_data["current_uses"]

            # Register first user
            response1 = client.post(
                "/auth/register",
                json={
                    "username": "usecount1",
                    "email": "usecount1@example.com",
                    "password": "securePassword123",
                    "auth_code": multi_use_auth_code,
                },
            )
            assert response1.status_code == 201

            # Check uses incremented
            code_data = repo.get_code_by_string(normalized_code)
            assert code_data["current_uses"] == initial_uses + 1

            # Register second user
            response2 = client.post(
                "/auth/register",
                json={
                    "username": "usecount2",
                    "email": "usecount2@example.com",
                    "password": "securePassword123",
                    "auth_code": multi_use_auth_code,
                },
            )
            assert response2.status_code == 201

            # Check uses incremented again
            code_data = repo.get_code_by_string(normalized_code)
            assert code_data["current_uses"] == initial_uses + 2
