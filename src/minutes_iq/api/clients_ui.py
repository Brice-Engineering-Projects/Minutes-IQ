"""Client API routes for UI - returns HTML fragments."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.dependencies import get_db_client

router = APIRouter(prefix="/api/clients", tags=["Client API"])


@router.get("/list", response_class=HTMLResponse)
async def get_clients_list(
    request: Request,
    db_client: Annotated[object, Depends(get_db_client)],
    page: int = 1,
    search: str = "",
):
    """Get paginated client list as HTML."""
    client_repo = ClientRepository(db_client)
    clients = client_repo.get_all_clients()

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
        <tr class="hover:bg-gray-50 cursor-pointer" onclick="window.location.href='/clients/{client['client_id']}'">
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div>
                        <div class="text-sm font-medium text-gray-900">{client.get('name', 'N/A')}</div>
                        <div class="text-sm text-gray-500">{client.get('description', '')[:50]}...</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {client.get('keyword_count', 0)} keywords
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <button
                    hx-post="/api/clients/{client['client_id']}/favorite"
                    hx-swap="outerHTML"
                    onclick="event.stopPropagation()"
                    class="text-gray-400 hover:text-red-500"
                >
                    <svg class="w-5 h-5 {'fill-current text-red-500' if client.get('is_favorite') else ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                    </svg>
                </button>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {'bg-green-100 text-green-800' if client.get('is_active') else 'bg-gray-100 text-gray-800'}">
                    {'Active' if client.get('is_active') else 'Inactive'}
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
                {'<button hx-get="/api/clients/list?page=' + str(page - 1) + '&search=' + search + '" hx-target="#clients-table" class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">Previous</button>' if page > 1 else ''}
                {'<button hx-get="/api/clients/list?page=' + str(page + 1) + '&search=' + search + '" hx-target="#clients-table" class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">Next</button>' if page < total_pages else ''}
            </div>
            <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                    <p class="text-sm text-gray-700">
                        Showing <span class="font-medium">{start + 1}</span> to <span class="font-medium">{min(end, total)}</span> of <span class="font-medium">{total}</span> results
                    </p>
                </div>
                <div>
                    <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        {'<button hx-get="/api/clients/list?page=' + str(page - 1) + '&search=' + search + '" hx-target="#clients-table" class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">Previous</button>' if page > 1 else ''}
                        <span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                            Page {page} of {total_pages}
                        </span>
                        {'<button hx-get="/api/clients/list?page=' + str(page + 1) + '&search=' + search + '" hx-target="#clients-table" class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">Next</button>' if page < total_pages else ''}
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
    db_client: Annotated[object, Depends(get_db_client)],
    request: Request,
):
    """Get user's favorite clients as HTML."""
    # TODO: Get current user ID from auth
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
    db_client: Annotated[object, Depends(get_db_client)],
):
    """Get client's keywords as HTML."""
    # TODO: Implement client-keyword relationship query
    return """
    <div class="text-center py-8">
        <p class="text-sm text-gray-500">No keywords assigned yet</p>
    </div>
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
