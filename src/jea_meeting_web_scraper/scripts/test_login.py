"""Debug script to test login flow"""

from jea_meeting_web_scraper.auth.service import AuthService
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.auth_repository import AuthRepository
from jea_meeting_web_scraper.db.client import get_db_connection


def test_login():
    print("🔍 Testing login flow...\n")

    # Get credentials from settings
    username = input("Username (default: admin): ").strip() or "admin"
    password = input("Password (default: from .env): ").strip() or settings.app_password

    print(f"\n📋 Testing login for: {username}")

    with get_db_connection() as conn:
        # Step 1: Check if user exists in database
        cursor = conn.execute(
            "SELECT user_id, username, email FROM users WHERE username = ?", (username,)
        )
        user_row = cursor.fetchone()

        if not user_row:
            print(f"❌ User '{username}' not found in database")
            return

        print(
            f"✅ User found: user_id={user_row[0]}, username={user_row[1]}, email={user_row[2]}"
        )

        # Step 2: Check auth_provider
        cursor = conn.execute(
            "SELECT provider_id, provider_type FROM auth_providers WHERE user_id = ?",
            (user_row[0],),
        )
        provider_row = cursor.fetchone()

        if not provider_row:
            print(f"❌ No auth_provider found for user_id={user_row[0]}")
            return

        print(
            f"✅ Auth provider found: provider_id={provider_row[0]}, type={provider_row[1]}"
        )

        # Step 3: Check auth_credentials
        cursor = conn.execute(
            "SELECT auth_id, hashed_password, is_active FROM auth_credentials WHERE provider_id = ?",
            (provider_row[0],),
        )
        cred_row = cursor.fetchone()

        if not cred_row:
            print(f"❌ No credentials found for provider_id={provider_row[0]}")
            return

        print(f"✅ Credentials found: auth_id={cred_row[0]}, is_active={cred_row[2]}")
        print(f"   Hash: {cred_row[1][:30]}...")

        # Step 4: Test full auth flow
        auth_repo = AuthRepository(conn)
        auth_service = AuthService(auth_repo)

        result = auth_service.authenticate_user(username, password)

        if result:
            print("\n✅ SUCCESS: Authentication passed!")
            print(f"   User context: {result}")
        else:
            print("\n❌ FAILED: Authentication returned None")
            print("   This means either:")
            print("   1. The password is incorrect")
            print("   2. The provider_type doesn't match (expected 'local')")
            print("   3. The credential is not active")


if __name__ == "__main__":
    test_login()
