"""
Service layer for scraper results processing and export.
"""

import csv
import json
import logging
import zipfile
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from minutes_iq.db.scraper_repository import ScraperRepository

logger = logging.getLogger(__name__)


class ResultsService:
    """Service for processing and exporting scraper results."""

    def __init__(self, repository: ScraperRepository):
        self.repository = repository

    def get_results_summary(self, job_id: int) -> dict[str, Any]:
        """
        Get aggregated statistics for job results.

        Args:
            job_id: The job ID

        Returns:
            Dict with summary statistics
        """
        job = self.repository.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Get basic counts
        result_count = self.repository.get_result_count(job_id)
        keyword_stats = self.repository.get_keyword_statistics(job_id)
        results = self.repository.get_job_results(job_id)

        # Count unique PDFs
        unique_pdfs = len(set(r["pdf_filename"] for r in results))

        # Calculate execution time if completed
        execution_time = None
        if job["started_at"] and job["completed_at"]:
            execution_time = job["completed_at"] - job["started_at"]

        summary = {
            "job_id": job_id,
            "status": job["status"],
            "total_matches": result_count,
            "unique_pdfs": unique_pdfs,
            "unique_keywords": len(keyword_stats),
            "keyword_breakdown": keyword_stats,
            "execution_time_seconds": execution_time,
            "created_at": job["created_at"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"],
            "error_message": job["error_message"],
        }

        return summary

    def generate_csv_export(self, job_id: int) -> str:
        """
        Generate CSV export of job results.

        Args:
            job_id: The job ID

        Returns:
            CSV content as string
        """
        results = self.repository.get_job_results(job_id)

        if not results:
            logger.warning(f"No results to export for job {job_id}")
            return ""

        # Create CSV in memory
        output = StringIO()
        fieldnames = [
            "result_id",
            "pdf_filename",
            "page_number",
            "keyword",
            "snippet",
            "entities",
            "created_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    "result_id": result["result_id"],
                    "pdf_filename": result["pdf_filename"],
                    "page_number": result["page_number"],
                    "keyword": result["keyword"],
                    "snippet": result["snippet"],
                    "entities": result["entities_json"] or "",
                    "created_at": result["created_at"],
                }
            )

        csv_content = output.getvalue()
        output.close()

        logger.info(f"Generated CSV export for job {job_id} ({len(results)} rows)")
        return csv_content

    def generate_zip_artifact(
        self,
        job_id: int,
        pdf_dir: str | Path,
        output_path: str | Path,
    ) -> Path:
        """
        Bundle PDFs, CSV results, and metadata into a ZIP file.

        Args:
            job_id: The job ID
            pdf_dir: Directory containing the PDFs
            output_path: Path to save the ZIP file

        Returns:
            Path to the created ZIP file
        """
        pdf_dir = Path(pdf_dir)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get results and summary
        results = self.repository.get_job_results(job_id)
        summary = self.get_results_summary(job_id)

        if not results:
            raise ValueError(f"No results found for job {job_id}")

        # Get unique PDF filenames
        pdf_filenames = set(r["pdf_filename"] for r in results)

        # Create ZIP file
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add CSV export
            csv_content = self.generate_csv_export(job_id)
            zf.writestr("results.csv", csv_content)

            # Add metadata JSON
            metadata = {
                "job_id": job_id,
                "export_date": datetime.now().isoformat(),
                "summary": summary,
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))

            # Add PDFs
            pdfs_added = 0
            for filename in pdf_filenames:
                pdf_path = pdf_dir / filename
                if pdf_path.exists():
                    zf.write(pdf_path, f"pdfs/{filename}")
                    pdfs_added += 1
                else:
                    logger.warning(f"PDF not found: {pdf_path}")

            logger.info(
                f"Created ZIP artifact for job {job_id}: {output_path} "
                f"({pdfs_added} PDFs, {len(results)} results)"
            )

        return output_path

    def save_csv_to_file(
        self,
        job_id: int,
        output_path: str | Path,
    ) -> Path:
        """
        Save CSV export to a file.

        Args:
            job_id: The job ID
            output_path: Path to save the CSV file

        Returns:
            Path to the created CSV file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        csv_content = self.generate_csv_export(job_id)

        if not csv_content:
            raise ValueError(f"No results to export for job {job_id}")

        output_path.write_text(csv_content)
        logger.info(f"Saved CSV export to {output_path}")

        return output_path
