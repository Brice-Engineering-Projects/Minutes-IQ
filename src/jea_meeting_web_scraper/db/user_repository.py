"""
User Repository
Handles identity-only database operations for the users table.
"""

from typing import Any

from libsql_experimental import Connection


class UserRepository:
    def __init__(self, db: Connection):
        """
        Initializes with a database connection.
        Note: libSQL doesn't support row_factory, so we manually map rows to dicts.
        """
        self.db = db

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """
        Retrieves identity-only fields for a user by their user_id.
        Follows JEA Schema v1 naming.
        """
        query = """
            SELECT user_id, username, email, role_id
            FROM users
            WHERE user_id = ?;
        """
        cursor = self.db.execute(query, (user_id,))
        row = cursor.fetchone()

        if not row:
            return None

        # Manually map row to dictionary (libSQL doesn't support row_factory)
        return {
            "user_id": row[0],
            "username": row[1],
            "email": row[2],
            "role_id": row[3],
        }

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """
        Retrieves identity-only fields for a user by their username.
        Used for initial identity lookup.
        """
        query = """
            SELECT user_id, username, email, role_id
            FROM users
            WHERE username = ?;
        """
        cursor = self.db.execute(query, (username,))
        row = cursor.fetchone()

        if not row:
            return None

        # Manually map row to dictionary (libSQL doesn't support row_factory)
        return {
            "user_id": row[0],
            "username": row[1],
            "email": row[2],
            "role_id": row[3],
        }

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """
        Retrieves identity-only fields for a user by their email.
        Used for duplicate email checking.
        """
        query = """
            SELECT user_id, username, email, role_id
            FROM users
            WHERE email = ?;
        """
        cursor = self.db.execute(query, (email,))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "user_id": row[0],
            "username": row[1],
            "email": row[2],
            "role_id": row[3],
        }

    def create_user(
        self, username: str, email: str, role_id: int = 2
    ) -> dict[str, Any]:
        """
        Creates a new user in the database.

        Args:
            username: Unique username for the user
            email: Unique email address
            role_id: Role ID (default: 2 for regular user)

        Returns:
            Dictionary containing the created user's data

        Raises:
            ValueError: If username or email already exists
        """
        # Check for existing username
        if self.get_user_by_username(username):
            raise ValueError(f"Username '{username}' already exists")

        # Check for existing email
        if self.get_user_by_email(email):
            raise ValueError(f"Email '{email}' already exists")

        query = """
            INSERT INTO users (username, email, role_id)
            VALUES (?, ?, ?)
            RETURNING user_id, username, email, role_id;
        """
        cursor = self.db.execute(query, (username, email, role_id))
        row = cursor.fetchone()
        cursor.close()

        return {
            "user_id": row[0],
            "username": row[1],
            "email": row[2],
            "role_id": row[3],
        }

    def update_user(
        self, user_id: int, username: str | None = None, email: str | None = None
    ) -> dict[str, Any] | None:
        """
        Updates user information.

        Args:
            user_id: ID of the user to update
            username: New username (optional)
            email: New email (optional)

        Returns:
            Updated user data, or None if user doesn't exist

        Raises:
            ValueError: If new username or email already exists
        """
        # Check if user exists
        existing_user = self.get_user_by_id(user_id)
        if not existing_user:
            return None

        # Check for username conflicts (if changing username)
        if username and username != existing_user["username"]:
            if self.get_user_by_username(username):
                raise ValueError(f"Username '{username}' already exists")

        # Check for email conflicts (if changing email)
        if email and email != existing_user["email"]:
            if self.get_user_by_email(email):
                raise ValueError(f"Email '{email}' already exists")

        # Build dynamic update query
        updates = []
        params = []

        if username:
            updates.append("username = ?")
            params.append(username)

        if email:
            updates.append("email = ?")
            params.append(email)

        # If nothing to update, return existing user
        if not updates:
            return existing_user

        params.append(user_id)

        query = f"""
            UPDATE users
            SET {', '.join(updates)}
            WHERE user_id = ?
            RETURNING user_id, username, email, role_id;
        """

        cursor = self.db.execute(query, tuple(params))
        row = cursor.fetchone()
        cursor.close()

        return {
            "user_id": row[0],
            "username": row[1],
            "email": row[2],
            "role_id": row[3],
        }

    def delete_user(self, user_id: int) -> bool:
        """
        Deletes a user from the database.

        Note: This will fail if there are foreign key constraints
        (e.g., auth_credentials). Consider implementing soft deletes
        or cascading deletes in production.

        Args:
            user_id: ID of the user to delete

        Returns:
            True if user was deleted, False if user didn't exist
        """
        # Check if user exists
        if not self.get_user_by_id(user_id):
            return False

        query = "DELETE FROM users WHERE user_id = ?;"
        cursor = self.db.execute(query, (user_id,))
        cursor.close()

        return True

    def list_users(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """
        Lists all users with pagination.

        Args:
            limit: Maximum number of users to return (default: 100)
            offset: Number of users to skip (default: 0)

        Returns:
            List of user dictionaries
        """
        query = """
            SELECT user_id, username, email, role_id
            FROM users
            ORDER BY user_id
            LIMIT ? OFFSET ?;
        """
        cursor = self.db.execute(query, (limit, offset))
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "role_id": row[3],
            }
            for row in rows
        ]
