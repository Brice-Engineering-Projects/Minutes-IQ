"""Seed admin credential into auth_credentials table"""

from jea_meeting_web_scraper.auth.security import get_password_hash
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.client import get_db_connection


def seed_admin_credential():
    # Use password from .env
    plain_password = settings.app_password
    print("📝 Using password from settings.app_password")

    # Hash it
    hashed = get_password_hash(plain_password)

    with get_db_connection() as conn:
        # Get the admin user and provider
        cursor = conn.execute("""
            SELECT u.user_id, ap.provider_id
            FROM users u
            JOIN auth_providers ap ON u.user_id = ap.user_id
            WHERE u.username = 'admin'
              AND ap.provider_type = 'local'
        """)
        row = cursor.fetchone()

        if not row:
            print("❌ Admin user or auth_provider not found!")
            return

        user_id, provider_id = row[0], row[1]
        print(f"✅ Found admin: user_id={user_id}, provider_id={provider_id}")

        # Insert the credential
        conn.execute(
            """
            INSERT INTO auth_credentials (provider_id, user_id, hashed_password, is_active)
            VALUES (?, ?, ?, 1)
        """,
            (provider_id, user_id, hashed),
        )

        conn.commit()
        print("✅ Admin credential seeded successfully!")
        print(f"   Hash: {hashed[:30]}...")


if __name__ == "__main__":
    seed_admin_credential()
