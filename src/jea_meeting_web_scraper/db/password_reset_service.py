"""
Password Reset Service
Business logic for password reset operations.
"""

import hashlib
import secrets
import time
from typing import Any

from jea_meeting_web_scraper.db.password_reset_repository import (
    PasswordResetRepository,
)
from jea_meeting_web_scraper.db.user_repository import UserRepository


class PasswordResetService:
    """Service for managing password reset operations."""

    # Token expiration time in seconds (30 minutes)
    TOKEN_EXPIRATION_SECONDS = 30 * 60

    def __init__(self, reset_repo: PasswordResetRepository, user_repo: UserRepository):
        """
        Initialize the service with repositories.

        Args:
            reset_repo: Password reset token repository
            user_repo: User repository
        """
        self.reset_repo = reset_repo
        self.user_repo = user_repo

    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure reset token.

        Returns a URL-safe token that is 32 bytes (256 bits) of randomness,
        encoded as a 43-character string.

        Returns:
            Secure random token string
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token using SHA-256 before storing it.

        This ensures that if the database is compromised, the actual
        tokens cannot be used to reset passwords.

        Args:
            token: The plaintext token

        Returns:
            SHA-256 hash of the token (hex string)
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def create_reset_token(self, email: str) -> tuple[bool, str | None, str | None]:
        """
        Create a password reset token for a user's email.

        This method:
        1. Looks up the user by email
        2. Generates a secure token
        3. Hashes the token for storage
        4. Stores the token with expiration
        5. Invalidates any previous tokens for this user

        Args:
            email: User's email address

        Returns:
            Tuple of (success, error_message, token)
            - success: True if token was created
            - error_message: Error message if failed, None if successful
            - token: The plaintext token to send via email, None if failed
        """
        # Look up user by email
        user = self.user_repo.get_user_by_email(email)

        if not user:
            # Security: Don't reveal whether email exists
            # Return success but don't actually create a token
            return True, None, None

        # Invalidate any existing tokens for this user
        self.reset_repo.invalidate_all_user_tokens(user["user_id"])

        # Generate new token
        token = self.generate_token()
        token_hash = self.hash_token(token)

        # Calculate expiration
        current_time = int(time.time())
        expires_at = current_time + self.TOKEN_EXPIRATION_SECONDS

        # Store the token
        try:
            self.reset_repo.create_token(
                user_id=user["user_id"],
                token_hash=token_hash,
                created_at=current_time,
                expires_at=expires_at,
            )

            self.reset_repo.db.commit()

            # Return the plaintext token (to be sent via email)
            return True, None, token

        except Exception as e:
            return False, f"Failed to create reset token: {str(e)}", None

    def validate_token(
        self, token: str
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Validate a password reset token.

        Checks:
        1. Token exists in database
        2. Token has not been used
        3. Token is still valid (not invalidated)
        4. Token has not expired

        Args:
            token: The plaintext token from the reset link

        Returns:
            Tuple of (is_valid, error_message, token_data)
            - is_valid: True if token is valid and can be used
            - error_message: Error message if invalid, None if valid
            - token_data: Token dictionary if found, None if not found
        """
        # Hash the token to look it up
        token_hash = self.hash_token(token)

        # Look up the token
        token_data = self.reset_repo.get_token_by_hash(token_hash)

        if not token_data:
            return False, "Invalid reset token", None

        # Check if token has been used
        if token_data["used_at"] is not None:
            return False, "Reset token has already been used", token_data

        # Check if token is valid
        if not token_data["is_valid"]:
            return False, "Reset token has been invalidated", token_data

        # Check if token is expired
        current_time = int(time.time())
        if current_time > token_data["expires_at"]:
            return False, "Reset token has expired", token_data

        # Token is valid
        return True, None, token_data

    def reset_password(self, token: str, new_password: str) -> tuple[bool, str | None]:
        """
        Reset a user's password using a valid token.

        This method:
        1. Validates the token
        2. Updates the user's password
        3. Marks the token as used
        4. Invalidates all other tokens for this user

        Args:
            token: The plaintext reset token
            new_password: The new password to set

        Returns:
            Tuple of (success, error_message)
            - success: True if password was reset
            - error_message: Error message if failed, None if successful
        """
        # Validate the token
        is_valid, error_msg, token_data = self.validate_token(token)

        if not is_valid or token_data is None:
            return False, error_msg

        user_id = token_data["user_id"]

        # Update the user's password
        try:
            self.user_repo.update_password(user_id, new_password)

            # Mark token as used
            current_time = int(time.time())
            self.reset_repo.mark_token_used(token_data["token_id"], current_time)

            # Invalidate all other tokens for this user
            self.reset_repo.invalidate_all_user_tokens(user_id)

            self.reset_repo.db.commit()

            return True, None

        except Exception as e:
            return False, f"Failed to reset password: {str(e)}"

    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from the database.

        This is a maintenance operation that should be run periodically.

        Returns:
            Number of tokens deleted
        """
        current_time = int(time.time())
        count = self.reset_repo.cleanup_expired_tokens(current_time)
        self.reset_repo.db.commit()
        return count
