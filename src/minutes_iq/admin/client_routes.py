"""
minutes_iq/admin/client_routes.py
----------------------------------------------

Admin routes for client management (agencies being tracked).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from minutes_iq.auth.dependencies import get_current_admin_user
from minutes_iq.db.client_service import ClientService
from minutes_iq.db.client_url_repository import ClientUrlRepository
from minutes_iq.db.dependencies import get_client_service, get_client_url_repository

router = APIRouter(prefix="/admin/clients", tags=["admin", "clients"])


# Request/Response Models
class ClientCreate(BaseModel):
    """Request model for creating a client."""

    name: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)


class ClientUpdate(BaseModel):
    """Request model for updating a client."""

    name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None


class ClientUrlResponse(BaseModel):
    """Response model for a client URL."""

    id: int
    alias: str
    url: str
    is_active: bool
    last_scraped_at: int | None
    created_at: int
    updated_at: int | None


class ClientResponse(BaseModel):
    """Response model for a single client."""

    client_id: int
    name: str
    description: str | None
    is_active: bool
    created_at: int
    created_by: int
    updated_at: int | None
    keywords: list[dict] | None = None
    urls: list[ClientUrlResponse] = []


class ClientListResponse(BaseModel):
    """Response model for list of clients."""

    clients: list[ClientResponse]
    total: int
    limit: int
    offset: int


class ClientKeywordAssociation(BaseModel):
    """Request model for associating a keyword with a client."""

    keyword_id: int


# Endpoints
@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client: ClientCreate,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
):
    """
    Create a new client (government agency to track).
    Requires admin privileges.
    """
    success, error_msg, client_data = client_service.create_client(
        name=client.name,
        created_by=admin_user["user_id"],
        description=client.description,
    )

    if not success or not client_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Get URLs for this client
    urls = client_url_repo.get_client_urls(client_data["client_id"])
    url_responses = [ClientUrlResponse(**url) for url in urls]

    return ClientResponse(**client_data, keywords=None, urls=url_responses)


@router.get("", response_model=ClientListResponse)
async def list_clients(
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
    is_active: bool | None = None,
    include_keywords: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    """
    List all clients with optional filtering.
    Requires admin privileges.
    """
    clients, total = client_service.list_clients(
        is_active=is_active,
        include_keywords=include_keywords,
        limit=limit,
        offset=offset,
    )

    # Add URLs for each client
    client_responses = []
    for client in clients:
        urls = client_url_repo.get_client_urls(client["client_id"])
        url_responses = [ClientUrlResponse(**url) for url in urls]
        client_responses.append(ClientResponse(**client, urls=url_responses))

    return ClientListResponse(
        clients=client_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
):
    """
    Get a specific client by ID with its keywords.
    Requires admin privileges.
    """
    client = client_service.get_client(client_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    # Get URLs for this client
    urls = client_url_repo.get_client_urls(client_id)
    url_responses = [ClientUrlResponse(**url) for url in urls]

    return ClientResponse(**client, urls=url_responses)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    update: ClientUpdate,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
):
    """
    Update a client's information.
    Requires admin privileges.
    """
    success, error_msg, client_data = client_service.update_client(
        client_id=client_id,
        name=update.name,
        description=update.description,
        is_active=update.is_active,
    )

    if not success or not client_data:
        if error_msg == "Client not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Get URLs for this client
    urls = client_url_repo.get_client_urls(client_id)
    url_responses = [ClientUrlResponse(**url) for url in urls]

    return ClientResponse(**client_data, keywords=None, urls=url_responses)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
):
    """
    Delete a client (soft delete - sets is_active to false).
    Requires admin privileges.
    """
    success, error_msg = client_service.delete_client(client_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)


@router.post("/{client_id}/keywords", status_code=status.HTTP_201_CREATED)
async def add_keyword_to_client(
    client_id: int,
    association: ClientKeywordAssociation,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
):
    """
    Associate a keyword with a client.
    Requires admin privileges.
    """
    success, error_msg = client_service.add_keyword_to_client(
        client_id=client_id,
        keyword_id=association.keyword_id,
        added_by=admin_user["user_id"],
    )

    if not success:
        if error_msg and "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return {"message": "Keyword added to client successfully"}


@router.delete(
    "/{client_id}/keywords/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_keyword_from_client(
    client_id: int,
    keyword_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
):
    """
    Remove a keyword association from a client.
    Requires admin privileges.
    """
    success, error_msg = client_service.remove_keyword_from_client(
        client_id=client_id, keyword_id=keyword_id
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)


@router.get("/{client_id}/keywords")
async def get_client_keywords(
    client_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
):
    """
    Get all keywords associated with a client.
    Requires admin privileges.
    """
    success, error_msg, keywords = client_service.get_client_keywords(client_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)

    return {"client_id": client_id, "keywords": keywords}
