"""
Shared pytest fixtures for all tests.
"""

import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from libsql_experimental import connect

from jea_meeting_web_scraper.auth.security import get_password_hash
from jea_meeting_web_scraper.config.settings import settings
from jea_meeting_web_scraper.main import app


@pytest.fixture(scope="session")
def test_db_file() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="session")
def test_db_connection(test_db_file):
    """
    Create a test database with schema.
    This is session-scoped to avoid recreating the schema for every test.
    """
    conn = connect(f"file:{test_db_file}")

    # Create schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY,
            role_name TEXT NOT NULL UNIQUE
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(role_id)
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_providers (
            provider_id INTEGER PRIMARY KEY,
            provider_name TEXT NOT NULL UNIQUE
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_credentials (
            credential_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider_id INTEGER NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (provider_id) REFERENCES auth_providers(provider_id)
        );
    """)

    # Create auth_codes table (Phase 3)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_codes (
            code_id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            created_by INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER,
            max_uses INTEGER DEFAULT 1,
            current_uses INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );
    """)

    # Create code_usage table (Phase 3)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS code_usage (
            usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            used_at INTEGER NOT NULL,
            FOREIGN KEY (code_id) REFERENCES auth_codes(code_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

    # Create password_reset_tokens table (Phase 4)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at INTEGER,
            is_valid INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)

    # Create clients table (Phase 5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            website_url TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            updated_at INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );
    """)

    # Create keywords table (Phase 5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            category TEXT,
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );
    """)

    # Create client_keywords table (Phase 5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS client_keywords (
            client_id INTEGER NOT NULL,
            keyword_id INTEGER NOT NULL,
            added_at INTEGER NOT NULL,
            added_by INTEGER NOT NULL,
            PRIMARY KEY (client_id, keyword_id),
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE CASCADE,
            FOREIGN KEY (added_by) REFERENCES users(user_id)
        );
    """)

    # Create user_client_favorites table (Phase 5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_client_favorites (
            user_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            favorited_at INTEGER NOT NULL,
            PRIMARY KEY (user_id, client_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
        );
    """)

    # Create client_sources table (Phase 5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS client_sources (
            source_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_type TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            scrape_frequency TEXT,
            last_scraped_at INTEGER,
            created_at INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );
    """)

    # Seed reference data
    conn.execute(
        "INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (1, 'admin');"
    )
    conn.execute("INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (2, 'user');")
    conn.execute(
        "INSERT OR IGNORE INTO auth_providers (provider_id, provider_name) VALUES (1, 'password');"
    )

    conn.commit()
    conn.close()

    return test_db_file


@pytest.fixture(autouse=True)
def setup_test_db(test_db_connection, monkeypatch):
    """
    Setup test database for all tests.
    Monkeypatches the db client to use the test database.
    This runs automatically for all tests.
    """

    def mock_get_db_connection():
        """Return a connection to the test database."""
        conn = connect(f"file:{test_db_connection}")
        try:
            yield conn
        finally:
            conn.close()

    # Monkeypatch the database connection function
    monkeypatch.setattr(
        "jea_meeting_web_scraper.db.client.get_db_connection", mock_get_db_connection
    )

    # Also patch the database URL in settings
    monkeypatch.setattr(settings.database, "db_url", f"file:{test_db_connection}")

    # Clean database before each test (order matters for foreign keys)
    conn = connect(f"file:{test_db_connection}")
    conn.execute("DELETE FROM client_sources;")
    conn.execute("DELETE FROM user_client_favorites;")
    conn.execute("DELETE FROM client_keywords;")
    conn.execute("DELETE FROM keywords;")
    conn.execute("DELETE FROM clients;")
    conn.execute("DELETE FROM password_reset_tokens;")
    conn.execute("DELETE FROM code_usage;")
    conn.execute("DELETE FROM auth_codes;")
    conn.execute("DELETE FROM auth_credentials;")
    conn.execute("DELETE FROM users;")
    conn.commit()
    conn.close()


@pytest.fixture
def db_connection(test_db_connection):
    """Provide a database connection for tests that need direct DB access."""
    conn = connect(f"file:{test_db_connection}")
    yield conn
    conn.close()


@pytest.fixture
def clean_db(test_db_connection):
    """Clean the database before a test (explicit fixture for tests that need it)."""
    conn = connect(f"file:{test_db_connection}")
    conn.execute("DELETE FROM client_sources;")
    conn.execute("DELETE FROM user_client_favorites;")
    conn.execute("DELETE FROM client_keywords;")
    conn.execute("DELETE FROM keywords;")
    conn.execute("DELETE FROM clients;")
    conn.execute("DELETE FROM password_reset_tokens;")
    conn.execute("DELETE FROM code_usage;")
    conn.execute("DELETE FROM auth_codes;")
    conn.execute("DELETE FROM auth_credentials;")
    conn.execute("DELETE FROM users;")
    conn.commit()
    conn.close()


@pytest.fixture
def test_user(test_db_connection):
    """Create a test user in the database."""
    conn = connect(f"file:{test_db_connection}")

    # Create user
    cursor = conn.execute(
        "INSERT INTO users (username, email, role_id) VALUES (?, ?, ?) RETURNING user_id;",
        ("testuser", "test@example.com", 2),
    )
    user_id = cursor.fetchone()[0]
    cursor.close()  # Close cursor before next statement

    # Create password credential
    hashed_password = get_password_hash("secret")
    cursor2 = conn.execute(
        "INSERT INTO auth_credentials (user_id, provider_id, hashed_password, is_active) VALUES (?, ?, ?, ?);",
        (user_id, 1, hashed_password, 1),
    )
    cursor2.close()  # Close cursor before commit

    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "username": "testuser",
        "email": "test@example.com",
        "role_id": 2,
        "password": "secret",  # Plain text for testing
    }


@pytest.fixture
def client():
    """Create a test client with the test database."""
    return TestClient(app)


@pytest.fixture
def test_user_credentials():
    """Provide test user credentials for login."""
    return {"username": "testuser", "password": "secret"}


@pytest.fixture
def admin_token(client: TestClient, test_db_connection):
    """Create an admin user and return their auth token."""
    from jea_meeting_web_scraper.auth.security import get_password_hash

    conn = connect(f"file:{test_db_connection}")

    # Create admin user (role_id=1 is admin)
    hashed_password = get_password_hash("adminpass")
    cursor = conn.execute(
        "INSERT INTO users (username, email, role_id) VALUES (?, ?, ?);",
        ("admin", "admin@example.com", 1),
    )
    admin_id = cursor.lastrowid
    conn.execute(
        "INSERT INTO auth_credentials (user_id, provider_id, hashed_password) VALUES (?, ?, ?);",
        (admin_id, 1, hashed_password),
    )
    conn.commit()
    conn.close()

    # Login to get token
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "adminpass"},
    )
    return response.json()["access_token"]


@pytest.fixture
def user_token(client: TestClient, test_user, test_user_credentials):
    """Return auth token for regular test user."""
    response = client.post(
        "/auth/login",
        data={
            "username": test_user_credentials["username"],
            "password": test_user_credentials["password"],
        },
    )
    return response.json()["access_token"]
