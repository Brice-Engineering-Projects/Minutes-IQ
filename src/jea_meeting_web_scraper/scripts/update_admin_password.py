"""Script to update admin password in Turso database"""

from jea_meeting_web_scraper.auth.security import get_password_hash
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.client import get_db_connection


def update_admin_password():
    print("🔐 Updating admin password...\n")

    # Use password from .env
    plain_password = settings.app_password
    print("📝 Using password from settings.app_password")
    print(f"   Length: {len(plain_password)} characters")

    # Hash it
    new_hash = get_password_hash(plain_password)
    print(f"🔒 Generated new hash: {new_hash[:30]}...")

    with get_db_connection() as conn:
        # Get the admin user and provider
        cursor = conn.execute("""
            SELECT u.user_id, ap.provider_id, ac.auth_id, ac.hashed_password
            FROM users u
            JOIN auth_providers ap ON u.user_id = ap.user_id
            JOIN auth_credentials ac ON ap.provider_id = ac.provider_id
            WHERE u.username = 'admin'
              AND ap.provider_type = 'local'
        """)
        row = cursor.fetchone()

        if not row:
            print("❌ Admin user or credentials not found!")
            return

        user_id, provider_id, auth_id, old_hash = row
        print("\n📊 Current state:")
        print(f"   user_id: {user_id}")
        print(f"   provider_id: {provider_id}")
        print(f"   auth_id: {auth_id}")
        print(f"   old_hash: {old_hash[:30]}...")

        # Update the password
        conn.execute(
            """
            UPDATE auth_credentials
            SET hashed_password = ?
            WHERE auth_id = ?
        """,
            (new_hash, auth_id),
        )

        conn.commit()

        # Verify the update
        cursor = conn.execute(
            """
            SELECT hashed_password FROM auth_credentials WHERE auth_id = ?
        """,
            (auth_id,),
        )
        updated_hash = cursor.fetchone()[0]

        print("\n✅ Password updated successfully!")
        print(f"   New hash: {updated_hash[:30]}...")
        print("\n🧪 Now test login with:")
        print("   Username: admin")
        print("   Password: (from your .env APP_PASSWORD)")


if __name__ == "__main__":
    update_admin_password()
