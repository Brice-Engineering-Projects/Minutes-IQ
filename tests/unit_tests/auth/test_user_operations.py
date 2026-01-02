"""Unit tests for user database operations."""

from jea_meeting_web_scraper.auth.schemas import UserInDB
from jea_meeting_web_scraper.auth.security import get_password_hash
from jea_meeting_web_scraper.auth.service import (
    authenticate_user,
    get_user,
)


class TestGetUser:
    """Test user retrieval from database."""

    def test_get_existing_user(self):
        """Test retrieving an existing user."""
        test_db = {
            "john": {
                "username": "john",
                "email": "john@example.com",
                "full_name": "John Doe",
                "hashed_password": "hashed_pw",
                "disabled": False,
            }
        }

        user = get_user(test_db, "john")

        assert user is not None
        assert isinstance(user, UserInDB)
        assert user.username == "john"
        assert user.email == "john@example.com"
        assert user.full_name == "John Doe"
        assert user.disabled is False

    def test_get_nonexistent_user(self):
        """Test retrieving a user that doesn't exist."""
        test_db = {"john": {"username": "john", "hashed_password": "hash"}}

        user = get_user(test_db, "jane")

        assert user is None

    def test_get_user_from_empty_database(self):
        """Test retrieving a user from an empty database."""
        test_db = {}

        user = get_user(test_db, "john")

        assert user is None


class TestAuthenticateUser:
    """Test user authentication."""

    def test_authenticate_valid_user(self):
        """Test authentication with valid credentials."""
        password = "secret123"
        hashed_password = get_password_hash(password)

        test_db = {
            "alice": {
                "username": "alice",
                "email": "alice@example.com",
                "hashed_password": hashed_password,
                "disabled": False,
            }
        }

        user = authenticate_user(test_db, "alice", password)

        assert user is not False
        assert isinstance(user, UserInDB)
        assert user.username == "alice"

    def test_authenticate_wrong_password(self):
        """Test authentication with wrong password."""
        password = "correct_password"
        hashed_password = get_password_hash(password)

        test_db = {
            "bob": {
                "username": "bob",
                "hashed_password": hashed_password,
                "disabled": False,
            }
        }

        user = authenticate_user(test_db, "bob", "wrong_password")

        assert user is False

    def test_authenticate_nonexistent_user(self):
        """Test authentication with nonexistent username."""
        test_db = {}

        user = authenticate_user(test_db, "ghost", "any_password")

        assert user is False

    def test_authenticate_disabled_user(self):
        """Test that disabled users can still authenticate (deactivation checked elsewhere)."""
        password = "password"
        hashed_password = get_password_hash(password)

        test_db = {
            "disabled_user": {
                "username": "disabled_user",
                "hashed_password": hashed_password,
                "disabled": True,
            }
        }

        # Authentication should succeed, but activation check happens in get_current_active_user
        user = authenticate_user(test_db, "disabled_user", password)

        assert user is not False
        assert isinstance(user, UserInDB)
        assert user.disabled is True
