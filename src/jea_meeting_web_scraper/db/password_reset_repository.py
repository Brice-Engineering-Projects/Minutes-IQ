"""
Password Reset Token Repository
Data access layer for password reset token operations.
"""

import sqlite3
from typing import Any


class PasswordResetRepository:
    """Repository for password reset token database operations."""

    def __init__(self, db: sqlite3.Connection):
        """
        Initialize the repository with a database connection.

        Args:
            db: SQLite database connection
        """
        self.db = db

    def create_token(
        self,
        user_id: int,
        token_hash: str,
        created_at: int,
        expires_at: int,
    ) -> dict[str, Any]:
        """
        Create a new password reset token.

        Args:
            user_id: ID of the user requesting the reset
            token_hash: SHA-256 hash of the reset token
            created_at: Unix timestamp when token was created
            expires_at: Unix timestamp when token expires

        Returns:
            Dictionary containing the created token data
        """
        cursor = self.db.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token_hash, created_at, expires_at, is_valid)
            VALUES (?, ?, ?, ?, 1)
            RETURNING token_id, user_id, token_hash, created_at, expires_at, used_at, is_valid;
            """,
            (user_id, token_hash, created_at, expires_at),
        )

        row = cursor.fetchone()
        cursor.close()

        if not row:
            raise ValueError("Failed to create password reset token")

        return {
            "token_id": row[0],
            "user_id": row[1],
            "token_hash": row[2],
            "created_at": row[3],
            "expires_at": row[4],
            "used_at": row[5],
            "is_valid": row[6],
        }

    def get_token_by_hash(self, token_hash: str) -> dict[str, Any] | None:
        """
        Get a password reset token by its hash.

        Args:
            token_hash: SHA-256 hash of the token

        Returns:
            Token dictionary if found, None otherwise
        """
        cursor = self.db.execute(
            """
            SELECT token_id, user_id, token_hash, created_at, expires_at, used_at, is_valid
            FROM password_reset_tokens
            WHERE token_hash = ?;
            """,
            (token_hash,),
        )

        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "token_id": row[0],
            "user_id": row[1],
            "token_hash": row[2],
            "created_at": row[3],
            "expires_at": row[4],
            "used_at": row[5],
            "is_valid": row[6],
        }

    def invalidate_token(self, token_id: int) -> bool:
        """
        Invalidate a password reset token.

        Args:
            token_id: ID of the token to invalidate

        Returns:
            True if token was invalidated, False if token doesn't exist
        """
        cursor = self.db.execute(
            """
            UPDATE password_reset_tokens
            SET is_valid = 0
            WHERE token_id = ?;
            """,
            (token_id,),
        )

        rows_affected = cursor.rowcount
        cursor.close()

        return rows_affected > 0

    def mark_token_used(self, token_id: int, used_at: int) -> bool:
        """
        Mark a token as used and invalidate it.

        Args:
            token_id: ID of the token to mark as used
            used_at: Unix timestamp when token was used

        Returns:
            True if token was marked as used, False if token doesn't exist
        """
        cursor = self.db.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?, is_valid = 0
            WHERE token_id = ?;
            """,
            (used_at, token_id),
        )

        rows_affected = cursor.rowcount
        cursor.close()

        return rows_affected > 0

    def invalidate_all_user_tokens(self, user_id: int) -> int:
        """
        Invalidate all password reset tokens for a specific user.

        This is useful when:
        - A user successfully resets their password (invalidate all pending tokens)
        - An admin revokes access

        Args:
            user_id: ID of the user

        Returns:
            Number of tokens invalidated
        """
        cursor = self.db.execute(
            """
            UPDATE password_reset_tokens
            SET is_valid = 0
            WHERE user_id = ? AND is_valid = 1;
            """,
            (user_id,),
        )

        rows_affected = cursor.rowcount
        cursor.close()

        return rows_affected

    def cleanup_expired_tokens(self, current_time: int) -> int:
        """
        Delete expired tokens from the database.

        This is a maintenance operation that should be run periodically
        to keep the table size manageable.

        Args:
            current_time: Current Unix timestamp

        Returns:
            Number of tokens deleted
        """
        cursor = self.db.execute(
            """
            DELETE FROM password_reset_tokens
            WHERE expires_at < ?;
            """,
            (current_time,),
        )

        rows_affected = cursor.rowcount
        cursor.close()

        return rows_affected

    def get_user_tokens(
        self, user_id: int, valid_only: bool = False
    ) -> list[dict[str, Any]]:
        """
        Get all password reset tokens for a specific user.

        Useful for auditing and debugging.

        Args:
            user_id: ID of the user
            valid_only: If True, only return valid tokens

        Returns:
            List of token dictionaries
        """
        if valid_only:
            query = """
                SELECT token_id, user_id, token_hash, created_at, expires_at, used_at, is_valid
                FROM password_reset_tokens
                WHERE user_id = ? AND is_valid = 1
                ORDER BY created_at DESC;
            """
        else:
            query = """
                SELECT token_id, user_id, token_hash, created_at, expires_at, used_at, is_valid
                FROM password_reset_tokens
                WHERE user_id = ?
                ORDER BY created_at DESC;
            """

        cursor = self.db.execute(query, (user_id,))
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "token_id": row[0],
                "user_id": row[1],
                "token_hash": row[2],
                "created_at": row[3],
                "expires_at": row[4],
                "used_at": row[5],
                "is_valid": row[6],
            }
            for row in rows
        ]
