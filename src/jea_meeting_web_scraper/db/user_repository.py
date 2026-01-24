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
        Note: Ensure your db/client.py sets 'conn.row_factory = sqlite3.Row'
        to support name-based access.
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

        return dict(row) if row else None

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

        return dict(row) if row else None
