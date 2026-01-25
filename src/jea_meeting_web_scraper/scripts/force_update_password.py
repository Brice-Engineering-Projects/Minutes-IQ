"""Force update admin password - delete old and insert new"""

from jea_meeting_web_scraper.auth.security import get_password_hash, verify_password
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.client import get_db_connection


def force_update():
    print("🔧 Force updating admin password...\n")

    # Get password from .env
    plain_password = settings.app_password
    print(f"📝 Password from .env: {repr(plain_password)}")
    print(f"   Length: {len(plain_password)}")

    # Generate fresh hash
    new_hash = get_password_hash(plain_password)
    print(f"\n🔒 Generated fresh hash: {new_hash[:50]}...")

    # Verify it works immediately
    test_verify = verify_password(plain_password, new_hash)
    print(f"   Immediate verification test: {test_verify}")

    if not test_verify:
        print(
            "❌ ERROR: Freshly generated hash doesn't verify! Something is very wrong."
        )
        return

    with get_db_connection() as conn:
        # Get current state
        cursor = conn.execute("""
            SELECT ac.auth_id, ac.hashed_password
            FROM users u
            JOIN auth_providers ap ON u.user_id = ap.user_id
            JOIN auth_credentials ac ON ap.provider_id = ac.provider_id
            WHERE u.username = 'admin' AND ap.provider_type = 'local'
        """)
        row = cursor.fetchone()

        if not row:
            print("❌ Admin credentials not found!")
            return

        auth_id, old_hash = row
        print("\n📊 Current database state:")
        print(f"   auth_id: {auth_id}")
        print(f"   old_hash: {old_hash[:50]}...")

        # Test old hash
        old_verify = verify_password(plain_password, old_hash)
        print(f"   Old hash verifies with .env password: {old_verify}")

        # Delete old credential
        print("\n🗑️  Deleting old credential...")
        conn.execute("DELETE FROM auth_credentials WHERE auth_id = ?", (auth_id,))
        conn.commit()

        # Insert new credential
        print("➕ Inserting new credential...")
        cursor = conn.execute(
            """
            INSERT INTO auth_credentials (provider_id, user_id, hashed_password, is_active)
            SELECT ap.provider_id, ap.user_id, ?, 1
            FROM users u
            JOIN auth_providers ap ON u.user_id = ap.user_id
            WHERE u.username = 'admin' AND ap.provider_type = 'local'
        """,
            (new_hash,),
        )
        conn.commit()

        # Verify it was inserted correctly
        cursor = conn.execute("""
            SELECT ac.hashed_password
            FROM users u
            JOIN auth_providers ap ON u.user_id = ap.user_id
            JOIN auth_credentials ac ON ap.provider_id = ac.provider_id
            WHERE u.username = 'admin' AND ap.provider_type = 'local'
        """)
        inserted_hash = cursor.fetchone()[0]

        print("\n✅ New credential inserted!")
        print(f"   Inserted hash: {inserted_hash[:50]}...")
        print(f"   Hash matches what we generated: {inserted_hash == new_hash}")

        # Final verification test
        final_verify = verify_password(plain_password, inserted_hash)
        print(f"   Final verification test: {final_verify}")

        if final_verify:
            print("\n🎉 SUCCESS! Password is now properly configured!")
            print("   Try logging in with:")
            print("   Username: admin")
            print(f"   Password: {plain_password}")
        else:
            print("\n❌ ERROR: Verification still failing after update!")


if __name__ == "__main__":
    force_update()
