# src/jea_meeting_web_scraper/db/auth_repository.py

from typing import Any

from libsql_experimental import Connection


class AuthRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def get_credentials_by_identifier(
        self, identifier: str, provider_name: str = "password"
    ) -> dict[str, Any] | None:
        """
        Retrieves credentials using exact column names from the JEA Schema.
        """
        # Note: Using 'active' and 'user_id' as per PDF sources 8, 71, and 52
        query = """
SELECT ac.hashed_password,
       ac.user_id,
       u.active
FROM auth_credentials ac
JOIN auth_providers ap ON ac.provider_id = ap.provider_id
JOIN users u ON ac.user_id = u.user_id
WHERE ac.identifier = ?
  AND ap.provider = ?
  AND u.active = 1
""".strip()

        cursor = self.conn.execute(query, (identifier, provider_name))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "hashed_password": row["hashed_password"],
            "user_id": row["user_id"],
            "is_active": bool(row["active"]),
        }
