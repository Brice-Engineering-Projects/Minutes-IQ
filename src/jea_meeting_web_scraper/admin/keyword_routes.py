"""
jea_meeting_web_scraper/admin/keyword_routes.py
-----------------------------------------------

Admin routes for keyword management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from jea_meeting_web_scraper.auth.dependencies import get_current_admin_user
from jea_meeting_web_scraper.db.dependencies import get_keyword_service
from jea_meeting_web_scraper.db.keyword_service import KeywordService

router = APIRouter(prefix="/admin/keywords", tags=["admin", "keywords"])


# Request/Response Models
class KeywordCreate(BaseModel):
    """Request model for creating a keyword."""

    keyword: str = Field(..., min_length=2, max_length=100)
    category: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=500)


class KeywordUpdate(BaseModel):
    """Request model for updating a keyword."""

    keyword: str | None = Field(None, min_length=2, max_length=100)
    category: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class KeywordResponse(BaseModel):
    """Response model for a single keyword."""

    keyword_id: int
    keyword: str
    category: str | None
    description: str | None
    is_active: bool
    created_at: int
    created_by: int


class KeywordListResponse(BaseModel):
    """Response model for list of keywords."""

    keywords: list[KeywordResponse]
    total: int
    limit: int
    offset: int


class KeywordUsageResponse(BaseModel):
    """Response model for keyword usage information."""

    keyword_id: int
    keyword: str
    clients: list[dict]


# Endpoints
@router.post("", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword(
    keyword: KeywordCreate,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
):
    """
    Create a new keyword for filtering meeting minutes.
    Requires admin privileges.
    """
    success, error_msg, keyword_data = keyword_service.create_keyword(
        keyword=keyword.keyword,
        created_by=admin_user["user_id"],
        category=keyword.category,
        description=keyword.description,
    )

    if not success or not keyword_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return KeywordResponse(**keyword_data)


@router.get("", response_model=KeywordListResponse)
async def list_keywords(
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
    is_active: bool | None = None,
    category: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    List all keywords with optional filtering.
    Requires admin privileges.
    """
    keywords, total = keyword_service.list_keywords(
        is_active=is_active, category=category, limit=limit, offset=offset
    )

    return KeywordListResponse(
        keywords=[KeywordResponse(**k) for k in keywords],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/search")
async def search_keywords(
    q: str,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
    limit: int = 50,
):
    """
    Search for keywords by partial text match.
    Requires admin privileges.
    """
    keywords = keyword_service.search_keywords(search_text=q, limit=limit)
    return {"query": q, "results": [KeywordResponse(**k) for k in keywords]}


@router.get("/categories")
async def get_categories(
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
):
    """
    Get all unique keyword categories.
    Requires admin privileges.
    """
    categories = keyword_service.get_categories()
    return {"categories": categories}


@router.get("/suggest")
async def suggest_keywords(
    q: str,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
    limit: int = 10,
):
    """
    Get keyword suggestions for autocomplete.
    Requires admin privileges.
    """
    suggestions = keyword_service.suggest_keywords(text=q, limit=limit)
    return {"query": q, "suggestions": [KeywordResponse(**k) for k in suggestions]}


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
):
    """
    Get a specific keyword by ID.
    Requires admin privileges.
    """
    keyword = keyword_service.get_keyword(keyword_id)

    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found"
        )

    return KeywordResponse(**keyword)


@router.put("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    keyword_id: int,
    update: KeywordUpdate,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
):
    """
    Update a keyword's information.
    Requires admin privileges.
    """
    success, error_msg, keyword_data = keyword_service.update_keyword(
        keyword_id=keyword_id,
        keyword=update.keyword,
        category=update.category,
        description=update.description,
        is_active=update.is_active,
    )

    if not success or not keyword_data:
        if error_msg == "Keyword not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return KeywordResponse(**keyword_data)


@router.delete("/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    keyword_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
):
    """
    Delete a keyword (soft delete - sets is_active to false).
    Requires admin privileges.
    """
    success, error_msg = keyword_service.delete_keyword(keyword_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)


@router.get("/{keyword_id}/usage", response_model=KeywordUsageResponse)
async def get_keyword_usage(
    keyword_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    keyword_service: Annotated[KeywordService, Depends(get_keyword_service)],
):
    """
    Get all clients using a specific keyword.
    Requires admin privileges.
    """
    success, error_msg, clients = keyword_service.get_keyword_usage(keyword_id)

    if not success or not clients:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)

    # Get keyword info
    keyword = keyword_service.get_keyword(keyword_id)

    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found"
        )

    return KeywordUsageResponse(
        keyword_id=keyword_id, keyword=keyword["keyword"], clients=clients
    )
