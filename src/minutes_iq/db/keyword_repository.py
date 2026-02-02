"""
minutes_iq/db/keyword_repository.py
------------------------------------------------

Repository for managing keywords used to filter meeting minutes.
Provides CRUD operations for keywords and client-keyword associations.
"""

import time
from typing import Any

from libsql_experimental import Connection


class KeywordRepository:
    """Repository for managing keywords in the database."""

    def __init__(self, db: Connection):
        """
        Initialize the repository with a database connection.

        Args:
            db: Database connection
        """
        self.db = db

    def create_keyword(
        self,
        keyword: str,
        created_by: int,
        category: str | None = None,
        description: str | None = None,
        is_active: bool = True,
    ) -> dict[str, Any]:
        """
        Create a new keyword.

        Args:
            keyword: The keyword/phrase
            created_by: User ID of admin creating the keyword
            category: Optional category (e.g., "Infrastructure", "Budget")
            description: Optional description
            is_active: Whether keyword is active

        Returns:
            Dictionary containing created keyword data

        Raises:
            ValueError: If keyword already exists
        """
        created_at = int(time.time())
        is_active_int = 1 if is_active else 0

        try:
            cursor = self.db.execute(
                """
                INSERT INTO keywords (keyword, category, description, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING keyword_id, keyword, category, description, is_active, created_at, created_by;
                """,
                (keyword, category, description, is_active_int, created_at, created_by),
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                raise ValueError("Failed to create keyword")

            self.db.commit()

            return {
                "keyword_id": row[0],
                "keyword": row[1],
                "category": row[2],
                "description": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5],
                "created_by": row[6],
            }
        except Exception as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Keyword '{keyword}' already exists") from e
            raise

    def get_keyword_by_id(self, keyword_id: int) -> dict[str, Any] | None:
        """
        Get a keyword by ID.

        Args:
            keyword_id: Keyword ID

        Returns:
            Dictionary containing keyword data, or None if not found
        """
        cursor = self.db.execute(
            """
            SELECT keyword_id, keyword, category, description, is_active, created_at, created_by
            FROM keywords
            WHERE keyword_id = ?;
            """,
            (keyword_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "keyword_id": row[0],
            "keyword": row[1],
            "category": row[2],
            "description": row[3],
            "is_active": bool(row[4]),
            "created_at": row[5],
            "created_by": row[6],
        }

    def get_keyword_by_text(self, keyword: str) -> dict[str, Any] | None:
        """
        Get a keyword by its text.

        Args:
            keyword: Keyword text

        Returns:
            Dictionary containing keyword data, or None if not found
        """
        cursor = self.db.execute(
            """
            SELECT keyword_id, keyword, category, description, is_active, created_at, created_by
            FROM keywords
            WHERE keyword = ?;
            """,
            (keyword,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "keyword_id": row[0],
            "keyword": row[1],
            "category": row[2],
            "description": row[3],
            "is_active": bool(row[4]),
            "created_at": row[5],
            "created_by": row[6],
        }

    def list_keywords(
        self,
        is_active: bool | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List keywords with optional filtering.

        Args:
            is_active: Filter by active status (None = all keywords)
            category: Filter by category (None = all categories)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of keyword dictionaries
        """
        query = """
            SELECT keyword_id, keyword, category, description, is_active, created_at, created_by
            FROM keywords
        """
        params: list[str | int] = []
        conditions: list[str] = []

        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(1 if is_active else 0)

        if category is not None:
            conditions.append("category = ?")
            params.append(category)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY keyword ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor = self.db.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "keyword_id": row[0],
                "keyword": row[1],
                "category": row[2],
                "description": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5],
                "created_by": row[6],
            }
            for row in rows
        ]

    def update_keyword(
        self,
        keyword_id: int,
        keyword: str | None = None,
        category: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> dict[str, Any] | None:
        """
        Update a keyword's information.

        Args:
            keyword_id: Keyword ID
            keyword: New keyword text (optional)
            category: New category (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Dictionary containing updated keyword data, or None if not found

        Raises:
            ValueError: If new keyword text already exists
        """
        updates: list[str] = []
        params: list[str | int] = []

        if keyword is not None:
            updates.append("keyword = ?")
            params.append(keyword)

        if category is not None:
            updates.append("category = ?")
            params.append(category)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not updates:
            return self.get_keyword_by_id(keyword_id)

        query = f"""
            UPDATE keywords
            SET {", ".join(updates)}
            WHERE keyword_id = ?
            RETURNING keyword_id, keyword, category, description, is_active, created_at, created_by;
        """
        params.append(keyword_id)

        try:
            cursor = self.db.execute(query, tuple(params))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            self.db.commit()

            return {
                "keyword_id": row[0],
                "keyword": row[1],
                "category": row[2],
                "description": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5],
                "created_by": row[6],
            }
        except Exception as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Keyword '{keyword}' already exists") from e
            raise

    def delete_keyword(self, keyword_id: int) -> bool:
        """
        Delete a keyword (soft delete by setting is_active to false).

        Args:
            keyword_id: Keyword ID

        Returns:
            True if keyword was deleted, False if not found
        """
        cursor = self.db.execute(
            """
            UPDATE keywords
            SET is_active = 0
            WHERE keyword_id = ?;
            """,
            (keyword_id,),
        )

        affected = cursor.rowcount
        cursor.close()
        self.db.commit()

        return affected > 0

    def add_keyword_to_client(
        self, client_id: int, keyword_id: int, added_by: int
    ) -> bool:
        """
        Associate a keyword with a client.

        Args:
            client_id: Client ID
            keyword_id: Keyword ID
            added_by: User ID of admin adding the association

        Returns:
            True if association was created, False if already exists

        Raises:
            ValueError: If client or keyword doesn't exist
        """
        added_at = int(time.time())

        try:
            cursor = self.db.execute(
                """
                INSERT INTO client_keywords (client_id, keyword_id, added_at, added_by)
                VALUES (?, ?, ?, ?);
                """,
                (client_id, keyword_id, added_at, added_by),
            )
            cursor.close()
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                return False
            if "FOREIGN KEY constraint failed" in str(e):
                raise ValueError("Client or keyword does not exist") from e
            raise

    def remove_keyword_from_client(self, client_id: int, keyword_id: int) -> bool:
        """
        Remove keyword association from a client.

        Args:
            client_id: Client ID
            keyword_id: Keyword ID

        Returns:
            True if association was removed, False if didn't exist
        """
        cursor = self.db.execute(
            """
            DELETE FROM client_keywords
            WHERE client_id = ? AND keyword_id = ?;
            """,
            (client_id, keyword_id),
        )

        affected = cursor.rowcount
        cursor.close()
        self.db.commit()

        return affected > 0

    def get_client_keywords(self, client_id: int) -> list[dict[str, Any]]:
        """
        Get all keywords associated with a client.

        Args:
            client_id: Client ID

        Returns:
            List of keyword dictionaries
        """
        cursor = self.db.execute(
            """
            SELECT k.keyword_id, k.keyword, k.category, k.description, k.is_active, k.created_at, k.created_by
            FROM keywords k
            INNER JOIN client_keywords ck ON k.keyword_id = ck.keyword_id
            WHERE ck.client_id = ?
            ORDER BY k.keyword ASC;
            """,
            (client_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "keyword_id": row[0],
                "keyword": row[1],
                "category": row[2],
                "description": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5],
                "created_by": row[6],
            }
            for row in rows
        ]

    def get_keyword_clients(self, keyword_id: int) -> list[dict[str, Any]]:
        """
        Get all clients associated with a keyword.

        Args:
            keyword_id: Keyword ID

        Returns:
            List of dictionaries containing client_id and name
        """
        cursor = self.db.execute(
            """
            SELECT c.client_id, c.name
            FROM client c
            INNER JOIN client_keywords ck ON c.client_id = ck.client_id
            WHERE ck.keyword_id = ?
            ORDER BY c.name ASC;
            """,
            (keyword_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        return [{"client_id": row[0], "name": row[1]} for row in rows]

    def get_keyword_count(
        self, is_active: bool | None = None, category: str | None = None
    ) -> int:
        """
        Get total count of keywords.

        Args:
            is_active: Filter by active status (None = all keywords)
            category: Filter by category (None = all categories)

        Returns:
            Total number of keywords
        """
        query = "SELECT COUNT(*) FROM keywords"
        params: list[str | int] = []
        conditions: list[str] = []

        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(1 if is_active else 0)

        if category is not None:
            conditions.append("category = ?")
            params.append(category)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += ";"

        cursor = self.db.execute(query, tuple(params) if params else ())
        count = cursor.fetchone()[0]
        cursor.close()
        return count
