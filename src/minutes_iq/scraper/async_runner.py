"""
Async job execution for scraper jobs.
Uses FastAPI BackgroundTasks for simple, dependency-free background execution.
"""

import logging
import threading
import time
from typing import Any

from minutes_iq.db.scraper_service import ScraperService

logger = logging.getLogger(__name__)

# Global cancellation flags (thread-safe)
_cancellation_flags: dict[int, threading.Event] = {}
_cancellation_lock = threading.Lock()

# Job timeout in seconds (30 minutes)
JOB_TIMEOUT = 30 * 60


class JobCancelledException(Exception):
    """Raised when a job is cancelled during execution."""

    pass


class JobTimeoutException(Exception):
    """Raised when a job exceeds the maximum execution time."""

    pass


def set_cancellation_flag(job_id: int) -> None:
    """
    Set the cancellation flag for a job.

    Args:
        job_id: The job ID to cancel
    """
    with _cancellation_lock:
        if job_id not in _cancellation_flags:
            _cancellation_flags[job_id] = threading.Event()
        _cancellation_flags[job_id].set()
        logger.info(f"Cancellation flag set for job {job_id}")


def check_cancellation(job_id: int) -> None:
    """
    Check if a job has been cancelled and raise exception if so.

    Args:
        job_id: The job ID to check

    Raises:
        JobCancelledException: If the job has been cancelled
    """
    with _cancellation_lock:
        if job_id in _cancellation_flags and _cancellation_flags[job_id].is_set():
            raise JobCancelledException(f"Job {job_id} was cancelled")


def clear_cancellation_flag(job_id: int) -> None:
    """
    Clear the cancellation flag for a job.

    Args:
        job_id: The job ID
    """
    with _cancellation_lock:
        if job_id in _cancellation_flags:
            del _cancellation_flags[job_id]
            logger.debug(f"Cancellation flag cleared for job {job_id}")


def run_scrape_job_async(
    job_id: int,
    service: ScraperService,
    source_urls: list[str],
    pdf_storage_dir: str | None = None,
    storage_manager=None,
) -> None:
    """
    Execute a scrape job in the background with timeout and cancellation support.

    This function is designed to be run as a FastAPI background task.

    Args:
        job_id: The job ID to execute
        service: The ScraperService instance
        source_urls: List of URLs to scrape for PDF links
        pdf_storage_dir: Optional directory to save matched PDFs (deprecated)
        storage_manager: Optional StorageManager for organized file storage
    """
    start_time = time.time()
    logger.info(f"Starting background execution of job {job_id}")

    try:
        # Initialize cancellation flag
        with _cancellation_lock:
            if job_id not in _cancellation_flags:
                _cancellation_flags[job_id] = threading.Event()

        # Update job status to running
        service.repository.update_job_status(job_id, "running")

        # Execute scrape with periodic cancellation checks
        result = _execute_with_monitoring(
            job_id=job_id,
            service=service,
            source_urls=source_urls,
            pdf_storage_dir=pdf_storage_dir,
            storage_manager=storage_manager,
            start_time=start_time,
        )

        # Check final status
        elapsed = time.time() - start_time
        logger.info(f"Job {job_id} completed successfully in {elapsed:.1f}s: {result}")

    except JobCancelledException as e:
        logger.warning(f"Job {job_id} was cancelled: {e}")
        service.repository.update_job_status(job_id, "cancelled", str(e))

    except JobTimeoutException as e:
        logger.error(f"Job {job_id} timed out: {e}")
        service.repository.update_job_status(job_id, "failed", str(e))

    except Exception as e:
        logger.error(f"Job {job_id} failed with error: {e}", exc_info=True)
        service.repository.update_job_status(job_id, "failed", str(e))

    finally:
        # Cleanup cancellation flag
        clear_cancellation_flag(job_id)


def _execute_with_monitoring(
    job_id: int,
    service: ScraperService,
    source_urls: list[str],
    pdf_storage_dir: str | None,
    storage_manager,
    start_time: float,
) -> dict[str, Any]:
    """
    Execute scrape job with timeout and cancellation monitoring.

    Args:
        job_id: The job ID
        service: The ScraperService instance
        source_urls: List of URLs to scrape
        pdf_storage_dir: Optional PDF storage directory (deprecated)
        storage_manager: Optional StorageManager for organized file storage
        start_time: Job start timestamp

    Returns:
        Execution result dict

    Raises:
        JobCancelledException: If job is cancelled
        JobTimeoutException: If job exceeds timeout
    """
    # Get job details
    job = service.repository.get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    # Get job configuration
    config = service.repository.get_job_config(job_id)
    if not config:
        raise ValueError(f"Configuration for job {job_id} not found")

    # Get client keywords
    keywords_data = service.repository.get_client_keywords(job["client_id"])
    if not keywords_data:
        raise ValueError(f"No keywords configured for client {job['client_id']}")

    keywords = [kw["keyword"] for kw in keywords_data]
    keyword_id_map = {kw["keyword"]: kw["keyword_id"] for kw in keywords_data}

    # Track progress
    pdfs_scanned = 0
    matches_found = 0
    errors = 0

    # Import scraper functions
    from minutes_iq.scraper.core import scrape_pdf_links, stream_and_scan_pdf

    # Scrape PDF links from all source URLs
    all_pdf_links = []
    for source_url in source_urls:
        check_cancellation(job_id)
        _check_timeout(job_id, start_time)

        logger.info(f"[Job {job_id}] Scraping PDF links from {source_url}")
        pdf_links = scrape_pdf_links(
            base_url=source_url,
            date_range_start=config["date_range_start"],
            date_range_end=config["date_range_end"],
            include_minutes=config["include_minutes"],
            include_packages=config["include_packages"],
        )
        all_pdf_links.extend(pdf_links)

    logger.info(f"[Job {job_id}] Found {len(all_pdf_links)} PDFs to scan")

    # Process each PDF
    for idx, pdf_info in enumerate(all_pdf_links):
        # Check cancellation and timeout periodically
        if idx % 5 == 0:  # Check every 5 PDFs
            check_cancellation(job_id)
            _check_timeout(job_id, start_time)

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
                    service.repository.save_result(
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
                        filepath = storage_manager.get_raw_pdf_path(job_id, filename)
                        with open(filepath, "wb") as f:
                            f.write(pdf_content)
                        logger.debug(
                            f"[Job {job_id}] Saved PDF to {filepath} using StorageManager"
                        )
                    elif pdf_storage_dir:
                        # Legacy flat directory storage
                        import os

                        filepath = os.path.join(pdf_storage_dir, filename)
                        with open(filepath, "wb") as f:
                            f.write(pdf_content)
                        logger.debug(f"[Job {job_id}] Saved PDF to {filepath}")

                logger.info(
                    f"[Job {job_id}] Found {len(matches)} matches in {filename} "
                    f"({pages_scanned} pages scanned)"
                )
            else:
                logger.debug(
                    f"[Job {job_id}] No matches in {filename} "
                    f"({pages_scanned} pages scanned)"
                )

        except Exception as e:
            logger.error(f"[Job {job_id}] Error processing PDF {pdf_info['url']}: {e}")
            errors += 1
            continue

    # Commit all results
    service.repository.conn.commit()

    # Update job status to completed
    service.repository.update_job_status(job_id, "completed")

    return {
        "pdfs_scanned": pdfs_scanned,
        "matches_found": matches_found,
        "errors": errors,
    }


def _check_timeout(job_id: int, start_time: float) -> None:
    """
    Check if job has exceeded timeout.

    Args:
        job_id: The job ID
        start_time: Job start timestamp

    Raises:
        JobTimeoutException: If job has exceeded timeout
    """
    elapsed = time.time() - start_time
    if elapsed > JOB_TIMEOUT:
        raise JobTimeoutException(
            f"Job {job_id} exceeded timeout of {JOB_TIMEOUT}s (elapsed: {elapsed:.1f}s)"
        )


def cancel_job_async(job_id: int, service: ScraperService) -> bool:
    """
    Cancel a running background job.

    Args:
        job_id: The job ID to cancel
        service: The ScraperService instance

    Returns:
        True if cancellation flag was set, False if job not found or not running
    """
    job = service.repository.get_job(job_id)
    if not job:
        logger.warning(f"Cannot cancel job {job_id}: job not found")
        return False

    if job["status"] not in ("pending", "running"):
        logger.warning(f"Cannot cancel job {job_id}: status is '{job['status']}'")
        return False

    # Set cancellation flag
    set_cancellation_flag(job_id)

    # If job is pending, update status immediately
    if job["status"] == "pending":
        service.repository.update_job_status(job_id, "cancelled")

    logger.info(f"Initiated cancellation for job {job_id}")
    return True
