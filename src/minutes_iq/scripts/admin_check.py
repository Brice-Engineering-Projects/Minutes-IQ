# admin_check.py
"""Module for checking admin status of users."""

from minutes_iq.db.client import get_db_client


def main():
    with get_db_client() as conn:
        rows = conn.execute(
            """
            SELECT user_id, username, email, role_id
            FROM users;
            """
        ).fetchall()

        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
