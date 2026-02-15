"""
minutes_iq/db/client_repository.py
-----------------------------------------------

Repository for managing clients (government agencies being tracked).
Provides CRUD operations for clients and their sources.
"""

import time
from typing import Any

from libsql_experimental import Connection


class ClientRepository:
    """Repository for managing clients in the database."""

    def __init__(self, db: Connection):
        """
        Initialize the repository with a database connection.

        Args:
            db: Database connection
        """
        self.db = db

    def create_client(
        self,
        name: str,
        created_by: int,
        description: str | None = None,
        is_active: bool = True,
    ) -> dict[str, Any]:
        """
        Create a new client.

        Args:
            name: Client organization name
            created_by: User ID of admin creating the client
            description: Optional description
            is_active: Whether client is active

        Returns:
            Dictionary containing created client data

        Raises:
            ValueError: If client name already exists

        Note:
            URLs should be added separately using ClientUrlRepository
        """
        created_at = int(time.time())
        is_active_int = 1 if is_active else 0

        try:
            cursor = self.db.execute(
                """
                INSERT INTO client (name, description, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?)
                RETURNING client_id, name, description, is_active, created_at, created_by, updated_at;
                """,
                (name, description, is_active_int, created_at, created_by),
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                raise ValueError("Failed to create client")

            self.db.commit()

            return {
                "client_id": row[0],
                "name": row[1],
                "description": row[2],
                "is_active": bool(row[3]),
                "created_at": row[4],
                "created_by": row[5],
                "updated_at": row[6],
            }
        except Exception as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Client with name '{name}' already exists") from e
            raise

    def get_client_by_id(self, client_id: int) -> dict[str, Any] | None:
        """
        Get a client by ID.

        Args:
            client_id: Client ID

        Returns:
            Dictionary containing client data, or None if not found
        """
        cursor = self.db.execute(
            """
            SELECT client_id, name, description, is_active, created_at, created_by, updated_at
            FROM client
            WHERE client_id = ?;
            """,
            (client_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "client_id": row[0],
            "name": row[1],
            "description": row[2],
            "is_active": bool(row[3]),
            "created_at": row[4],
            "created_by": row[5],
            "updated_at": row[6],
        }

    def get_client_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Get a client by name.

        Args:
            name: Client name

        Returns:
            Dictionary containing client data, or None if not found
        """
        cursor = self.db.execute(
            """
            SELECT client_id, name, description, is_active, created_at, created_by, updated_at
            FROM client
            WHERE name = ?;
            """,
            (name,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "client_id": row[0],
            "name": row[1],
            "description": row[2],
            "is_active": bool(row[3]),
            "created_at": row[4],
            "created_by": row[5],
            "updated_at": row[6],
        }

    def list_clients(
        self, is_active: bool | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List clients with optional filtering.

        Args:
            is_active: Filter by active status (None = all clients)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of client dictionaries
        """
        query = """
            SELECT client_id, name, description, is_active, created_at, created_by, updated_at
            FROM client
        """
        params: list[int] = []

        if is_active is not None:
            query += " WHERE is_active = ?"
            params.append(1 if is_active else 0)

        query += " ORDER BY name ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor = self.db.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "client_id": row[0],
                "name": row[1],
                "description": row[2],
                "is_active": bool(row[3]),
                "created_at": row[4],
                "created_by": row[5],
                "updated_at": row[6],
            }
            for row in rows
        ]

    def update_client(
        self,
        client_id: int,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> dict[str, Any] | None:
        """
        Update a client's information.

        Args:
            client_id: Client ID
            name: New name (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Dictionary containing updated client data, or None if not found

        Raises:
            ValueError: If new name already exists for another client

        Note:
            URLs should be managed separately using ClientUrlRepository
        """
        # Build dynamic update query based on provided fields
        updates: list[str] = []
        params: list[str | int] = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not updates:
            # No updates provided, return current data
            return self.get_client_by_id(client_id)

        updates.append("updated_at = ?")
        params.append(int(time.time()))

        query = f"""
            UPDATE client
            SET {", ".join(updates)}
            WHERE client_id = ?
            RETURNING client_id, name, description, is_active, created_at, created_by, updated_at;
        """
        params.append(client_id)

        try:
            cursor = self.db.execute(query, tuple(params))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            self.db.commit()

            return {
                "client_id": row[0],
                "name": row[1],
                "description": row[2],
                "is_active": bool(row[3]),
                "created_at": row[4],
                "created_by": row[5],
                "updated_at": row[6],
            }
        except Exception as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Client with name '{name}' already exists") from e
            raise

    def delete_client(self, client_id: int) -> bool:
        """
        Delete a client (soft delete by setting is_active to false).

        Args:
            client_id: Client ID

        Returns:
            True if client was deleted, False if not found
        """
        updated_at = int(time.time())

        cursor = self.db.execute(
            """
            UPDATE client
            SET is_active = 0, updated_at = ?
            WHERE client_id = ?;
            """,
            (updated_at, client_id),
        )

        affected = cursor.rowcount
        cursor.close()
        self.db.commit()

        return affected > 0

    def get_client_count(self, is_active: bool | None = None) -> int:
        """
        Get total count of clients.

        Args:
            is_active: Filter by active status (None = all clients)

        Returns:
            Total number of clients
        """
        if is_active is None:
            query = "SELECT COUNT(*) FROM client;"
            cursor = self.db.execute(query)
        else:
            query = "SELECT COUNT(*) FROM client WHERE is_active = ?;"
            cursor = self.db.execute(query, (1 if is_active else 0,))

        count = cursor.fetchone()[0]
        cursor.close()
        return count
