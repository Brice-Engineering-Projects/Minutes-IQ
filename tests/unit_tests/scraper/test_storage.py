"""
Unit tests for storage management.
"""

import shutil
import tempfile
import time
from pathlib import Path

import pytest

from minutes_iq.scraper.storage import StorageManager


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir)


class TestStorageManager:
    """Tests for StorageManager class."""

    def test_initialization_creates_directories(self, temp_storage):
        """Test that StorageManager creates base directories on init."""
        StorageManager(base_dir=temp_storage)

        assert (temp_storage / "raw_pdfs").exists()
        assert (temp_storage / "annotated_pdfs").exists()
        assert (temp_storage / "artifacts").exists()

    def test_get_raw_pdf_path(self, temp_storage):
        """Test raw PDF path generation."""
        manager = StorageManager(base_dir=temp_storage)
        path = manager.get_raw_pdf_path(job_id=123, filename="test.pdf")

        expected = temp_storage / "raw_pdfs" / "123" / "test.pdf"
        assert path == expected

    def test_get_annotated_pdf_path_adds_suffix(self, temp_storage):
        """Test annotated PDF path generation adds _annotated suffix."""
        manager = StorageManager(base_dir=temp_storage)
        path = manager.get_annotated_pdf_path(job_id=123, filename="test.pdf")

        expected = temp_storage / "annotated_pdfs" / "123" / "test_annotated.pdf"
        assert path == expected

    def test_get_annotated_pdf_path_preserves_existing_suffix(self, temp_storage):
        """Test that existing _annotated suffix is preserved."""
        manager = StorageManager(base_dir=temp_storage)
        path = manager.get_annotated_pdf_path(job_id=123, filename="test_annotated.pdf")

        expected = temp_storage / "annotated_pdfs" / "123" / "test_annotated.pdf"
        assert path == expected

    def test_get_artifact_path(self, temp_storage):
        """Test artifact path generation."""
        manager = StorageManager(base_dir=temp_storage)
        path = manager.get_artifact_path(job_id=123, artifact_id="abc123")

        expected = temp_storage / "artifacts" / "123" / "abc123.zip"
        assert path == expected

    def test_ensure_job_directories(self, temp_storage):
        """Test creating all directories for a job."""
        manager = StorageManager(base_dir=temp_storage)
        manager.ensure_job_directories(job_id=456)

        assert (temp_storage / "raw_pdfs" / "456").exists()
        assert (temp_storage / "annotated_pdfs" / "456").exists()
        assert (temp_storage / "artifacts" / "456").exists()

    def test_cleanup_job_empty(self, temp_storage):
        """Test cleaning up job with no files."""
        manager = StorageManager(base_dir=temp_storage)
        manager.ensure_job_directories(job_id=789)

        result = manager.cleanup_job(job_id=789)

        assert result["raw_pdfs"] == 0
        assert result["annotated_pdfs"] == 0
        assert result["artifacts"] == 0

    def test_cleanup_job_with_files(self, temp_storage):
        """Test cleaning up job with files."""
        manager = StorageManager(base_dir=temp_storage)
        job_id = 999

        # Create directories and add files
        manager.ensure_job_directories(job_id)

        # Add raw PDFs
        raw_pdf_dir = manager.get_raw_pdf_dir(job_id)
        (raw_pdf_dir / "test1.pdf").write_text("pdf content 1")
        (raw_pdf_dir / "test2.pdf").write_text("pdf content 2")

        # Add annotated PDFs
        annotated_pdf_dir = manager.get_annotated_pdf_dir(job_id)
        (annotated_pdf_dir / "test1_annotated.pdf").write_text("annotated 1")

        # Add artifacts
        artifacts_dir = manager.get_artifacts_dir(job_id)
        (artifacts_dir / "artifact1.zip").write_text("zip content")

        # Perform cleanup
        result = manager.cleanup_job(job_id)

        assert result["raw_pdfs"] == 2
        assert result["annotated_pdfs"] == 1
        assert result["artifacts"] == 1

        # Verify directories are removed
        assert not raw_pdf_dir.exists()
        assert not annotated_pdf_dir.exists()
        assert not artifacts_dir.exists()

    def test_cleanup_job_exclude_artifacts(self, temp_storage):
        """Test cleaning up job but preserving artifacts."""
        manager = StorageManager(base_dir=temp_storage)
        job_id = 888

        # Create directories and add files
        manager.ensure_job_directories(job_id)

        # Add files
        raw_pdf_dir = manager.get_raw_pdf_dir(job_id)
        (raw_pdf_dir / "test.pdf").write_text("pdf content")

        artifacts_dir = manager.get_artifacts_dir(job_id)
        (artifacts_dir / "artifact.zip").write_text("zip content")

        # Cleanup without artifacts
        result = manager.cleanup_job(job_id, include_artifacts=False)

        assert result["raw_pdfs"] == 1
        assert result["artifacts"] == 0

        # Verify artifacts directory still exists
        assert artifacts_dir.exists()
        assert not raw_pdf_dir.exists()

    def test_get_storage_stats_empty(self, temp_storage):
        """Test getting storage stats with no files."""
        manager = StorageManager(base_dir=temp_storage)
        stats = manager.get_storage_stats()

        assert stats["raw_pdfs"]["size_bytes"] == 0
        assert stats["raw_pdfs"]["file_count"] == 0
        assert stats["raw_pdfs"]["job_count"] == 0

        assert stats["annotated_pdfs"]["size_bytes"] == 0
        assert stats["artifacts"]["size_bytes"] == 0
        assert stats["total_size_bytes"] >= 0  # May include directory overhead

    def test_get_storage_stats_with_files(self, temp_storage):
        """Test getting storage stats with files."""
        manager = StorageManager(base_dir=temp_storage)
        job_id = 777

        # Create files
        manager.ensure_job_directories(job_id)

        raw_pdf_path = manager.get_raw_pdf_path(job_id, "test.pdf")
        raw_pdf_path.write_text("x" * 1000)  # 1000 bytes

        annotated_pdf_path = manager.get_annotated_pdf_path(job_id, "test.pdf")
        annotated_pdf_path.write_text("y" * 2000)  # 2000 bytes

        # Get stats
        stats = manager.get_storage_stats()

        assert stats["raw_pdfs"]["size_bytes"] == 1000
        assert stats["raw_pdfs"]["file_count"] == 1
        assert stats["raw_pdfs"]["job_count"] == 1

        assert stats["annotated_pdfs"]["size_bytes"] == 2000
        assert stats["annotated_pdfs"]["file_count"] == 1

        assert stats["total_size_bytes"] >= 3000

    def test_cleanup_old_files_no_old_files(self, temp_storage):
        """Test cleanup with no old files."""
        manager = StorageManager(
            base_dir=temp_storage,
            raw_pdf_retention_days=30,
            annotated_pdf_retention_days=90,
            artifact_retention_days=30,
        )

        # Create recent job
        job_id = 111
        manager.ensure_job_directories(job_id)
        (manager.get_raw_pdf_dir(job_id) / "test.pdf").write_text("content")

        # Cleanup should not delete anything
        summary = manager.cleanup_old_files()

        assert summary["raw_pdfs_deleted"] == 0
        assert summary["annotated_pdfs_deleted"] == 0
        assert summary["artifacts_deleted"] == 0
        assert len(summary["jobs_cleaned"]) == 0

    def test_cleanup_old_files_with_retention_zero(self, temp_storage):
        """Test cleanup with zero retention (immediate deletion)."""
        manager = StorageManager(
            base_dir=temp_storage,
            raw_pdf_retention_days=0,
            annotated_pdf_retention_days=0,
            artifact_retention_days=0,
        )

        # Create job with files
        job_id = 222
        manager.ensure_job_directories(job_id)

        raw_pdf_dir = manager.get_raw_pdf_dir(job_id)
        (raw_pdf_dir / "test.pdf").write_text("content")

        # Make directory appear old by modifying timestamp
        # Note: This is tricky with newly created directories
        # Wait a tiny bit to ensure modification time differs
        time.sleep(0.01)

        # Cleanup
        summary = manager.cleanup_old_files()

        # With 0-day retention, files should be deleted
        assert summary["raw_pdfs_deleted"] == 1
        assert job_id in summary["jobs_cleaned"]

    def test_custom_retention_periods(self, temp_storage):
        """Test initializing with custom retention periods."""
        manager = StorageManager(
            base_dir=temp_storage,
            raw_pdf_retention_days=7,
            annotated_pdf_retention_days=14,
            artifact_retention_days=21,
        )

        assert manager.raw_pdf_retention_days == 7
        assert manager.annotated_pdf_retention_days == 14
        assert manager.artifact_retention_days == 21

    def test_multiple_jobs_storage(self, temp_storage):
        """Test managing storage for multiple jobs."""
        manager = StorageManager(base_dir=temp_storage)

        # Create files for multiple jobs
        for job_id in [101, 102, 103]:
            manager.ensure_job_directories(job_id)
            (manager.get_raw_pdf_dir(job_id) / f"job{job_id}.pdf").write_text("data")

        # Get stats
        stats = manager.get_storage_stats()

        assert stats["raw_pdfs"]["job_count"] == 3
        assert stats["raw_pdfs"]["file_count"] == 3

        # Cleanup one job
        result = manager.cleanup_job(102)
        assert result["raw_pdfs"] == 1

        # Stats should update
        stats = manager.get_storage_stats()
        assert stats["raw_pdfs"]["job_count"] == 2
        assert stats["raw_pdfs"]["file_count"] == 2
