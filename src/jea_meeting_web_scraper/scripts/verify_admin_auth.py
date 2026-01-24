"""
Maintenance Script: Admin Login Verification
Refined for libSQL / Turso connection compatibility.
"""

from jea_meeting_web_scraper.auth.service import AuthService
from jea_meeting_web_scraper.db.auth_repository import AuthRepository
from jea_meeting_web_scraper.db.client import get_db_connection


def verify_admin_login():
    print("🚀 Starting Admin Auth Verification...")

    # Standard admin credentials from seed
    admin_username = "admin"
    # Note: Use the actual plain-text password you used when generating the hash
    test_password = "your_admin_password_here"

    try:
        # get_db_connection handles the connection lifecycle
        with get_db_connection() as conn:
            # We initialize the repository with the connection
            auth_repo = AuthRepository(conn)
            # We initialize the service with the repository
            auth_service = AuthService(auth_repo)

            print(f"🔍 Testing credentials for: {admin_username}")

            # authenticate_user performs the triple-join and bcrypt check
            user_context = auth_service.authenticate_user(admin_username, test_password)

            if user_context:
                print("✅ SUCCESS: Admin authenticated successfully.")
                print(f"👤 User Context: {user_context}")
            else:
                print("❌ FAILURE: Authentication returned None.")
                print("Possible reasons:")
                print("- Password mismatch.")
                print("- Table names 'auth_providers' or 'auth_credentials' mismatch.")
                print("- User 'is_active' is not set to 1.")

    except Exception as e:
        print(f"💥 CRITICAL ERROR during verification: {e}")


if __name__ == "__main__":
    verify_admin_login()
