from typing import Any

from libsql_experimental import Connection


class UserRepository:
    def __init__(self, db: Connection):
        self.db = db

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """
        Retrieves identity-only fields for a user by their ID.
        """
        query = (
            "SELECT id, username, email, full_name, is_active FROM users WHERE id = ?;"
        )
        cursor = self.db.execute(query, (user_id,))
        row = cursor.fetchone()

        return self._map_row_to_dict(row) if row else None

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """
        Retrieves identity-only fields for a user by their username.
        """
        query = "SELECT id, username, email, full_name, is_active FROM users WHERE username = ?;"
        cursor = self.db.execute(query, (username,))
        row = cursor.fetchone()

        return self._map_row_to_dict(row) if row else None

    def _map_row_to_dict(self, row: Any) -> dict[str, Any]:
        """
        Helper to convert raw tuple results into a structured dictionary.
        """
        # Note: In libsql/sqlite, row behaves like a sequence.
        # If you haven't set a row_factory, access by index.
        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "full_name": row[3],
            "is_active": bool(row[4]),
        }
