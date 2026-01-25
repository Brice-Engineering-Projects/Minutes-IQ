"""
jea_meeting_web_scraper/auth/schemas.py
----------------------------------------

This module contains schemas for handling authentication-related data structures.
"""

from pydantic import BaseModel, field_validator


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
