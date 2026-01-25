"""
Authorization Code Service
Business logic for authorization code operations.
"""

import secrets
import string
import time
from typing import Any

from jea_meeting_web_scraper.db.auth_code_repository import AuthCodeRepository


class AuthCodeService:
    """Service for managing authorization codes."""

    def __init__(self, repo: AuthCodeRepository):
        """
        Initialize the service with a repository.

        Args:
            repo: Authorization code repository
        """
        self.repo = repo

    @staticmethod
    def generate_code() -> str:
        """
        Generate a cryptographically secure authorization code.

        Format: XXXX-XXXX-XXXX (12 characters, uppercase letters and digits)
        Example: XK7M-9P2N-4QW8

        Returns:
            Formatted authorization code string
        """
        alphabet = string.ascii_uppercase + string.digits
        code = "".join(secrets.choice(alphabet) for _ in range(12))
        # Format with hyphens for readability
        return f"{code[0:4]}-{code[4:8]}-{code[8:12]}"

    @staticmethod
    def normalize_code(code: str) -> str:
        """
        Normalize a code for comparison (remove hyphens, uppercase).

        Args:
            code: The code to normalize

        Returns:
            Normalized code string
        """
        return code.replace("-", "").replace(" ", "").upper()

    def create_code(
        self,
        created_by: int,
        expires_in_days: int | None = None,
        max_uses: int = 1,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new authorization code.

        Args:
            created_by: User ID of the admin creating the code
            expires_in_days: Number of days until expiration (None = never)
            max_uses: Maximum number of times the code can be used
            notes: Optional notes about the code

        Returns:
            Dictionary containing the created code's data
        """
        # Generate a unique code
        code = self.generate_code()

        # Calculate expiration timestamp
        expires_at = None
        if expires_in_days is not None:
            expires_at = int(time.time()) + (expires_in_days * 24 * 60 * 60)

        # Create the code
        result = self.repo.create_code(
            code=code,
            created_by=created_by,
            expires_at=expires_at,
            max_uses=max_uses,
            notes=notes,
        )

        self.repo.db.commit()
        return result

    def validate_code(
        self, code: str
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Validate an authorization code.

        Args:
            code: The code to validate

        Returns:
            Tuple of (is_valid, error_message, code_data)
            - is_valid: True if code is valid and can be used
            - error_message: Error message if invalid, None if valid
            - code_data: Code dictionary if found, None if not found
        """
        # Normalize the code
        normalized_code = self.normalize_code(code)

        # Look up the code
        code_data = self.repo.get_code_by_string(normalized_code)

        if not code_data:
            return False, "Invalid authorization code", None

        # Check if code is active
        if not code_data["is_active"]:
            return False, "Authorization code has been revoked", code_data

        # Check if code is expired
        if code_data["expires_at"] is not None:
            current_time = int(time.time())
            if current_time > code_data["expires_at"]:
                return False, "Authorization code has expired", code_data

        # Check if code has uses remaining
        if code_data["current_uses"] >= code_data["max_uses"]:
            return False, "Authorization code has been fully used", code_data

        # Code is valid
        return True, None, code_data

    def use_code(self, code: str, user_id: int) -> tuple[bool, str | None]:
        """
        Mark a code as used by a specific user.

        This should be called after successfully creating a user account.

        Args:
            code: The authorization code
            user_id: The ID of the user who used the code

        Returns:
            Tuple of (success, error_message)
        """
        # Validate the code first
        is_valid, error_msg, code_data = self.validate_code(code)

        if not is_valid:
            return False, error_msg

        # Increment usage count
        self.repo.increment_usage(code_data["code_id"])

        # Record the usage
        self.repo.record_usage(code_data["code_id"], user_id)

        self.repo.db.commit()
        return True, None

    def list_codes(
        self, status: str = "active", limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List authorization codes with filtering.

        Args:
            status: Filter by status ("active", "expired", "used", "revoked", "all")
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of code dictionaries (with masked codes for security)
        """
        codes = self.repo.list_codes(status=status, limit=limit, offset=offset)

        # Mask codes for security (show only first 4 characters)
        for code in codes:
            if len(code["code"]) >= 4:
                code["code_masked"] = code["code"][:4] + "-****-****"
            else:
                code["code_masked"] = "****-****-****"

        return codes

    def revoke_code(self, code_id: int) -> bool:
        """
        Revoke an authorization code.

        Args:
            code_id: The code ID to revoke

        Returns:
            True if code was revoked, False if code doesn't exist
        """
        result = self.repo.revoke_code(code_id)
        if result:
            self.repo.db.commit()
        return result

    def get_code_usage_history(self, code_id: int) -> list[dict[str, Any]]:
        """
        Get the usage history for a specific code.

        Args:
            code_id: The code ID

        Returns:
            List of usage records
        """
        return self.repo.get_usage_history(code_id)
