"""
minutes_iq/db/client_url_repository.py
-----------------------------------------------

Repository for managing client URLs (scraping targets).
Provides CRUD operations for multiple URLs per client.
"""

import time
from typing import Any

from libsql_experimental import Connection


class ClientUrlRepository:
    """Repository for managing client URLs in the database."""

    def __init__(self, db: Connection):
        """
        Initialize the repository with a database connection.

        Args:
            db: Database connection
        """
        self.db = db

    def create_url(
        self,
        client_id: int,
        alias: str,
        url: str,
        is_active: bool = True,
    ) -> dict[str, Any]:
        """
        Create a new URL for a client.

        Args:
            client_id: Client ID
            alias: Descriptive alias (e.g., "current", "archive")
            url: The actual URL to scrape
            is_active: Whether URL is active

        Returns:
            Dictionary containing created URL data

        Raises:
            ValueError: If client doesn't exist or duplicate alias
        """
        created_at = int(time.time())
        is_active_int = 1 if is_active else 0

        try:
            cursor = self.db.execute(
                """
                INSERT INTO client_urls (client_id, alias, url, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id, client_id, alias, url, is_active, last_scraped_at, created_at, updated_at;
                """,
                (client_id, alias, url, is_active_int, created_at),
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                raise ValueError("Failed to create client URL")

            self.db.commit()

            return {
                "id": row[0],
                "client_id": row[1],
                "alias": row[2],
                "url": row[3],
                "is_active": bool(row[4]),
                "last_scraped_at": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            }
        except Exception as e:
            self.db.rollback()
            if "FOREIGN KEY constraint failed" in str(e):
                raise ValueError(f"Client with ID {client_id} does not exist") from e
            raise

    def get_url(self, url_id: int) -> dict[str, Any] | None:
        """
        Get a URL by ID.

        Args:
            url_id: URL ID

        Returns:
            Dictionary containing URL data, or None if not found
        """
        cursor = self.db.execute(
            """
            SELECT id, client_id, alias, url, is_active, last_scraped_at, created_at, updated_at
            FROM client_urls
            WHERE id = ?;
            """,
            (url_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "id": row[0],
            "client_id": row[1],
            "alias": row[2],
            "url": row[3],
            "is_active": bool(row[4]),
            "last_scraped_at": row[5],
            "created_at": row[6],
            "updated_at": row[7],
        }

    def get_client_urls(
        self, client_id: int, active_only: bool = False
    ) -> list[dict[str, Any]]:
        """
        Get all URLs for a client.

        Args:
            client_id: Client ID
            active_only: Only return active URLs

        Returns:
            List of URL dictionaries
        """
        query = """
            SELECT id, client_id, alias, url, is_active, last_scraped_at, created_at, updated_at
            FROM client_urls
            WHERE client_id = ?
        """

        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY alias"

        cursor = self.db.execute(query, (client_id,))
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "id": row[0],
                "client_id": row[1],
                "alias": row[2],
                "url": row[3],
                "is_active": bool(row[4]),
                "last_scraped_at": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            }
            for row in rows
        ]

    def update_url(
        self,
        url_id: int,
        alias: str | None = None,
        url: str | None = None,
        is_active: bool | None = None,
    ) -> bool:
        """
        Update a URL.

        Args:
            url_id: URL ID
            alias: New alias (optional)
            url: New URL (optional)
            is_active: New active status (optional)

        Returns:
            True if updated, False if URL not found
        """
        updates: list[str] = []
        params: list[str | int] = []

        if alias is not None:
            updates.append("alias = ?")
            params.append(alias)

        if url is not None:
            updates.append("url = ?")
            params.append(url)

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(int(time.time()))
        params.append(url_id)

        query = f"UPDATE client_urls SET {', '.join(updates)} WHERE id = ?"

        try:
            cursor = self.db.execute(query, tuple(params))
            rows_affected = cursor.rowcount
            cursor.close()
            self.db.commit()
            return rows_affected > 0
        except Exception:
            self.db.rollback()
            raise

    def delete_url(self, url_id: int) -> bool:
        """
        Delete a URL.

        Args:
            url_id: URL ID

        Returns:
            True if deleted, False if URL not found
        """
        try:
            cursor = self.db.execute("DELETE FROM client_urls WHERE id = ?", (url_id,))
            rows_affected = cursor.rowcount
            cursor.close()
            self.db.commit()
            return rows_affected > 0
        except Exception:
            self.db.rollback()
            raise

    def update_last_scraped(self, url_id: int) -> bool:
        """
        Update the last_scraped_at timestamp for a URL.

        Args:
            url_id: URL ID

        Returns:
            True if updated, False if URL not found
        """
        try:
            timestamp = int(time.time())
            cursor = self.db.execute(
                """
                UPDATE client_urls
                SET last_scraped_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (timestamp, timestamp, url_id),
            )
            rows_affected = cursor.rowcount
            cursor.close()
            self.db.commit()
            return rows_affected > 0
        except Exception:
            self.db.rollback()
            raise

    def list_all_urls(
        self, active_only: bool = False, limit: int = 100, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List all URLs across all clients.

        Args:
            active_only: Only return active URLs
            limit: Maximum number of URLs to return
            offset: Number of URLs to skip

        Returns:
            Tuple of (list of URL dictionaries, total count)
        """
        # Count query
        count_query = "SELECT COUNT(*) FROM client_urls"
        if active_only:
            count_query += " WHERE is_active = 1"

        cursor = self.db.execute(count_query)
        total = cursor.fetchone()[0]
        cursor.close()

        # Data query
        query = """
            SELECT cu.id, cu.client_id, cu.alias, cu.url, cu.is_active,
                   cu.last_scraped_at, cu.created_at, cu.updated_at,
                   c.name as client_name
            FROM client_urls cu
            JOIN client c ON c.client_id = cu.client_id
        """

        if active_only:
            query += " WHERE cu.is_active = 1"

        query += " ORDER BY c.name, cu.alias LIMIT ? OFFSET ?"

        cursor = self.db.execute(query, (limit, offset))
        rows = cursor.fetchall()
        cursor.close()

        return (
            [
                {
                    "id": row[0],
                    "client_id": row[1],
                    "alias": row[2],
                    "url": row[3],
                    "is_active": bool(row[4]),
                    "last_scraped_at": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                    "client_name": row[8],
                }
                for row in rows
            ],
            total,
        )
