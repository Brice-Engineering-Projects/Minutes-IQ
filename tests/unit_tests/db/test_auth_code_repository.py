"""Unit tests for authorization code repository."""

import time

from minutes_iq.db.auth_code_repository import AuthCodeRepository


class TestCreateCode:
    """Test code creation."""

    def test_create_code_success(self, db_connection, test_user):
        """Test successful code creation."""
        repo = AuthCodeRepository(db_connection)

        code_data = repo.create_code(
            code="TEST-CODE-1234",
            created_by=test_user["user_id"],
            expires_at=None,
            max_uses=1,
            notes="Test code",
        )

        assert code_data["code"] == "TEST-CODE-1234"
        assert code_data["created_by"] == test_user["user_id"]
        assert code_data["max_uses"] == 1
        assert code_data["current_uses"] == 0
        assert code_data["is_active"] == 1
        assert code_data["notes"] == "Test code"
        assert "code_id" in code_data
        assert "created_at" in code_data

    def test_create_code_with_expiration(self, db_connection, test_user):
        """Test creating code with expiration."""
        repo = AuthCodeRepository(db_connection)
        future_time = int(time.time()) + 86400  # 1 day from now

        code_data = repo.create_code(
            code="EXPIRE-TEST-99",
            created_by=test_user["user_id"],
            expires_at=future_time,
            max_uses=5,
        )

        assert code_data["expires_at"] == future_time
        assert code_data["max_uses"] == 5

    def test_create_code_no_notes(self, db_connection, test_user):
        """Test creating code without notes."""
        repo = AuthCodeRepository(db_connection)

        code_data = repo.create_code(
            code="NO-NOTES-CODE",
            created_by=test_user["user_id"],
        )

        assert code_data["notes"] is None


class TestGetCode:
    """Test code retrieval."""

    def test_get_code_by_string(self, db_connection, test_user):
        """Test retrieving code by string."""
        repo = AuthCodeRepository(db_connection)

        # Create a code
        created = repo.create_code(
            code="FIND-ME-1234",
            created_by=test_user["user_id"],
        )
        db_connection.commit()

        # Retrieve it
        found = repo.get_code_by_string("FIND-ME-1234")

        assert found is not None
        assert found["code_id"] == created["code_id"]
        assert found["code"] == "FIND-ME-1234"

    def test_get_code_by_string_not_found(self, db_connection):
        """Test that non-existent code returns None."""
        repo = AuthCodeRepository(db_connection)

        found = repo.get_code_by_string("NONEXISTENT")

        assert found is None

    def test_get_code_by_id(self, db_connection, test_user):
        """Test retrieving code by ID."""
        repo = AuthCodeRepository(db_connection)

        # Create a code
        created = repo.create_code(
            code="ID-TEST-5678",
            created_by=test_user["user_id"],
        )
        db_connection.commit()

        # Retrieve it by ID
        found = repo.get_code_by_id(created["code_id"])

        assert found is not None
        assert found["code"] == "ID-TEST-5678"

    def test_get_code_by_id_not_found(self, db_connection):
        """Test that non-existent ID returns None."""
        repo = AuthCodeRepository(db_connection)

        found = repo.get_code_by_id(99999)

        assert found is None


class TestListCodes:
    """Test listing codes with filters."""

    def test_list_codes_empty(self, db_connection, clean_db):
        """Test listing codes when none exist."""
        repo = AuthCodeRepository(db_connection)

        codes = repo.list_codes()

        assert codes == []

    def test_list_active_codes(self, db_connection, test_user):
        """Test listing only active codes."""
        repo = AuthCodeRepository(db_connection)

        # Create active code
        repo.create_code("ACTIVE-CODE-1", created_by=test_user["user_id"])

        # Create expired code
        past_time = int(time.time()) - 3600  # 1 hour ago
        repo.create_code(
            "EXPIRED-CODE", created_by=test_user["user_id"], expires_at=past_time
        )

        # Create revoked code
        revoked = repo.create_code("REVOKED-CODE", created_by=test_user["user_id"])
        repo.revoke_code(revoked["code_id"])

        db_connection.commit()

        # List active codes
        active_codes = repo.list_codes(status="active")

        assert len(active_codes) == 1
        assert active_codes[0]["code"] == "ACTIVE-CODE-1"

    def test_list_expired_codes(self, db_connection, test_user):
        """Test listing expired codes."""
        repo = AuthCodeRepository(db_connection)

        # Create expired code
        past_time = int(time.time()) - 3600
        repo.create_code(
            "EXPIRED-1", created_by=test_user["user_id"], expires_at=past_time
        )

        # Create active code
        future_time = int(time.time()) + 3600
        repo.create_code(
            "ACTIVE-1", created_by=test_user["user_id"], expires_at=future_time
        )

        db_connection.commit()

        # List expired codes
        expired_codes = repo.list_codes(status="expired")

        assert len(expired_codes) == 1
        assert expired_codes[0]["code"] == "EXPIRED-1"

    def test_list_all_codes(self, db_connection, test_user):
        """Test listing all codes regardless of status."""
        repo = AuthCodeRepository(db_connection)

        # Create multiple codes
        repo.create_code("CODE-1", created_by=test_user["user_id"])
        repo.create_code("CODE-2", created_by=test_user["user_id"])
        repo.create_code("CODE-3", created_by=test_user["user_id"])

        db_connection.commit()

        # List all
        all_codes = repo.list_codes(status="all")

        assert len(all_codes) == 3

    def test_list_codes_pagination(self, db_connection, test_user):
        """Test pagination in code listing."""
        repo = AuthCodeRepository(db_connection)

        # Create 5 codes
        for i in range(5):
            repo.create_code(f"CODE-{i}", created_by=test_user["user_id"])

        db_connection.commit()

        # Get first page
        page1 = repo.list_codes(status="all", limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = repo.list_codes(status="all", limit=2, offset=2)
        assert len(page2) == 2

        # Ensure no overlap
        page1_codes = {c["code"] for c in page1}
        page2_codes = {c["code"] for c in page2}
        assert page1_codes.isdisjoint(page2_codes)


class TestCodeUsage:
    """Test code usage tracking."""

    def test_increment_usage(self, db_connection, test_user):
        """Test incrementing code usage count."""
        repo = AuthCodeRepository(db_connection)

        # Create code
        code_data = repo.create_code("USAGE-TEST", created_by=test_user["user_id"])
        db_connection.commit()

        assert code_data["current_uses"] == 0

        # Increment usage
        repo.increment_usage(code_data["code_id"])
        db_connection.commit()

        # Verify increment
        updated = repo.get_code_by_id(code_data["code_id"])
        assert updated["current_uses"] == 1

    def test_record_usage(self, db_connection, test_user):
        """Test recording code usage."""
        repo = AuthCodeRepository(db_connection)

        # Create code
        code_data = repo.create_code("RECORD-TEST", created_by=test_user["user_id"])
        db_connection.commit()

        # Record usage
        repo.record_usage(code_data["code_id"], test_user["user_id"])
        db_connection.commit()

        # Verify usage was recorded
        usage_history = repo.get_usage_history(code_data["code_id"])
        assert len(usage_history) == 1
        assert usage_history[0]["user_id"] == test_user["user_id"]
        assert usage_history[0]["code_id"] == code_data["code_id"]

    def test_get_usage_history_empty(self, db_connection, test_user):
        """Test getting usage history for unused code."""
        repo = AuthCodeRepository(db_connection)

        # Create code
        code_data = repo.create_code("UNUSED-CODE", created_by=test_user["user_id"])
        db_connection.commit()

        # Get usage history
        history = repo.get_usage_history(code_data["code_id"])

        assert history == []


class TestRevokeCode:
    """Test code revocation."""

    def test_revoke_code(self, db_connection, test_user):
        """Test revoking a code."""
        repo = AuthCodeRepository(db_connection)

        # Create code
        code_data = repo.create_code("REVOKE-ME", created_by=test_user["user_id"])
        db_connection.commit()

        assert code_data["is_active"] == 1

        # Revoke it
        result = repo.revoke_code(code_data["code_id"])
        db_connection.commit()

        assert result is True

        # Verify it's revoked
        updated = repo.get_code_by_id(code_data["code_id"])
        assert updated["is_active"] == 0

    def test_revoke_nonexistent_code(self, db_connection):
        """Test that revoking non-existent code returns False."""
        repo = AuthCodeRepository(db_connection)

        result = repo.revoke_code(99999)

        assert result is False
