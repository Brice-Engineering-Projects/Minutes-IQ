"""Client API routes for UI - returns HTML fragments."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from minutes_iq.auth.dependencies import get_current_user
from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.client_url_repository import ClientUrlRepository
from minutes_iq.db.dependencies import (
    get_client_repository,
    get_client_url_repository,
    get_favorites_repository,
    get_keyword_repository,
)
from minutes_iq.db.favorites_repository import FavoritesRepository
from minutes_iq.db.keyword_repository import KeywordRepository

router = APIRouter(prefix="/api/clients", tags=["Client API"])


@router.get("/all")
async def get_all_clients(
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
):
    """Get all active clients as JSON for dropdowns."""
    clients = client_repo.list_clients(is_active=True, limit=1000)
    return [
        {
            "client_id": c["client_id"],
            "name": c["name"],
        }
        for c in clients
    ]


@router.get("/list", response_class=HTMLResponse)
async def get_clients_list(
    request: Request,
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    page: int = 1,
    search: str = "",
):
    """Get paginated client list as HTML."""
    clients = client_repo.list_clients()

    # Filter by search if provided
    if search:
        clients = [c for c in clients if search.lower() in c.get("name", "").lower()]

    # Pagination
    per_page = 20
    total = len(clients)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_clients = clients[start:end]

    # Empty state
    if not paginated_clients:
        return """
        <div class="bg-white shadow-sm rounded-lg border border-gray-200 p-12">
            <div class="text-center">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No clients found</h3>
                <p class="mt-1 text-sm text-gray-500">Get started by creating a new client.</p>
                <div class="mt-6">
                    <a href="/clients/new" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                        <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                        </svg>
                        New Client
                    </a>
                </div>
            </div>
        </div>
        """

    # Render table
    rows_html = ""
    for client in paginated_clients:
        rows_html += f"""
        <tr class="hover:bg-gray-50 cursor-pointer" onclick="window.location.href='/clients/{client["client_id"]}'">
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div>
                        <div class="text-sm font-medium text-gray-900">{client.get("name", "N/A")}</div>
                        <div class="text-sm text-gray-500">{client.get("description", "")[:50]}...</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {client.get("keyword_count", 0)} keywords
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <button
                    hx-post="/api/clients/{client["client_id"]}/favorite"
                    hx-swap="outerHTML"
                    onclick="event.stopPropagation()"
                    class="text-gray-400 hover:text-red-500"
                >
                    <svg class="w-5 h-5 {"fill-current text-red-500" if client.get("is_favorite") else ""}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                    </svg>
                </button>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {"bg-green-100 text-green-800" if client.get("is_active") else "bg-gray-100 text-gray-800"}">
                    {"Active" if client.get("is_active") else "Inactive"}
                </span>
            </td>
        </tr>
        """

    # Pagination controls
    pagination_html = ""
    if total_pages > 1:
        pagination_html = f"""
        <div class="px-6 py-4 flex items-center justify-between border-t border-gray-200">
            <div class="flex-1 flex justify-between sm:hidden">
                {'<button hx-get="/api/clients/list?page=' + str(page - 1) + "&search=" + search + '" hx-target="#clients-table" class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">Previous</button>' if page > 1 else ""}
                {'<button hx-get="/api/clients/list?page=' + str(page + 1) + "&search=" + search + '" hx-target="#clients-table" class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">Next</button>' if page < total_pages else ""}
            </div>
            <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                    <p class="text-sm text-gray-700">
                        Showing <span class="font-medium">{start + 1}</span> to <span class="font-medium">{min(end, total)}</span> of <span class="font-medium">{total}</span> results
                    </p>
                </div>
                <div>
                    <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        {'<button hx-get="/api/clients/list?page=' + str(page - 1) + "&search=" + search + '" hx-target="#clients-table" class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">Previous</button>' if page > 1 else ""}
                        <span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                            Page {page} of {total_pages}
                        </span>
                        {'<button hx-get="/api/clients/list?page=' + str(page + 1) + "&search=" + search + '" hx-target="#clients-table" class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">Next</button>' if page < total_pages else ""}
                    </nav>
                </div>
            </div>
        </div>
        """

    html = f"""
    <div class="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Keywords</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Favorite</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {rows_html}
            </tbody>
        </table>
        {pagination_html}
    </div>
    """

    return html


@router.get("/favorites", response_class=HTMLResponse)
async def get_favorites_list(
    request: Request,
):
    """Get user's favorite clients as HTML."""
    # TODO: Get current user ID from auth and query favorites
    # For now, return empty state
    return """
    <div class="bg-white shadow-sm rounded-lg border border-gray-200 p-12">
        <div class="text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No favorites yet</h3>
            <p class="mt-1 text-sm text-gray-500">Click the heart icon on any client to add them to your favorites.</p>
            <div class="mt-6">
                <a href="/clients" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                    Browse Clients
                </a>
            </div>
        </div>
    </div>
    """


@router.get("/{client_id}/keywords", response_class=HTMLResponse)
async def get_client_keywords(
    client_id: int,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Get client's keywords as HTML."""
    # Get keywords for this client
    keywords = keyword_repo.get_client_keywords(client_id)

    if not keywords:
        return """
        <div class="text-center py-8">
            <p class="text-sm text-gray-500">No keywords assigned yet</p>
        </div>
        """

    # Build keyword list HTML
    items_html = ""
    for kw in keywords:
        items_html += f"""
        <li class="py-2">
            <a href="/keywords/{kw["keyword_id"]}" class="text-sm text-blue-600 hover:text-blue-800">
                {kw.get("keyword", "")}
            </a>
        </li>
        """

    return f"""
    <ul class="divide-y divide-gray-200">
        {items_html}
    </ul>
    """


@router.get("/{client_id}/scrape-jobs", response_class=HTMLResponse)
async def get_client_scrape_jobs(client_id: int):
    """Get client's recent scrape jobs as HTML."""
    # TODO: Implement scrape jobs query
    return """
    <div class="text-center py-8">
        <p class="text-sm text-gray-500">No scrape jobs yet</p>
    </div>
    """


@router.post("", response_class=HTMLResponse)
async def create_client(
    request: Request,
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Create a new client."""
    from fastapi.responses import Response

    # Get form data
    form_data = await request.form()
    name = str(form_data.get("name", "")).strip()
    description_raw = form_data.get("description", "")
    description = str(description_raw).strip() or None if description_raw else None
    is_active = form_data.get("is_active") == "on"
    keyword_ids = form_data.getlist("keyword_ids")

    # Get URL data
    url_aliases = form_data.getlist("url_alias[]")
    url_values = form_data.getlist("url_value[]")
    url_is_active = form_data.getlist("url_is_active[]")

    if not name:
        return '<div class="p-4 bg-red-50 border border-red-200 rounded-md"><p class="text-sm text-red-800">Client name is required</p></div>'

    # Create client
    # TODO: Get created_by from current_user when auth is integrated
    created_by_user = 1  # Temporary: use admin user ID
    client = client_repo.create_client(
        name=name,
        description=description,
        is_active=is_active,
        created_by=created_by_user,
    )
    client_id = client["client_id"]

    # Add URLs to client
    for i, (alias, url_value) in enumerate(zip(url_aliases, url_values, strict=False)):
        if alias and url_value:
            url_active = i < len(url_is_active)
            try:
                client_url_repo.create_url(
                    client_id=client_id,
                    alias=str(alias),
                    url=str(url_value),
                    is_active=url_active,
                )
            except Exception:
                pass  # Skip invalid URLs

    # Add keywords to client
    if keyword_ids:
        for keyword_id_raw in keyword_ids:
            try:
                keyword_id = int(str(keyword_id_raw))
                keyword_repo.add_keyword_to_client(
                    client_id, keyword_id, created_by_user
                )
            except (ValueError, TypeError):
                pass  # Skip invalid keyword IDs

    # Return success with redirect header
    response = Response(
        content='<div class="p-4 bg-green-50 border border-green-200 rounded-md"><p class="text-sm text-green-800">Client created successfully!</p></div>',
        status_code=200,
    )
    response.headers["HX-Redirect"] = f"/clients/{client_id}"
    return response


@router.put("/{client_id}", response_class=HTMLResponse)
async def update_client(
    client_id: int,
    request: Request,
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Update an existing client."""
    from fastapi.responses import Response

    # Get form data
    form_data = await request.form()
    name = str(form_data.get("name", "")).strip()
    description_raw = form_data.get("description", "")
    description = str(description_raw).strip() or None if description_raw else None
    is_active = form_data.get("is_active") == "on"
    keyword_ids = form_data.getlist("keyword_ids")

    # Get URL data
    url_ids = form_data.getlist("url_id[]")
    url_aliases = form_data.getlist("url_alias[]")
    url_values = form_data.getlist("url_value[]")
    url_is_active_list = form_data.getlist("url_is_active[]")

    if not name:
        return '<div class="p-4 bg-red-50 border border-red-200 rounded-md"><p class="text-sm text-red-800">Client name is required</p></div>'

    # Update client
    client_repo.update_client(
        client_id=client_id,
        name=name,
        description=description,
        is_active=is_active,
    )

    # Update URLs - get existing URLs, update/delete/create as needed
    existing_urls = {
        url["id"]: url for url in client_url_repo.get_client_urls(client_id)
    }
    submitted_url_ids = set()

    for i, (url_id, alias, url_value) in enumerate(
        zip(url_ids, url_aliases, url_values, strict=False)
    ):
        if alias and url_value:
            url_active = i < len(url_is_active_list)
            url_id_str = str(url_id)
            alias_str = str(alias)
            url_value_str = str(url_value)

            if url_id_str and url_id_str.strip():  # Existing URL
                url_id_int = int(url_id_str)
                submitted_url_ids.add(url_id_int)
                try:
                    client_url_repo.update_url(
                        url_id=url_id_int,
                        alias=alias_str,
                        url=url_value_str,
                        is_active=url_active,
                    )
                except Exception:
                    pass  # Skip invalid updates
            else:  # New URL
                try:
                    client_url_repo.create_url(
                        client_id=client_id,
                        alias=alias_str,
                        url=url_value_str,
                        is_active=url_active,
                    )
                except Exception:
                    pass  # Skip invalid URLs

    # Delete URLs that were removed from form
    for existing_url_id in existing_urls.keys():
        if existing_url_id not in submitted_url_ids:
            try:
                client_url_repo.delete_url(existing_url_id)
            except Exception:
                pass

    # Update keywords - remove all and re-add
    # TODO: Get updated_by from current_user when auth is integrated
    updated_by_user = 1  # Temporary: use admin user ID

    # First, get current keywords and remove them
    current_keywords = keyword_repo.get_client_keywords(client_id)
    for kw in current_keywords:
        keyword_repo.remove_keyword_from_client(kw["keyword_id"], client_id)

    # Add new keywords
    if keyword_ids:
        for keyword_id_raw in keyword_ids:
            try:
                keyword_id = int(str(keyword_id_raw))
                keyword_repo.add_keyword_to_client(
                    client_id, keyword_id, updated_by_user
                )
            except (ValueError, TypeError):
                pass

    # Return success with redirect header
    response = Response(
        content='<div class="p-4 bg-green-50 border border-green-200 rounded-md"><p class="text-sm text-green-800">Client updated successfully!</p></div>',
        status_code=200,
    )
    response.headers["HX-Redirect"] = f"/clients/{client_id}"
    return response


@router.post("/{client_id}/favorite", response_class=HTMLResponse)
async def toggle_favorite(
    client_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    favorites_repo: Annotated[FavoritesRepository, Depends(get_favorites_repository)],
):
    """Toggle favorite status for a client."""
    # Verify client exists and is active
    client = client_repo.get_client_by_id(client_id)
    if not client or not client.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    user_id = current_user["user_id"]
    is_favorited = favorites_repo.is_favorite(user_id, client_id)

    # Toggle favorite status
    if is_favorited:
        favorites_repo.remove_favorite(user_id, client_id)
        is_favorited = False
    else:
        favorites_repo.add_favorite(user_id, client_id)
        is_favorited = True

    # Return updated heart icon
    return f"""
    <button
        hx-post="/api/clients/{client_id}/favorite"
        hx-swap="outerHTML"
        onclick="event.stopPropagation()"
        class="text-gray-400 hover:text-red-500"
    >
        <svg class="w-5 h-5 {"fill-current text-red-500" if is_favorited else ""}" fill="{"currentColor" if is_favorited else "none"}" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
        </svg>
    </button>
    """
