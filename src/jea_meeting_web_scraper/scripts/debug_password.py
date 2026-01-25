"""Debug script to test password verification"""

from jea_meeting_web_scraper.auth.security import get_password_hash, verify_password
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.client import get_db_connection


def debug_password():
    print("🔍 Debugging password verification...\n")

    # Get password from .env
    env_password = settings.app_password
    print("📝 Password from .env (APP_PASSWORD):")
    print(f"   Length: {len(env_password)} characters")
    print(f"   First 3 chars: '{env_password[:3]}...'")
    print(f"   Last 3 chars: '...{env_password[-3:]}'")
    print(f"   Contains spaces: {' ' in env_password}")
    print(f"   Raw repr: {repr(env_password)}")

    with get_db_connection() as conn:
        # Get stored hash
        cursor = conn.execute("""
            SELECT ac.hashed_password
            FROM users u
            JOIN auth_providers ap ON u.user_id = ap.user_id
            JOIN auth_credentials ac ON ap.provider_id = ac.provider_id
            WHERE u.username = 'admin'
              AND ap.provider_type = 'local'
        """)
        row = cursor.fetchone()

        if not row:
            print("\n❌ No credentials found in database!")
            return

        stored_hash = row[0]
        print("\n🔒 Stored hash in database:")
        print(f"   {stored_hash[:50]}...")

        # Test verification
        print("\n🧪 Testing password verification...")
        is_valid = verify_password(env_password, stored_hash)

        if is_valid:
            print("   ✅ Password matches the stored hash!")
        else:
            print("   ❌ Password does NOT match the stored hash!")

            # Generate what the hash SHOULD be
            print("\n🔧 Generating fresh hash from .env password...")
            fresh_hash = get_password_hash(env_password)
            print(f"   Fresh hash: {fresh_hash[:50]}...")

            # Test if fresh hash matches itself (sanity check)
            fresh_verify = verify_password(env_password, fresh_hash)
            print(f"   Fresh hash verifies: {fresh_verify}")

            if stored_hash != fresh_hash:
                print("\n⚠️  The stored hash was created from a DIFFERENT password!")
                print(
                    "   This means the password in .env when you seeded != current .env password"
                )


if __name__ == "__main__":
    debug_password()
