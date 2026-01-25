"""
jea_meeting_web_scraper/api/clients.py
--------------------------------------

User-facing routes for viewing clients and managing favorites.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from jea_meeting_web_scraper.auth.dependencies import get_current_user
from jea_meeting_web_scraper.db.client_service import ClientService
from jea_meeting_web_scraper.db.dependencies import (
    get_client_service,
    get_favorites_repository,
)
from jea_meeting_web_scraper.db.favorites_repository import FavoritesRepository

router = APIRouter(prefix="/clients", tags=["clients"])


# Response Models
class ClientResponse(BaseModel):
    """Response model for a single client."""

    client_id: int
    name: str
    description: str | None
    website_url: str | None
    is_active: bool
    is_favorited: bool = False
    keywords: list[dict] | None = None


class ClientListResponse(BaseModel):
    """Response model for list of clients."""

    clients: list[ClientResponse]
    total: int


class FavoriteResponse(BaseModel):
    """Response model for a favorited client."""

    client_id: int
    name: str
    description: str | None
    website_url: str | None
    is_active: bool
    favorited_at: int
    keywords: list[dict] | None = None


# Endpoints
@router.get("", response_model=ClientListResponse)
async def list_clients(
    current_user: Annotated[dict, Depends(get_current_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    favorites_repo: Annotated[FavoritesRepository, Depends(get_favorites_repository)],
    include_keywords: bool = False,
):
    """
    List all active clients available to the user.
    Returns clients with favorite status for the current user.
    """
    # Get all active clients
    clients, total = client_service.list_clients(
        is_active=True, include_keywords=include_keywords, limit=1000
    )

    # Get user's favorites
    user_id = current_user["user_id"]
    favorites = favorites_repo.get_user_favorites(user_id)
    favorite_ids = {fav["client_id"] for fav in favorites}

    # Mark favorited clients
    client_responses = [
        ClientResponse(
            **client,
            is_favorited=client["client_id"] in favorite_ids,
        )
        for client in clients
    ]

    return ClientListResponse(clients=client_responses, total=total)


@router.get("/favorites", response_model=list[FavoriteResponse])
async def get_favorites(
    current_user: Annotated[dict, Depends(get_current_user)],
    favorites_repo: Annotated[FavoritesRepository, Depends(get_favorites_repository)],
):
    """
    Get all clients favorited by the current user.
    """
    user_id = current_user["user_id"]
    favorites = favorites_repo.get_user_favorites(user_id)

    return [FavoriteResponse(**fav) for fav in favorites]


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    favorites_repo: Annotated[FavoritesRepository, Depends(get_favorites_repository)],
):
    """
    Get a specific client by ID with its keywords.
    """
    client = client_service.get_client(client_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    # Only show active clients to regular users
    if not client["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    # Check if favorited by current user
    user_id = current_user["user_id"]
    is_favorited = favorites_repo.is_favorite(user_id, client_id)

    return ClientResponse(**client, is_favorited=is_favorited)


@router.post("/{client_id}/favorite", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    client_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    favorites_repo: Annotated[FavoritesRepository, Depends(get_favorites_repository)],
):
    """
    Add a client to the current user's favorites.
    """
    # Verify client exists and is active
    client = client_service.get_client(client_id)
    if not client or not client["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    user_id = current_user["user_id"]

    try:
        success = favorites_repo.add_favorite(user_id, client_id)
        if not success:
            return {"message": "Client is already in your favorites"}
        return {"message": "Client added to favorites"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete("/{client_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    client_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    favorites_repo: Annotated[FavoritesRepository, Depends(get_favorites_repository)],
):
    """
    Remove a client from the current user's favorites.
    """
    user_id = current_user["user_id"]
    success = favorites_repo.remove_favorite(user_id, client_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client is not in your favorites",
        )
