"""API endpoints for scraper job management UI fragments."""

import re
from datetime import datetime
from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.dependencies import (
    get_client_repository,
    get_keyword_repository,
    get_scraper_repository,
)
from minutes_iq.db.keyword_repository import KeywordRepository
from minutes_iq.db.scraper_repository import ScraperRepository

router = APIRouter(prefix="/api/scraper/jobs", tags=["Scraper Jobs UI API"])


class JobCreate(BaseModel):
    """Schema for creating a scrape job."""

    client_id: int
    start_date: str
    end_date: str
    max_scan_pages: int = 15
    include_board_minutes: bool = True
    include_packages: bool = False


@router.get("/list", response_class=HTMLResponse)
async def get_jobs_list(
    request: Request,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    page: int = 1,
    status: str = "",
    client_id: int = 0,
):
    """Return paginated jobs table HTML."""
    # Get all jobs
    jobs = scraper_repo.list_jobs()

    # Filter by status
    if status:
        jobs = [j for j in jobs if j.get("status") == status]

    # Filter by client
    if client_id:
        jobs = [j for j in jobs if j.get("client_id") == client_id]

    # Sort by created_at (newest first)
    jobs.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    # Pagination
    per_page = 20
    total = len(jobs)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_jobs = jobs[start:end]

    if not paginated_jobs:
        return """
        <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No scrape jobs found</h3>
            <p class="mt-1 text-sm text-gray-500">Get started by creating a new scrape job.</p>
            <div class="mt-6">
                <a href="/scraper/jobs/new" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                    <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                    </svg>
                    New Scrape Job
                </a>
            </div>
        </div>
        """

    # Get client names
    clients = {c["client_id"]: c["name"] for c in client_repo.list_clients()}

    # Build table HTML
    rows_html = ""
    for job in paginated_jobs:
        # Status badge
        status_class = {
            "pending": "bg-gray-100 text-gray-800",
            "running": "bg-blue-100 text-blue-800",
            "completed": "bg-green-100 text-green-800",
            "failed": "bg-red-100 text-red-800",
        }.get(job.get("status", ""), "bg-gray-100 text-gray-800")

        status_text = job.get("status", "unknown").capitalize()
        if job.get("status") == "running":
            status_badge = f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_class}"><svg class="animate-spin -ml-1 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>{status_text}</span>'
        else:
            status_badge = f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_class}">{status_text}</span>'

        # Format dates
        created_at = job.get("created_at", 0)
        created_date = (
            datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M")
            if created_at
            else "Unknown"
        )

        # Duration
        duration = "—"
        if job.get("started_at") and job.get("completed_at"):
            elapsed = job["completed_at"] - job["started_at"]
            minutes = elapsed // 60
            seconds = elapsed % 60
            duration = f"{minutes}m {seconds}s"
        elif job.get("started_at"):
            elapsed = int(datetime.now().timestamp()) - job["started_at"]
            minutes = elapsed // 60
            seconds = elapsed % 60
            duration = f"{minutes}m {seconds}s (running)"

        # Results count
        results_count = job.get("result_count", 0)

        client_name = clients.get(job.get("client_id"), "Unknown")

        rows_html += f"""
        <tr class="hover:bg-gray-50 cursor-pointer" onclick="window.location='/scraper/jobs/{job["job_id"]}'">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {client_name}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                {status_badge}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {created_date}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {duration}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {results_count}
            </td>
        </tr>
        """

    # Pagination controls
    pagination_html = ""
    if total_pages > 1:
        prev_disabled = (
            'disabled class="opacity-50 cursor-not-allowed"' if page <= 1 else ""
        )
        next_disabled = (
            'disabled class="opacity-50 cursor-not-allowed"'
            if page >= total_pages
            else ""
        )

        pagination_html = f"""
        <div class="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
            <div class="flex flex-1 justify-between sm:hidden">
                <button
                    hx-get="/api/scraper/jobs/list?page={page - 1}&status={status}&client_id={client_id}"
                    hx-target="#jobs-table"
                    {prev_disabled}
                    class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                    Previous
                </button>
                <button
                    hx-get="/api/scraper/jobs/list?page={page + 1}&status={status}&client_id={client_id}"
                    hx-target="#jobs-table"
                    {next_disabled}
                    class="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                    Next
                </button>
            </div>
            <div class="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div>
                    <p class="text-sm text-gray-700">
                        Showing <span class="font-medium">{start + 1}</span> to <span class="font-medium">{min(end, total)}</span> of{" "}
                        <span class="font-medium">{total}</span> results
                    </p>
                </div>
                <div>
                    <nav class="isolate inline-flex -space-x-px rounded-md shadow-sm">
                        <button
                            hx-get="/api/scraper/jobs/list?page={page - 1}&status={status}&client_id={client_id}"
                            hx-target="#jobs-table"
                            {prev_disabled}
                            class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        >
                            Previous
                        </button>
                        <span class="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300">
                            {page} / {total_pages}
                        </span>
                        <button
                            hx-get="/api/scraper/jobs/list?page={page + 1}&status={status}&client_id={client_id}"
                            hx-target="#jobs-table"
                            {next_disabled}
                            class="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        >
                            Next
                        </button>
                    </nav>
                </div>
            </div>
        </div>
        """

    html = f"""
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Client
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Duration
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Results
                    </th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {rows_html}
            </tbody>
        </table>
    </div>
    {pagination_html}
    """

    return html


@router.get("/preview-keywords", response_class=HTMLResponse)
async def preview_keywords(
    client_id: int,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Return HTML preview of keywords for selected client."""
    if not client_id:
        return (
            '<p class="text-sm text-gray-500">Select a client to preview keywords</p>'
        )

    keywords = keyword_repo.get_client_keywords(client_id)

    if not keywords:
        return """
        <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <p class="text-sm text-yellow-800">
                <strong>Warning:</strong> This client has no keywords configured.
                The scraper will not find any matches.
            </p>
        </div>
        """

    keywords_list = ", ".join([kw.get("keyword", "") for kw in keywords[:10]])
    if len(keywords) > 10:
        keywords_list += f" and {len(keywords) - 10} more..."

    return f"""
    <div class="p-4 bg-blue-50 border border-blue-200 rounded-md">
        <p class="text-sm font-medium text-blue-900 mb-1">
            Keywords to track ({len(keywords)} total):
        </p>
        <p class="text-sm text-blue-800">
            {keywords_list}
        </p>
    </div>
    """


@router.post("", response_class=HTMLResponse)
async def create_job(
    job_data: JobCreate,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Create a new scrape job."""
    # TODO: Get created_by from current_user when auth is integrated
    created_by = 1  # Temporary: use admin user ID

    # Create job
    job_id = scraper_repo.create_job(
        client_id=job_data.client_id,
        created_by=created_by,
        status="pending",
    )

    # Create job config
    scraper_repo.create_job_config(
        job_id=job_id,
        date_range_start=job_data.start_date,
        date_range_end=job_data.end_date,
        max_scan_pages=job_data.max_scan_pages,
        include_minutes=job_data.include_board_minutes,
        include_packages=job_data.include_packages,
    )

    # Redirect to job detail page
    response = Response(status_code=200)
    response.headers["HX-Redirect"] = f"/scraper/jobs/{job_id}"
    return response


@router.get("/{job_id}/status", response_class=HTMLResponse)
async def get_job_status(
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
):
    """Return job status card HTML (for polling)."""
    job = scraper_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

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

    # Status badge
    status_badges = {
        "pending": '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Pending</span>',
        "running": '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"><svg class="animate-spin -ml-1 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Running</span>',
        "completed": '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Completed</span>',
        "failed": '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Failed</span>',
    }

    # Build HTML
    hx_attrs = ""
    if job["status"] in ["pending", "running"]:
        hx_attrs = f'hx-get="/api/scraper/jobs/{job_id}/status" hx-trigger="every 5s" hx-swap="outerHTML"'

    html = f"""
    <div
        id="job-info-card"
        {hx_attrs}
        class="bg-white shadow-sm rounded-lg border border-gray-200 p-6"
    >
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Job Information</h2>

        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <dt class="text-sm font-medium text-gray-500">Client</dt>
                <dd class="mt-1 text-sm text-gray-900">
                    <a href="/clients/{
        job["client_id"]
    }" class="text-blue-600 hover:text-blue-800">
                        {client_name}
                    </a>
                </dd>
            </div>

            <div>
                <dt class="text-sm font-medium text-gray-500">Status</dt>
                <dd class="mt-1">
                    {status_badges.get(job["status"], status_badges["pending"])}
                </dd>
            </div>

            <div>
                <dt class="text-sm font-medium text-gray-500">Created</dt>
                <dd class="mt-1 text-sm text-gray-900">{created_at_formatted}</dd>
            </div>

            {
        ""
        if not started_at_formatted
        else f'''<div>
                <dt class="text-sm font-medium text-gray-500">Started</dt>
                <dd class="mt-1 text-sm text-gray-900">{started_at_formatted}</dd>
            </div>'''
    }

            {
        ""
        if not completed_at_formatted
        else f'''<div>
                <dt class="text-sm font-medium text-gray-500">Completed</dt>
                <dd class="mt-1 text-sm text-gray-900">{completed_at_formatted}</dd>
            </div>'''
    }

            {
        ""
        if not duration
        else f'''<div>
                <dt class="text-sm font-medium text-gray-500">Duration</dt>
                <dd class="mt-1 text-sm text-gray-900">{duration}</dd>
            </div>'''
    }
        </dl>

        {
        ""
        if not job.get("error_message")
        else f'''<div class="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <h3 class="text-sm font-medium text-red-800 mb-1">Error</h3>
            <p class="text-sm text-red-700">{job["error_message"]}</p>
        </div>'''
    }
    </div>
    """

    return html


@router.get("/{job_id}/progress", response_class=HTMLResponse)
async def get_job_progress(
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Return job progress HTML (defensive - only show data that exists)."""
    job = scraper_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get results count
    result_count = scraper_repo.get_result_count(job_id)

    # Defensive: only show data that exists
    html = f"""
    <div
        id="job-progress"
        hx-get="/api/scraper/jobs/{job_id}/progress"
        hx-trigger="every 5s"
        hx-swap="outerHTML"
        class="bg-white shadow-sm rounded-lg border border-gray-200 p-6"
    >
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Progress</h2>

        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <dt class="text-sm font-medium text-gray-500">Matches Found</dt>
                <dd class="mt-1 text-2xl font-semibold text-gray-900">{result_count}</dd>
            </div>
        </dl>

        <p class="mt-4 text-xs text-gray-500">Progress updates every 5 seconds</p>
    </div>
    """

    return html


def highlight_snippet(snippet: str, keyword: str) -> str:
    """Highlight keyword matches in snippet with <mark> tags.

    Args:
        snippet: The text snippet to highlight
        keyword: The keyword to highlight (case-insensitive)

    Returns:
        HTML-escaped snippet with matched keywords wrapped in <mark> tags
    """
    if not keyword:
        return escape(snippet)

    # Escape HTML first
    escaped_snippet = escape(snippet)

    # Use regex for case-insensitive replacement
    # Escape special regex characters in keyword
    keyword_escaped = re.escape(keyword)
    pattern = re.compile(f"({keyword_escaped})", re.IGNORECASE)

    # Replace with <mark> tags
    highlighted = pattern.sub(r"<mark>\1</mark>", escaped_snippet)

    return highlighted


@router.get("/{job_id}/results", response_class=HTMLResponse)
async def get_job_results(
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
    page: int = 1,
    keyword_filter: str = "",
    page_number_filter: str = "",
    sort_by: str = "",
    sort_order: str = "asc",
):
    """Return paginated results table HTML with filtering, sorting, and highlighting."""
    results = scraper_repo.get_job_results(job_id)

    if not results:
        return """
        <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No results yet</h3>
            <p class="mt-1 text-sm text-gray-500">Results will appear here as the scraper finds matches.</p>
        </div>
        """

    # Apply filters
    filtered_results = results

    # Filter by keyword (case-insensitive)
    if keyword_filter:
        filtered_results = [
            r
            for r in filtered_results
            if keyword_filter.lower() in r.get("keyword_matched", "").lower()
        ]

    # Filter by page number (exact match)
    if page_number_filter:
        try:
            page_num = int(page_number_filter)
            filtered_results = [
                r for r in filtered_results if r.get("page_number") == page_num
            ]
        except ValueError:
            # Invalid page number, skip filter
            pass

    # Apply sorting
    if sort_by == "pdf":
        filtered_results.sort(
            key=lambda x: x.get("pdf_filename", "").lower(),
            reverse=(sort_order == "desc"),
        )
    elif sort_by == "page":
        filtered_results.sort(
            key=lambda x: x.get("page_number", 0), reverse=(sort_order == "desc")
        )
    elif sort_by == "keyword":
        filtered_results.sort(
            key=lambda x: x.get("keyword_matched", "").lower(),
            reverse=(sort_order == "desc"),
        )

    # Pagination
    per_page = 20
    total = len(filtered_results)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = filtered_results[start:end]

    # Build query params string for pagination
    query_params = []
    if keyword_filter:
        query_params.append(f"keyword_filter={escape(keyword_filter)}")
    if page_number_filter:
        query_params.append(f"page_number_filter={escape(page_number_filter)}")
    if sort_by:
        query_params.append(f"sort_by={escape(sort_by)}")
    if sort_order:
        query_params.append(f"sort_order={escape(sort_order)}")
    query_string = "&" + "&".join(query_params) if query_params else ""

    # Build table rows
    rows_html = ""
    for result in paginated_results:
        pdf_filename = result.get("pdf_filename", "Unknown")
        page_number = result.get("page_number", "—")
        keyword = result.get("keyword_matched", "")
        snippet = result.get("snippet", "")

        # Truncate snippet before highlighting
        if len(snippet) > 100:
            snippet = snippet[:97] + "..."

        # Highlight snippet
        highlighted_snippet = highlight_snippet(
            snippet, keyword_filter if keyword_filter else ""
        )

        # Escape other fields
        escaped_filename = escape(pdf_filename)
        escaped_keyword = escape(keyword)

        # Build PDF link
        pdf_link = f"/api/scraper/jobs/{job_id}/pdfs/{escaped_filename}"

        rows_html += f"""
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 text-sm">
                <a href="{pdf_link}" target="_blank" class="text-blue-600 hover:text-blue-800">
                    {escaped_filename}
                </a>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {escape(str(page_number))}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {escaped_keyword}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
                {highlighted_snippet}
            </td>
        </tr>
        """

    # Determine sort icons for headers
    def get_sort_icon(column: str) -> str:
        """Get sort icon based on current sort state."""
        if sort_by == column:
            if sort_order == "asc":
                return "↑"
            else:
                return "↓"
        return "↕"

    # Build query params for sorting (without page)
    def get_sort_query_params(column: str) -> str:
        """Build query params for sort toggle."""
        params = []
        if keyword_filter:
            params.append(f"keyword_filter={escape(keyword_filter)}")
        if page_number_filter:
            params.append(f"page_number_filter={escape(page_number_filter)}")
        params.append(f"sort_by={column}")
        # Toggle order if same column, otherwise default to asc
        if sort_by == column:
            new_order = "desc" if sort_order == "asc" else "asc"
        else:
            new_order = "asc"
        params.append(f"sort_order={new_order}")
        return "&".join(params)

    # Pagination controls
    pagination_html = ""
    if total_pages > 1:
        prev_disabled = (
            'disabled class="opacity-50 cursor-not-allowed"' if page <= 1 else ""
        )
        next_disabled = (
            'disabled class="opacity-50 cursor-not-allowed"'
            if page >= total_pages
            else ""
        )

        pagination_html = f"""
        <div class="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
            <div class="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div>
                    <p class="text-sm text-gray-700">
                        Showing <span class="font-medium">{start + 1}</span> to <span class="font-medium">{min(end, total)}</span> of{" "}
                        <span class="font-medium">{total}</span> results
                    </p>
                </div>
                <div>
                    <nav class="isolate inline-flex -space-x-px rounded-md shadow-sm">
                        <button
                            hx-get="/api/scraper/jobs/{job_id}/results?page={page - 1}{query_string}"
                            hx-target="#results-table"
                            {prev_disabled}
                            class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        >
                            Previous
                        </button>
                        <span class="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300">
                            {page} / {total_pages}
                        </span>
                        <button
                            hx-get="/api/scraper/jobs/{job_id}/results?page={page + 1}{query_string}"
                            hx-target="#results-table"
                            {next_disabled}
                            class="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        >
                            Next
                        </button>
                    </nav>
                </div>
            </div>
        </div>
        """

    html = f"""
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <button
                            hx-get="/api/scraper/jobs/{job_id}/results?{get_sort_query_params("pdf")}"
                            hx-target="#results-table"
                            class="hover:text-gray-700 flex items-center gap-1"
                        >
                            PDF Filename <span>{get_sort_icon("pdf")}</span>
                        </button>
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <button
                            hx-get="/api/scraper/jobs/{job_id}/results?{get_sort_query_params("page")}"
                            hx-target="#results-table"
                            class="hover:text-gray-700 flex items-center gap-1"
                        >
                            Page <span>{get_sort_icon("page")}</span>
                        </button>
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <button
                            hx-get="/api/scraper/jobs/{job_id}/results?{get_sort_query_params("keyword")}"
                            hx-target="#results-table"
                            class="hover:text-gray-700 flex items-center gap-1"
                        >
                            Keyword <span>{get_sort_icon("keyword")}</span>
                        </button>
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Snippet
                    </th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {rows_html}
            </tbody>
        </table>
    </div>
    {pagination_html}
    """

    return html


@router.get("/{job_id}/summary", response_class=HTMLResponse)
async def get_job_summary(
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Return job summary HTML."""
    result_count = scraper_repo.get_result_count(job_id)
    keyword_stats = scraper_repo.get_keyword_statistics(job_id)

    # Get top 5 keywords
    top_keywords = sorted(
        keyword_stats, key=lambda x: x.get("match_count", 0), reverse=True
    )[:5]

    keywords_html = ""
    for kw in top_keywords:
        keywords_html += f"""
        <li class="flex justify-between py-2">
            <span class="text-sm text-gray-900">{kw.get("keyword", "")}</span>
            <span class="text-sm font-medium text-gray-600">{kw.get("match_count", 0)}</span>
        </li>
        """

    html = f"""
    <h2 class="text-lg font-semibold text-gray-900 mb-4">Summary</h2>

    <dl class="space-y-4">
        <div>
            <dt class="text-sm font-medium text-gray-500">Total Matches</dt>
            <dd class="mt-1 text-2xl font-semibold text-gray-900">{result_count}</dd>
        </div>

        <div>
            <dt class="text-sm font-medium text-gray-500">Keywords Found</dt>
            <dd class="mt-1 text-2xl font-semibold text-gray-900">{
        len(keyword_stats)
    }</dd>
        </div>

        {
        ""
        if not top_keywords
        else f'''<div>
            <dt class="text-sm font-medium text-gray-500 mb-2">Top Keywords</dt>
            <dd>
                <ul class="divide-y divide-gray-200">
                    {keywords_html}
                </ul>
            </dd>
        </div>'''
    }
    </dl>
    """

    return html


@router.post("/{job_id}/cancel", response_class=HTMLResponse)
async def cancel_job(
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Cancel a running job."""
    job = scraper_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")

    # Update status to failed with cancellation message
    scraper_repo.update_job_status(
        job_id=job_id, status="failed", error_message="Cancelled by user"
    )

    # Redirect to job detail
    response = Response(status_code=200)
    response.headers["HX-Redirect"] = f"/scraper/jobs/{job_id}"
    return response


@router.delete("/{job_id}", response_class=HTMLResponse)
async def delete_job(
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Delete a job (placeholder - actual deletion not implemented in repository)."""
    job = scraper_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] in ["pending", "running"]:
        raise HTTPException(
            status_code=400, detail="Cannot delete a pending or running job"
        )

    # TODO: Add delete_job method to ScraperRepository
    # For now, just redirect back to jobs list
    response = Response(status_code=200)
    response.headers["HX-Redirect"] = "/scraper/jobs"
    return response


@router.post("/{job_id}/generate-artifact", response_class=HTMLResponse)
async def generate_artifact(
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Trigger async artifact generation."""
    job = scraper_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # TODO: Implement actual artifact generation
    # For now, return a message
    return """
    <div class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
        <p class="text-sm text-yellow-800">
            Artifact generation is not yet implemented. This will create a ZIP file with all matched PDFs.
        </p>
    </div>
    """


@router.get("/{job_id}/export/csv", response_class=HTMLResponse)
async def export_csv(
    job_id: int,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Export job results as CSV (synchronous download)."""
    job = scraper_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = scraper_repo.get_job_results(job_id)

    # Build CSV content
    import csv
    import io

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "pdf_filename",
            "page_number",
            "keyword_matched",
            "snippet",
            "entities",
        ],
    )
    writer.writeheader()
    for result in results:
        # Get entities if they exist, otherwise empty string
        entities = result.get("entities_json", "") or ""

        writer.writerow(
            {
                "pdf_filename": result.get("pdf_filename", ""),
                "page_number": result.get("page_number", ""),
                "keyword_matched": result.get("keyword_matched", ""),
                "snippet": result.get("snippet", ""),
                "entities": entities,
            }
        )

    csv_content = output.getvalue()

    # Return as downloadable file
    from fastapi.responses import Response

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=job_{job_id}_results.csv"
        },
    )


@router.get("/{job_id}/pdfs/{filename}", response_class=HTMLResponse)
async def serve_pdf(
    job_id: int,
    filename: str,
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Serve PDF file for viewing (with authentication and ownership validation)."""
    from pathlib import Path

    from fastapi.responses import FileResponse

    # Validate job exists
    job = scraper_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # TODO: Validate user owns this job when auth is integrated
    # if current_user.user_id != job["created_by"]:
    #     raise HTTPException(status_code=403, detail="Access denied")

    # Construct PDF path
    # PDFs are stored in: data/scraper_output/{job_id}/pdfs/{filename}
    base_dir = Path(__file__).resolve().parent.parent.parent.parent  # Project root
    pdf_path = base_dir / "data" / "scraper_output" / str(job_id) / "pdfs" / filename

    # Verify file exists
    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found")

    # Verify it's actually in the job's directory (prevent path traversal)
    try:
        pdf_path.resolve().relative_to(
            (base_dir / "data" / "scraper_output" / str(job_id)).resolve()
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail="Access denied") from e

    # Serve the PDF
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
    )
