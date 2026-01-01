"""
jea_meeting_web_scraper/auth/dependencies.py
--------------------------------------------

Auth dependencies module.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from jea_meeting_web_scraper.auth.schemas import TokenData, User, fake_users_db
from jea_meeting_web_scraper.auth.security import ALGORITHM, SECRET_KEY
from jea_meeting_web_scraper.auth.service import get_user

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        assert SECRET_KEY is not None  # Already validated at module level
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception from None
    if token_data.username is None:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current active user (not disabled)."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
