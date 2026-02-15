"""Client UI routes - renders HTML pages."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from minutes_iq.auth.dependencies import get_current_user
from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.dependencies import get_client_repository
from minutes_iq.templates_config import templates

router = APIRouter(prefix="/clients", tags=["Client UI"])


@router.get("", response_class=HTMLResponse)
async def clients_list(request: Request):
    """Render the clients list page."""
    return templates.TemplateResponse("clients/list.html", {"request": request})


@router.get("/favorites", response_class=HTMLResponse)
async def clients_favorites(request: Request):
    """Render the favorites page."""
    return templates.TemplateResponse("clients/favorites.html", {"request": request})


@router.get("/new", response_class=HTMLResponse)
async def new_client(request: Request):
    """Render the new client form (admin only)."""
    # TODO: Add auth check for admin role
    return templates.TemplateResponse("clients/form.html", {"request": request})


@router.get("/{client_id}", response_class=HTMLResponse)
async def client_detail(
    request: Request,
    client_id: int,
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render the client detail page."""
    client = client_repo.get_client_by_id(client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return templates.TemplateResponse(
        "clients/detail.html",
        {"request": request, "client": client, "current_user": current_user},
    )


@router.get("/{client_id}/edit", response_class=HTMLResponse)
async def edit_client(
    request: Request,
    client_id: int,
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
):
    """Render the edit client form (admin only)."""
    # TODO: Add auth check for admin role
    client = client_repo.get_client_by_id(client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return templates.TemplateResponse(
        "clients/form.html", {"request": request, "client": client}
    )
