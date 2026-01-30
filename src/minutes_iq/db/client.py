# src/minutes_iq/db/client.py
"""Database client module for interacting with the database."""

from collections.abc import Iterator
from contextlib import contextmanager

from libsql_experimental import Connection, connect

from minutes_iq.config.settings import settings


def get_db_client() -> Connection:
    """
    Create and return a new database connection.
    """
    conn = connect(
        settings.database.db_url,
        auth_token=settings.database.auth_token,
    )

    return conn


@contextmanager
def get_db_connection() -> Iterator[Connection]:
    """
    Context-managed database connection.

    Ensures connections are always closed.
    """
    conn = get_db_client()
    try:
        yield conn
    finally:
        conn.close()


def healthcheck() -> bool:
    """
    Verify database connectivity.
    """
    try:
        with get_db_connection() as conn:
            # Simple query to verify the connection is alive
            conn.execute("SELECT 1;")
        return True
    except Exception:
        return False
