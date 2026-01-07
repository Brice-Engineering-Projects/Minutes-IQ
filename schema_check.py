# schema_check.py
"""Module for checking schema of users table."""

from jea_meeting_web_scraper.db.client import get_db


def main():
    with get_db() as conn:
        rows = conn.execute("PRAGMA table_info(users);").fetchall()
        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
