"""
User Service
Business logic layer for user management operations.
Coordinates between repositories and handles transactions.
"""

from typing import Any

from minutes_iq.auth.security import get_password_hash
from minutes_iq.db.auth_repository import AuthRepository
from minutes_iq.db.user_repository import UserRepository


class UserService:
    """Service for managing user accounts and associated credentials."""

    def __init__(self, user_repo: UserRepository, auth_repo: AuthRepository):
        """
        Initialize the user service with required repositories.

        Args:
            user_repo: Repository for user data operations
            auth_repo: Repository for authentication credentials
        """
        self.user_repo = user_repo
        self.auth_repo = auth_repo

    def create_user_with_password(
        self, username: str, email: str, password: str, role_id: int = 2
    ) -> dict[str, Any]:
        """
        Creates a new user with password credentials.

        This is a transactional operation that creates both the user
        and their authentication credentials.

        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            role_id: Role ID (default: 2 for regular user)

        Returns:
            Dictionary containing the created user's data (no password)

        Raises:
            ValueError: If username or email already exists
        """
        # Create the user
        user = self.user_repo.create_user(username, email, role_id)

        # Hash the password
        hashed_password = get_password_hash(password)

        # Create auth credentials
        # Note: We need to execute this on the same connection
        # In a real transaction, we'd want to wrap this in BEGIN/COMMIT
        query = """
            INSERT INTO auth_credentials (user_id, provider_id, hashed_password, is_active)
            VALUES (?, ?, ?, ?);
        """
        cursor = self.user_repo.db.execute(
            query, (user["user_id"], 1, hashed_password, 1)
        )
        cursor.close()
        self.user_repo.db.commit()

        return user

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        """Get user by ID."""
        return self.user_repo.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Get user by username."""
        return self.user_repo.get_user_by_username(username)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email."""
        return self.user_repo.get_user_by_email(email)

    def update_user(
        self, user_id: int, username: str | None = None, email: str | None = None
    ) -> dict[str, Any] | None:
        """
        Update user information.

        Args:
            user_id: ID of the user to update
            username: New username (optional)
            email: New email (optional)

        Returns:
            Updated user data, or None if user doesn't exist

        Raises:
            ValueError: If new username or email already exists
        """
        result = self.user_repo.update_user(user_id, username, email)
        if result:
            self.user_repo.db.commit()
        return result

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user and all associated credentials.

        This is a cascading delete that removes:
        - User record
        - All authentication credentials

        Args:
            user_id: ID of the user to delete

        Returns:
            True if user was deleted, False if user didn't exist
        """
        # Check if user exists
        if not self.user_repo.get_user_by_id(user_id):
            return False

        # Delete auth credentials first (foreign key constraint)
        query = "DELETE FROM auth_credentials WHERE user_id = ?;"
        cursor = self.user_repo.db.execute(query, (user_id,))
        cursor.close()

        # Delete user
        result = self.user_repo.delete_user(user_id)
        if result:
            self.user_repo.db.commit()

        return result

    def list_users(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """
        List all users with pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of user dictionaries
        """
        return self.user_repo.list_users(limit, offset)

    def update_password(self, user_id: int, new_password: str) -> bool:
        """
        Update a user's password.

        Args:
            user_id: ID of the user
            new_password: New plain text password (will be hashed)

        Returns:
            True if password was updated, False if user doesn't exist
        """
        # Check if user exists
        if not self.user_repo.get_user_by_id(user_id):
            return False

        # Hash the new password
        hashed_password = get_password_hash(new_password)

        # Update the password in auth_credentials
        query = """
            UPDATE auth_credentials
            SET hashed_password = ?
            WHERE user_id = ? AND provider_id = 1 AND is_active = 1;
        """
        cursor = self.user_repo.db.execute(query, (hashed_password, user_id))
        cursor.close()
        self.user_repo.db.commit()

        return True
