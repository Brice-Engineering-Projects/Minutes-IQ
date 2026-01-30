"""
Storage management for scraper PDFs, annotated PDFs, and artifacts.

This module provides:
- Organized directory structure for job outputs
- Path generation utilities
- Age-based file cleanup policies
- Disk space management
"""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default retention periods in days
DEFAULT_RAW_PDF_RETENTION = 30
DEFAULT_ANNOTATED_PDF_RETENTION = 90
DEFAULT_ARTIFACT_RETENTION = 30


class StorageManager:
    """Manages file storage for scraper jobs."""

    def __init__(
        self,
        base_dir: str | Path,
        raw_pdf_retention_days: int = DEFAULT_RAW_PDF_RETENTION,
        annotated_pdf_retention_days: int = DEFAULT_ANNOTATED_PDF_RETENTION,
        artifact_retention_days: int = DEFAULT_ARTIFACT_RETENTION,
    ):
        """
        Initialize storage manager.

        Args:
            base_dir: Base directory for all storage (typically 'data/')
            raw_pdf_retention_days: Days to keep raw PDFs (default: 30)
            annotated_pdf_retention_days: Days to keep annotated PDFs (default: 90)
            artifact_retention_days: Days to keep artifacts (default: 30)
        """
        self.base_dir = Path(base_dir)
        self.raw_pdf_retention_days = raw_pdf_retention_days
        self.annotated_pdf_retention_days = annotated_pdf_retention_days
        self.artifact_retention_days = artifact_retention_days

        # Ensure base directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create base storage directories if they don't exist."""
        (self.base_dir / "raw_pdfs").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "annotated_pdfs").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    # === Path Generation ===

    def get_raw_pdf_dir(self, job_id: int) -> Path:
        """Get directory path for raw PDFs for a job."""
        return self.base_dir / "raw_pdfs" / str(job_id)

    def get_raw_pdf_path(self, job_id: int, filename: str) -> Path:
        """Get full path for a raw PDF file."""
        return self.get_raw_pdf_dir(job_id) / filename

    def get_annotated_pdf_dir(self, job_id: int) -> Path:
        """Get directory path for annotated PDFs for a job."""
        return self.base_dir / "annotated_pdfs" / str(job_id)

    def get_annotated_pdf_path(self, job_id: int, filename: str) -> Path:
        """Get full path for an annotated PDF file."""
        # Add _annotated suffix if not present
        if not filename.endswith("_annotated.pdf"):
            filename = filename.replace(".pdf", "_annotated.pdf")
        return self.get_annotated_pdf_dir(job_id) / filename

    def get_artifacts_dir(self, job_id: int) -> Path:
        """Get directory path for artifacts for a job."""
        return self.base_dir / "artifacts" / str(job_id)

    def get_artifact_path(self, job_id: int, artifact_id: str) -> Path:
        """Get full path for an artifact file."""
        return self.get_artifacts_dir(job_id) / f"{artifact_id}.zip"

    # === File Management ===

    def ensure_job_directories(self, job_id: int) -> None:
        """Create all directories for a job."""
        self.get_raw_pdf_dir(job_id).mkdir(parents=True, exist_ok=True)
        self.get_annotated_pdf_dir(job_id).mkdir(parents=True, exist_ok=True)
        self.get_artifacts_dir(job_id).mkdir(parents=True, exist_ok=True)

    def cleanup_job(
        self, job_id: int, include_artifacts: bool = True
    ) -> dict[str, int]:
        """
        Delete all files for a job.

        Args:
            job_id: The job ID to clean up
            include_artifacts: Whether to delete artifacts (default: True)

        Returns:
            Dict with counts of deleted files by type
        """
        deleted = {
            "raw_pdfs": 0,
            "annotated_pdfs": 0,
            "artifacts": 0,
        }

        # Delete raw PDFs
        raw_pdf_dir = self.get_raw_pdf_dir(job_id)
        if raw_pdf_dir.exists():
            deleted["raw_pdfs"] = len(list(raw_pdf_dir.glob("*.pdf")))
            shutil.rmtree(raw_pdf_dir)
            logger.info(f"Deleted {deleted['raw_pdfs']} raw PDFs for job {job_id}")

        # Delete annotated PDFs
        annotated_pdf_dir = self.get_annotated_pdf_dir(job_id)
        if annotated_pdf_dir.exists():
            deleted["annotated_pdfs"] = len(list(annotated_pdf_dir.glob("*.pdf")))
            shutil.rmtree(annotated_pdf_dir)
            logger.info(
                f"Deleted {deleted['annotated_pdfs']} annotated PDFs for job {job_id}"
            )

        # Delete artifacts if requested
        if include_artifacts:
            artifacts_dir = self.get_artifacts_dir(job_id)
            if artifacts_dir.exists():
                deleted["artifacts"] = len(list(artifacts_dir.glob("*.zip")))
                shutil.rmtree(artifacts_dir)
                logger.info(
                    f"Deleted {deleted['artifacts']} artifacts for job {job_id}"
                )

        return deleted

    # === Age-Based Cleanup ===

    def cleanup_old_files(self) -> dict[str, Any]:
        """
        Clean up files older than retention periods.

        Returns:
            Dict with cleanup summary
        """
        now = datetime.now()
        summary: dict[str, Any] = {
            "raw_pdfs_deleted": 0,
            "annotated_pdfs_deleted": 0,
            "artifacts_deleted": 0,
            "jobs_cleaned": [],
        }

        # Clean up raw PDFs
        raw_pdf_dir = self.base_dir / "raw_pdfs"
        if raw_pdf_dir.exists():
            for job_dir in raw_pdf_dir.iterdir():
                if not job_dir.is_dir():
                    continue

                # Check age based on directory modification time
                dir_age = now - datetime.fromtimestamp(job_dir.stat().st_mtime)
                if dir_age > timedelta(days=self.raw_pdf_retention_days):
                    file_count = len(list(job_dir.glob("*.pdf")))
                    shutil.rmtree(job_dir)
                    summary["raw_pdfs_deleted"] += file_count
                    summary["jobs_cleaned"].append(int(job_dir.name))
                    logger.info(
                        f"Deleted {file_count} raw PDFs from job {job_dir.name} "
                        f"(age: {dir_age.days} days)"
                    )

        # Clean up annotated PDFs
        annotated_pdf_dir = self.base_dir / "annotated_pdfs"
        if annotated_pdf_dir.exists():
            for job_dir in annotated_pdf_dir.iterdir():
                if not job_dir.is_dir():
                    continue

                dir_age = now - datetime.fromtimestamp(job_dir.stat().st_mtime)
                if dir_age > timedelta(days=self.annotated_pdf_retention_days):
                    file_count = len(list(job_dir.glob("*.pdf")))
                    shutil.rmtree(job_dir)
                    summary["annotated_pdfs_deleted"] += file_count
                    if int(job_dir.name) not in summary["jobs_cleaned"]:
                        summary["jobs_cleaned"].append(int(job_dir.name))
                    logger.info(
                        f"Deleted {file_count} annotated PDFs from job {job_dir.name} "
                        f"(age: {dir_age.days} days)"
                    )

        # Clean up artifacts
        artifacts_dir = self.base_dir / "artifacts"
        if artifacts_dir.exists():
            for job_dir in artifacts_dir.iterdir():
                if not job_dir.is_dir():
                    continue

                dir_age = now - datetime.fromtimestamp(job_dir.stat().st_mtime)
                if dir_age > timedelta(days=self.artifact_retention_days):
                    file_count = len(list(job_dir.glob("*.zip")))
                    shutil.rmtree(job_dir)
                    summary["artifacts_deleted"] += file_count
                    if int(job_dir.name) not in summary["jobs_cleaned"]:
                        summary["jobs_cleaned"].append(int(job_dir.name))
                    logger.info(
                        f"Deleted {file_count} artifacts from job {job_dir.name} "
                        f"(age: {dir_age.days} days)"
                    )

        logger.info(
            f"Cleanup completed: {summary['raw_pdfs_deleted']} raw PDFs, "
            f"{summary['annotated_pdfs_deleted']} annotated PDFs, "
            f"{summary['artifacts_deleted']} artifacts deleted from "
            f"{len(summary['jobs_cleaned'])} jobs"
        )

        return summary

    # === Disk Usage ===

    def get_storage_stats(self) -> dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dict with storage usage by type
        """

        def get_dir_size(path: Path) -> int:
            """Calculate total size of directory in bytes."""
            if not path.exists():
                return 0
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

        def count_files(path: Path) -> int:
            """Count files in directory."""
            if not path.exists():
                return 0
            return sum(1 for _ in path.rglob("*") if _.is_file())

        raw_pdf_dir = self.base_dir / "raw_pdfs"
        annotated_pdf_dir = self.base_dir / "annotated_pdfs"
        artifacts_dir = self.base_dir / "artifacts"

        return {
            "raw_pdfs": {
                "size_bytes": get_dir_size(raw_pdf_dir),
                "file_count": count_files(raw_pdf_dir),
                "job_count": len(list(raw_pdf_dir.iterdir()))
                if raw_pdf_dir.exists()
                else 0,
            },
            "annotated_pdfs": {
                "size_bytes": get_dir_size(annotated_pdf_dir),
                "file_count": count_files(annotated_pdf_dir),
                "job_count": len(list(annotated_pdf_dir.iterdir()))
                if annotated_pdf_dir.exists()
                else 0,
            },
            "artifacts": {
                "size_bytes": get_dir_size(artifacts_dir),
                "file_count": count_files(artifacts_dir),
                "job_count": len(list(artifacts_dir.iterdir()))
                if artifacts_dir.exists()
                else 0,
            },
            "total_size_bytes": get_dir_size(self.base_dir),
        }
