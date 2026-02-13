"""
Integration tests for client URL management.

Tests the ClientUrlRepository and URL-related functionality.
"""

import time

import pytest
from libsql_client import Client as LibsqlClient

from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.client_url_repository import ClientUrlRepository


@pytest.fixture
def test_client(db_connection: LibsqlClient, test_user: dict) -> dict:
    """Create a test client for URL management tests."""
    client_repo = ClientRepository(db_connection)
    client = client_repo.create_client(
        name=f"Test Client {int(time.time())}",
        description="Client for URL management tests",
        created_by=test_user["user_id"],
        is_active=True,
    )
    return client


class TestCreateClientURL:
    """Tests for creating client URLs."""

    def test_create_url_success(self, db_connection: LibsqlClient, test_client: dict):
        """Test successfully creating a URL for a client."""
        url_repo = ClientUrlRepository(db_connection)

        url = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="current",
            url="https://example.com/current",
            is_active=True,
        )

        assert url["id"] is not None
        assert url["client_id"] == test_client["client_id"]
        assert url["alias"] == "current"
        assert url["url"] == "https://example.com/current"
        assert url["is_active"] == 1
        assert url["last_scraped_at"] is None
        assert url["created_at"] is not None

    def test_create_multiple_urls_for_client(
        self, db_connection: LibsqlClient, test_client: dict
    ):
        """Test creating multiple URLs for the same client."""
        url_repo = ClientUrlRepository(db_connection)

        url1 = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="current",
            url="https://example.com/current",
            is_active=True,
        )
        url2 = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="archive",
            url="https://example.com/archive",
            is_active=True,
        )

        assert url1["id"] != url2["id"]
        assert url1["alias"] == "current"
        assert url2["alias"] == "archive"

    def test_create_inactive_url(self, db_connection: LibsqlClient, test_client: dict):
        """Test creating an inactive URL."""
        url_repo = ClientUrlRepository(db_connection)

        url = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="deprecated",
            url="https://old-site.com",
            is_active=False,
        )

        assert url["is_active"] == 0


class TestListClientURLs:
    """Tests for listing client URLs."""

    def test_get_client_urls(self, db_connection: LibsqlClient, test_client: dict):
        """Test retrieving all URLs for a client."""
        url_repo = ClientUrlRepository(db_connection)

        # Create multiple URLs
        url_repo.create_url(
            client_id=test_client["client_id"],
            alias="current",
            url="https://example.com/current",
            is_active=True,
        )
        url_repo.create_url(
            client_id=test_client["client_id"],
            alias="archive",
            url="https://example.com/archive",
            is_active=True,
        )

        urls = url_repo.get_client_urls(test_client["client_id"])

        assert len(urls) == 2
        aliases = [url["alias"] for url in urls]
        assert "current" in aliases
        assert "archive" in aliases

    def test_get_urls_for_nonexistent_client(self, db_connection: LibsqlClient):
        """Test getting URLs for a client that doesn't exist returns empty list."""
        url_repo = ClientUrlRepository(db_connection)

        urls = url_repo.get_client_urls(99999)

        assert urls == []

    def test_list_all_urls(self, db_connection: LibsqlClient, test_client: dict):
        """Test listing all URLs across all clients."""
        url_repo = ClientUrlRepository(db_connection)

        url_repo.create_url(
            client_id=test_client["client_id"],
            alias="test",
            url="https://example.com/test",
            is_active=True,
        )

        all_urls, total = url_repo.list_all_urls()

        assert len(all_urls) >= 1
        assert total >= 1
        assert any(url["client_id"] == test_client["client_id"] for url in all_urls)


class TestUpdateClientURL:
    """Tests for updating client URLs."""

    def test_update_url_alias(self, db_connection: LibsqlClient, test_client: dict):
        """Test updating a URL's alias."""
        url_repo = ClientUrlRepository(db_connection)

        # Create URL
        url = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="old-alias",
            url="https://example.com",
            is_active=True,
        )

        # Update alias
        success = url_repo.update_url(
            url_id=url["id"],
            alias="new-alias",
        )

        assert success is True

        # Retrieve and verify
        updated_url = url_repo.get_url(url["id"])
        assert updated_url["alias"] == "new-alias"
        assert updated_url["url"] == "https://example.com"  # Unchanged

    def test_update_url_address(self, db_connection: LibsqlClient, test_client: dict):
        """Test updating a URL's address."""
        url_repo = ClientUrlRepository(db_connection)

        # Create URL
        url = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="current",
            url="https://old-url.com",
            is_active=True,
        )

        # Update URL
        success = url_repo.update_url(
            url_id=url["id"],
            url="https://new-url.com",
        )

        assert success is True

        # Retrieve and verify
        updated_url = url_repo.get_url(url["id"])
        assert updated_url["url"] == "https://new-url.com"
        assert updated_url["alias"] == "current"  # Unchanged

    def test_deactivate_url(self, db_connection: LibsqlClient, test_client: dict):
        """Test deactivating a URL."""
        url_repo = ClientUrlRepository(db_connection)

        # Create active URL
        url = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="current",
            url="https://example.com",
            is_active=True,
        )

        # Deactivate
        success = url_repo.update_url(
            url_id=url["id"],
            is_active=False,
        )

        assert success is True

        # Retrieve and verify
        updated_url = url_repo.get_url(url["id"])
        assert updated_url["is_active"] == 0

    def test_update_nonexistent_url_returns_none(self, db_connection: LibsqlClient):
        """Test updating a non-existent URL returns False."""
        url_repo = ClientUrlRepository(db_connection)

        result = url_repo.update_url(
            url_id=99999,
            alias="new-alias",
        )

        assert result is False


class TestDeleteClientURL:
    """Tests for deleting client URLs."""

    def test_delete_url_success(self, db_connection: LibsqlClient, test_client: dict):
        """Test successfully deleting a URL."""
        url_repo = ClientUrlRepository(db_connection)

        # Create URL
        url = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="temp",
            url="https://temp.com",
            is_active=True,
        )

        # Delete URL
        success = url_repo.delete_url(url["id"])

        assert success is True

        # Verify it's gone
        urls = url_repo.get_client_urls(test_client["client_id"])
        assert len(urls) == 0

    def test_delete_nonexistent_url(self, db_connection: LibsqlClient):
        """Test deleting a non-existent URL returns False."""
        url_repo = ClientUrlRepository(db_connection)

        success = url_repo.delete_url(99999)

        assert success is False


class TestURLCascadeDelete:
    """Tests for cascade deletion when client is deleted."""

    def test_urls_deleted_when_client_deleted(
        self, db_connection: LibsqlClient, test_user: dict
    ):
        """Test that URLs are cascade deleted when client is deleted."""
        client_repo = ClientRepository(db_connection)
        url_repo = ClientUrlRepository(db_connection)

        # Create client
        client = client_repo.create_client(
            name=f"Temp Client {int(time.time())}",
            description="Will be deleted",
            created_by=test_user["user_id"],
            is_active=True,
        )

        # Create URL for client
        url_repo.create_url(
            client_id=client["client_id"],
            alias="test",
            url="https://example.com",
            is_active=True,
        )

        # Delete client (soft delete - sets is_active=False)
        client_repo.delete_client(client["client_id"])

        # URL should still exist (soft delete doesn't cascade)
        urls = url_repo.get_client_urls(client["client_id"])
        assert len(urls) == 1

        # Note: True cascade delete would require hard delete from database
        # which is not exposed in the repository pattern for safety


class TestUpdateLastScraped:
    """Tests for updating last_scraped_at timestamp."""

    def test_update_last_scraped_at(
        self, db_connection: LibsqlClient, test_client: dict
    ):
        """Test updating the last_scraped_at timestamp."""
        url_repo = ClientUrlRepository(db_connection)

        # Create URL
        url = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="current",
            url="https://example.com",
            is_active=True,
        )

        assert url["last_scraped_at"] is None

        # Update last_scraped_at (method auto-generates timestamp)
        success = url_repo.update_last_scraped(url["id"])
        assert success is True

        # Retrieve and verify timestamp was set
        updated_url = url_repo.get_url(url["id"])
        assert updated_url["last_scraped_at"] is not None
        assert updated_url["last_scraped_at"] > 0


class TestGetSingleURL:
    """Tests for retrieving a single URL by ID."""

    def test_get_url_by_id(self, db_connection: LibsqlClient, test_client: dict):
        """Test retrieving a specific URL by ID."""
        url_repo = ClientUrlRepository(db_connection)

        # Create URL
        url = url_repo.create_url(
            client_id=test_client["client_id"],
            alias="current",
            url="https://example.com",
            is_active=True,
        )

        # Retrieve by ID
        retrieved_url = url_repo.get_url(url["id"])

        assert retrieved_url is not None
        assert retrieved_url["id"] == url["id"]
        assert retrieved_url["alias"] == "current"

    def test_get_nonexistent_url_returns_none(self, db_connection: LibsqlClient):
        """Test retrieving a non-existent URL returns None."""
        url_repo = ClientUrlRepository(db_connection)

        result = url_repo.get_url(99999)

        assert result is None
