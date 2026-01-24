# src/jea_meeting_web_scraper/db/auth_repository.py
"""
Auth Repository
Handles specialized authentication lookups using triple-joins.
"""

from typing import Any

from libsql_experimental import Connection


class AuthRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def get_credentials_by_username(
        self, username: str, provider_type: str = "local"
    ) -> dict[str, Any] | None:
        """
        Retrieves hashed credentials and user identity by joining
        users, auth_providers, and auth_credentials.
        """
        # Note: We join on provider_type to support future OAuth/SAML
        # We also filter for active credentials at the database level
        query = """
            SELECT
                ac.hashed_password,
                u.user_id,
                u.username,
                u.email
            FROM users u
            JOIN auth_providers ap ON u.user_id = ap.user_id
            JOIN auth_credentials ac ON ap.provider_id = ac.provider_id
            WHERE u.username = ?
              AND ap.provider_type = ?
              AND ac.is_active = 1;
        """.strip()

        cursor = self.conn.execute(query, (username, provider_type))
        row = cursor.fetchone()

        if not row:
            return None

        # Manually map row to dictionary (libSQL doesn't support row_factory)
        return {
            "hashed_password": row[0],
            "user_id": row[1],
            "username": row[2],
            "email": row[3],
        }
