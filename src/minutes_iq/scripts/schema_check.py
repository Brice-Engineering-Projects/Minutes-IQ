# schema_check.py
"""Module for checking schema of users table."""

from minutes_iq.db.client import get_db_client


def main():
    with get_db_client() as conn:
        rows = conn.execute("PRAGMA table_info(users);").fetchall()
        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
