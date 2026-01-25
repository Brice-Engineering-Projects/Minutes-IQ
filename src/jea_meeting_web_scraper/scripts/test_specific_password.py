"""Test a specific password you type against the database hash"""

from jea_meeting_web_scraper.auth.security import verify_password
from jea_meeting_web_scraper.db.client import get_db_connection


def test_password():
    print("🔍 Password verification test\n")

    # Ask user to type the password they're using in FastAPI
    typed_password = input("Enter the EXACT password you're typing in FastAPI docs: ")

    print("\n📝 You entered:")
    print(f"   Length: {len(typed_password)}")
    print(f"   First 3: '{typed_password[:3]}...'")
    print(f"   Last 3: '...{typed_password[-3:]}'")
    print(f"   Repr: {repr(typed_password)}")

    with get_db_connection() as conn:
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
            print("❌ No hash found in database")
            return

        stored_hash = row[0]

        print("\n🧪 Testing verification...")
        is_valid = verify_password(typed_password, stored_hash)

        if is_valid:
            print("✅ PASSWORD MATCHES! The issue must be in FastAPI request handling.")
        else:
            print("❌ PASSWORD DOES NOT MATCH!")
            print("\n💡 Possible reasons:")
            print("   1. You're typing a different password than what's in .env")
            print("   2. There are hidden characters (spaces, quotes, etc.)")
            print("   3. Copy/paste added extra characters")

            # Show what the .env password is
            from jea_meeting_web_scraper.config.settings import settings

            env_password = settings.app_password
            print("\n📋 For comparison, .env APP_PASSWORD is:")
            print(f"   Length: {len(env_password)}")
            print(f"   Value: {env_password}")

            if typed_password == env_password:
                print("\n   ⚠️  They look identical but verification still fails!")
                print("   This is very strange. Checking character by character...")
                for i, (c1, c2) in enumerate(
                    zip(typed_password, env_password, strict=False)
                ):
                    if c1 != c2:
                        print(
                            f"   Difference at position {i}: typed='{c1}' ({ord(c1)}) vs env='{c2}' ({ord(c2)})"
                        )
            else:
                print("\n   ⚠️  They are DIFFERENT!")


if __name__ == "__main__":
    test_password()
