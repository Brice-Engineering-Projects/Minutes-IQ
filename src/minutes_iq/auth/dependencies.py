# src/minutes_iq/auth/dependencies.py

from collections.abc import Generator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from minutes_iq.auth.service import AuthService
from minutes_iq.config.settings import settings
from minutes_iq.db.auth_code_repository import AuthCodeRepository
from minutes_iq.db.auth_code_service import AuthCodeService
from minutes_iq.db.auth_repository import AuthRepository
from minutes_iq.db.client import get_db_connection
from minutes_iq.db.password_reset_repository import (
    PasswordResetRepository,
)
from minutes_iq.db.password_reset_service import PasswordResetService
from minutes_iq.db.user_repository import UserRepository
from minutes_iq.db.user_service import UserService


def get_user_repository() -> Generator[UserRepository, None, None]:
    """
    Provides a UserRepository instance with proper connection lifecycle management.
    Uses generator to ensure connection is closed after request completes.
    """
    with get_db_connection() as conn:
        yield UserRepository(conn)


# OAuth2 scheme for Swagger UI - this makes the "Authorize" button appear
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token_from_scheme: Annotated[str | None, Depends(oauth2_scheme)],
    # Annotated satisfies B008 by moving the function call into the type hint
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> dict[str, Any]:
    """
    Validates JWT from HttpOnly cookie OR Authorization header and retrieves user identity.
    Supports both cookie-based auth (for browser) and Bearer token (for API/Swagger).
    """
    # Try to get token from Authorization header first (for Swagger UI)
    # The oauth2_scheme dependency will extract it automatically
    token = None
    if token_from_scheme:
        token = token_from_scheme
    else:
        # Fall back to cookie (for browser-based auth)
        token_cookie = request.cookies.get("access_token")
        if token_cookie and token_cookie.startswith("Bearer "):
            token = token_cookie.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - no token in Authorization header or cookie",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except JWTError as err:
        # B904 fix: use 'from err' to preserve the stack trace
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from err

    user = user_repo.get_user_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


def get_auth_service() -> Generator[AuthService, None, None]:
    """
    Factory function for AuthService with proper connection lifecycle management.
    Uses generator to ensure connection is closed after request completes.
    """
    with get_db_connection() as conn:
        repo = AuthRepository(conn)
        yield AuthService(repo)


def get_auth_code_service() -> Generator[AuthCodeService, None, None]:
    """
    Factory function for AuthCodeService with proper connection lifecycle management.
    Uses generator to ensure connection is closed after request completes.
    """
    with get_db_connection() as conn:
        repo = AuthCodeRepository(conn)
        yield AuthCodeService(repo)


def get_user_service() -> Generator[UserService, None, None]:
    """
    Factory function for UserService with proper connection lifecycle management.
    Uses generator to ensure connection is closed after request completes.
    """
    with get_db_connection() as conn:
        user_repo = UserRepository(conn)
        auth_repo = AuthRepository(conn)
        yield UserService(user_repo, auth_repo)


def get_password_reset_service() -> Generator[PasswordResetService, None, None]:
    """
    Factory function for PasswordResetService with proper connection lifecycle management.
    Uses generator to ensure connection is closed after request completes.
    """
    with get_db_connection() as conn:
        reset_repo = PasswordResetRepository(conn)
        user_repo = UserRepository(conn)
        yield PasswordResetService(reset_repo, user_repo)


async def get_current_admin_user(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Validates that the current user is an admin.

    Args:
        current_user: The authenticated user from get_current_user

    Returns:
        The user dict if they are an admin

    Raises:
        HTTPException: 403 if user is not an admin
    """
    # role_id 1 is admin (from our schema)
    if current_user.get("role_id") != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
