"""Unit tests for authorization code service."""

import time

from jea_meeting_web_scraper.db.auth_code_repository import AuthCodeRepository
from jea_meeting_web_scraper.db.auth_code_service import AuthCodeService


class TestCreateCode:
    """Test service-level code creation."""

    def test_create_code_generates_unique_code(self, db_connection, test_user):
        """Test that service generates unique codes."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        code1 = service.create_code(created_by=test_user["user_id"])
        code2 = service.create_code(created_by=test_user["user_id"])

        assert code1["code"] != code2["code"]

    def test_create_code_with_expiration(self, db_connection, test_user):
        """Test creating code with expiration in days."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        current_time = int(time.time())
        code = service.create_code(created_by=test_user["user_id"], expires_in_days=7)

        # Should expire in approximately 7 days
        expected_expiry = current_time + (7 * 24 * 60 * 60)
        assert abs(code["expires_at"] - expected_expiry) < 10  # Within 10 seconds

    def test_create_code_never_expires(self, db_connection, test_user):
        """Test creating code that never expires."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        code = service.create_code(
            created_by=test_user["user_id"], expires_in_days=None
        )

        assert code["expires_at"] is None

    def test_create_code_with_max_uses(self, db_connection, test_user):
        """Test creating code with custom max uses."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        code = service.create_code(created_by=test_user["user_id"], max_uses=5)

        assert code["max_uses"] == 5

    def test_create_code_with_notes(self, db_connection, test_user):
        """Test creating code with notes."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        code = service.create_code(
            created_by=test_user["user_id"], notes="For Jane Doe"
        )

        assert code["notes"] == "For Jane Doe"


class TestValidateCode:
    """Test code validation logic."""

    def test_validate_valid_code(self, db_connection, test_user):
        """Test validating a valid code."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create a valid code
        created = service.create_code(created_by=test_user["user_id"])

        # Validate it
        is_valid, error_msg, code_data = service.validate_code(created["code"])

        assert is_valid is True
        assert error_msg is None
        assert code_data is not None
        assert code_data["code_id"] == created["code_id"]

    def test_validate_nonexistent_code(self, db_connection):
        """Test validating a code that doesn't exist."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        is_valid, error_msg, code_data = service.validate_code("FAKE-CODE-9999")

        assert is_valid is False
        assert error_msg == "Invalid authorization code"
        assert code_data is None

    def test_validate_revoked_code(self, db_connection, test_user):
        """Test validating a revoked code."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create and revoke a code
        created = service.create_code(created_by=test_user["user_id"])
        service.revoke_code(created["code_id"])

        # Try to validate it
        is_valid, error_msg, code_data = service.validate_code(created["code"])

        assert is_valid is False
        assert error_msg == "Authorization code has been revoked"
        assert code_data is not None

    def test_validate_expired_code(self, db_connection, test_user):
        """Test validating an expired code."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create an expired code (expire 1 hour ago) - use normalized code
        past_time = int(time.time()) - 3600
        formatted_code = service.generate_code()
        normalized_code = service.normalize_code(formatted_code)

        repo.create_code(
            code=normalized_code,
            created_by=test_user["user_id"],
            expires_at=past_time,
        )
        db_connection.commit()

        # Try to validate it (use formatted code with hyphens)
        is_valid, error_msg, code_data = service.validate_code(formatted_code)

        assert is_valid is False
        assert error_msg == "Authorization code has expired"
        assert code_data is not None

    def test_validate_fully_used_code(self, db_connection, test_user):
        """Test validating a code that has been fully used."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create a single-use code
        created = service.create_code(created_by=test_user["user_id"], max_uses=1)

        # Mark it as used
        repo.increment_usage(created["code_id"])
        db_connection.commit()

        # Try to validate it
        is_valid, error_msg, code_data = service.validate_code(created["code"])

        assert is_valid is False
        assert error_msg == "Authorization code has been fully used"
        assert code_data is not None

    def test_validate_code_with_uses_remaining(self, db_connection, test_user):
        """Test validating multi-use code with uses remaining."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create a 3-use code
        created = service.create_code(created_by=test_user["user_id"], max_uses=3)

        # Use it once
        repo.increment_usage(created["code_id"])
        db_connection.commit()

        # Should still be valid
        is_valid, error_msg, code_data = service.validate_code(created["code"])

        assert is_valid is True
        assert error_msg is None

    def test_validate_code_case_insensitive(self, db_connection, test_user):
        """Test that validation is case-insensitive."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create code in uppercase
        created = service.create_code(created_by=test_user["user_id"])
        original_code = created["code"]

        # Validate with lowercase
        lowercase_code = original_code.lower()
        is_valid, error_msg, code_data = service.validate_code(lowercase_code)

        assert is_valid is True

    def test_validate_code_with_extra_hyphens(self, db_connection, test_user):
        """Test that validation handles extra hyphens."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create code
        created = service.create_code(created_by=test_user["user_id"])

        # Validate with different hyphenation
        code_without_hyphens = created["code"].replace("-", "")
        is_valid, error_msg, code_data = service.validate_code(code_without_hyphens)

        assert is_valid is True


class TestUseCode:
    """Test marking codes as used."""

    def test_use_valid_code(self, db_connection, test_user):
        """Test using a valid code."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create code
        created = service.create_code(created_by=test_user["user_id"])

        # Use it
        success, error_msg = service.use_code(created["code"], test_user["user_id"])

        assert success is True
        assert error_msg is None

        # Verify usage was recorded
        updated = repo.get_code_by_id(created["code_id"])
        assert updated["current_uses"] == 1

        # Verify usage history
        history = repo.get_usage_history(created["code_id"])
        assert len(history) == 1
        assert history[0]["user_id"] == test_user["user_id"]

    def test_use_invalid_code(self, db_connection, test_user):
        """Test using an invalid code."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        success, error_msg = service.use_code("INVALID-CODE", test_user["user_id"])

        assert success is False
        assert error_msg == "Invalid authorization code"

    def test_use_code_twice_single_use(self, db_connection, test_user):
        """Test that single-use code can't be used twice."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create single-use code
        created = service.create_code(created_by=test_user["user_id"], max_uses=1)

        # Use it once
        success1, _ = service.use_code(created["code"], test_user["user_id"])
        assert success1 is True

        # Try to use it again
        success2, error_msg = service.use_code(created["code"], test_user["user_id"])
        assert success2 is False
        assert error_msg == "Authorization code has been fully used"


class TestListCodes:
    """Test listing codes."""

    def test_list_codes_masks_codes(self, db_connection, test_user):
        """Test that listed codes are masked for security."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create a code
        service.create_code(created_by=test_user["user_id"])

        # List codes
        codes = service.list_codes(status="all")

        assert len(codes) == 1
        assert "code_masked" in codes[0]
        assert codes[0]["code_masked"].endswith("****-****")

    def test_list_active_codes_only(self, db_connection, test_user):
        """Test listing only active codes."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create active code
        service.create_code(created_by=test_user["user_id"])

        # Create and revoke another code
        revoked = service.create_code(created_by=test_user["user_id"])
        service.revoke_code(revoked["code_id"])

        # List active only
        active_codes = service.list_codes(status="active")

        assert len(active_codes) == 1


class TestRevokeCode:
    """Test code revocation."""

    def test_revoke_existing_code(self, db_connection, test_user):
        """Test revoking an existing code."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create code
        created = service.create_code(created_by=test_user["user_id"])

        # Revoke it
        result = service.revoke_code(created["code_id"])

        assert result is True

        # Verify it's revoked
        updated = repo.get_code_by_id(created["code_id"])
        assert updated["is_active"] == 0

    def test_revoke_nonexistent_code(self, db_connection):
        """Test revoking non-existent code."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        result = service.revoke_code(99999)

        assert result is False


class TestGetUsageHistory:
    """Test retrieving usage history."""

    def test_get_usage_history_with_users(self, db_connection, test_user):
        """Test getting usage history includes user information."""
        repo = AuthCodeRepository(db_connection)
        service = AuthCodeService(repo)

        # Create code
        created = service.create_code(created_by=test_user["user_id"])

        # Use it
        service.use_code(created["code"], test_user["user_id"])

        # Get history
        history = service.get_code_usage_history(created["code_id"])

        assert len(history) == 1
        assert history[0]["username"] == test_user["username"]
        assert history[0]["email"] == test_user["email"]
