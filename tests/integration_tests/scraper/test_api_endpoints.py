"""
Integration tests for scraper API endpoints.
Tests authentication, authorization, and full request/response cycles.
"""

import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from minutes_iq.scraper.storage import StorageManager


@pytest.fixture
def sample_scraper_client(db_connection, admin_token):
    """Create a test client with keywords for scraper tests."""
    # Get admin user ID
    cursor = db_connection.execute("SELECT user_id FROM users WHERE username = 'admin'")
    admin_id = cursor.fetchone()[0]
    cursor.close()

    # Create client
    timestamp = int(time.time())
    cursor = db_connection.execute(
        """
        INSERT INTO client (name, description, is_active, created_at, created_by)
        VALUES (?, ?, ?, ?, ?)
        RETURNING client_id
        """,
        ("Scraper Test Client", "Test", 1, timestamp, admin_id),
    )
    client_id = cursor.fetchone()[0]
    cursor.close()

    # Create client URL record; current API uses this ID when creating jobs.
    cursor = db_connection.execute(
        """
        INSERT INTO client_urls (client_id, alias, url, is_active, created_at)
        VALUES (?, ?, ?, ?, ?)
        RETURNING id
        """,
        (client_id, "primary", "https://example.com/meetings", 1, timestamp),
    )
    client_url_id = cursor.fetchone()[0]
    cursor.close()

    # Create keyword
    cursor = db_connection.execute(
        """
        INSERT INTO keywords (keyword, is_active, created_at, created_by)
        VALUES (?, ?, ?, ?)
        RETURNING keyword_id
        """,
        ("testword", 1, timestamp, admin_id),
    )
    keyword_id = cursor.fetchone()[0]
    cursor.close()

    # Link keyword to client
    db_connection.execute(
        """
        INSERT INTO client_keywords (client_id, keyword_id, added_at, added_by)
        VALUES (?, ?, ?, ?)
        """,
        (client_id, keyword_id, timestamp, admin_id),
    )

    db_connection.commit()

    return {
        "client_id": client_url_id,
        "raw_client_id": client_id,
        "keyword_id": keyword_id,
        "admin_id": admin_id,
    }


class TestJobCreationEndpoint:
    """Test POST /scraper/jobs endpoint."""

    def test_create_job_authenticated(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test creating a job with valid authentication."""
        response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "date_range_start": "2024-01",
                "date_range_end": "2024-12",
                "max_scan_pages": 10,
                "include_minutes": True,
                "include_packages": False,
                "source_urls": ["https://example.com/meetings"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_create_job_unauthenticated(
        self, client: TestClient, sample_scraper_client
    ):
        """Test creating a job without authentication."""
        response = client.post(
            "/scraper/jobs",
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com/meetings"],
            },
        )

        assert response.status_code == 401

    def test_create_job_minimal_config(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test creating a job with minimal configuration."""
        response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com/meetings"],
            },
        )

        assert response.status_code == 201


class TestJobListingEndpoint:
    """Test GET /scraper/jobs endpoint."""

    def test_list_jobs_authenticated(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test listing jobs with authentication."""
        # Create a job first
        client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )

        # List jobs
        response = client.get(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert len(data["jobs"]) > 0

    def test_list_jobs_with_status_filter(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test listing jobs filtered by status."""
        response = client.get(
            "/scraper/jobs?status=pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        for job in data["jobs"]:
            assert job["status"] == "pending"

    def test_list_jobs_with_pagination(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test listing jobs with pagination."""
        response = client.get(
            "/scraper/jobs?limit=2&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_list_jobs_unauthenticated(self, client: TestClient):
        """Test listing jobs without authentication."""
        response = client.get("/scraper/jobs")
        assert response.status_code == 401


class TestJobDetailsEndpoint:
    """Test GET /scraper/jobs/{job_id} endpoint."""

    def test_get_job_details_own_job(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test getting details for own job."""
        # Create job
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        # Get details
        response = client.get(
            f"/scraper/jobs/{job_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "config" in data
        assert "statistics" in data

    def test_get_job_details_not_found(self, client: TestClient, admin_token):
        """Test getting details for non-existent job."""
        response = client.get(
            "/scraper/jobs/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    def test_get_job_details_unauthenticated(self, client: TestClient):
        """Test getting job details without authentication."""
        response = client.get("/scraper/jobs/1")
        assert response.status_code == 401


class TestJobCancellationEndpoint:
    """Test DELETE /scraper/jobs/{job_id} endpoint."""

    def test_cancel_own_pending_job(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test cancelling own pending job."""
        # Create job
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        # Cancel job
        response = client.delete(
            f"/scraper/jobs/{job_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 204

    def test_cancel_job_not_found(self, client: TestClient, admin_token):
        """Test cancelling non-existent job."""
        response = client.delete(
            "/scraper/jobs/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    def test_cancel_job_unauthenticated(self, client: TestClient):
        """Test cancelling job without authentication."""
        response = client.delete("/scraper/jobs/1")
        assert response.status_code == 401


class TestJobStatusEndpoint:
    """Test GET /scraper/jobs/{job_id}/status endpoint."""

    def test_get_job_status(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test getting job status."""
        # Create job
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        # Get status
        response = client.get(
            f"/scraper/jobs/{job_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data


class TestResultsEndpoints:
    """Test results-related endpoints."""

    def test_list_results(
        self, client: TestClient, admin_token, sample_scraper_client, db_connection
    ):
        """Test listing results for a job."""
        # Create job
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        # Add a result directly to database
        timestamp = int(time.time())
        db_connection.execute(
            """
            INSERT INTO scrape_results
            (job_id, pdf_filename, page_number, keyword_id, snippet, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                "test.pdf",
                1,
                sample_scraper_client["keyword_id"],
                "Test snippet",
                timestamp,
            ),
        )
        db_connection.commit()

        # List results
        response = client.get(
            f"/scraper/jobs/{job_id}/results",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_list_results_with_pagination(
        self, client: TestClient, admin_token, sample_scraper_client, db_connection
    ):
        """Test listing results with pagination."""
        # Create job and add results
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        # Add multiple results
        timestamp = int(time.time())
        for i in range(5):
            db_connection.execute(
                """
                INSERT INTO scrape_results
                (job_id, pdf_filename, page_number, keyword_id, snippet, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    f"test_{i}.pdf",
                    i + 1,
                    sample_scraper_client["keyword_id"],
                    f"Snippet {i}",
                    timestamp,
                ),
            )
        db_connection.commit()

        # Get first page
        response = client.get(
            f"/scraper/jobs/{job_id}/results?limit=2&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["total"] == 5

    def test_get_results_summary(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test getting results summary."""
        # Create job
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        # Get summary
        response = client.get(
            f"/scraper/jobs/{job_id}/results/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_matches" in data
        assert "unique_pdfs" in data
        assert "keyword_breakdown" in data

    def test_export_results_csv(
        self, client: TestClient, admin_token, sample_scraper_client, db_connection
    ):
        """Test exporting results as CSV."""
        # Create job and add result
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        timestamp = int(time.time())
        db_connection.execute(
            """
            INSERT INTO scrape_results
            (job_id, pdf_filename, page_number, keyword_id, snippet, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                "test.pdf",
                1,
                sample_scraper_client["keyword_id"],
                "Test snippet",
                timestamp,
            ),
        )
        db_connection.commit()

        # Export CSV
        response = client.get(
            f"/scraper/jobs/{job_id}/results/export",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

    def test_export_results_csv_no_results(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test exporting CSV with no results."""
        # Create job without results
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        # Export CSV
        response = client.get(
            f"/scraper/jobs/{job_id}/results/export",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404


class TestArtifactEndpoints:
    """Test artifact generation endpoints."""

    def test_create_artifact_not_implemented(
        self, client: TestClient, admin_token, sample_scraper_client
    ):
        """Test that artifact creation returns 501 (not yet implemented)."""
        # Create job
        create_response = client.post(
            "/scraper/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "client_id": sample_scraper_client["client_id"],
                "source_urls": ["https://example.com"],
            },
        )
        job_id = create_response.json()["job_id"]

        # Try to create artifact
        response = client.post(
            f"/scraper/jobs/{job_id}/artifacts",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "include_raw_pdfs": True,
                "include_annotated_pdfs": True,
                "include_csv": True,
                "include_metadata": True,
            },
        )

        assert response.status_code == 501  # Not implemented


class TestDownloadResultsEndpoint:
    """Test GET /download-results/{job_id} endpoint."""

    def _create_test_pdf(self, file_path: Path, text: str) -> None:
        import fitz

        file_path.parent.mkdir(parents=True, exist_ok=True)
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text)
        doc.save(file_path)
        doc.close()

    def test_download_results_zip_success_and_grouped_by_page(
        self,
        client: TestClient,
        admin_token,
        sample_scraper_client,
        db_connection,
        tmp_path,
    ):
        """Returns ZIP and produces one output page per (pdf, page)."""
        # Route uses StorageManager(base_dir="data") by default; override to isolated tmp storage.
        from minutes_iq.main import app
        from minutes_iq.scraper.routes import get_storage_manager

        app.dependency_overrides[get_storage_manager] = lambda: StorageManager(
            base_dir=tmp_path
        )

        try:
            create_response = client.post(
                "/scraper/jobs",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "client_id": sample_scraper_client["client_id"],
                    "source_urls": ["https://example.com"],
                },
            )
            job_id = create_response.json()["job_id"]

            raw_pdf_path = tmp_path / "raw_pdfs" / str(job_id) / "meeting.pdf"
            self._create_test_pdf(
                raw_pdf_path,
                "Stormwater improvements and lift station upgrade discussion.",
            )

            timestamp = int(time.time())
            # Two matches on same page should produce a single output PDF page.
            db_connection.execute(
                """
                INSERT INTO scrape_results
                (job_id, pdf_filename, page_number, keyword_id, snippet, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    "meeting.pdf",
                    1,
                    sample_scraper_client["keyword_id"],
                    "Stormwater improvements",
                    timestamp,
                ),
            )
            db_connection.execute(
                """
                INSERT INTO scrape_results
                (job_id, pdf_filename, page_number, keyword_id, snippet, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    "meeting.pdf",
                    1,
                    sample_scraper_client["keyword_id"],
                    "lift station upgrade",
                    timestamp + 1,
                ),
            )
            db_connection.commit()

            response = client.get(
                f"/download-results/{job_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"

            zip_out = tmp_path / "result.zip"
            zip_out.write_bytes(response.content)
            with zipfile.ZipFile(zip_out, "r") as archive:
                names = archive.namelist()
                assert len(names) == 1
                assert names[0].startswith("meeting_page_1_")
                assert names[0].endswith(".pdf")
        finally:
            app.dependency_overrides.pop(get_storage_manager, None)

    def test_download_results_zip_includes_page_when_no_highlight_match(
        self,
        client: TestClient,
        admin_token,
        sample_scraper_client,
        db_connection,
        tmp_path,
    ):
        """Includes the relevant page even when snippet and keyword search both fail."""
        from minutes_iq.main import app
        from minutes_iq.scraper.routes import get_storage_manager

        app.dependency_overrides[get_storage_manager] = lambda: StorageManager(
            base_dir=tmp_path
        )

        try:
            create_response = client.post(
                "/scraper/jobs",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "client_id": sample_scraper_client["client_id"],
                    "source_urls": ["https://example.com"],
                },
            )
            job_id = create_response.json()["job_id"]

            raw_pdf_path = tmp_path / "raw_pdfs" / str(job_id) / "notes.pdf"
            self._create_test_pdf(raw_pdf_path, "Completely unrelated text content.")

            timestamp = int(time.time())
            db_connection.execute(
                """
                INSERT INTO scrape_results
                (job_id, pdf_filename, page_number, keyword_id, snippet, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    "notes.pdf",
                    1,
                    sample_scraper_client["keyword_id"],
                    "this snippet is not present",
                    timestamp,
                ),
            )
            db_connection.commit()

            response = client.get(
                f"/download-results/{job_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200

            zip_out = tmp_path / "result_no_highlight.zip"
            zip_out.write_bytes(response.content)
            with zipfile.ZipFile(zip_out, "r") as archive:
                names = archive.namelist()
                assert len(names) == 1
                assert names[0].startswith("notes_page_1_")
        finally:
            app.dependency_overrides.pop(get_storage_manager, None)

    def test_download_results_zip_forbidden_for_non_owner(
        self,
        client: TestClient,
        admin_token,
        user_token,
        sample_scraper_client,
        db_connection,
        tmp_path,
    ):
        """Regular users cannot download artifacts for jobs they do not own."""
        from minutes_iq.main import app
        from minutes_iq.scraper.routes import get_storage_manager

        app.dependency_overrides[get_storage_manager] = lambda: StorageManager(
            base_dir=tmp_path
        )

        try:
            create_response = client.post(
                "/scraper/jobs",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "client_id": sample_scraper_client["client_id"],
                    "source_urls": ["https://example.com"],
                },
            )
            job_id = create_response.json()["job_id"]

            raw_pdf_path = tmp_path / "raw_pdfs" / str(job_id) / "secured.pdf"
            self._create_test_pdf(raw_pdf_path, "Protected content.")

            timestamp = int(time.time())
            db_connection.execute(
                """
                INSERT INTO scrape_results
                (job_id, pdf_filename, page_number, keyword_id, snippet, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    "secured.pdf",
                    1,
                    sample_scraper_client["keyword_id"],
                    "Protected",
                    timestamp,
                ),
            )
            db_connection.commit()

            forbidden_response = client.get(
                f"/download-results/{job_id}",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert forbidden_response.status_code == 403

            allowed_response = client.get(
                f"/download-results/{job_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert allowed_response.status_code == 200
        finally:
            app.dependency_overrides.pop(get_storage_manager, None)
