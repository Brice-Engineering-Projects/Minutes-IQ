"""Error handlers for custom error pages."""

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="src/minutes_iq/templates")


async def not_found_handler(request: Request, exc: Exception) -> HTMLResponse:
    """Handle 404 Not Found errors."""
    return templates.TemplateResponse(
        "errors/404.html",
        {
            "request": request,
        },
        status_code=404,
    )


async def forbidden_handler(request: Request, exc: Exception) -> HTMLResponse:
    """Handle 403 Forbidden errors."""
    return templates.TemplateResponse(
        "errors/403.html",
        {
            "request": request,
        },
        status_code=403,
    )


async def internal_server_error_handler(
    request: Request, exc: Exception
) -> HTMLResponse:
    """Handle 500 Internal Server Error."""
    # TODO: Log the error with proper error tracking (e.g., Sentry)
    # import logging
    # logging.error(f"Internal server error: {exc}", exc_info=True)

    return templates.TemplateResponse(
        "errors/500.html",
        {
            "request": request,
            "error_id": None,  # TODO: Generate unique error ID for tracking
        },
        status_code=500,
    )


async def unauthorized_handler(
    request: Request, exc: Exception
) -> RedirectResponse | HTMLResponse:
    """
    Handle 401 Unauthorized errors.

    For UI routes (HTML requests), redirect to landing page.
    For API routes (JSON requests), return 401 with message.
    """
    # Check if this is an API request (JSON) or UI request (HTML)
    accept_header = request.headers.get("accept", "")
    is_htmx = request.headers.get("hx-request") == "true"

    # If it's an API request or htmx request, return JSON/HTML error
    if (
        "application/json" in accept_header
        or is_htmx
        or request.url.path.startswith("/api/")
    ):
        return HTMLResponse(
            content="<div class='text-red-600'>Not authenticated. Please log in.</div>",
            status_code=401,
        )

    # For UI requests, redirect to landing page
    return RedirectResponse(url="/", status_code=303)
