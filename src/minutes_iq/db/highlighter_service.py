"""
Service layer for PDF highlighting and annotation.
"""

import logging
import zipfile
from pathlib import Path
from typing import Any

from minutes_iq.db.scraper_repository import ScraperRepository
from minutes_iq.scraper.highlighter import (
    batch_highlight_pdfs,
    highlight_job_results,
    highlight_pdf,
)

logger = logging.getLogger(__name__)


class HighlighterService:
    """Service for highlighting and annotating PDFs."""

    def __init__(self, repository: ScraperRepository):
        self.repository = repository

    def highlight_job_results(
        self,
        job_id: int,
        pdf_dir: str | Path,
        output_base_dir: str | Path,
    ) -> dict[str, Any]:
        """
        Annotate all PDFs for a scrape job.

        Args:
            job_id: The job ID
            pdf_dir: Directory containing source PDFs
            output_base_dir: Base directory for annotated PDFs

        Returns:
            Dict with highlighting summary
        """
        # Get job results from database
        results = self.repository.get_job_results(job_id)

        if not results:
            logger.warning(f"No results found for job {job_id}")
            return {
                "files_processed": 0,
                "files_succeeded": 0,
                "files_failed": 0,
                "output_dir": None,
            }

        # Use highlighter module to process PDFs
        summary = highlight_job_results(
            job_id=job_id,
            pdf_dir=pdf_dir,
            output_base_dir=output_base_dir,
            results=results,
        )

        logger.info(f"Highlighted PDFs for job {job_id}: {summary}")
        return summary

    def add_highlights_to_pdf(
        self,
        pdf_path: str | Path,
        output_path: str | Path,
        matches: list[dict[str, Any]],
    ) -> bool:
        """
        Process a single PDF and add highlights.

        Args:
            pdf_path: Path to source PDF
            output_path: Path to save annotated PDF
            matches: List of match dicts with page and keyword

        Returns:
            True if successful, False otherwise
        """
        success = highlight_pdf(
            pdf_path=pdf_path,
            output_path=output_path,
            matches=matches,
        )

        if success:
            logger.info(f"Highlighted PDF: {output_path}")
        else:
            logger.error(f"Failed to highlight PDF: {pdf_path}")

        return success

    def create_annotated_zip(
        self,
        job_id: int,
        annotated_pdf_dir: str | Path,
        output_path: str | Path,
    ) -> Path:
        """
        Bundle annotated PDFs into a ZIP file.

        Args:
            job_id: The job ID
            annotated_pdf_dir: Directory containing annotated PDFs
            output_path: Path to save the ZIP file

        Returns:
            Path to the created ZIP file
        """
        annotated_pdf_dir = Path(annotated_pdf_dir) / str(job_id)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not annotated_pdf_dir.exists():
            raise ValueError(f"Annotated PDF directory not found: {annotated_pdf_dir}")

        # Get list of annotated PDFs
        annotated_pdfs = list(annotated_pdf_dir.glob("*_annotated.pdf"))

        if not annotated_pdfs:
            raise ValueError(f"No annotated PDFs found in {annotated_pdf_dir}")

        # Create ZIP file
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for pdf_path in annotated_pdfs:
                zf.write(pdf_path, pdf_path.name)

        logger.info(
            f"Created annotated ZIP for job {job_id}: {output_path} "
            f"({len(annotated_pdfs)} PDFs)"
        )

        return output_path

    def batch_highlight(
        self,
        pdf_dir: str | Path,
        output_dir: str | Path,
        matches_by_file: dict[str, list[dict[str, Any]]],
    ) -> dict[str, bool]:
        """
        Highlight multiple PDFs in batch.

        Args:
            pdf_dir: Directory containing source PDFs
            output_dir: Directory to save annotated PDFs
            matches_by_file: Dict mapping filename to list of matches

        Returns:
            Dict mapping filename to success status
        """
        results = batch_highlight_pdfs(
            pdf_dir=pdf_dir,
            output_dir=output_dir,
            matches_by_file=matches_by_file,
        )

        succeeded = sum(1 for success in results.values() if success)
        failed = len(results) - succeeded

        logger.info(
            f"Batch highlighting complete: {succeeded} succeeded, {failed} failed"
        )

        return results
