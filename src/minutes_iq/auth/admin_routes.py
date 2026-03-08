"""Admin routes for authentication support operations."""

import logging
import secrets
import string
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from minutes_iq.auth.dependencies import get_current_admin_user
from minutes_iq.auth.schemas import (
    AdminResetPasswordRequest,
    AdminResetPasswordResponse,
)
from minutes_iq.auth.security import get_password_hash, validate_password_strength
from minutes_iq.db.client import get_db_connection

router = APIRouter(prefix="/admin", tags=["Admin Authentication"])
logger = logging.getLogger(__name__)


def _is_strong_temporary_password(candidate: str) -> bool:
    """Validate temporary password requirements for admin-generated credentials."""
    if len(candidate) < 12:
        return False
    if not any(ch.islower() for ch in candidate):
        return False
    if not any(ch.isupper() for ch in candidate):
        return False
    if not any(ch.isdigit() for ch in candidate):
        return False
    if not any(not ch.isalnum() for ch in candidate):
        return False
    return True


def _generate_temporary_password() -> str:
    """Generate a temporary password that meets complexity rules."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}:,.?"
    while True:
        candidate = "".join(secrets.choice(alphabet) for _ in range(16))
        if _is_strong_temporary_password(candidate):
            validate_password_strength(candidate)
            return candidate


@router.post(
    "/reset-user-password",
    response_model=AdminResetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_user_password(
    request: AdminResetPasswordRequest,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
):
    """Reset a user's password and require password change on next login."""
    temporary_password = _generate_temporary_password()
    hashed_password = get_password_hash(temporary_password)

    with get_db_connection() as conn:
        user_cursor = conn.execute(
            """
            SELECT user_id, email
            FROM users
            WHERE email = ?;
            """,
            (request.email,),
        )
        user_row = user_cursor.fetchone()
        user_cursor.close()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user_id = user_row[0]
        target_email = user_row[1]

        credentials_cursor = conn.execute(
            """
            UPDATE auth_credentials
            SET hashed_password = ?
            WHERE user_id = ? AND provider_id = 1 AND is_active = 1;
            """,
            (hashed_password, user_id),
        )
        credentials_updated = credentials_cursor.rowcount
        credentials_cursor.close()

        if credentials_updated == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User password credentials not found",
            )

        force_cursor = conn.execute(
            """
            UPDATE users
            SET force_password_change = 1
            WHERE user_id = ?;
            """,
            (user_id,),
        )
        force_cursor.close()

        invalidate_cursor = conn.execute(
            """
            UPDATE password_reset_tokens
            SET is_valid = 0
            WHERE user_id = ? AND is_valid = 1;
            """,
            (user_id,),
        )
        invalidate_cursor.close()

        conn.commit()

    logger.info(
        "Admin password reset",
        extra={
            "admin": admin_user.get("email"),
            "target_user": target_email,
        },
    )

    return AdminResetPasswordResponse(
        message="Temporary password generated",
        temporary_password=temporary_password,
    )
