"""
minutes_iq/auth/security.py
----------------------------------------

This module contains security-related functions and utilities for handling authentication and authorization in the JEA meeting web scraper application.
"""

from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from minutes_iq.config import settings

# configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = settings.secret_key

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)
    to_encode.update(
        {
            "exp": expire,
            "iat": now.timestamp(),  # Use timestamp with microseconds for uniqueness
        }
    )
    assert SECRET_KEY is not None  # Already validated at module level
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
