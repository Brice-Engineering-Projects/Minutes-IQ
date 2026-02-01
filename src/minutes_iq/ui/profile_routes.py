"""Profile UI routes - renders full pages for user profile management."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from minutes_iq.auth.dependencies import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile UI"])
templates = Jinja2Templates(directory="src/minutes_iq/templates")


@router.get("", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render the user profile page."""
    # Note: created_at field doesn't exist in users table
    # Will display "Date unavailable" in template
    return templates.TemplateResponse(
        "profile/profile.html",
        {
            "request": request,
            "current_user": current_user,
            "created_at": None,  # TODO: Add when created_at column is added to users table
        },
    )


@router.get("/edit", response_class=HTMLResponse)
async def edit_profile_page(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render the edit profile page."""
    return templates.TemplateResponse(
        "profile/profile_edit.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )
