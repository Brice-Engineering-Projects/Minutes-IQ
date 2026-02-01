"""UI routes for keyword management pages."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from minutes_iq.auth.dependencies import get_current_user
from minutes_iq.db.dependencies import get_keyword_repository
from minutes_iq.db.keyword_repository import KeywordRepository
from minutes_iq.templates_config import templates

router = APIRouter(prefix="/keywords", tags=["Keyword UI"])


@router.get("", response_class=HTMLResponse)
async def keywords_list(
    request: Request,
    current_user: Annotated[dict | None, Depends(get_current_user)] = None,
):
    """Render keywords list page."""
    return templates.TemplateResponse(
        "keywords/list.html", {"request": request, "current_user": current_user}
    )


@router.get("/categories", response_class=HTMLResponse)
async def keywords_categories(
    request: Request,
    current_user: Annotated[dict | None, Depends(get_current_user)] = None,
):
    """Render keywords categories page."""
    return templates.TemplateResponse(
        "keywords/categories.html", {"request": request, "current_user": current_user}
    )


@router.get("/new", response_class=HTMLResponse)
async def keyword_create(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render keyword create form (admin only)."""
    # Check if user is admin
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    return templates.TemplateResponse(
        "keywords/form.html", {"request": request, "current_user": current_user}
    )


@router.get("/{keyword_id}", response_class=HTMLResponse)
async def keyword_detail(
    request: Request,
    keyword_id: int,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
    current_user: Annotated[dict | None, Depends(get_current_user)] = None,
):
    """Render keyword detail page."""
    keyword = keyword_repo.get_keyword_by_id(keyword_id)

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return templates.TemplateResponse(
        "keywords/detail.html",
        {"request": request, "keyword": keyword, "current_user": current_user},
    )


@router.get("/{keyword_id}/edit", response_class=HTMLResponse)
async def keyword_edit(
    request: Request,
    keyword_id: int,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render keyword edit form (admin only)."""
    # Check if user is admin
    if not current_user or current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Admin access required")

    keyword = keyword_repo.get_keyword_by_id(keyword_id)

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return templates.TemplateResponse(
        "keywords/form.html",
        {"request": request, "keyword": keyword, "current_user": current_user},
    )
