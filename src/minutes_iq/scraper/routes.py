"""
API endpoints for scraper job management.
"""

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import Response

from minutes_iq.auth.dependencies import get_current_user
from minutes_iq.db.dependencies import get_scraper_repository
from minutes_iq.db.highlighter_service import HighlighterService
from minutes_iq.db.results_service import ResultsService
from minutes_iq.db.scraper_repository import ScraperRepository
from minutes_iq.db.scraper_service import ScraperService
from minutes_iq.scraper.async_runner import cancel_job_async, run_scrape_job_async
from minutes_iq.scraper.schemas import (
    CleanupResponse,
    CreateArtifactRequest,
    CreateArtifactResponse,
    CreateJobRequest,
    CreateJobResponse,
    JobConfig,
    JobDetails,
    JobListResponse,
    JobStatistics,
    JobStatusResponse,
    JobSummary,
    ResultMatch,
    ResultsListResponse,
    ResultsSummaryResponse,
    StorageStatsResponse,
)
from minutes_iq.scraper.storage import StorageManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraper", tags=["scraper"])


# === Dependency Injection ===


def get_scraper_service(
    repository: Annotated[ScraperRepository, Depends(get_scraper_repository)],
) -> ScraperService:
    """Get ScraperService instance."""
    return ScraperService(repository)


def get_results_service(
    repository: Annotated[ScraperRepository, Depends(get_scraper_repository)],
) -> ResultsService:
    """Get ResultsService instance."""
    return ResultsService(repository)


def get_highlighter_service(
    repository: Annotated[ScraperRepository, Depends(get_scraper_repository)],
) -> HighlighterService:
    """Get HighlighterService instance."""
    return HighlighterService(repository)


def get_storage_manager() -> StorageManager:
    """Get StorageManager instance."""
    # TODO: Load configuration from settings
    return StorageManager(base_dir="data")


# === Job Management Endpoints ===


@router.post(
    "/jobs", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED
)
def create_scrape_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
) -> CreateJobResponse:
    """
    Create a new scrape job.

    The job will be executed in the background. Use the job_id to poll for status.
    """
    try:
        # Create job in database
        job_id = service.create_scrape_job(
            client_id=request.client_id,
            created_by=current_user["user_id"],
            date_range_start=request.date_range_start,
            date_range_end=request.date_range_end,
            max_scan_pages=request.max_scan_pages,
            include_minutes=request.include_minutes,
            include_packages=request.include_packages,
        )

        # Get storage manager
        storage = get_storage_manager()

        # Start background execution
        background_tasks.add_task(
            run_scrape_job_async,
            job_id=job_id,
            service=service,
            source_urls=request.source_urls,
            storage_manager=storage,
        )

        logger.info(f"Created scrape job {job_id} for user {current_user['user_id']}")

        return CreateJobResponse(
            job_id=job_id,
            status="pending",
            message=f"Scrape job {job_id} created and queued for execution",
        )

    except Exception as e:
        logger.error(f"Failed to create scrape job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scrape job: {str(e)}",
        ) from e


@router.get("/jobs", response_model=JobListResponse)
def list_scrape_jobs(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
    status_filter: str | None = Query(None, alias="status"),
    client_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> JobListResponse:
    """
    List scrape jobs for the current user.

    Supports filtering by status and client_id.
    """
    try:
        # Convert client_id from string to int, treating empty string as None
        client_id_int = int(client_id) if client_id and client_id.strip() else None

        jobs = service.repository.list_jobs(
            user_id=current_user["user_id"],
            client_id=client_id_int,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        job_summaries = [JobSummary(**job) for job in jobs]

        return JobListResponse(
            jobs=job_summaries,
            total=len(job_summaries),
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}",
        ) from e


@router.get("/jobs/{job_id}", response_model=JobDetails)
def get_job_details(
    job_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
    results_service: Annotated[ResultsService, Depends(get_results_service)],
) -> JobDetails:
    """
    Get full details for a specific job.

    Includes configuration and execution statistics.
    """
    try:
        # Get job
        job = service.repository.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Verify ownership
        if job["created_by"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this job",
            )

        # Get config
        config = service.repository.get_job_config(job_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration for job {job_id} not found",
            )

        # Get statistics
        summary = results_service.get_results_summary(job_id)

        return JobDetails(
            job_id=job["job_id"],
            client_id=job["client_id"],
            status=job["status"],
            created_by=job["created_by"],
            created_at=job["created_at"],
            started_at=job["started_at"],
            completed_at=job["completed_at"],
            error_message=job["error_message"],
            config=JobConfig(**config),
            statistics=JobStatistics(
                total_matches=summary["total_matches"],
                unique_pdfs=summary["unique_pdfs"],
                unique_keywords=summary["unique_keywords"],
                execution_time_seconds=summary["execution_time_seconds"],
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job details: {str(e)}",
        ) from e


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_scrape_job(
    job_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
) -> None:
    """
    Cancel a pending or running scrape job.

    Only the job creator can cancel a job.
    """
    try:
        # Get job
        job = service.repository.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Verify ownership
        if job["created_by"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this job",
            )

        # Attempt cancellation
        success = cancel_job_async(job_id, service)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job {job_id} with status '{job['status']}'",
            )

        logger.info(f"User {current_user['user_id']} cancelled job {job_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}",
        ) from e


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    job_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
) -> JobStatusResponse:
    """
    Poll the current status of a scrape job.

    Use this endpoint for progress updates during job execution.
    """
    try:
        # Get job
        job = service.repository.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Verify ownership
        if job["created_by"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this job",
            )

        # Get basic progress info
        result_count = service.repository.get_result_count(job_id)

        progress = {
            "matches_found": result_count,
        }

        return JobStatusResponse(
            job_id=job_id,
            status=job["status"],
            progress=progress,
            error_message=job["error_message"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        ) from e


# === Results Endpoints ===


@router.get("/jobs/{job_id}/results", response_model=ResultsListResponse)
def list_job_results(
    job_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
    keyword_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> ResultsListResponse:
    """
    List results for a scrape job.

    Supports filtering by keyword and pagination.
    """
    try:
        # Get job and verify ownership
        job = service.repository.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        if job["created_by"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this job",
            )

        # Get results
        all_results = service.repository.get_job_results(job_id)

        # Filter by keyword if specified
        if keyword_id is not None:
            all_results = [r for r in all_results if r["keyword_id"] == keyword_id]

        # Apply pagination
        paginated_results = all_results[offset : offset + limit]

        # Convert to ResultMatch objects
        result_matches = [ResultMatch(**r) for r in paginated_results]

        return ResultsListResponse(
            results=result_matches,
            total=len(all_results),
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list results: {str(e)}",
        ) from e


@router.get("/jobs/{job_id}/results/summary", response_model=ResultsSummaryResponse)
def get_results_summary(
    job_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
    results_service: Annotated[ResultsService, Depends(get_results_service)],
) -> ResultsSummaryResponse:
    """
    Get aggregated statistics for job results.
    """
    try:
        # Get job and verify ownership
        job = service.repository.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        if job["created_by"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this job",
            )

        # Get summary
        summary = results_service.get_results_summary(job_id)

        return ResultsSummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get results summary: {str(e)}",
        ) from e


@router.get("/jobs/{job_id}/results/export")
def export_results_csv(
    job_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
    results_service: Annotated[ResultsService, Depends(get_results_service)],
) -> Response:
    """
    Download results as CSV file.
    """
    try:
        # Get job and verify ownership
        job = service.repository.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        if job["created_by"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this job",
            )

        # Generate CSV
        csv_content = results_service.generate_csv_export(job_id)

        if not csv_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No results found for job {job_id}",
            )

        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=job_{job_id}_results.csv"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export results: {str(e)}",
        ) from e


# === Artifact Endpoints ===


@router.post(
    "/jobs/{job_id}/artifacts",
    response_model=CreateArtifactResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_job_artifact(
    job_id: int,
    request: CreateArtifactRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
) -> CreateArtifactResponse:
    """
    Generate a ZIP artifact containing job results and PDFs.

    This is a placeholder for artifact generation. Implementation requires
    file storage configuration (S3, local filesystem, etc.).
    """
    try:
        # Get job and verify ownership
        job = service.repository.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        if job["created_by"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this job",
            )

        # TODO: Implement artifact generation
        # - Create ZIP with requested components
        # - Store in configured storage backend
        # - Generate signed download URL
        # - Set expiration time

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Artifact generation not yet implemented",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create artifact: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create artifact: {str(e)}",
        ) from e


# === Storage Management Endpoints ===


@router.delete("/jobs/{job_id}/cleanup", response_model=CleanupResponse)
def cleanup_job_files(
    job_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ScraperService, Depends(get_scraper_service)],
    storage: Annotated[StorageManager, Depends(get_storage_manager)],
    include_artifacts: bool = Query(True),
) -> CleanupResponse:
    """
    Delete all files associated with a job.

    Admin-only endpoint. Removes raw PDFs, annotated PDFs, and optionally artifacts.
    """
    try:
        # Get job and verify ownership
        job = service.repository.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Admin-only check (requires is_admin field in user context)
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can cleanup job files",
            )

        # Perform cleanup
        deleted = storage.cleanup_job(job_id, include_artifacts=include_artifacts)

        logger.info(f"Admin {current_user['user_id']} cleaned up job {job_id}")

        return CleanupResponse(
            job_id=job_id,
            files_deleted=deleted,
            message=f"Cleaned up {sum(deleted.values())} files for job {job_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup job files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup job files: {str(e)}",
        ) from e


@router.get("/storage/stats", response_model=StorageStatsResponse)
def get_storage_statistics(
    current_user: Annotated[dict, Depends(get_current_user)],
    storage: Annotated[StorageManager, Depends(get_storage_manager)],
) -> StorageStatsResponse:
    """
    Get storage usage statistics.

    Admin-only endpoint showing disk space usage by file type.
    """
    try:
        # Admin-only check
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view storage statistics",
            )

        # Get statistics
        stats = storage.get_storage_stats()

        return StorageStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}",
        ) from e
