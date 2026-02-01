"""UI routes for admin panel pages."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from minutes_iq.auth.dependencies import get_current_user
from minutes_iq.templates_config import templates

router = APIRouter(prefix="/admin", tags=["Admin UI"])


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render admin dashboard (admin only)."""
    # Check if user is admin
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    return templates.TemplateResponse(
        "admin/dashboard.html", {"request": request, "current_user": current_user}
    )


@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render user management page (admin only)."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    return templates.TemplateResponse(
        "admin/users.html", {"request": request, "current_user": current_user}
    )


@router.get("/auth-codes", response_class=HTMLResponse)
async def auth_codes_list(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render authorization codes management page (admin only)."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    return templates.TemplateResponse(
        "admin/auth_codes.html", {"request": request, "current_user": current_user}
    )


@router.get("/cleanup", response_class=HTMLResponse)
async def storage_cleanup(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render storage cleanup page (admin only)."""
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    return templates.TemplateResponse(
        "admin/cleanup.html", {"request": request, "current_user": current_user}
    )
