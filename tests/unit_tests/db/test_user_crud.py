"""Unit tests for user CRUD operations."""

import pytest

from minutes_iq.db.user_repository import UserRepository


class TestUserCreate:
    """Test user creation."""

    def test_create_user_success(self, db_connection):
        """Test successful user creation."""
        repo = UserRepository(db_connection)

        user = repo.create_user("newuser", "new@example.com", role_id=2)

        assert user["username"] == "newuser"
        assert user["email"] == "new@example.com"
        assert user["role_id"] == 2
        assert "user_id" in user

    def test_create_user_duplicate_username(self, db_connection, test_user):
        """Test that creating a user with duplicate username fails."""
        repo = UserRepository(db_connection)

        with pytest.raises(ValueError, match="Username 'testuser' already exists"):
            repo.create_user("testuser", "different@example.com")

    def test_create_user_duplicate_email(self, db_connection, test_user):
        """Test that creating a user with duplicate email fails."""
        repo = UserRepository(db_connection)

        with pytest.raises(ValueError, match="Email 'test@example.com' already exists"):
            repo.create_user("differentuser", "test@example.com")


class TestUserRead:
    """Test user retrieval operations."""

    def test_get_user_by_id(self, db_connection, test_user):
        """Test retrieving user by ID."""
        repo = UserRepository(db_connection)

        user = repo.get_user_by_id(test_user["user_id"])

        assert user is not None
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"

    def test_get_user_by_id_not_found(self, db_connection):
        """Test that non-existent user ID returns None."""
        repo = UserRepository(db_connection)

        user = repo.get_user_by_id(99999)

        assert user is None

    def test_get_user_by_username(self, db_connection, test_user):
        """Test retrieving user by username."""
        repo = UserRepository(db_connection)

        user = repo.get_user_by_username("testuser")

        assert user is not None
        assert user["user_id"] == test_user["user_id"]
        assert user["email"] == "test@example.com"

    def test_get_user_by_username_not_found(self, db_connection):
        """Test that non-existent username returns None."""
        repo = UserRepository(db_connection)

        user = repo.get_user_by_username("nonexistent")

        assert user is None

    def test_get_user_by_email(self, db_connection, test_user):
        """Test retrieving user by email."""
        repo = UserRepository(db_connection)

        user = repo.get_user_by_email("test@example.com")

        assert user is not None
        assert user["user_id"] == test_user["user_id"]
        assert user["username"] == "testuser"

    def test_get_user_by_email_not_found(self, db_connection):
        """Test that non-existent email returns None."""
        repo = UserRepository(db_connection)

        user = repo.get_user_by_email("nonexistent@example.com")

        assert user is None


class TestUserUpdate:
    """Test user update operations."""

    def test_update_username(self, db_connection, test_user):
        """Test updating username."""
        repo = UserRepository(db_connection)

        updated = repo.update_user(test_user["user_id"], username="newusername")
        db_connection.commit()

        assert updated is not None
        assert updated["username"] == "newusername"
        assert updated["email"] == "test@example.com"

    def test_update_email(self, db_connection, test_user):
        """Test updating email."""
        repo = UserRepository(db_connection)

        updated = repo.update_user(test_user["user_id"], email="newemail@example.com")
        db_connection.commit()

        assert updated is not None
        assert updated["username"] == "testuser"
        assert updated["email"] == "newemail@example.com"

    def test_update_both(self, db_connection, test_user):
        """Test updating both username and email."""
        repo = UserRepository(db_connection)

        updated = repo.update_user(
            test_user["user_id"], username="newname", email="newemail@example.com"
        )
        db_connection.commit()

        assert updated is not None
        assert updated["username"] == "newname"
        assert updated["email"] == "newemail@example.com"

    def test_update_nonexistent_user(self, db_connection):
        """Test updating non-existent user returns None."""
        repo = UserRepository(db_connection)

        updated = repo.update_user(99999, username="newname")

        assert updated is None

    def test_update_duplicate_username(self, db_connection, test_user):
        """Test that updating to duplicate username fails."""
        repo = UserRepository(db_connection)

        # Create another user
        repo.create_user("otheruser", "other@example.com")
        db_connection.commit()

        # Try to update test_user to have otheruser's username
        with pytest.raises(ValueError, match="Username 'otheruser' already exists"):
            repo.update_user(test_user["user_id"], username="otheruser")

    def test_update_no_changes(self, db_connection, test_user):
        """Test that updating with no changes returns existing user."""
        repo = UserRepository(db_connection)

        updated = repo.update_user(test_user["user_id"])

        assert updated is not None
        assert updated["username"] == "testuser"
        assert updated["email"] == "test@example.com"


class TestUserDelete:
    """Test user deletion operations."""

    def test_delete_user(self, db_connection):
        """Test deleting a user."""
        repo = UserRepository(db_connection)

        # Create a user without credentials (so delete won't fail on FK constraint)
        user = repo.create_user("deleteuser", "delete@example.com")
        db_connection.commit()

        # Delete the user
        result = repo.delete_user(user["user_id"])
        db_connection.commit()

        assert result is True

        # Verify user is gone
        assert repo.get_user_by_id(user["user_id"]) is None

    def test_delete_nonexistent_user(self, db_connection):
        """Test deleting non-existent user returns False."""
        repo = UserRepository(db_connection)

        result = repo.delete_user(99999)

        assert result is False


class TestUserList:
    """Test user listing operations."""

    def test_list_users_empty(self, db_connection, clean_db):
        """Test listing users when none exist."""
        repo = UserRepository(db_connection)

        users = repo.list_users()

        assert users == []

    def test_list_users_single(self, db_connection, test_user):
        """Test listing users with one user."""
        repo = UserRepository(db_connection)

        users = repo.list_users()

        assert len(users) == 1
        assert users[0]["username"] == "testuser"

    def test_list_users_multiple(self, db_connection):
        """Test listing multiple users."""
        repo = UserRepository(db_connection)

        # Create multiple users
        repo.create_user("user1", "user1@example.com")
        repo.create_user("user2", "user2@example.com")
        repo.create_user("user3", "user3@example.com")
        db_connection.commit()

        users = repo.list_users()

        assert len(users) == 3
        usernames = [u["username"] for u in users]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" in usernames

    def test_list_users_pagination(self, db_connection):
        """Test pagination in user listing."""
        repo = UserRepository(db_connection)

        # Create 5 users
        for i in range(5):
            repo.create_user(f"user{i}", f"user{i}@example.com")
        db_connection.commit()

        # Get first 2
        page1 = repo.list_users(limit=2, offset=0)
        assert len(page1) == 2

        # Get next 2
        page2 = repo.list_users(limit=2, offset=2)
        assert len(page2) == 2

        # Ensure no overlap
        page1_ids = {u["user_id"] for u in page1}
        page2_ids = {u["user_id"] for u in page2}
        assert page1_ids.isdisjoint(page2_ids)
