# src/minutes_iq/db/auth_repository.py
"""
Auth Repository
Handles specialized authentication lookups using triple-joins.
"""

from typing import Any

from libsql_experimental import Connection


class AuthRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    @staticmethod
    def _is_missing_force_password_change_column(exc: Exception) -> bool:
        """Detect schema drift where users.force_password_change is not present yet."""
        message = str(exc).lower()
        return "no such column" in message and "force_password_change" in message

    def get_credentials_by_username(
        self, username: str, provider_name: str = "password"
    ) -> dict[str, Any] | None:
        """
        Retrieves hashed credentials and user identity by joining
        users, auth_providers, and auth_credentials.
        """
        # Note: We join on provider_name to support future OAuth/SAML
        # We also filter for active credentials at the database level
        query_with_force_password_change = """
            SELECT
                ac.hashed_password,
                u.user_id,
                u.username,
                u.email,
                u.role_id,
                u.force_password_change
            FROM users u
            JOIN auth_credentials ac ON u.user_id = ac.user_id
            JOIN auth_providers ap ON ac.provider_id = ap.provider_id
            WHERE u.username = ?
              AND ap.provider_name = ?
              AND ac.is_active = 1;
        """.strip()

        query_without_force_password_change = """
            SELECT
                ac.hashed_password,
                u.user_id,
                u.username,
                u.email,
                u.role_id,
                0 AS force_password_change
            FROM users u
            JOIN auth_credentials ac ON u.user_id = ac.user_id
            JOIN auth_providers ap ON ac.provider_id = ap.provider_id
            WHERE u.username = ?
              AND ap.provider_name = ?
              AND ac.is_active = 1;
        """.strip()

        try:
            cursor = self.conn.execute(
                query_with_force_password_change, (username, provider_name)
            )
        except ValueError as exc:
            if not self._is_missing_force_password_change_column(exc):
                raise

            # Backward compatibility: allow login against DBs that have not yet
            # applied the force_password_change migration.
            cursor = self.conn.execute(
                query_without_force_password_change, (username, provider_name)
            )

        row = cursor.fetchone()

        if not row:
            return None

        # Manually map row to dictionary (libSQL doesn't support row_factory)
        return {
            "hashed_password": row[0],
            "user_id": row[1],
            "username": row[2],
            "email": row[3],
            "role_id": row[4],
            "force_password_change": row[5],
        }
