"""Debug script to check database contents"""

from jea_meeting_web_scraper.db.client import get_db_connection


def debug_database():
    print("🔍 Checking database contents...\n")

    with get_db_connection() as conn:
        # Check users
        print("=== USERS ===")
        cursor = conn.execute("SELECT user_id, username, email FROM users")
        users = cursor.fetchall()
        if users:
            for row in users:
                print(f"  user_id={row[0]}, username={row[1]}, email={row[2]}")
        else:
            print("  (no users found)")

        # Check auth_providers
        print("\n=== AUTH_PROVIDERS ===")
        cursor = conn.execute(
            "SELECT provider_id, user_id, provider_type FROM auth_providers"
        )
        providers = cursor.fetchall()
        if providers:
            for row in providers:
                print(
                    f"  provider_id={row[0]}, user_id={row[1]}, provider_type={row[2]}"
                )
        else:
            print("  (no providers found)")

        # Check auth_credentials
        print("\n=== AUTH_CREDENTIALS ===")
        cursor = conn.execute(
            "SELECT auth_id, provider_id, user_id, hashed_password, is_active FROM auth_credentials"
        )
        credentials = cursor.fetchall()
        if credentials:
            for row in credentials:
                print(
                    f"  auth_id={row[0]}, provider_id={row[1]}, user_id={row[2]}, hash={row[3][:20] if row[3] else 'NULL'}..., is_active={row[4]}"
                )
        else:
            print("  (no credentials found)")


if __name__ == "__main__":
    debug_database()
