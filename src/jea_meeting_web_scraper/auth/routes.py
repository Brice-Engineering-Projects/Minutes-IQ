"""
jea_meeting_web_scraper/auth/routes.py
--------------------------------------

This module contains routes for handling authentication-related functionality.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from jea_meeting_web_scraper.auth.dependencies import get_current_active_user
from jea_meeting_web_scraper.auth.schemas import (
    Token,
    User,
    UserCreate,
    UserInDB,
    fake_users_db,
)
from jea_meeting_web_scraper.auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_password_hash,
)
from jea_meeting_web_scraper.auth.service import authenticate_user

router = APIRouter()


# Routes
@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Login endpoint to get an access token."""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user or not isinstance(user, UserInDB):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=User)
async def register(user_data: UserCreate) -> User:
    """Register a new user."""
    # Check if user already exists
    if user_data.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_dict = {
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": hashed_password,
        "disabled": False,
    }
    fake_users_db[user_data.username] = user_dict

    return User(**user_dict)


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Get current user information."""
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Token:
    """Refresh the access token."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
