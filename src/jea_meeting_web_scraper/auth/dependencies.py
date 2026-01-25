# src/jea_meeting_web_scraper/auth/dependencies.py

from collections.abc import Generator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from jea_meeting_web_scraper.auth.service import AuthService
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.auth_repository import AuthRepository
from jea_meeting_web_scraper.db.client import get_db_connection
from jea_meeting_web_scraper.db.user_repository import UserRepository


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
