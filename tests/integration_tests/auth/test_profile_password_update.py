"""Integration tests for profile password update flow."""

from fastapi.testclient import TestClient

from minutes_iq.auth.security import get_password_hash, verify_password
from minutes_iq.db.client import get_db_connection
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


def test_profile_password_update_persists_and_allows_new_login():
    user = _create_user_with_password(
        username="profile_pw_user",
        email="profile.pw.user@test.com",
        password="StartPass123",
        role_id=2,
    )

    initial_login = client.post(
        "/auth/login",
        data={"username": user["username"], "password": "StartPass123"},
    )
    assert initial_login.status_code == 200
    user_token = initial_login.json()["access_token"]

    update_response = client.put(
        "/api/profile/update-password",
        headers={"Authorization": f"Bearer {user_token}"},
        data={
            "current_password": "StartPass123",
            "new_password": "BrandNewPass123",
            "confirm_password": "BrandNewPass123",
        },
    )
    assert update_response.status_code == 200
    assert "Password Updated" in update_response.text

    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT hashed_password
            FROM auth_credentials
            WHERE user_id = ? AND provider_id = 1 AND is_active = 1;
            """,
            (user["user_id"],),
        ).fetchone()
        assert row is not None
        assert verify_password("BrandNewPass123", row[0])
        assert not verify_password("StartPass123", row[0])

    new_password_login = client.post(
        "/auth/login",
        data={"username": user["username"], "password": "BrandNewPass123"},
    )
    assert new_password_login.status_code == 200
    assert "access_token" in new_password_login.json()

    old_password_login = client.post(
        "/auth/login",
        data={"username": user["username"], "password": "StartPass123"},
    )
    assert "text/html" in old_password_login.headers.get("content-type", "")
