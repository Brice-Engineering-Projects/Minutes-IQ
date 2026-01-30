"""
Service layer for scraper job orchestration.
Integrates core scraper functions with database operations.
"""

import logging
from typing import Any

from minutes_iq.db.scraper_repository import ScraperRepository
from minutes_iq.scraper.core import (
    scrape_pdf_links,
    stream_and_scan_pdf,
)
from minutes_iq.scraper.highlighter import highlight_job_results

logger = logging.getLogger(__name__)


class ScraperService:
    """Service for orchestrating scraper jobs."""

    def __init__(self, repository: ScraperRepository):
        self.repository = repository

    def create_scrape_job(
        self,
        client_id: int,
        created_by: int,
        date_range_start: str | None = None,
        date_range_end: str | None = None,
        max_scan_pages: int | None = None,
        include_minutes: bool = True,
        include_packages: bool = True,
    ) -> int:
        """
        Create a new scrape job with configuration.

        Args:
            client_id: The client ID to scrape for
            created_by: The user ID who created the job
            date_range_start: Start date in YYYY-MM format
            date_range_end: End date in YYYY-MM format
            max_scan_pages: Maximum pages to scan per PDF
            include_minutes: Whether to include minutes PDFs
            include_packages: Whether to include package PDFs

        Returns:
            The job_id of the created job
        """
        # Create job
        job_id = self.repository.create_job(
            client_id=client_id,
            created_by=created_by,
            status="pending",
        )

        # Create job configuration
        self.repository.create_job_config(
            job_id=job_id,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            max_scan_pages=max_scan_pages,
            include_minutes=include_minutes,
            include_packages=include_packages,
        )

        self.repository.conn.commit()
        logger.info(f"Created scrape job {job_id} for client {client_id}")
        return job_id

    def execute_scrape_job(
        self,
        job_id: int,
        source_urls: list[str],
        pdf_storage_dir: str | None = None,
        storage_manager=None,
    ) -> dict[str, Any]:
        """
        Execute a scrape job.

        Args:
            job_id: The job ID to execute
            source_urls: List of URLs to scrape for PDF links
            pdf_storage_dir: Optional directory to save matched PDFs (deprecated)
            storage_manager: Optional StorageManager for organized file storage

        Returns:
            Dict with execution summary (pdfs_scanned, matches_found, errors)
        """
        # Get job details
        job = self.repository.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job["status"] != "pending":
            raise ValueError(f"Job {job_id} is not in pending status")

        # Get job configuration
        config = self.repository.get_job_config(job_id)
        if not config:
            raise ValueError(f"Configuration for job {job_id} not found")

        # Get client keywords
        keywords_data = self.repository.get_client_keywords(job["client_id"])
        if not keywords_data:
            logger.warning(f"No keywords found for client {job['client_id']}")
            self.repository.update_job_status(
                job_id, "failed", "No keywords configured for client"
            )
            return {"pdfs_scanned": 0, "matches_found": 0, "errors": 1}

        # Extract keyword strings and create keyword lookup
        keywords = [kw["keyword"] for kw in keywords_data]
        keyword_id_map = {kw["keyword"]: kw["keyword_id"] for kw in keywords_data}

        # Update job status to running
        self.repository.update_job_status(job_id, "running")

        # Track progress
        pdfs_scanned = 0
        matches_found = 0
        errors = 0

        try:
            # Scrape PDF links from all source URLs
            all_pdf_links = []
            for source_url in source_urls:
                logger.info(f"Scraping PDF links from {source_url}")
                pdf_links = scrape_pdf_links(
                    base_url=source_url,
                    date_range_start=config["date_range_start"],
                    date_range_end=config["date_range_end"],
                    include_minutes=config["include_minutes"],
                    include_packages=config["include_packages"],
                )
                all_pdf_links.extend(pdf_links)

            logger.info(f"Found {len(all_pdf_links)} PDFs to scan for job {job_id}")

            # Process each PDF
            for pdf_info in all_pdf_links:
                try:
                    url = pdf_info["url"]
                    filename = pdf_info["filename"]

                    # Scan PDF for keywords
                    matches, pdf_content, pages_scanned = stream_and_scan_pdf(
                        url=url,
                        keywords=keywords,
                        max_pages=config["max_scan_pages"],
                    )

                    pdfs_scanned += 1

                    # Save matches to database
                    if matches:
                        for match in matches:
                            keyword_id = keyword_id_map[match["keyword"]]
                            self.repository.save_result(
                                job_id=job_id,
                                pdf_filename=match["filename"],
                                page_number=match["page"],
                                keyword_id=keyword_id,
                                snippet=match["snippet"],
                                entities=match["entities"],
                            )
                            matches_found += 1

                        # Download PDF using storage manager (preferred) or legacy path
                        if pdf_content:
                            if storage_manager:
                                # Use storage manager for organized storage
                                storage_manager.ensure_job_directories(job_id)
                                filepath = storage_manager.get_raw_pdf_path(
                                    job_id, filename
                                )
                                with open(filepath, "wb") as f:
                                    f.write(pdf_content)
                                logger.info(
                                    f"Saved PDF to {filepath} using StorageManager"
                                )
                            elif pdf_storage_dir:
                                # Legacy flat directory storage
                                import os

                                filepath = os.path.join(pdf_storage_dir, filename)
                                with open(filepath, "wb") as f:
                                    f.write(pdf_content)
                                logger.info(f"Saved PDF to {filepath}")

                        logger.info(
                            f"Found {len(matches)} matches in {filename} "
                            f"({pages_scanned} pages scanned)"
                        )
                    else:
                        logger.debug(
                            f"No matches in {filename} ({pages_scanned} pages scanned)"
                        )

                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_info['url']}: {e}")
                    errors += 1
                    continue

            # Commit all results
            self.repository.conn.commit()

            # Update job status to completed
            self.repository.update_job_status(job_id, "completed")
            logger.info(
                f"Job {job_id} completed: {pdfs_scanned} PDFs scanned, "
                f"{matches_found} matches found, {errors} errors"
            )

            return {
                "pdfs_scanned": pdfs_scanned,
                "matches_found": matches_found,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            self.repository.update_job_status(job_id, "failed", str(e))
            return {
                "pdfs_scanned": pdfs_scanned,
                "matches_found": matches_found,
                "errors": errors + 1,
            }

    def get_job_status(self, job_id: int) -> dict[str, Any]:
        """
        Get the current status of a scrape job.

        Args:
            job_id: The job ID

        Returns:
            Dict with job details and progress
        """
        job = self.repository.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        config = self.repository.get_job_config(job_id)
        results = self.repository.get_job_results(job_id)

        return {
            "job": job,
            "config": config,
            "matches_found": len(results),
        }

    def get_job_results(self, job_id: int) -> list[dict[str, Any]]:
        """
        Get all results for a scrape job.

        Args:
            job_id: The job ID

        Returns:
            List of result dicts
        """
        return self.repository.get_job_results(job_id)

    def cancel_job(self, job_id: int) -> bool:
        """
        Cancel a running or pending scrape job.

        Args:
            job_id: The job ID to cancel

        Returns:
            True if job was cancelled, False if job was not in cancellable state
        """
        job = self.repository.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Only pending or running jobs can be cancelled
        if job["status"] not in ("pending", "running"):
            logger.warning(f"Cannot cancel job {job_id} with status '{job['status']}'")
            return False

        self.repository.update_job_status(job_id, "cancelled")
        logger.info(f"Cancelled job {job_id}")
        return True

    def highlight_pdfs(
        self,
        job_id: int,
        pdf_dir: str,
        output_base_dir: str,
    ) -> dict[str, Any]:
        """
        Highlight PDFs for all results from a scrape job.

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

        # Use highlighter to process PDFs
        summary = highlight_job_results(
            job_id=job_id,
            pdf_dir=pdf_dir,
            output_base_dir=output_base_dir,
            results=results,
        )

        logger.info(f"Highlighted PDFs for job {job_id}: {summary}")
        return summary
