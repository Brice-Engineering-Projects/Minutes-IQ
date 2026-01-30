"""
Integration tests for storage management API endpoints.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from minutes_iq.main import app
from minutes_iq.scraper.storage import StorageManager


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def storage_manager(temp_storage):
    """Create StorageManager with temporary directory."""
    return StorageManager(base_dir=temp_storage)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token(test_db):
    """Get admin authentication token."""
    # Use the existing admin from conftest
    from minutes_iq.auth.security import create_access_token

    return create_access_token(
        data={"sub": "admin@test.com", "user_id": 1, "is_admin": True}
    )


@pytest.fixture
def regular_user_token(test_db):
    """Get regular user authentication token."""
    from minutes_iq.auth.security import create_access_token

    return create_access_token(
        data={"sub": "user@test.com", "user_id": 2, "is_admin": False}
    )


class TestStorageCleanupAPI:
    """Tests for storage cleanup endpoints."""

    def test_cleanup_job_files_admin_success(
        self, client, admin_token, test_db, temp_storage
    ):
        """Test admin can cleanup job files."""
        from minutes_iq.db.client import get_db_connection
        from minutes_iq.db.scraper_repository import ScraperRepository
        from minutes_iq.db.scraper_service import ScraperService

        # Create a test job
        conn = get_db_connection()
        repo = ScraperRepository(conn)
        service = ScraperService(repo)

        job_id = service.create_scrape_job(
            client_id=1,
            created_by=1,
            date_range_start="2024-01",
            date_range_end="2024-12",
        )

        # Create some test files
        manager = StorageManager(base_dir=temp_storage)
        manager.ensure_job_directories(job_id)

        raw_pdf_dir = manager.get_raw_pdf_dir(job_id)
        (raw_pdf_dir / "test.pdf").write_text("pdf content")

        # Mock the storage manager dependency
        from unittest.mock import patch

        with patch(
            "minutes_iq.scraper.routes.get_storage_manager", return_value=manager
        ):
            response = client.delete(
                f"/scraper/jobs/{job_id}/cleanup",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["files_deleted"]["raw_pdfs"] == 1

    def test_cleanup_job_files_non_admin_forbidden(
        self, client, regular_user_token, test_db
    ):
        """Test non-admin cannot cleanup job files."""
        response = client.delete(
            "/scraper/jobs/1/cleanup",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )

        assert response.status_code == 403
        assert "Only administrators" in response.json()["detail"]

    def test_cleanup_job_files_no_auth(self, client):
        """Test cleanup requires authentication."""
        response = client.delete("/scraper/jobs/1/cleanup")

        assert response.status_code == 401

    def test_cleanup_job_not_found(self, client, admin_token, test_db, temp_storage):
        """Test cleanup for non-existent job."""
        manager = StorageManager(base_dir=temp_storage)

        from unittest.mock import patch

        with patch(
            "minutes_iq.scraper.routes.get_storage_manager", return_value=manager
        ):
            response = client.delete(
                "/scraper/jobs/99999/cleanup",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_cleanup_job_exclude_artifacts(
        self, client, admin_token, test_db, temp_storage
    ):
        """Test cleanup with exclude artifacts option."""
        from minutes_iq.db.client import get_db_connection
        from minutes_iq.db.scraper_repository import ScraperRepository
        from minutes_iq.db.scraper_service import ScraperService

        # Create a test job
        conn = get_db_connection()
        repo = ScraperRepository(conn)
        service = ScraperService(repo)

        job_id = service.create_scrape_job(
            client_id=1, created_by=1, date_range_start="2024-01"
        )

        # Create test files including artifacts
        manager = StorageManager(base_dir=temp_storage)
        manager.ensure_job_directories(job_id)

        (manager.get_raw_pdf_dir(job_id) / "test.pdf").write_text("pdf")
        (manager.get_artifacts_dir(job_id) / "artifact.zip").write_text("zip")

        # Cleanup without artifacts
        from unittest.mock import patch

        with patch(
            "minutes_iq.scraper.routes.get_storage_manager", return_value=manager
        ):
            response = client.delete(
                f"/scraper/jobs/{job_id}/cleanup?include_artifacts=false",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["files_deleted"]["raw_pdfs"] == 1
        assert data["files_deleted"]["artifacts"] == 0

        # Verify artifacts still exist
        assert (manager.get_artifacts_dir(job_id) / "artifact.zip").exists()


class TestStorageStatsAPI:
    """Tests for storage statistics endpoints."""

    def test_get_storage_stats_admin_success(
        self, client, admin_token, test_db, temp_storage
    ):
        """Test admin can get storage statistics."""
        # Create some test files
        manager = StorageManager(base_dir=temp_storage)
        manager.ensure_job_directories(100)

        (manager.get_raw_pdf_dir(100) / "test.pdf").write_bytes(b"x" * 1000)
        (manager.get_annotated_pdf_dir(100) / "test_annotated.pdf").write_bytes(
            b"y" * 2000
        )

        # Get stats
        from unittest.mock import patch

        with patch(
            "minutes_iq.scraper.routes.get_storage_manager", return_value=manager
        ):
            response = client.get(
                "/scraper/storage/stats",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()

        assert "raw_pdfs" in data
        assert "annotated_pdfs" in data
        assert "artifacts" in data
        assert "total_size_bytes" in data

        assert data["raw_pdfs"]["size_bytes"] == 1000
        assert data["raw_pdfs"]["file_count"] == 1
        assert data["raw_pdfs"]["job_count"] == 1

        assert data["annotated_pdfs"]["size_bytes"] == 2000
        assert data["annotated_pdfs"]["file_count"] == 1

    def test_get_storage_stats_non_admin_forbidden(
        self, client, regular_user_token, test_db
    ):
        """Test non-admin cannot get storage statistics."""
        response = client.get(
            "/scraper/storage/stats",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )

        assert response.status_code == 403
        assert "Only administrators" in response.json()["detail"]

    def test_get_storage_stats_no_auth(self, client):
        """Test storage stats requires authentication."""
        response = client.get("/scraper/storage/stats")

        assert response.status_code == 401

    def test_get_storage_stats_empty(self, client, admin_token, test_db, temp_storage):
        """Test getting stats with no files."""
        manager = StorageManager(base_dir=temp_storage)

        from unittest.mock import patch

        with patch(
            "minutes_iq.scraper.routes.get_storage_manager", return_value=manager
        ):
            response = client.get(
                "/scraper/storage/stats",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["raw_pdfs"]["size_bytes"] == 0
        assert data["raw_pdfs"]["file_count"] == 0
        assert data["annotated_pdfs"]["size_bytes"] == 0
        assert data["artifacts"]["size_bytes"] == 0

    def test_get_storage_stats_multiple_jobs(
        self, client, admin_token, test_db, temp_storage
    ):
        """Test stats with multiple jobs."""
        manager = StorageManager(base_dir=temp_storage)

        # Create files for 3 jobs
        for job_id in [201, 202, 203]:
            manager.ensure_job_directories(job_id)
            (manager.get_raw_pdf_dir(job_id) / f"job{job_id}.pdf").write_bytes(
                b"x" * 500
            )

        from unittest.mock import patch

        with patch(
            "minutes_iq.scraper.routes.get_storage_manager", return_value=manager
        ):
            response = client.get(
                "/scraper/storage/stats",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["raw_pdfs"]["size_bytes"] == 1500  # 3 jobs * 500 bytes
        assert data["raw_pdfs"]["file_count"] == 3
        assert data["raw_pdfs"]["job_count"] == 3
