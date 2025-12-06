"""Unit tests for JWT token operations."""

from datetime import timedelta, datetime, timezone
import pytest
from jose import jwt, JWTError
from jea_meeting_web_scraper.auth.routes import (
    create_access_token,
    ALGORITHM,
    SECRET_KEY,
)


class TestCreateAccessToken:
    """Test JWT token creation."""

    def test_create_token_with_username(self):
        """Test creating a token with username data."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        assert SECRET_KEY is not None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    def test_create_token_with_custom_expiration(self):
        """Test creating a token with custom expiration time."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=5)

        token = create_access_token(data, expires_delta=expires_delta)

        assert SECRET_KEY is not None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Should expire approximately 5 minutes from now
        time_diff = (exp_time - now).total_seconds()
    def test_create_token_default_expiration(self):
        """Test that token has default 15 minute expiration when not specified."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert SECRET_KEY is not None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Should expire approximately 15 minutes from now (default)
    def test_create_token_preserves_custom_claims(self):
        """Test that additional custom claims are preserved in token."""
        data = {"sub": "testuser", "role": "admin", "permissions": ["read", "write"]}
        token = create_access_token(data)

        assert SECRET_KEY is not None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    def test_token_cannot_be_decoded_with_wrong_secret(self):
        """Test that token cannot be decoded with incorrect secret."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
    def test_expired_token_raises_error(self):
        """Test that expired tokens raise an error when decoded."""
        data = {"sub": "testuser"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)

        assert SECRET_KEY is not None
        with pytest.raises(JWTError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token = create_access_token(data, expires_delta=expires_delta)

        with pytest.raises(JWTError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
