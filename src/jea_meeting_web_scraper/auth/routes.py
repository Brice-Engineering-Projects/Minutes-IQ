# jea_meeting_web_scraper/auth/routes.py
"""
Auth Routes
Handles HTTP requests for login, logout, and registration.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from jea_meeting_web_scraper.auth.dependencies import (
    get_auth_code_service,
    get_auth_service,
    get_current_user,
    get_user_service,
)
from jea_meeting_web_scraper.auth.schemas import RegisterRequest, RegisterResponse
from jea_meeting_web_scraper.auth.security import create_access_token
from jea_meeting_web_scraper.auth.service import AuthService
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.db.auth_code_service import AuthCodeService
from jea_meeting_web_scraper.db.user_service import UserService

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


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_code_service: Annotated[AuthCodeService, Depends(get_auth_code_service)],
):
    """
    Register a new user with an authorization code.

    This endpoint:
    1. Validates the provided authorization code
    2. Creates a new user account with the provided credentials
    3. Marks the authorization code as used
    4. Returns the created user information

    Args:
        request: Registration details including username, email, password, and auth_code
        user_service: User service for account creation
        auth_code_service: Authorization code service for validation

    Returns:
        RegisterResponse with success message and user data

    Raises:
        HTTPException 400: If authorization code is invalid, expired, or already used
        HTTPException 409: If username or email already exists
        HTTPException 500: If user creation or code marking fails
    """
    # Step 1: Validate the authorization code
    is_valid, error_message, code_data = auth_code_service.validate_code(
        request.auth_code
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid authorization code: {error_message}",
        )

    # Step 2: Create the user account
    try:
        user = user_service.create_user_with_password(
            username=request.username,
            email=request.email,
            password=request.password,
            role_id=2,  # Regular user role
        )
    except ValueError as e:
        # Handle duplicate username/email
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except Exception as e:
        # Handle any other errors during user creation
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account",
        ) from e

    # Step 3: Mark the authorization code as used
    try:
        success, error_msg = auth_code_service.use_code(
            request.auth_code, user["user_id"]
        )
        if not success:
            raise ValueError(error_msg)
    except Exception as e:
        # This is a critical error - user was created but code wasn't marked as used
        # In production, you might want to implement a rollback or compensating transaction
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User created but failed to mark authorization code as used",
        ) from e

    # Return success response
    return RegisterResponse(
        message="User registered successfully",
        user={
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role_id": user["role_id"],
        },
    )


@router.get("/me")
async def read_users_me(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Returns the currently authenticated user's profile.
    This verifies that the persistence layer and JWT flow are fully integrated.
    """
    return current_user
