"""API endpoints for admin panel UI fragments."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from minutes_iq.auth.dependencies import get_current_user
from minutes_iq.db.auth_code_repository import AuthCodeRepository
from minutes_iq.db.auth_code_service import AuthCodeService
from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.dependencies import (
    get_auth_code_repository,
    get_auth_code_service,
    get_client_repository,
    get_keyword_repository,
    get_scraper_repository,
    get_user_repository,
)
from minutes_iq.db.keyword_repository import KeywordRepository
from minutes_iq.db.scraper_repository import ScraperRepository
from minutes_iq.db.user_repository import UserRepository

router = APIRouter(prefix="/api/admin", tags=["Admin UI API"])


@router.get("/stats", response_class=HTMLResponse)
async def get_admin_stats(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Return admin statistics cards HTML."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get real statistics
    users = user_repo.list_users()
    clients = client_repo.list_clients()
    keywords = keyword_repo.list_keywords()
    job_stats = scraper_repo.get_job_statistics()

    total_jobs = sum(job_stats.values())

    # Storage calculation (defensive - show 0 if not available)
    storage_gb = 0  # TODO: Calculate from filesystem when implemented

    html = f"""
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-500">Total Users</h3>
        <p class="mt-2 text-3xl font-semibold text-gray-900">{len(users)}</p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-500">Total Clients</h3>
        <p class="mt-2 text-3xl font-semibold text-gray-900">{len(clients)}</p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-500">Total Keywords</h3>
        <p class="mt-2 text-3xl font-semibold text-gray-900">{len(keywords)}</p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-500">Scrape Jobs</h3>
        <p class="mt-2 text-3xl font-semibold text-gray-900">{total_jobs}</p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-500">Storage Used</h3>
        <p class="mt-2 text-3xl font-semibold text-gray-900">{storage_gb} GB</p>
    </div>
    """

    return html


@router.get("/recent-activity", response_class=HTMLResponse)
async def get_recent_activity(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return recent user activity HTML."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # TODO: Implement activity tracking in backend
    # For now, return empty state
    return """
    <div class="text-center py-8">
        <svg class="mx-auto h-10 w-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <p class="mt-2 text-sm text-gray-500">No activity tracking configured</p>
    </div>
    """


@router.get("/failed-jobs", response_class=HTMLResponse)
async def get_failed_jobs(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Return failed jobs list HTML."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get all jobs and filter failed
    jobs = scraper_repo.list_jobs()
    failed_jobs = [j for j in jobs if j.get("status") == "failed"]

    # Sort by most recent first
    failed_jobs.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    # Limit to 5 most recent
    failed_jobs = failed_jobs[:5]

    if not failed_jobs:
        return """
        <div class="text-center py-8">
            <svg class="mx-auto h-10 w-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p class="mt-2 text-sm text-gray-500">No failed jobs</p>
        </div>
        """

    rows_html = ""
    for job in failed_jobs:
        created_at = datetime.fromtimestamp(job["created_at"]).strftime(
            "%Y-%m-%d %H:%M"
        )
        error_msg = job.get("error_message", "Unknown error")
        if len(error_msg) > 50:
            error_msg = error_msg[:47] + "..."

        rows_html += f"""
        <li class="py-3">
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <a href="/scraper/jobs/{job["job_id"]}" class="text-sm font-medium text-blue-600 hover:text-blue-800">
                        Job #{job["job_id"]}
                    </a>
                    <p class="text-xs text-gray-500">{created_at}</p>
                    <p class="text-xs text-red-600 mt-1">{error_msg}</p>
                </div>
            </div>
        </li>
        """

    html = f"""
    <ul class="divide-y divide-gray-200">
        {rows_html}
    </ul>
    <div class="mt-4 text-center">
        <a href="/scraper/jobs?status=failed" class="text-sm text-blue-600 hover:text-blue-800">
            View all failed jobs →
        </a>
    </div>
    """

    return html


# User Management Endpoints


@router.get("/users/list", response_class=HTMLResponse)
async def get_users_list(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    page: int = 1,
    search: str = "",
    role_filter: str = "",
    status_filter: str = "",
):
    """Return paginated users table HTML."""
    from html import escape

    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get all users
    users = user_repo.list_users()

    # Filter by search
    if search:
        users = [
            u
            for u in users
            if search.lower() in u.get("username", "").lower()
            or search.lower() in u.get("email", "").lower()
        ]

    # Filter by role
    if role_filter:
        try:
            role_id = int(role_filter)
            users = [u for u in users if u.get("role_id") == role_id]
        except ValueError:
            pass

    # Filter by status
    # Note: is_active column doesn't exist in users table yet
    # TODO: Add is_active column support
    # For now, status filter does nothing
    if status_filter:
        pass  # Placeholder until is_active column is added

    # Pagination
    per_page = 20
    total = len(users)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_users = users[start:end]

    if not paginated_users:
        return """
        <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No users found</h3>
            <p class="mt-1 text-sm text-gray-500">Try adjusting your search or filter criteria.</p>
        </div>
        """

    # Build table rows
    rows_html = ""
    for user in paginated_users:
        role_badge = (
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">Admin</span>'
            if user.get("role_id") == 1
            else '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">User</span>'
        )

        # Status badge - currently all users are considered active since is_active column doesn't exist
        # TODO: Add is_active column support
        status_badge = '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>'

        created_at = (
            datetime.fromtimestamp(user["created_at"]).strftime("%Y-%m-%d")
            if user.get("created_at")
            else "Unknown"
        )

        rows_html += f"""
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {escape(user.get("username", "Unknown"))}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {escape(user.get("email", "Unknown"))}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                {role_badge}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                {status_badge}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {created_at}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button
                    hx-get="/api/admin/users/{user["user_id"]}/edit-modal"
                    hx-target="#edit-modal"
                    class="text-blue-600 hover:text-blue-900 mr-3"
                >
                    Edit
                </button>
                {"" if user.get("is_active", True) else '<button class="text-green-600 hover:text-green-900" hx-post="/api/admin/users/' + str(user["user_id"]) + '/activate" hx-target="closest tr" hx-swap="outerHTML">Activate</button>'}
                {"" if not user.get("is_active", True) else '<button class="text-gray-600 hover:text-gray-900" hx-post="/api/admin/users/' + str(user["user_id"]) + '/deactivate" hx-target="closest tr" hx-swap="outerHTML">Deactivate</button>'}
            </td>
        </tr>
        """

    # Build query params
    query_params = (
        f"search={search}&role_filter={role_filter}&status_filter={status_filter}"
    )

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
                            hx-get="/api/admin/users/list?page={page - 1}&{query_params}"
                            hx-target="#users-table"
                            {prev_disabled}
                            class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        >
                            Previous
                        </button>
                        <span class="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300">
                            {page} / {total_pages}
                        </span>
                        <button
                            hx-get="/api/admin/users/list?page={page + 1}&{query_params}"
                            hx-target="#users-table"
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
                        Username
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Email
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Role
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                    </th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
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


@router.get("/users/{user_id}/edit-modal", response_class=HTMLResponse)
async def get_edit_user_modal(
    user_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Return edit user modal HTML."""
    from html import escape

    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    user = user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    html = f"""
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50" id="edit-user-modal">
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">Edit User</h3>
            </div>
            <form hx-put="/api/admin/users/{user_id}" hx-target="#users-table" hx-swap="innerHTML">
                <div class="px-6 py-4 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
                        <input type="text" value="{escape(user.get("username", ""))}" disabled class="block w-full rounded-md border-gray-300 bg-gray-50 sm:text-sm"/>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                        <input type="email" value="{escape(user.get("email", ""))}" disabled class="block w-full rounded-md border-gray-300 bg-gray-50 sm:text-sm"/>
                    </div>
                    <div>
                        <label for="role_id" class="block text-sm font-medium text-gray-700 mb-1">Role</label>
                        <select name="role_id" id="role_id" class="block w-full rounded-md border-gray-300 sm:text-sm">
                            <option value="2" {"selected" if user.get("role_id") == 2 else ""}>User</option>
                            <option value="1" {"selected" if user.get("role_id") == 1 else ""}>Admin</option>
                        </select>
                    </div>
                </div>
                <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                    <button
                        type="button"
                        onclick="document.getElementById('edit-user-modal').remove()"
                        class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        class="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                    >
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    </div>
    """

    return html


@router.put("/users/{user_id}", response_class=HTMLResponse)
async def update_user(
    user_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    request: Request,
):
    """Update user role."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    form_data = await request.form()
    role_id_str = form_data.get("role_id", "2")
    # Handle both str and UploadFile types from form data
    if hasattr(role_id_str, "file"):
        raise HTTPException(status_code=400, detail="Invalid role_id format")
    role_id = int(str(role_id_str))

    # Update user using the available update_user method
    # Note: UserRepository.update_user doesn't support role_id changes
    # We need to use raw SQL or add a new method
    # For now, fetch user, verify exists, then update directly
    user = user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Direct SQL update for role_id (since update_user doesn't support it)
    # This is a temporary solution - ideally add update_user_role method to repository
    from minutes_iq.db.client import get_db_connection

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET role_id = ? WHERE user_id = ?", (role_id, user_id)
        )

    # Close modal and refresh table
    from fastapi.responses import Response

    response = Response(status_code=200)
    response.headers["HX-Trigger"] = "closeModal"
    response.headers["HX-Redirect"] = "/admin/users"
    return response


@router.post("/users/{user_id}/deactivate", response_class=HTMLResponse)
async def deactivate_user(
    user_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Deactivate a user (delete from database)."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Prevent deactivating yourself
    if user_id == current_user.get("user_id"):
        raise HTTPException(
            status_code=400, detail="Cannot deactivate your own account"
        )

    # Note: Currently deletes user since there's no is_active column
    # TODO: Add is_active column to users table for soft deletes
    user_repo.delete_user(user_id)

    # Refresh users list
    from fastapi.responses import Response

    response = Response(status_code=200)
    response.headers["HX-Trigger"] = "refreshTable"
    return response


@router.post("/users/{user_id}/activate", response_class=HTMLResponse)
async def activate_user(
    user_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Activate a user."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Note: This functionality requires is_active column which doesn't exist yet
    # TODO: Add is_active column support
    # For now, return error
    raise HTTPException(status_code=501, detail="User activation not yet implemented")

    # Refresh users list
    from fastapi.responses import Response

    response = Response(status_code=200)
    response.headers["HX-Trigger"] = "refreshTable"
    return response


# Auth Codes Management Endpoints


@router.get("/auth-codes/list", response_class=HTMLResponse)
async def get_auth_codes_list(
    current_user: Annotated[dict, Depends(get_current_user)],
    auth_code_repo: Annotated[AuthCodeRepository, Depends(get_auth_code_repository)],
):
    """Return auth codes list HTML."""
    from html import escape

    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get all auth codes
    codes = auth_code_repo.list_codes(status="all")

    # Sort by created_at descending
    codes.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    if not codes:
        return """
        <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No authorization codes</h3>
            <p class="mt-1 text-sm text-gray-500">Generate a new code to allow user registration.</p>
        </div>
        """

    # Build code cards
    cards_html = ""
    import time

    current_time = time.time()

    for code in codes:
        is_used = code.get("is_used", False)
        is_active = code.get("is_active", True)
        expires_at = code.get("expires_at")
        is_expired = expires_at and current_time > expires_at

        created_at = (
            datetime.fromtimestamp(code["created_at"]).strftime("%Y-%m-%d %H:%M")
            if code.get("created_at")
            else "Unknown"
        )
        used_at = (
            datetime.fromtimestamp(code["used_at"]).strftime("%Y-%m-%d %H:%M")
            if code.get("used_at")
            else None
        )

        # Format expiration display
        if expires_at:
            expires_display = datetime.fromtimestamp(expires_at).strftime(
                "%Y-%m-%d %H:%M"
            )
        else:
            expires_display = "Never"

        # Determine status badge
        if not is_active:
            status_badge = '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Revoked</span>'
        elif is_used:
            status_badge = '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Used</span>'
        elif is_expired:
            status_badge = '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Expired</span>'
        else:
            status_badge = '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>'

        # Usage display
        current_uses = code.get("current_uses", 0)
        max_uses = code.get("max_uses", 1)
        usage_display = f"{current_uses}/{max_uses} uses"

        # Notes display
        notes = code.get("notes", "")
        notes_display = (
            f'<p class="text-xs text-gray-500 mt-1">{escape(notes)}</p>'
            if notes
            else ""
        )

        cards_html += f"""
        <div class="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center">
                        <code class="text-lg font-mono font-semibold text-gray-900 select-all">
                            {escape(code.get("code", ""))}
                        </code>
                        <button
                            onclick="navigator.clipboard.writeText('{escape(code.get("code", ""))}'); this.textContent='Copied!'; setTimeout(() => this.textContent='Copy', 2000)"
                            class="ml-3 text-sm text-blue-600 hover:text-blue-800"
                        >
                            Copy
                        </button>
                    </div>
                    <div class="mt-2 text-sm text-gray-600 space-y-1">
                        <p><span class="font-medium">Created:</span> {created_at}</p>
                        {"" if not used_at else f'<p><span class="font-medium">Used:</span> {used_at}</p>'}
                        <p><span class="font-medium">Expires:</span> {expires_display}</p>
                        <p><span class="font-medium">Usage:</span> {usage_display}</p>
                    </div>
                    {notes_display}
                    <div class="mt-3">
                        {status_badge}
                    </div>
                </div>
                <div>
                    <button
                        hx-delete="/api/admin/auth-codes/{code["code_id"]}"
                        hx-confirm="Are you sure you want to delete this authorization code?"
                        hx-target="closest div.bg-white"
                        hx-swap="outerHTML"
                        class="text-red-600 hover:text-red-900"
                    >
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
        """

    html = f"""
    <div class="p-6 space-y-4">
        {cards_html}
    </div>
    """

    return html


@router.post("/auth-codes/generate", response_class=HTMLResponse)
async def generate_auth_code(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    auth_code_service: Annotated[AuthCodeService, Depends(get_auth_code_service)],
):
    """Generate a new authorization code."""
    import logging
    from html import escape

    logger = logging.getLogger(__name__)
    logger.info("=== AUTH CODE GENERATION REQUEST STARTED ===")

    if not current_user or current_user.get("role_id") != 1:
        logger.error(f"Unauthorized access attempt. User: {current_user}")
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get form parameters
    form_data = await request.form()
    expires_in_days = form_data.get("expires_in_days", "")
    max_uses = form_data.get("max_uses", "1")
    notes = form_data.get("notes", "Generated from admin panel")

    logger.info(
        f"Form data received: expires_in_days={expires_in_days}, max_uses={max_uses}, notes={notes}"
    )

    # Convert to proper types with validation
    try:
        expires_in_days_int = (
            int(expires_in_days)
            if expires_in_days and expires_in_days.strip()
            else None
        )
        max_uses_int = int(max_uses) if max_uses else 1

        logger.info(
            f"Parsed values: expires_in_days_int={expires_in_days_int}, max_uses_int={max_uses_int}"
        )

        if expires_in_days_int is not None and expires_in_days_int < 1:
            raise HTTPException(
                status_code=400, detail="Expiration days must be at least 1"
            )
        if max_uses_int < 1:
            raise HTTPException(status_code=400, detail="Max uses must be at least 1")
    except ValueError:
        logger.error("ValueError parsing numeric parameters")
        raise HTTPException(
            status_code=400, detail="Invalid numeric parameters"
        ) from None

    # Use the service layer to create code
    logger.info("Creating code via service layer...")
    code_record = auth_code_service.create_code(
        created_by=current_user.get("user_id", 1),
        expires_in_days=expires_in_days_int,
        max_uses=max_uses_int,
        notes=notes,
    )

    logger.info(f"Code created successfully: {code_record}")

    # Get the formatted code for display
    code_string = code_record.get("code_formatted", code_record["code"])
    logger.info(f"Formatted code: {code_string}")

    # Format expiration for display
    expires_at = code_record.get("expires_at")
    if expires_at:
        expiration_display = datetime.fromtimestamp(expires_at).strftime(
            "%Y-%m-%d %H:%M"
        )
        expires_badge = f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Expires: {expiration_display}</span>'
    else:
        expiration_display = "Never"
        expires_badge = '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">No expiration</span>'

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Return HTML for the new code card (to be prepended to list)
    html = f"""
    <div class="bg-white shadow-sm rounded-lg border-2 border-green-500 p-6" id="code-{code_record["code_id"]}">
        <div class="flex items-start justify-between">
            <div class="flex-1">
                <div class="mb-3">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        ✓ New Code Generated
                    </span>
                </div>
                <div class="flex items-center">
                    <code class="text-xl font-mono font-bold text-gray-900 select-all">
                        {escape(code_string)}
                    </code>
                    <button
                        onclick="navigator.clipboard.writeText('{escape(code_string)}'); this.textContent='✓ Copied!'; setTimeout(() => this.textContent='Copy', 2000)"
                        class="ml-3 px-3 py-1 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded"
                    >
                        Copy
                    </button>
                </div>
                <div class="mt-3 text-sm text-gray-600 space-y-1">
                    <p><span class="font-medium">Created:</span> {created_at}</p>
                    <p><span class="font-medium">Expires:</span> {expiration_display}</p>
                    <p><span class="font-medium">Max uses:</span> {code_record.get('current_uses', 0)}/{max_uses_int}</p>
                    {f'<p><span class="font-medium">Notes:</span> {escape(notes)}</p>' if notes and notes != 'Generated from admin panel' else ''}
                </div>
                <div class="mt-3 flex gap-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>
                    {expires_badge}
                </div>
            </div>
            <div>
                <button
                    hx-delete="/api/admin/auth-codes/{code_record['code_id']}"
                    hx-confirm="Are you sure you want to delete this authorization code?"
                    hx-target="closest div.bg-white"
                    hx-swap="outerHTML"
                    class="text-red-600 hover:text-red-900"
                >
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    """

    logger.info(f"Returning HTML response (length: {len(html)} chars)")
    logger.info("=== AUTH CODE GENERATION REQUEST COMPLETED ===")

    return html


@router.delete("/auth-codes/{code_id}", response_class=HTMLResponse)
async def delete_auth_code(
    code_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    auth_code_repo: Annotated[AuthCodeRepository, Depends(get_auth_code_repository)],
):
    """Delete an authorization code."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Revoke the code (mark as inactive)
    auth_code_repo.revoke_code(code_id)

    # Return empty to remove the card
    return ""


# Storage Cleanup Endpoints


@router.get("/cleanup/overview", response_class=HTMLResponse)
async def get_storage_overview(
    current_user: Annotated[dict, Depends(get_current_user)],
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
):
    """Return storage overview cards HTML."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Count old jobs (>30 days)
    jobs = scraper_repo.list_jobs()
    import time

    thirty_days_ago = int(time.time()) - (30 * 24 * 60 * 60)
    old_jobs_count = len([j for j in jobs if j.get("created_at", 0) < thirty_days_ago])

    # TODO: Calculate actual storage from filesystem
    total_storage_gb = 0
    old_storage_gb = 0

    html = f"""
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-500">Total Storage</h3>
        <p class="mt-2 text-3xl font-semibold text-gray-900">{total_storage_gb} GB</p>
        <p class="mt-1 text-xs text-gray-500">Across all scrape jobs</p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-500">Old Jobs (&gt;30 Days)</h3>
        <p class="mt-2 text-3xl font-semibold text-gray-900">{old_jobs_count}</p>
        <p class="mt-1 text-xs text-gray-500">Jobs eligible for cleanup</p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-500">Reclaimable Space</h3>
        <p class="mt-2 text-3xl font-semibold text-gray-900">{old_storage_gb} GB</p>
        <p class="mt-1 text-xs text-gray-500">From old jobs</p>
    </div>
    """

    return html


@router.get("/cleanup/old-jobs", response_class=HTMLResponse)
async def get_old_jobs(
    current_user: Annotated[dict, Depends(get_current_user)],
    scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
):
    """Return old jobs table HTML."""
    import time
    from html import escape

    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get jobs older than 30 days
    jobs = scraper_repo.list_jobs()
    thirty_days_ago = int(time.time()) - (30 * 24 * 60 * 60)
    old_jobs = [j for j in jobs if j.get("created_at", 0) < thirty_days_ago]

    # Sort by created_at ascending (oldest first)
    old_jobs.sort(key=lambda x: x.get("created_at", 0))

    if not old_jobs:
        return """
        <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No old jobs found</h3>
            <p class="mt-1 text-sm text-gray-500">All jobs are less than 30 days old.</p>
        </div>
        """

    # Get client names
    clients = {c["client_id"]: c["name"] for c in client_repo.list_clients()}

    # Build table rows
    rows_html = ""
    for job in old_jobs:
        created_at = datetime.fromtimestamp(job["created_at"]).strftime("%Y-%m-%d")
        client_name = clients.get(job.get("client_id"), "Unknown")

        # Calculate age in days
        age_days = (int(time.time()) - job.get("created_at", 0)) // (24 * 60 * 60)

        status_class = {
            "completed": "bg-green-100 text-green-800",
            "failed": "bg-red-100 text-red-800",
            "pending": "bg-gray-100 text-gray-800",
            "running": "bg-blue-100 text-blue-800",
        }.get(job.get("status", ""), "bg-gray-100 text-gray-800")

        rows_html += f"""
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="checkbox" name="selected_jobs" value="{job["job_id"]}" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <a href="/scraper/jobs/{job["job_id"]}" class="text-blue-600 hover:text-blue-800">
                    Job #{job["job_id"]}
                </a>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {escape(client_name)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_class}">
                    {job.get("status", "unknown").capitalize()}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {created_at}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {age_days} days
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                0 MB
            </td>
        </tr>
        """

    html = f"""
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input type="checkbox" id="select-all" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Job ID
                    </th>
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
                        Age
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Size
                    </th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {rows_html}
            </tbody>
        </table>
    </div>
    <script>
    document.getElementById('select-all').addEventListener('change', function() {{
        const checkboxes = document.querySelectorAll('input[name="selected_jobs"]');
        checkboxes.forEach(cb => cb.checked = this.checked);
        const event = new Event('change', {{ bubbles: true }});
        checkboxes[0]?.dispatchEvent(event);
    }});
    </script>
    """

    return html


@router.post("/cleanup/bulk", response_class=HTMLResponse)
async def bulk_cleanup(
    current_user: Annotated[dict, Depends(get_current_user)],
    # request: Request,  # TODO: Uncomment when implementing actual cleanup
):
    """Perform bulk cleanup of selected jobs."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    # TODO: Implement actual cleanup logic (delete files, database records)
    # TODO: Get selected jobs from form: form_data = await request.form()
    # TODO: selected_jobs = form_data.getlist("selected_jobs")
    # For now, just return success message

    from fastapi.responses import Response

    response = Response(status_code=200)
    response.headers["HX-Trigger"] = "refreshTable"
    return response
