"""
Auth Service Layer
Handles the business logic for user authentication.
"""

from typing import Any

from jea_meeting_web_scraper.auth.security import verify_password
from jea_meeting_web_scraper.db.auth_repository import AuthRepository


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
        # Fetch data from Repository (which handles all SQL)
        credential = self.auth_repo.get_credentials_by_username(username)

        if not credential:
            # Generic fail for security (prevents username enumeration)
            return None

        # verify_password handles the bcrypt comparison
        is_valid = verify_password(password, credential["hashed_password"])

        if not is_valid:
            return None

        # Return sanitized user data (no passwords or sensitive IDs)
        return {
            "user_id": credential["user_id"],
            "username": credential["username"],
            "email": credential["email"],
        }
