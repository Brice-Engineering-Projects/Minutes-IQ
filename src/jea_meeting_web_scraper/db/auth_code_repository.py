"""
Authorization Code Repository
Handles database operations for authorization codes.
"""

import time
from typing import Any

from libsql_experimental import Connection


class AuthCodeRepository:
    """Repository for authorization code operations."""

    def __init__(self, db: Connection):
        """
        Initialize with a database connection.

        Args:
            db: Database connection
        """
        self.db = db

    def create_code(
        self,
        code: str,
        created_by: int,
        expires_at: int | None = None,
        max_uses: int = 1,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new authorization code.

        Args:
            code: The authorization code string
            created_by: User ID of the admin creating the code
            expires_at: Unix timestamp when code expires (None = never)
            max_uses: Maximum number of times the code can be used
            notes: Optional notes about the code

        Returns:
            Dictionary containing the created code's data
        """
        created_at = int(time.time())

        query = """
            INSERT INTO auth_codes (code, created_by, created_at, expires_at, max_uses, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING code_id, code, created_by, created_at, expires_at, max_uses, current_uses, is_active, notes;
        """
        cursor = self.db.execute(
            query, (code, created_by, created_at, expires_at, max_uses, notes)
        )
        row = cursor.fetchone()
        cursor.close()

        return {
            "code_id": row[0],
            "code": row[1],
            "created_by": row[2],
            "created_at": row[3],
            "expires_at": row[4],
            "max_uses": row[5],
            "current_uses": row[6],
            "is_active": row[7],
            "notes": row[8],
        }

    def get_code_by_string(self, code: str) -> dict[str, Any] | None:
        """
        Retrieve a code by its string value.

        Args:
            code: The authorization code string

        Returns:
            Dictionary containing the code's data, or None if not found
        """
        query = """
            SELECT code_id, code, created_by, created_at, expires_at, max_uses, current_uses, is_active, notes
            FROM auth_codes
            WHERE code = ?;
        """
        cursor = self.db.execute(query, (code,))
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "code_id": row[0],
            "code": row[1],
            "created_by": row[2],
            "created_at": row[3],
            "expires_at": row[4],
            "max_uses": row[5],
            "current_uses": row[6],
            "is_active": row[7],
            "notes": row[8],
        }

    def get_code_by_id(self, code_id: int) -> dict[str, Any] | None:
        """
        Retrieve a code by its ID.

        Args:
            code_id: The code ID

        Returns:
            Dictionary containing the code's data, or None if not found
        """
        query = """
            SELECT code_id, code, created_by, created_at, expires_at, max_uses, current_uses, is_active, notes
            FROM auth_codes
            WHERE code_id = ?;
        """
        cursor = self.db.execute(query, (code_id,))
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "code_id": row[0],
            "code": row[1],
            "created_by": row[2],
            "created_at": row[3],
            "expires_at": row[4],
            "max_uses": row[5],
            "current_uses": row[6],
            "is_active": row[7],
            "notes": row[8],
        }

    def list_codes(
        self,
        status: str = "active",
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List authorization codes with filtering.

        Args:
            status: Filter by status ("active", "expired", "used", "revoked", "all")
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of code dictionaries
        """
        current_time = int(time.time())

        # Build query based on status filter
        if status == "active":
            where_clause = """
                WHERE is_active = 1
                AND (expires_at IS NULL OR expires_at > ?)
                AND current_uses < max_uses
            """
            params = (current_time, limit, offset)
        elif status == "expired":
            where_clause = "WHERE expires_at IS NOT NULL AND expires_at <= ?"
            params = (current_time, limit, offset)
        elif status == "used":
            where_clause = "WHERE current_uses >= max_uses"
            params = (limit, offset)
        elif status == "revoked":
            where_clause = "WHERE is_active = 0"
            params = (limit, offset)
        else:  # "all"
            where_clause = ""
            params = (limit, offset)

        query = f"""
            SELECT code_id, code, created_by, created_at, expires_at, max_uses, current_uses, is_active, notes
            FROM auth_codes
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?;
        """

        cursor = self.db.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "code_id": row[0],
                "code": row[1],
                "created_by": row[2],
                "created_at": row[3],
                "expires_at": row[4],
                "max_uses": row[5],
                "current_uses": row[6],
                "is_active": row[7],
                "notes": row[8],
            }
            for row in rows
        ]

    def increment_usage(self, code_id: int) -> None:
        """
        Increment the usage count for a code.

        Args:
            code_id: The code ID
        """
        query = """
            UPDATE auth_codes
            SET current_uses = current_uses + 1
            WHERE code_id = ?;
        """
        cursor = self.db.execute(query, (code_id,))
        cursor.close()

    def record_usage(self, code_id: int, user_id: int) -> None:
        """
        Record that a user used a specific code.

        Args:
            code_id: The code ID
            user_id: The user ID who used the code
        """
        used_at = int(time.time())

        query = """
            INSERT INTO code_usage (code_id, user_id, used_at)
            VALUES (?, ?, ?);
        """
        cursor = self.db.execute(query, (code_id, user_id, used_at))
        cursor.close()

    def revoke_code(self, code_id: int) -> bool:
        """
        Revoke a code (mark as inactive).

        Args:
            code_id: The code ID to revoke

        Returns:
            True if code was revoked, False if code doesn't exist
        """
        # Check if code exists
        if not self.get_code_by_id(code_id):
            return False

        query = """
            UPDATE auth_codes
            SET is_active = 0
            WHERE code_id = ?;
        """
        cursor = self.db.execute(query, (code_id,))
        cursor.close()

        return True

    def get_usage_history(self, code_id: int) -> list[dict[str, Any]]:
        """
        Get the usage history for a specific code.

        Args:
            code_id: The code ID

        Returns:
            List of usage records with user information
        """
        query = """
            SELECT cu.usage_id, cu.code_id, cu.user_id, cu.used_at, u.username, u.email
            FROM code_usage cu
            JOIN users u ON cu.user_id = u.user_id
            WHERE cu.code_id = ?
            ORDER BY cu.used_at DESC;
        """
        cursor = self.db.execute(query, (code_id,))
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "usage_id": row[0],
                "code_id": row[1],
                "user_id": row[2],
                "used_at": row[3],
                "username": row[4],
                "email": row[5],
            }
            for row in rows
        ]
