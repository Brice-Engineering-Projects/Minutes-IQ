# src/jea_meeting_web_scraper/auth/dependencies.py

from typing import Annotated, Any  # Import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from jea_meeting_web_scraper.auth.service import AuthService
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.auth_repository import AuthRepository
from jea_meeting_web_scraper.db.client import get_db_connection
from jea_meeting_web_scraper.db.user_repository import UserRepository


def get_user_repository() -> UserRepository:
    """Provides a UserRepository instance with a fresh DB connection."""
    return UserRepository(get_db_connection())


async def get_current_user(
    request: Request,
    # Annotated satisfies B008 by moving the function call into the type hint
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> dict[str, Any]:
    """
    Validates JWT from HttpOnly cookie and retrieves user identity.
    """
    token_cookie = request.cookies.get("access_token")
    if not token_cookie or not token_cookie.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = token_cookie.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
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


def get_auth_service() -> AuthService:
    """Factory function for AuthService using context-managed DB connection."""
    with get_db_connection() as conn:
        repo = AuthRepository(conn)
        return AuthService(repo)
