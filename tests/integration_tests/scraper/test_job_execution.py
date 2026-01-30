"""
Integration tests for scraper job execution.
Tests the full job lifecycle from creation to completion.
"""

import time

import pytest

from minutes_iq.db.results_service import ResultsService
from minutes_iq.db.scraper_repository import ScraperRepository
from minutes_iq.db.scraper_service import ScraperService


@pytest.fixture
def scraper_service(db_connection):
    """Create ScraperService with test database."""
    repository = ScraperRepository(db_connection)
    return ScraperService(repository)


@pytest.fixture
def results_service(db_connection):
    """Create ResultsService with test database."""
    repository = ScraperRepository(db_connection)
    return ResultsService(repository)


@pytest.fixture
def sample_client(db_connection, admin_token):
    """Create a test client."""
    # Get admin user ID
    cursor = db_connection.execute("SELECT user_id FROM users WHERE username = 'admin'")
    admin_id = cursor.fetchone()[0]
    cursor.close()

    # Create client
    timestamp = int(time.time())
    cursor = db_connection.execute(
        """
        INSERT INTO clients (name, description, is_active, created_at, created_by)
        VALUES (?, ?, ?, ?, ?)
        RETURNING client_id
        """,
        ("Test Client", "Test Description", 1, timestamp, admin_id),
    )
    client_id = cursor.fetchone()[0]
    cursor.close()

    # Create keyword
    cursor = db_connection.execute(
        """
        INSERT INTO keywords (keyword, is_active, created_at, created_by)
        VALUES (?, ?, ?, ?)
        RETURNING keyword_id
        """,
        ("test", 1, timestamp, admin_id),
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

    return {"client_id": client_id, "keyword_id": keyword_id, "admin_id": admin_id}


class TestJobCreation:
    """Test job creation."""

    def test_create_job_with_valid_config(self, scraper_service, sample_client):
        """Test creating a job with valid configuration."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
            date_range_start="2024-01",
            date_range_end="2024-12",
            max_scan_pages=10,
            include_minutes=True,
            include_packages=False,
        )

        assert job_id > 0

        # Verify job was created
        job = scraper_service.repository.get_job(job_id)
        assert job is not None
        assert job["status"] == "pending"
        assert job["client_id"] == sample_client["client_id"]

        # Verify config was created
        config = scraper_service.repository.get_job_config(job_id)
        assert config is not None
        assert config["date_range_start"] == "2024-01"
        assert config["max_scan_pages"] == 10
        assert config["include_minutes"] is True
        assert config["include_packages"] is False

    def test_create_job_with_minimal_config(self, scraper_service, sample_client):
        """Test creating a job with minimal configuration."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        assert job_id > 0

        config = scraper_service.repository.get_job_config(job_id)
        assert config["date_range_start"] is None
        assert config["max_scan_pages"] is None
        assert config["include_minutes"] is True  # Default


class TestJobLifecycle:
    """Test complete job lifecycle."""

    def test_job_status_transitions(self, scraper_service, sample_client):
        """Test job status transitions: pending → running → completed."""
        # Create job
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        # Initial status should be pending
        job = scraper_service.repository.get_job(job_id)
        assert job["status"] == "pending"
        assert job["started_at"] is None
        assert job["completed_at"] is None

        # Update to running
        scraper_service.repository.update_job_status(job_id, "running")
        job = scraper_service.repository.get_job(job_id)
        assert job["status"] == "running"
        assert job["started_at"] is not None
        assert job["completed_at"] is None

        # Update to completed
        scraper_service.repository.update_job_status(job_id, "completed")
        job = scraper_service.repository.get_job(job_id)
        assert job["status"] == "completed"
        assert job["started_at"] is not None
        assert job["completed_at"] is not None

    def test_job_failure_with_error_message(self, scraper_service, sample_client):
        """Test job failure handling."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        error_msg = "Network timeout error"
        scraper_service.repository.update_job_status(job_id, "failed", error_msg)

        job = scraper_service.repository.get_job(job_id)
        assert job["status"] == "failed"
        assert job["error_message"] == error_msg
        assert job["completed_at"] is not None


class TestJobCancellation:
    """Test job cancellation."""

    def test_cancel_pending_job(self, scraper_service, sample_client):
        """Test cancelling a pending job."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        success = scraper_service.cancel_job(job_id)
        assert success is True

        job = scraper_service.repository.get_job(job_id)
        assert job["status"] == "cancelled"

    def test_cancel_running_job(self, scraper_service, sample_client):
        """Test cancelling a running job."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        scraper_service.repository.update_job_status(job_id, "running")
        success = scraper_service.cancel_job(job_id)
        assert success is True

        job = scraper_service.repository.get_job(job_id)
        assert job["status"] == "cancelled"

    def test_cannot_cancel_completed_job(self, scraper_service, sample_client):
        """Test that completed jobs cannot be cancelled."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        scraper_service.repository.update_job_status(job_id, "completed")
        success = scraper_service.cancel_job(job_id)
        assert success is False


class TestResultStorage:
    """Test storing and retrieving results."""

    def test_store_and_retrieve_results(self, scraper_service, sample_client):
        """Test storing results and retrieving them."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        # Store results
        result_id = scraper_service.repository.save_result(
            job_id=job_id,
            pdf_filename="test.pdf",
            page_number=1,
            keyword_id=sample_client["keyword_id"],
            snippet="This is a test snippet",
            entities="John (PERSON), NASA (ORG)",
        )

        assert result_id > 0

        # Retrieve results
        results = scraper_service.repository.get_job_results(job_id)
        assert len(results) == 1
        assert results[0]["pdf_filename"] == "test.pdf"
        assert results[0]["page_number"] == 1
        assert results[0]["snippet"] == "This is a test snippet"

    def test_store_multiple_results(self, scraper_service, sample_client):
        """Test storing multiple results for same job."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        # Store 3 results
        for i in range(3):
            scraper_service.repository.save_result(
                job_id=job_id,
                pdf_filename=f"test_{i}.pdf",
                page_number=i + 1,
                keyword_id=sample_client["keyword_id"],
                snippet=f"Snippet {i}",
                entities=None,
            )

        results = scraper_service.repository.get_job_results(job_id)
        assert len(results) == 3


class TestCsvExport:
    """Test CSV export generation."""

    def test_generate_csv_with_results(
        self, scraper_service, results_service, sample_client
    ):
        """Test generating CSV export."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        # Add result
        scraper_service.repository.save_result(
            job_id=job_id,
            pdf_filename="test.pdf",
            page_number=1,
            keyword_id=sample_client["keyword_id"],
            snippet="Test snippet",
            entities="",
        )

        csv_content = results_service.generate_csv_export(job_id)
        assert csv_content != ""
        assert "test.pdf" in csv_content
        assert "Test snippet" in csv_content

    def test_generate_csv_empty_results(
        self, results_service, scraper_service, sample_client
    ):
        """Test generating CSV with no results."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        csv_content = results_service.generate_csv_export(job_id)
        assert csv_content == ""


class TestJobStatistics:
    """Test job statistics and summaries."""

    def test_get_results_summary(self, scraper_service, results_service, sample_client):
        """Test getting results summary."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        # Add multiple results
        for i in range(5):
            scraper_service.repository.save_result(
                job_id=job_id,
                pdf_filename=f"test_{i % 2}.pdf",  # 2 unique PDFs
                page_number=i + 1,
                keyword_id=sample_client["keyword_id"],
                snippet=f"Snippet {i}",
                entities=None,
            )

        summary = results_service.get_results_summary(job_id)
        assert summary["total_matches"] == 5
        assert summary["unique_pdfs"] == 2
        assert summary["unique_keywords"] == 1

    def test_get_keyword_statistics(
        self, scraper_service, sample_client, db_connection
    ):
        """Test keyword statistics aggregation."""
        job_id = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        # Create another keyword
        timestamp = int(time.time())
        cursor = db_connection.execute(
            """
            INSERT INTO keywords (keyword, is_active, created_at, created_by)
            VALUES (?, ?, ?, ?)
            RETURNING keyword_id
            """,
            ("keyword2", 1, timestamp, sample_client["admin_id"]),
        )
        keyword2_id = cursor.fetchone()[0]
        cursor.close()
        db_connection.commit()

        # Add results with different keywords
        for _ in range(3):
            scraper_service.repository.save_result(
                job_id=job_id,
                pdf_filename="test.pdf",
                page_number=1,
                keyword_id=sample_client["keyword_id"],
                snippet="Snippet",
                entities=None,
            )

        for _ in range(2):
            scraper_service.repository.save_result(
                job_id=job_id,
                pdf_filename="test.pdf",
                page_number=2,
                keyword_id=keyword2_id,
                snippet="Snippet",
                entities=None,
            )

        stats = scraper_service.repository.get_keyword_statistics(job_id)
        assert len(stats) == 2
        assert stats[0]["match_count"] == 3  # Sorted by count desc
        assert stats[1]["match_count"] == 2


class TestJobListing:
    """Test job listing and filtering."""

    def test_list_jobs_by_user(self, scraper_service, sample_client, db_connection):
        """Test listing jobs filtered by user."""
        # Create 3 jobs
        for _ in range(3):
            scraper_service.create_scrape_job(
                client_id=sample_client["client_id"],
                created_by=sample_client["admin_id"],
            )

        jobs = scraper_service.repository.list_jobs(user_id=sample_client["admin_id"])
        assert len(jobs) == 3

    def test_list_jobs_by_status(self, scraper_service, sample_client):
        """Test listing jobs filtered by status."""
        # Create jobs with different statuses
        scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )

        job2 = scraper_service.create_scrape_job(
            client_id=sample_client["client_id"],
            created_by=sample_client["admin_id"],
        )
        scraper_service.repository.update_job_status(job2, "completed")

        # List only completed jobs
        jobs = scraper_service.repository.list_jobs(
            user_id=sample_client["admin_id"],
            status="completed",
        )
        assert len(jobs) == 1
        assert jobs[0]["status"] == "completed"

    def test_list_jobs_with_pagination(self, scraper_service, sample_client):
        """Test job listing with pagination."""
        # Create 5 jobs
        for _ in range(5):
            scraper_service.create_scrape_job(
                client_id=sample_client["client_id"],
                created_by=sample_client["admin_id"],
            )

        # Get first page (2 items)
        jobs_page1 = scraper_service.repository.list_jobs(
            user_id=sample_client["admin_id"],
            limit=2,
            offset=0,
        )
        assert len(jobs_page1) == 2

        # Get second page (2 items)
        jobs_page2 = scraper_service.repository.list_jobs(
            user_id=sample_client["admin_id"],
            limit=2,
            offset=2,
        )
        assert len(jobs_page2) == 2

        # Ensure different jobs
        assert jobs_page1[0]["job_id"] != jobs_page2[0]["job_id"]
