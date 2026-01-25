# jea_meeting_web_scraper/auth/routes.py
"""
Auth Routes
Handles HTTP requests for login, logout, and registration.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from jea_meeting_web_scraper.auth.dependencies import get_auth_service, get_current_user
from jea_meeting_web_scraper.auth.security import create_access_token
from jea_meeting_web_scraper.auth.service import AuthService
from jea_meeting_web_scraper.config.settings import settings

router = APIRouter(tags=["Authentication"])


@router.post("/login")
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Handles the login flow:
    1. Authenticates user via AuthService (DB-backed).
    2. Generates a JWT access token.
    3. Sets an HttpOnly cookie for security.
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.info("🌐 FastAPI received login request")
    logger.info(f"   Username: '{form_data.username}' (len={len(form_data.username)})")
    logger.info(
        f"   Password: len={len(form_data.password)}, repr={repr(form_data.password[:10])}..."
    )

    # Use the service layer to verify credentials (this triggers the triple-join)
    user = auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT containing the user_id context
    access_token = create_access_token(data={"sub": str(user["user_id"])})

    # Store token in a secure, HttpOnly cookie to prevent XSS attacks
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,  # 30 minutes
        samesite="lax",
        secure=settings.app.env == "production",  # Only require HTTPS in production
    )

    # Also return the token in response body for testing in Swagger UI
    return {
        "message": "Successfully logged in",
        "user": user,
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me")
async def read_users_me(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Returns the currently authenticated user's profile.
    This verifies that the persistence layer and JWT flow are fully integrated.
    """
    return current_user
