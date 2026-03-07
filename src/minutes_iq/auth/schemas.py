"""
minutes_iq/auth/schemas.py
----------------------------------------

This module contains schemas for handling authentication-related data structures.
"""

from pydantic import BaseModel, field_validator

from minutes_iq.auth.security import validate_password_strength


# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate that username is not empty."""
        if not v or not v.strip():
            raise ValueError("Username cannot be empty")
        return v


class RegisterRequest(BaseModel):
    """Request model for user registration with authorization code."""

    username: str
    email: str
    password: str
    auth_code: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate that username is not empty."""
        if not v or not v.strip():
            raise ValueError("Username cannot be empty")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if not v or "@" not in v:
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        return validate_password_strength(v)

    @field_validator("auth_code")
    @classmethod
    def validate_auth_code(cls, v: str) -> str:
        """Validate that auth code is not empty."""
        if not v or not v.strip():
            raise ValueError("Authorization code is required")
        return v.strip()


class RegisterResponse(BaseModel):
    """Response model for successful registration."""

    message: str
    user: dict


class PasswordResetRequest(BaseModel):
    """Request model for initiating password reset."""

    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if not v or "@" not in v:
            raise ValueError("Invalid email address")
        return v.strip().lower()


class PasswordResetConfirm(BaseModel):
    """Request model for completing password reset."""

    token: str
    new_password: str

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate that token is not empty."""
        if not v or not v.strip():
            raise ValueError("Reset token is required")
        return v.strip()

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        return validate_password_strength(v)


class PasswordResetResponse(BaseModel):
    """Response model for password reset operations."""

    message: str


class AdminResetPasswordRequest(BaseModel):
    """Request model for admin-triggered password reset."""

    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if not v or "@" not in v:
            raise ValueError("Invalid email address")
        return v.strip().lower()


class AdminResetPasswordResponse(BaseModel):
    """Response model for admin-triggered password reset."""

    message: str
    temporary_password: str


class ChangePasswordRequest(BaseModel):
    """Request model for authenticated password change."""

    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate password strength."""
        return validate_password_strength(v)
