"""
Integration tests for admin authorization code management endpoints.

Tests the admin API endpoints for:
- Creating authorization codes
- Listing codes with filters
- Revoking codes
- Viewing usage history
"""

import pytest
from fastapi.testclient import TestClient

from minutes_iq.auth.security import create_access_token, get_password_hash
from minutes_iq.db.auth_code_repository import AuthCodeRepository
from minutes_iq.db.auth_code_service import AuthCodeService
from minutes_iq.db.client import get_db_connection
from minutes_iq.db.user_repository import UserRepository
from minutes_iq.main import app

client = TestClient(app)


@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    with get_db_connection() as conn:
        user_repo = UserRepository(conn)

        # Create admin user
        user = user_repo.create_user(
            username="admin", email="admin@test.com", role_id=1
        )

        # Create password credentials for admin
        hashed_password = get_password_hash("adminpassword")
        cursor = conn.execute(
            """
            INSERT INTO auth_credentials (user_id, provider_id, hashed_password, is_active)
            VALUES (?, 1, ?, 1);
            """,
            (user["user_id"], hashed_password),
        )
        cursor.close()
        conn.commit()

        return user


@pytest.fixture
def regular_user():
    """Create a regular user for testing unauthorized access."""
    with get_db_connection() as conn:
        user_repo = UserRepository(conn)

        # Create regular user
        user = user_repo.create_user(
            username="regular", email="regular@test.com", role_id=2
        )

        # Create password credentials for regular user
        hashed_password = get_password_hash("regularpassword")
        cursor = conn.execute(
            """
            INSERT INTO auth_credentials (user_id, provider_id, hashed_password, is_active)
            VALUES (?, 1, ?, 1);
            """,
            (user["user_id"], hashed_password),
        )
        cursor.close()
        conn.commit()

        return user


@pytest.fixture
def admin_token(admin_user):
    """Create an admin authentication token."""
    return create_access_token(data={"sub": str(admin_user["user_id"])})


@pytest.fixture
def regular_token(regular_user):
    """Create a regular user authentication token."""
    return create_access_token(data={"sub": str(regular_user["user_id"])})


class TestCreateAuthCode:
    """Tests for creating authorization codes."""

    def test_admin_can_create_code(self, admin_token):
        """Test that admin can successfully create an authorization code."""
        response = client.post(
            "/admin/auth-codes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"expires_in_days": 7, "max_uses": 5, "notes": "Test code"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "code_id" in data
        assert "code_formatted" in data
        assert data["max_uses"] == 5
        assert data["current_uses"] == 0
        assert data["is_active"] is True
        assert data["notes"] == "Test code"
        assert data["expires_at"] is not None

    def test_admin_can_create_code_with_defaults(self, admin_token):
        """Test that admin can create a code with default values."""
        response = client.post(
            "/admin/auth-codes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["max_uses"] == 1
        assert data["current_uses"] == 0
        assert data["notes"] is None

    def test_admin_can_create_code_without_expiration(self, admin_token):
        """Test that admin can create a code that never expires."""
        response = client.post(
            "/admin/auth-codes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"expires_in_days": None, "max_uses": 1},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is None

    def test_regular_user_cannot_create_code(self, regular_token):
        """Test that regular users cannot create authorization codes."""
        response = client.post(
            "/admin/auth-codes",
            headers={"Authorization": f"Bearer {regular_token}"},
            json={"max_uses": 1},
        )

        assert response.status_code == 403

    def test_unauthenticated_cannot_create_code(self):
        """Test that unauthenticated requests cannot create codes."""
        response = client.post(
            "/admin/auth-codes",
            json={"max_uses": 1},
        )

        assert response.status_code == 401


class TestListAuthCodes:
    """Tests for listing authorization codes."""

    def test_admin_can_list_active_codes(self, admin_token, admin_user):
        """Test that admin can list active authorization codes."""
        # Create some test codes
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            service.create_code(
                created_by=admin_user["user_id"], max_uses=1, notes="Active code 1"
            )
            service.create_code(
                created_by=admin_user["user_id"], max_uses=1, notes="Active code 2"
            )

        response = client.get(
            "/admin/auth-codes?status_filter=active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "codes" in data
        assert "total" in data
        assert data["total"] >= 2

    def test_admin_can_filter_by_status(self, admin_token, admin_user):
        """Test that admin can filter codes by status."""
        # Create and revoke a code
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            code = service.create_code(
                created_by=admin_user["user_id"], max_uses=1, notes="To be revoked"
            )
            service.revoke_code(code["code_id"])

        # List revoked codes
        response = client.get(
            "/admin/auth-codes?status_filter=revoked",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_admin_can_paginate_results(self, admin_token, admin_user):
        """Test that admin can paginate through results."""
        # Create multiple codes
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            for i in range(5):
                service.create_code(
                    created_by=admin_user["user_id"], max_uses=1, notes=f"Code {i}"
                )

        # Get first page
        response1 = client.get(
            "/admin/auth-codes?limit=2&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["codes"]) <= 2

        # Get second page
        response2 = client.get(
            "/admin/auth-codes?limit=2&offset=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["codes"]) <= 2

    def test_regular_user_cannot_list_codes(self, regular_token):
        """Test that regular users cannot list authorization codes."""
        response = client.get(
            "/admin/auth-codes",
            headers={"Authorization": f"Bearer {regular_token}"},
        )

        assert response.status_code == 403

    def test_unauthenticated_cannot_list_codes(self):
        """Test that unauthenticated requests cannot list codes."""
        response = client.get("/admin/auth-codes")

        assert response.status_code == 401


class TestRevokeAuthCode:
    """Tests for revoking authorization codes."""

    def test_admin_can_revoke_code(self, admin_token, admin_user):
        """Test that admin can revoke an authorization code."""
        # Create a code to revoke
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            code = service.create_code(
                created_by=admin_user["user_id"], max_uses=1, notes="To be revoked"
            )
            code_id = code["code_id"]

        # Revoke the code
        response = client.delete(
            f"/admin/auth-codes/{code_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Authorization code revoked successfully"
        assert data["code_id"] == code_id

        # Verify the code is revoked
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            code_data = repo.get_code_by_id(code_id)
            assert code_data["is_active"] == 0

    def test_revoke_nonexistent_code_returns_404(self, admin_token):
        """Test that revoking a nonexistent code returns 404."""
        response = client.delete(
            "/admin/auth-codes/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_regular_user_cannot_revoke_code(self, regular_token, admin_user):
        """Test that regular users cannot revoke authorization codes."""
        # Create a code
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            code = service.create_code(
                created_by=admin_user["user_id"], max_uses=1, notes="Protected code"
            )
            code_id = code["code_id"]

        # Try to revoke as regular user
        response = client.delete(
            f"/admin/auth-codes/{code_id}",
            headers={"Authorization": f"Bearer {regular_token}"},
        )

        assert response.status_code == 403

    def test_unauthenticated_cannot_revoke_code(self):
        """Test that unauthenticated requests cannot revoke codes."""
        response = client.delete("/admin/auth-codes/1")

        assert response.status_code == 401


class TestGetCodeUsageHistory:
    """Tests for viewing authorization code usage history."""

    def test_admin_can_view_usage_history(self, admin_token, admin_user):
        """Test that admin can view usage history for a code."""
        # Create a code and use it for registration
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            code = service.create_code(
                created_by=admin_user["user_id"],
                max_uses=3,
                notes="Multi-use test code",
            )
            code_id = code["code_id"]
            code_formatted = code["code_formatted"]

        # Register a user with the code
        client.post(
            "/auth/register",
            json={
                "username": "usagetest1",
                "email": "usagetest1@example.com",
                "password": "securePassword123",
                "auth_code": code_formatted,
            },
        )

        # Get usage history
        response = client.get(
            f"/admin/auth-codes/{code_id}/usage",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code_id"] == code_id
        assert "usage_history" in data
        assert data["total_uses"] >= 1

        # Verify the usage record contains expected fields
        if data["total_uses"] > 0:
            usage = data["usage_history"][0]
            assert "user_id" in usage
            assert "used_at" in usage

    def test_usage_history_shows_multiple_uses(self, admin_token, admin_user):
        """Test that usage history shows all uses of a multi-use code."""
        # Create a multi-use code
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            code = service.create_code(
                created_by=admin_user["user_id"], max_uses=3, notes="Multi-use code"
            )
            code_id = code["code_id"]
            code_formatted = code["code_formatted"]

        # Register multiple users with the code
        for i in range(2):
            client.post(
                "/auth/register",
                json={
                    "username": f"multitest{i}",
                    "email": f"multitest{i}@example.com",
                    "password": "securePassword123",
                    "auth_code": code_formatted,
                },
            )

        # Get usage history
        response = client.get(
            f"/admin/auth-codes/{code_id}/usage",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_uses"] >= 2

    def test_unused_code_has_empty_history(self, admin_token, admin_user):
        """Test that an unused code has empty usage history."""
        # Create a code but don't use it
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            code = service.create_code(
                created_by=admin_user["user_id"], max_uses=1, notes="Unused code"
            )
            code_id = code["code_id"]

        # Get usage history
        response = client.get(
            f"/admin/auth-codes/{code_id}/usage",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_uses"] == 0
        assert len(data["usage_history"]) == 0

    def test_regular_user_cannot_view_usage_history(self, regular_token, admin_user):
        """Test that regular users cannot view usage history."""
        # Create a code
        with get_db_connection() as conn:
            repo = AuthCodeRepository(conn)
            service = AuthCodeService(repo)

            code = service.create_code(
                created_by=admin_user["user_id"], max_uses=1, notes="Protected code"
            )
            code_id = code["code_id"]

        # Try to view usage history as regular user
        response = client.get(
            f"/admin/auth-codes/{code_id}/usage",
            headers={"Authorization": f"Bearer {regular_token}"},
        )

        assert response.status_code == 403

    def test_unauthenticated_cannot_view_usage_history(self):
        """Test that unauthenticated requests cannot view usage history."""
        response = client.get("/admin/auth-codes/1/usage")

        assert response.status_code == 401
