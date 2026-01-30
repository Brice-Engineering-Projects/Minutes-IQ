"""
minutes_iq/db/dependencies.py
------------------------------------------

Dependency injection functions for database repositories and services.
Used by FastAPI endpoints to get database connections and service instances.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from minutes_iq.db.auth_code_repository import AuthCodeRepository
from minutes_iq.db.auth_code_service import AuthCodeService
from minutes_iq.db.client import get_db_connection
from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.client_service import ClientService
from minutes_iq.db.favorites_repository import FavoritesRepository
from minutes_iq.db.keyword_repository import KeywordRepository
from minutes_iq.db.keyword_service import KeywordService
from minutes_iq.db.password_reset_repository import (
    PasswordResetRepository,
)
from minutes_iq.db.password_reset_service import PasswordResetService
from minutes_iq.db.user_repository import UserRepository


# Phase 3 & 4 Dependencies (existing)
def get_user_repository() -> Generator[UserRepository, None, None]:
    """Get UserRepository instance with database connection."""
    with get_db_connection() as conn:
        yield UserRepository(conn)


def get_auth_code_repository() -> Generator[AuthCodeRepository, None, None]:
    """Get AuthCodeRepository instance with database connection."""
    with get_db_connection() as conn:
        yield AuthCodeRepository(conn)


def get_auth_code_service(
    auth_code_repo: Annotated[AuthCodeRepository, Depends(get_auth_code_repository)],
) -> AuthCodeService:
    """Get AuthCodeService instance with injected repositories."""
    return AuthCodeService(auth_code_repo)


def get_password_reset_repository() -> Generator[PasswordResetRepository, None, None]:
    """Get PasswordResetRepository instance with database connection."""
    with get_db_connection() as conn:
        yield PasswordResetRepository(conn)


def get_password_reset_service(
    reset_repo: Annotated[
        PasswordResetRepository, Depends(get_password_reset_repository)
    ],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> PasswordResetService:
    """Get PasswordResetService instance with injected repositories."""
    return PasswordResetService(reset_repo, user_repo)


# Phase 5 Dependencies (new)
def get_client_repository() -> Generator[ClientRepository, None, None]:
    """Get ClientRepository instance with database connection."""
    with get_db_connection() as conn:
        yield ClientRepository(conn)


def get_keyword_repository() -> Generator[KeywordRepository, None, None]:
    """Get KeywordRepository instance with database connection."""
    with get_db_connection() as conn:
        yield KeywordRepository(conn)


def get_favorites_repository() -> Generator[FavoritesRepository, None, None]:
    """Get FavoritesRepository instance with database connection."""
    with get_db_connection() as conn:
        yield FavoritesRepository(conn)


def get_client_service(
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
) -> ClientService:
    """Get ClientService instance with injected repositories."""
    return ClientService(client_repo, keyword_repo)


def get_keyword_service(
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
) -> KeywordService:
    """Get KeywordService instance with injected repositories."""
    return KeywordService(keyword_repo)
