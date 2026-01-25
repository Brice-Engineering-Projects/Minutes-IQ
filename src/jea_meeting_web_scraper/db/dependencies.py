"""
jea_meeting_web_scraper/db/dependencies.py
------------------------------------------

Dependency injection functions for database repositories and services.
Used by FastAPI endpoints to get database connections and service instances.
"""

from typing import Annotated

from fastapi import Depends

from jea_meeting_web_scraper.db.auth_code_repository import AuthCodeRepository
from jea_meeting_web_scraper.db.auth_code_service import AuthCodeService
from jea_meeting_web_scraper.db.client import get_db_connection
from jea_meeting_web_scraper.db.client_repository import ClientRepository
from jea_meeting_web_scraper.db.client_service import ClientService
from jea_meeting_web_scraper.db.favorites_repository import FavoritesRepository
from jea_meeting_web_scraper.db.keyword_repository import KeywordRepository
from jea_meeting_web_scraper.db.keyword_service import KeywordService
from jea_meeting_web_scraper.db.password_reset_repository import (
    PasswordResetRepository,
)
from jea_meeting_web_scraper.db.password_reset_service import PasswordResetService
from jea_meeting_web_scraper.db.user_repository import UserRepository


# Phase 3 & 4 Dependencies (existing)
def get_user_repository():
    """Get UserRepository instance with database connection."""
    db = get_db_connection()
    return UserRepository(db)


def get_auth_code_repository():
    """Get AuthCodeRepository instance with database connection."""
    db = get_db_connection()
    return AuthCodeRepository(db)


def get_auth_code_service(
    auth_code_repo: Annotated[AuthCodeRepository, Depends(get_auth_code_repository)],
):
    """Get AuthCodeService instance with injected repositories."""
    return AuthCodeService(auth_code_repo)


def get_password_reset_repository():
    """Get PasswordResetRepository instance with database connection."""
    db = get_db_connection()
    return PasswordResetRepository(db)


def get_password_reset_service(
    reset_repo: Annotated[
        PasswordResetRepository, Depends(get_password_reset_repository)
    ],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Get PasswordResetService instance with injected repositories."""
    return PasswordResetService(reset_repo, user_repo)


# Phase 5 Dependencies (new)
def get_client_repository():
    """Get ClientRepository instance with database connection."""
    db = get_db_connection()
    return ClientRepository(db)


def get_keyword_repository():
    """Get KeywordRepository instance with database connection."""
    db = get_db_connection()
    return KeywordRepository(db)


def get_favorites_repository():
    """Get FavoritesRepository instance with database connection."""
    db = get_db_connection()
    return FavoritesRepository(db)


def get_client_service(
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Get ClientService instance with injected repositories."""
    return ClientService(client_repo, keyword_repo)


def get_keyword_service(
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Get KeywordService instance with injected repositories."""
    return KeywordService(keyword_repo)
