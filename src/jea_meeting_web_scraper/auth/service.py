"""
jea_meeting_web_scraper/auth/security.py
----------------------------------------

This module contains security-related functions and utilities for handling authentication and authorization in the JEA meeting web scraper application.
"""

from jea_meeting_web_scraper.auth.schemas import UserInDB
from jea_meeting_web_scraper.auth.security import verify_password


def get_user(db: dict, username: str) -> UserInDB | None:
    """Get a user from the database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(db: dict, username: str, password: str) -> UserInDB | bool:
    """Authenticate a user."""
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
