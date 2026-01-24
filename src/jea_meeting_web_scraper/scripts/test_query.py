"""Test the exact query used by AuthRepository"""

from jea_meeting_web_scraper.db.client import get_db_connection


def test_auth_query():
    with get_db_connection() as conn:
        # The exact query from auth_repository.py
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

        print("🔍 Testing query with username='admin', provider_type='local'")
        cursor = conn.execute(query, ("admin", "local"))
        row = cursor.fetchone()

        if row:
            print(
                f"✅ Found: hash={row[0][:30]}..., user_id={row[1]}, username={row[2]}, email={row[3]}"
            )
        else:
            print("❌ No results from query")
            print("\n🔧 Debugging: Let's check the join conditions...")

            # Check if credentials exist at all
            cursor = conn.execute("SELECT COUNT(*) FROM auth_credentials")
            count = cursor.fetchone()[0]
            print(f"   auth_credentials count: {count}")

            if count > 0:
                cursor = conn.execute(
                    "SELECT auth_id, provider_id, user_id FROM auth_credentials"
                )
                for r in cursor.fetchall():
                    print(f"     - auth_id={r[0]}, provider_id={r[1]}, user_id={r[2]}")


if __name__ == "__main__":
    test_auth_query()
