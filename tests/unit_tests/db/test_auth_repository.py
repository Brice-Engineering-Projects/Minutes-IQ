"""Unit tests for AuthRepository schema compatibility behavior."""

from minutes_iq.db.auth_repository import AuthRepository


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _FallbackConnection:
    """Simulates a DB missing users.force_password_change on first query."""

    def __init__(self, expected_row):
        self.expected_row = expected_row
        self.execute_calls = 0

    def execute(self, query, params):
        self.execute_calls += 1

        if self.execute_calls == 1:
            raise ValueError(
                'Hrana: `stream error: `Error { message: "SQLite input error: no such column: u.force_password_change", code: "SQL_INPUT_ERROR" }``'
            )

        # Second query should use the backward-compatible fallback
        assert "0 AS force_password_change" in query
        assert params == ("admin", "password")
        return _FakeCursor(self.expected_row)


def test_get_credentials_by_username_falls_back_when_force_password_change_missing():
    conn = _FallbackConnection(
        expected_row=(
            "hashed",
            1,
            "admin",
            "admin@example.com",
            1,
            0,
        )
    )
    repo = AuthRepository(conn)

    credential = repo.get_credentials_by_username("admin")

    assert conn.execute_calls == 2
    assert credential is not None
    assert credential["username"] == "admin"
    assert credential["force_password_change"] == 0
