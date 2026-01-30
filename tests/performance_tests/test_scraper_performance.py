"""
Performance tests for scraper module.

These tests are marked with @pytest.mark.performance and can be run separately:
    pytest -m performance

Note: These tests may take longer to run and are typically excluded from CI.
"""

import time
from unittest.mock import Mock, patch

import pytest


@pytest.mark.performance
class TestLargePdfScanning:
    """Test performance with large PDFs."""

    @patch("minutes_iq.scraper.core.requests.get")
    @patch("minutes_iq.scraper.core.pdfplumber.open")
    def test_scan_large_pdf(self, mock_pdf_open, mock_get):
        """Test scanning a large (100+ page) PDF."""
        from minutes_iq.scraper.core import stream_and_scan_pdf

        # Mock PDF response
        mock_response = Mock()
        mock_response.content = b"fake pdf content"
        mock_get.return_value = mock_response

        # Mock 150 pages
        mock_pages = []
        for i in range(150):
            mock_page = Mock()
            # Add keyword every 10 pages
            if i % 10 == 0:
                mock_page.extract_text.return_value = f"Page {i} with keyword match"
            else:
                mock_page.extract_text.return_value = f"Page {i} content"
            mock_pages.append(mock_page)

        mock_pdf = Mock()
        mock_pdf.pages = mock_pages
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdf_open.return_value = mock_pdf

        # Measure performance
        start_time = time.time()
        keywords = ["keyword"]
        matches, pdf_content, pages_scanned = stream_and_scan_pdf(
            url="https://example.com/large.pdf",
            keywords=keywords,
            max_pages=None,  # Scan all pages
        )
        elapsed = time.time() - start_time

        assert pages_scanned == 150
        assert len(matches) >= 15  # Should find ~15 matches
        assert elapsed < 30  # Should complete in under 30 seconds
        print(f"Scanned 150 pages in {elapsed:.2f}s")


@pytest.mark.performance
class TestConcurrentJobExecution:
    """Test concurrent job execution."""

    def test_multiple_jobs_simultaneously(self, db_connection):
        """Test running 3 jobs simultaneously (simulation)."""
        from minutes_iq.db.scraper_repository import ScraperRepository
        from minutes_iq.db.scraper_service import ScraperService

        repository = ScraperRepository(db_connection)
        service = ScraperService(repository)

        # Create 3 clients with keywords
        clients = []
        timestamp = int(time.time())
        for i in range(3):
            # Create client
            cursor = db_connection.execute(
                """
                INSERT INTO clients (name, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?)
                RETURNING client_id
                """,
                (f"Client {i}", 1, timestamp, 1),
            )
            client_id = cursor.fetchone()[0]

            # Create keyword
            cursor = db_connection.execute(
                """
                INSERT INTO keywords (keyword, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?)
                RETURNING keyword_id
                """,
                (f"keyword{i}", 1, timestamp, 1),
            )
            keyword_id = cursor.fetchone()[0]

            # Link them
            db_connection.execute(
                """
                INSERT INTO client_keywords (client_id, keyword_id, added_at, added_by)
                VALUES (?, ?, ?, ?)
                """,
                (client_id, keyword_id, timestamp, 1),
            )

            clients.append({"client_id": client_id, "keyword_id": keyword_id})

        db_connection.commit()

        # Create jobs
        start_time = time.time()
        job_ids = []
        for client in clients:
            job_id = service.create_scrape_job(
                client_id=client["client_id"],
                created_by=1,
                max_scan_pages=5,
            )
            job_ids.append(job_id)

        elapsed = time.time() - start_time

        assert len(job_ids) == 3
        assert elapsed < 1.0  # Job creation should be fast
        print(f"Created 3 jobs in {elapsed:.3f}s")


@pytest.mark.performance
class TestTimeoutEnforcement:
    """Test timeout enforcement."""

    def test_job_timeout_limit(self):
        """Test that timeout constant is set correctly."""
        from minutes_iq.scraper.async_runner import JOB_TIMEOUT

        # Verify timeout is 30 minutes
        assert JOB_TIMEOUT == 30 * 60

    @patch("minutes_iq.scraper.async_runner.time.time")
    def test_timeout_check_triggers(self, mock_time):
        """Test that timeout check raises exception."""
        from minutes_iq.scraper.async_runner import (
            JobTimeoutException,
            _check_timeout,
        )

        # Simulate job running for 31 minutes
        mock_time.side_effect = [0, 31 * 60 + 1]

        with pytest.raises(JobTimeoutException):
            _check_timeout(job_id=1, start_time=0)


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage with large result sets."""

    def test_large_result_set_storage(self, db_connection):
        """Test storing and retrieving large result set."""
        from minutes_iq.db.scraper_repository import ScraperRepository
        from minutes_iq.db.scraper_service import ScraperService

        repository = ScraperRepository(db_connection)
        service = ScraperService(repository)

        # Create client and keyword
        timestamp = int(time.time())
        cursor = db_connection.execute(
            """
            INSERT INTO clients (name, is_active, created_at, created_by)
            VALUES (?, ?, ?, ?)
            RETURNING client_id
            """,
            ("Test Client", 1, timestamp, 1),
        )
        client_id = cursor.fetchone()[0]

        cursor = db_connection.execute(
            """
            INSERT INTO keywords (keyword, is_active, created_at, created_by)
            VALUES (?, ?, ?, ?)
            RETURNING keyword_id
            """,
            ("test", 1, timestamp, 1),
        )
        keyword_id = cursor.fetchone()[0]

        db_connection.execute(
            """
            INSERT INTO client_keywords (client_id, keyword_id, added_at, added_by)
            VALUES (?, ?, ?, ?)
            """,
            (client_id, keyword_id, timestamp, 1),
        )
        db_connection.commit()

        # Create job
        job_id = service.create_scrape_job(
            client_id=client_id,
            created_by=1,
        )

        # Store 1000 results
        start_time = time.time()
        for i in range(1000):
            repository.save_result(
                job_id=job_id,
                pdf_filename=f"doc_{i % 100}.pdf",
                page_number=(i % 20) + 1,
                keyword_id=keyword_id,
                snippet=f"This is test snippet number {i} with some content",
                entities="Person (PERSON), Organization (ORG)",
            )

        db_connection.commit()
        store_elapsed = time.time() - start_time

        # Retrieve results
        start_time = time.time()
        results = repository.get_job_results(job_id)
        retrieve_elapsed = time.time() - start_time

        assert len(results) == 1000
        assert store_elapsed < 10.0  # Should store 1000 results in under 10s
        assert retrieve_elapsed < 2.0  # Should retrieve in under 2s

        print(f"Stored 1000 results in {store_elapsed:.2f}s")
        print(f"Retrieved 1000 results in {retrieve_elapsed:.3f}s")


@pytest.mark.performance
class TestCsvExportPerformance:
    """Test CSV export performance."""

    def test_export_large_result_set(self, db_connection):
        """Test CSV export with large result set."""
        from minutes_iq.db.results_service import ResultsService
        from minutes_iq.db.scraper_repository import ScraperRepository
        from minutes_iq.db.scraper_service import ScraperService

        repository = ScraperRepository(db_connection)
        service = ScraperService(repository)
        results_service = ResultsService(repository)

        # Create client and keyword
        timestamp = int(time.time())
        cursor = db_connection.execute(
            """
            INSERT INTO clients (name, is_active, created_at, created_by)
            VALUES (?, ?, ?, ?)
            RETURNING client_id
            """,
            ("Test Client", 1, timestamp, 1),
        )
        client_id = cursor.fetchone()[0]

        cursor = db_connection.execute(
            """
            INSERT INTO keywords (keyword, is_active, created_at, created_by)
            VALUES (?, ?, ?, ?)
            RETURNING keyword_id
            """,
            ("test", 1, timestamp, 1),
        )
        keyword_id = cursor.fetchone()[0]

        db_connection.execute(
            """
            INSERT INTO client_keywords (client_id, keyword_id, added_at, added_by)
            VALUES (?, ?, ?, ?)
            """,
            (client_id, keyword_id, timestamp, 1),
        )
        db_connection.commit()

        # Create job and add 500 results
        job_id = service.create_scrape_job(client_id=client_id, created_by=1)

        for i in range(500):
            repository.save_result(
                job_id=job_id,
                pdf_filename=f"doc_{i}.pdf",
                page_number=1,
                keyword_id=keyword_id,
                snippet=f"Snippet {i}",
                entities="Test (PERSON)",
            )

        db_connection.commit()

        # Generate CSV export
        start_time = time.time()
        csv_content = results_service.generate_csv_export(job_id)
        elapsed = time.time() - start_time

        assert len(csv_content) > 0
        assert csv_content.count("\n") >= 500  # At least 500 rows + header
        assert elapsed < 5.0  # Should generate CSV in under 5 seconds

        print(f"Generated CSV for 500 results in {elapsed:.3f}s")
        print(f"CSV size: {len(csv_content)} bytes")
