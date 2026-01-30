"""
Auth Service Layer
Handles the business logic for user authentication.
"""

from typing import Any

from minutes_iq.auth.security import verify_password
from minutes_iq.db.auth_repository import AuthRepository


class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        """
        Dependency injection of the repository.
        Allows for clean separation and easier testing.
        """
        self.auth_repo = auth_repo

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        """
        Orchestrates authentication:
        1. Fetch credentials via triple-join repository logic.
        2. Verify hashed password via security utilities.
        3. Return user context or None.
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.info(f"🔐 Authentication attempt for username: '{username}'")
        logger.info(f"   Password length: {len(password)}")
        logger.info(f"   Password first 10 chars: {repr(password[:10])}")

        # Fetch data from Repository (which handles all SQL)
        credential = self.auth_repo.get_credentials_by_username(username)

        if not credential:
            # Generic fail for security (prevents username enumeration)
            logger.warning(f"❌ No credentials found for username: '{username}'")
            return None

        logger.info(
            f"✅ Found credentials for user: '{username}' (user_id={credential.get('user_id')})"
        )
        logger.info(f"   Stored hash: {credential['hashed_password'][:50]}...")

        # Import settings for debugging
        from minutes_iq.config.settings import settings

        # verify_password handles the bcrypt comparison
        logger.info("🔍 About to call verify_password...")
        logger.info(f"   password == env password: {password == settings.app_password}")

        is_valid = verify_password(password, credential["hashed_password"])
        logger.info(f"   verify_password returned: {is_valid}")

        if not is_valid:
            logger.warning(
                f"❌ Password verification failed for username: '{username}'"
            )

            # Extra debugging - test with the env password
            from minutes_iq.config.settings import settings as settings2

            env_password = settings2.app_password
            logger.info("🔧 DEBUG: Testing with .env password")
            logger.info(f"   .env password: {repr(env_password)}")
            logger.info(f"   request password: {repr(password)}")
            logger.info(f"   Are they equal? {password == env_password}")

            env_test = verify_password(env_password, credential["hashed_password"])
            logger.info(f"   .env password verification result: {env_test}")

            if env_test and not is_valid and password == env_password:
                logger.error("🚨 IMPOSSIBLE: Same password, different results!")
                logger.error("   This suggests a threading/caching issue")
            elif not env_test and password == env_password:
                logger.error("🚨 BOTH PASSWORDS FAIL! Hash in DB is wrong!")
            elif password != env_password:
                logger.error("⚠️  Request password != .env password")

            return None

        logger.info(f"✅ Authentication successful for username: '{username}'")

        # Return sanitized user data (no passwords or sensitive IDs)
        return {
            "user_id": credential["user_id"],
            "username": credential["username"],
            "email": credential["email"],
        }
