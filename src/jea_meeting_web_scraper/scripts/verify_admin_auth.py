"""
Maintenance Script: Admin Login Verification
Refactored to avoid 'row_factory' attribute errors with libSQL.
"""

import sys

from jea_meeting_web_scraper.auth.service import AuthService
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.auth_repository import AuthRepository
from jea_meeting_web_scraper.db.client import get_db_connection


def verify_admin_login():
    print("🚀 Starting Admin Auth Verification...")

    # Use the plain-text password from .env
    admin_username = "admin"
    test_password = settings.app_password
    provider_type = "local"  # Match the provider_type in database

    try:
        # The context manager in client.py should yield the raw connection
        with get_db_connection() as conn:
            # Initialize layers
            auth_repo = AuthRepository(conn)
            auth_service = AuthService(auth_repo)

            print(
                f"🔍 Testing credentials for: {admin_username} (provider: {provider_type})"
            )

            # First check if credentials exist
            creds = auth_repo.get_credentials_by_username(admin_username, provider_type)
            print(f"📊 Credentials found: {creds is not None}")
            if creds:
                print(f"   Fields: {list(creds.keys())}")

            # This is where password hashing happens, but only IF the DB query succeeds
            user_context = auth_service.authenticate_user(admin_username, test_password)

            if user_context:
                print("✅ SUCCESS: Admin authenticated successfully.")
                print(f"👤 User Context: {user_context}")
            else:
                print("❌ FAILURE: Authentication returned None.")

    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    verify_admin_login()
