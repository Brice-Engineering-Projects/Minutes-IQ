"""
minutes_iq/db/favorites_repository.py
-------------------------------------------------

Repository for managing user client favorites.
Allows users to mark clients as favorites for quick access.
"""

import time
from typing import Any

from libsql_experimental import Connection


class FavoritesRepository:
    """Repository for managing user client favorites in the database."""

    def __init__(self, db: Connection):
        """
        Initialize the repository with a database connection.

        Args:
            db: Database connection
        """
        self.db = db

    def add_favorite(self, user_id: int, client_id: int) -> bool:
        """
        Add a client to user's favorites.

        Args:
            user_id: User ID
            client_id: Client ID

        Returns:
            True if favorite was added, False if already exists

        Raises:
            ValueError: If user or client doesn't exist
        """
        favorited_at = int(time.time())

        try:
            cursor = self.db.execute(
                """
                INSERT INTO user_client_favorites (user_id, client_id, favorited_at)
                VALUES (?, ?, ?);
                """,
                (user_id, client_id, favorited_at),
            )
            cursor.close()
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                return False
            if "FOREIGN KEY constraint failed" in str(e):
                raise ValueError("User or client does not exist") from e
            raise

    def remove_favorite(self, user_id: int, client_id: int) -> bool:
        """
        Remove a client from user's favorites.

        Args:
            user_id: User ID
            client_id: Client ID

        Returns:
            True if favorite was removed, False if didn't exist
        """
        cursor = self.db.execute(
            """
            DELETE FROM user_client_favorites
            WHERE user_id = ? AND client_id = ?;
            """,
            (user_id, client_id),
        )

        affected = cursor.rowcount
        cursor.close()
        self.db.commit()

        return affected > 0

    def is_favorite(self, user_id: int, client_id: int) -> bool:
        """
        Check if a client is in user's favorites.

        Args:
            user_id: User ID
            client_id: Client ID

        Returns:
            True if client is favorited, False otherwise
        """
        cursor = self.db.execute(
            """
            SELECT 1 FROM user_client_favorites
            WHERE user_id = ? AND client_id = ?;
            """,
            (user_id, client_id),
        )
        result = cursor.fetchone()
        cursor.close()

        return result is not None

    def get_user_favorites(self, user_id: int) -> list[dict[str, Any]]:
        """
        Get all clients favorited by a user.

        Args:
            user_id: User ID

        Returns:
            List of dictionaries containing client data with favorited_at timestamp
        """
        cursor = self.db.execute(
            """
            SELECT c.client_id, c.name, c.description, c.website_url,
                   c.is_active, c.created_at, c.created_by, c.updated_at,
                   f.favorited_at
            FROM clients c
            INNER JOIN user_client_favorites f ON c.client_id = f.client_id
            WHERE f.user_id = ?
            ORDER BY f.favorited_at DESC;
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "client_id": row[0],
                "name": row[1],
                "description": row[2],
                "website_url": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5],
                "created_by": row[6],
                "updated_at": row[7],
                "favorited_at": row[8],
            }
            for row in rows
        ]

    def get_client_favorite_count(self, client_id: int) -> int:
        """
        Get the number of users who have favorited a client.

        Args:
            client_id: Client ID

        Returns:
            Number of users who favorited this client
        """
        cursor = self.db.execute(
            """
            SELECT COUNT(*) FROM user_client_favorites
            WHERE client_id = ?;
            """,
            (client_id,),
        )
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    def get_user_favorite_count(self, user_id: int) -> int:
        """
        Get the number of clients a user has favorited.

        Args:
            user_id: User ID

        Returns:
            Number of favorited clients
        """
        cursor = self.db.execute(
            """
            SELECT COUNT(*) FROM user_client_favorites
            WHERE user_id = ?;
            """,
            (user_id,),
        )
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    def clear_user_favorites(self, user_id: int) -> int:
        """
        Remove all favorites for a user.

        Args:
            user_id: User ID

        Returns:
            Number of favorites removed
        """
        cursor = self.db.execute(
            """
            DELETE FROM user_client_favorites
            WHERE user_id = ?;
            """,
            (user_id,),
        )

        affected = cursor.rowcount
        cursor.close()
        self.db.commit()

        return affected
