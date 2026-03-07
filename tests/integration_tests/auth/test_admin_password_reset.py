"""Integration tests for admin fallback password reset flow."""

import re

from fastapi.testclient import TestClient

from minutes_iq.auth.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from minutes_iq.db.client import get_db_connection
from minutes_iq.db.password_reset_repository import PasswordResetRepository
from minutes_iq.db.password_reset_service import PasswordResetService
from minutes_iq.db.user_repository import UserRepository
from minutes_iq.main import app

client = TestClient(app)


def _create_user_with_password(username: str, email: str, password: str, role_id: int):
    with get_db_connection() as conn:
        user_repo = UserRepository(conn)
        user = user_repo.create_user(username=username, email=email, role_id=role_id)
        hashed_password = get_password_hash(password)
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


def _has_temp_password_complexity(password: str) -> bool:
    return (
        len(password) >= 12
        and bool(re.search(r"[a-z]", password))
        and bool(re.search(r"[A-Z]", password))
        and bool(re.search(r"\d", password))
        and bool(re.search(r"[^A-Za-z0-9]", password))
    )


def test_admin_reset_password_flow_sets_force_flag_and_clears_on_change():
    admin_user = _create_user_with_password(
        username="admin_reset",
        email="admin.reset@test.com",
        password="AdminPass123",
        role_id=1,
    )
    target_user = _create_user_with_password(
        username="target_reset",
        email="target.reset@test.com",
        password="StartPass123",
        role_id=2,
    )

    with get_db_connection() as conn:
        reset_repo = PasswordResetRepository(conn)
        reset_service = PasswordResetService(reset_repo, UserRepository(conn))
        created, _, _ = reset_service.create_reset_token(target_user["email"])
        assert created is True

    admin_token = create_access_token(data={"sub": str(admin_user["user_id"])})

    reset_response = client.post(
        "/admin/reset-user-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": target_user["email"]},
    )

    assert reset_response.status_code == 200
    reset_data = reset_response.json()
    assert reset_data["message"] == "Temporary password generated"
    temporary_password = reset_data["temporary_password"]
    assert _has_temp_password_complexity(temporary_password)

    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT u.force_password_change, ac.hashed_password
            FROM users u
            JOIN auth_credentials ac ON ac.user_id = u.user_id
            WHERE u.user_id = ? AND ac.provider_id = 1 AND ac.is_active = 1;
            """,
            (target_user["user_id"],),
        ).fetchone()
        assert row is not None
        assert row[0] == 1
        assert verify_password(temporary_password, row[1])

        valid_token_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM password_reset_tokens
            WHERE user_id = ? AND is_valid = 1;
            """,
            (target_user["user_id"],),
        ).fetchone()[0]
        assert valid_token_count == 0

    login_response = client.post(
        "/auth/login",
        data={"username": target_user["username"], "password": temporary_password},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["force_password_change"] is True

    user_token = login_data["access_token"]
    change_response = client.post(
        "/change-password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "current_password": temporary_password,
            "new_password": "NewPass1234",
            "confirm_password": "NewPass1234",
        },
    )
    assert change_response.status_code == 200

    with get_db_connection() as conn:
        force_flag = conn.execute(
            "SELECT force_password_change FROM users WHERE user_id = ?;",
            (target_user["user_id"],),
        ).fetchone()[0]
        assert force_flag == 0


def test_non_admin_cannot_reset_user_password():
    regular_user = _create_user_with_password(
        username="regular_reset",
        email="regular.reset@test.com",
        password="RegularPass123",
        role_id=2,
    )
    target_user = _create_user_with_password(
        username="target_regular_reset",
        email="target.regular.reset@test.com",
        password="StartPass123",
        role_id=2,
    )

    regular_token = create_access_token(data={"sub": str(regular_user["user_id"])})

    response = client.post(
        "/admin/reset-user-password",
        headers={"Authorization": f"Bearer {regular_token}"},
        json={"email": target_user["email"]},
    )

    assert response.status_code == 403
