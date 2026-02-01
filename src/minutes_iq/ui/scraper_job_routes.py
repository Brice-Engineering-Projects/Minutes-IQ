"""UI routes for scraper job management pages."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.dependencies import get_client_repository, get_scraper_repository
from minutes_iq.db.scraper_repository import ScraperRepository
from minutes_iq.templates_config import templates

router = APIRouter(prefix="/scraper/jobs", tags=["Scraper Job UI"])


@router.get("", response_class=HTMLResponse)
async def jobs_list(request: Request):
    """Render scraper jobs list page."""
    return templates.TemplateResponse("scraper/jobs_list.html", {"request": request})


@router.get("/new", response_class=HTMLResponse)
async def job_create(request: Request):
    """Render scrape job creation form."""
    return templates.TemplateResponse("scraper/job_create.html", {"request": request})


@router.get("/{job_id}", response_class=HTMLResponse)
async def job_detail(
    request: Request,
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
):
    """Render scrape job detail page."""
    job = scraper_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    config = scraper_repo.get_job_config(job_id)

    # Get client name
    client = client_repo.get_client_by_id(job["client_id"])
    client_name = client.get("name", "Unknown") if client else "Unknown"

    # Format timestamps
    created_at_formatted = (
        datetime.fromtimestamp(job["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        if job.get("created_at")
        else "Unknown"
    )
    started_at_formatted = (
        datetime.fromtimestamp(job["started_at"]).strftime("%Y-%m-%d %H:%M:%S")
        if job.get("started_at")
        else None
    )
    completed_at_formatted = (
        datetime.fromtimestamp(job["completed_at"]).strftime("%Y-%m-%d %H:%M:%S")
        if job.get("completed_at")
        else None
    )

    # Calculate duration
    duration = None
    if job.get("started_at") and job.get("completed_at"):
        elapsed = job["completed_at"] - job["started_at"]
        minutes = elapsed // 60
        seconds = elapsed % 60
        duration = f"{minutes}m {seconds}s"
    elif job.get("started_at"):
        elapsed = int(datetime.now().timestamp()) - job["started_at"]
        minutes = elapsed // 60
        seconds = elapsed % 60
        duration = f"{minutes}m {seconds}s"

    # Build context
    context = {
        "request": request,
        "job": {
            "job_id": job["job_id"],
            "client_id": job["client_id"],
            "client_name": client_name,
            "status": job["status"],
            "created_at": job.get("created_at"),
            "created_at_formatted": created_at_formatted,
            "started_at": job.get("started_at"),
            "started_at_formatted": started_at_formatted,
            "completed_at": job.get("completed_at"),
            "completed_at_formatted": completed_at_formatted,
            "duration": duration,
            "error_message": job.get("error_message"),
            "start_date": config.get("date_range_start", "Unknown")
            if config
            else "Unknown",
            "end_date": config.get("date_range_end", "Unknown")
            if config
            else "Unknown",
            "max_scan_pages": config.get("max_scan_pages", 15) if config else 15,
            "include_packages": config.get("include_packages", False)
            if config
            else False,
        },
    }

    return templates.TemplateResponse("scraper/job_detail.html", context)
