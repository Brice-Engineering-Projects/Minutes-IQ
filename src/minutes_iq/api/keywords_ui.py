"""API endpoints for keyword management UI fragments."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.dependencies import get_client_repository, get_keyword_repository
from minutes_iq.db.keyword_repository import KeywordRepository

router = APIRouter(prefix="/api/keywords", tags=["Keywords UI API"])


class KeywordCreate(BaseModel):
    """Schema for creating a keyword."""

    keyword: str
    category: str | None = None
    description: str | None = None


class KeywordUpdate(BaseModel):
    """Schema for updating a keyword."""

    keyword: str | None = None
    category: str | None = None
    description: str | None = None


@router.get("/list", response_class=HTMLResponse)
async def get_keywords_list(
    request: Request,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
    page: int = 1,
    search: str = "",
    category: str = "",
):
    """Return paginated keywords table HTML."""
    keywords = keyword_repo.list_keywords()

    # Filter by search
    if search:
        keywords = [
            k
            for k in keywords
            if search.lower() in k.get("keyword", "").lower()
            or search.lower() in k.get("description", "").lower()
        ]

    # Filter by category
    if category:
        keywords = [k for k in keywords if k.get("category") == category]

    # Pagination
    per_page = 20
    total = len(keywords)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_keywords = keywords[start:end]

    if not paginated_keywords:
        return """
        <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No keywords found</h3>
            <p class="mt-1 text-sm text-gray-500">Try adjusting your search or filter criteria, or create a new keyword.</p>
            <div class="mt-6">
                <a href="/keywords/new" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                    <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                    </svg>
                    Create Keyword
                </a>
            </div>
        </div>
        """

    # Build table HTML
    rows_html = ""
    for kw in paginated_keywords:
        category_badge = ""
        if kw.get("category"):
            category_badge = f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">{kw["category"]}</span>'
        else:
            category_badge = '<span class="text-gray-400 text-xs">Uncategorized</span>'

        description = kw.get("description", "")
        if description and len(description) > 80:
            description = description[:77] + "..."

        rows_html += f"""
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
                <a href="/keywords/{kw["keyword_id"]}" class="text-sm font-medium text-blue-600 hover:text-blue-800">
                    {kw.get("keyword", "")}
                </a>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                {category_badge}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
                {description or '<span class="text-gray-400">No description</span>'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <a href="/keywords/{kw["keyword_id"]}" class="text-blue-600 hover:text-blue-900 mr-3">View</a>
                <a href="/keywords/{kw["keyword_id"]}/edit" class="text-gray-600 hover:text-gray-900">Edit</a>
            </td>
        </tr>
        """

    # Pagination controls
    pagination_html = ""
    if total_pages > 1:
        prev_disabled = (
            'disabled class="opacity-50 cursor-not-allowed"' if page <= 1 else ""
        )
        next_disabled = (
            'disabled class="opacity-50 cursor-not-allowed"'
            if page >= total_pages
            else ""
        )

        pagination_html = f"""
        <div class="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
            <div class="flex flex-1 justify-between sm:hidden">
                <button
                    hx-get="/api/keywords/list?page={page - 1}&search={search}&category={category}"
                    hx-target="#keywords-table"
                    {prev_disabled}
                    class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                    Previous
                </button>
                <button
                    hx-get="/api/keywords/list?page={page + 1}&search={search}&category={category}"
                    hx-target="#keywords-table"
                    {next_disabled}
                    class="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                    Next
                </button>
            </div>
            <div class="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div>
                    <p class="text-sm text-gray-700">
                        Showing <span class="font-medium">{start + 1}</span> to <span class="font-medium">{min(end, total)}</span> of{" "}
                        <span class="font-medium">{total}</span> results
                    </p>
                </div>
                <div>
                    <nav class="isolate inline-flex -space-x-px rounded-md shadow-sm">
                        <button
                            hx-get="/api/keywords/list?page={page - 1}&search={search}&category={category}"
                            hx-target="#keywords-table"
                            {prev_disabled}
                            class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        >
                            Previous
                        </button>
                        <span class="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300">
                            {page} / {total_pages}
                        </span>
                        <button
                            hx-get="/api/keywords/list?page={page + 1}&search={search}&category={category}"
                            hx-target="#keywords-table"
                            {next_disabled}
                            class="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        >
                            Next
                        </button>
                    </nav>
                </div>
            </div>
        </div>
        """

    html = f"""
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Keyword
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Category
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Description
                    </th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                    </th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {rows_html}
            </tbody>
        </table>
    </div>
    {pagination_html}
    """

    return html


@router.get("/categories", response_class=HTMLResponse)
async def get_categories(
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Return JSON array of categories with counts."""
    keywords = keyword_repo.list_keywords()

    # Count keywords by category
    category_counts: dict[str, int] = {}
    for kw in keywords:
        category = kw.get("category") or "Uncategorized"
        category_counts[category] = category_counts.get(category, 0) + 1

    # Convert to list of dicts
    categories = [
        {"category": cat, "count": count} for cat, count in category_counts.items()
    ]
    categories.sort(key=lambda x: str(x["category"]))

    # Return as JSON
    from fastapi.responses import JSONResponse

    return JSONResponse(content=categories)


@router.get("/categories-grid", response_class=HTMLResponse)
async def get_categories_grid(
    request: Request,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Return HTML grid of category cards."""
    keywords = keyword_repo.list_keywords()

    # Count keywords by category
    category_counts: dict[str, int] = {}
    for kw in keywords:
        category = kw.get("category") or "Uncategorized"
        category_counts[category] = category_counts.get(category, 0) + 1

    if not category_counts:
        return """
        <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No categories yet</h3>
            <p class="mt-1 text-sm text-gray-500">Create keywords with categories to organize them.</p>
            <div class="mt-6">
                <a href="/keywords/new" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                    <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                    </svg>
                    Create Keyword
                </a>
            </div>
        </div>
        """

    # Build category cards
    cards_html = ""
    for category, count in sorted(category_counts.items()):
        cards_html += f"""
        <a href="/keywords?category={category}" class="bg-white shadow-sm rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">{category}</h3>
            <p class="text-2xl font-bold text-blue-600">{count} keyword{"s" if count != 1 else ""}</p>
        </a>
        """

    html = f"""
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards_html}
    </div>
    """

    return html


@router.get("/{keyword_id}/clients", response_class=HTMLResponse)
async def get_keyword_clients(
    request: Request,
    keyword_id: int,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
):
    """Return HTML list of clients using this keyword."""
    # Get keyword
    keyword = keyword_repo.get_keyword_by_id(keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Get clients tracking this keyword
    tracking_clients = keyword_repo.get_keyword_clients(keyword_id)

    if not tracking_clients:
        return """
        <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No clients tracking this keyword</h3>
            <p class="mt-1 text-sm text-gray-500">Add this keyword to a client's tracking list to see it here.</p>
        </div>
        """

    # Build list HTML
    items_html = ""
    for client in tracking_clients:
        active_badge = ""
        if client.get("is_active"):
            active_badge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Active</span>'
        else:
            active_badge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">Inactive</span>'

        items_html += f"""
        <li class="py-3">
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <a href="/clients/{client["client_id"]}" class="text-sm font-medium text-blue-600 hover:text-blue-800">
                        {client.get("name", "Unknown")}
                    </a>
                    <p class="text-xs text-gray-500">{client.get("jurisdiction", "Unknown")}</p>
                </div>
                <div>
                    {active_badge}
                </div>
            </div>
        </li>
        """

    html = f"""
    <ul class="divide-y divide-gray-200">
        {items_html}
    </ul>
    """

    return html


@router.get("/{keyword_id}/stats", response_class=HTMLResponse)
async def get_keyword_stats(
    keyword_id: int,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
):
    """Return JSON stats for keyword."""
    # Get keyword
    keyword = keyword_repo.get_keyword_by_id(keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Count clients tracking this keyword
    tracking_clients = keyword_repo.get_keyword_clients(keyword_id)
    client_count = len(tracking_clients)

    # TODO: Get mention count and last found from scraper results when implemented
    stats = {
        "client_count": client_count,
        "mention_count": 0,
        "last_found": "Never",
    }

    from fastapi.responses import JSONResponse

    return JSONResponse(content=stats)


@router.get("/related", response_class=HTMLResponse)
async def get_related_keywords(
    request: Request,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
    category: str = "",
    exclude: int = 0,
):
    """Return HTML list of related keywords in same category."""
    keywords = keyword_repo.list_keywords()

    # Filter by category and exclude current keyword
    related = [
        k
        for k in keywords
        if k.get("category") == category and k["keyword_id"] != exclude
    ]

    if not related:
        return (
            '<p class="text-sm text-gray-500">No related keywords in this category.</p>'
        )

    # Build list HTML
    items_html = ""
    for kw in related[:5]:  # Limit to 5 related keywords
        items_html += f"""
        <li class="py-2">
            <a href="/keywords/{kw["keyword_id"]}" class="text-sm text-blue-600 hover:text-blue-800">
                {kw.get("keyword", "")}
            </a>
        </li>
        """

    html = f"""
    <p class="text-xs text-gray-500 mb-2">Other keywords in the "{category}" category:</p>
    <ul class="space-y-1">
        {items_html}
    </ul>
    """

    return html


@router.post("", response_class=HTMLResponse)
async def create_keyword(
    keyword_data: KeywordCreate,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Create a new keyword."""
    # Check if keyword already exists
    existing = keyword_repo.list_keywords()
    if any(
        k.get("keyword", "").lower() == keyword_data.keyword.lower() for k in existing
    ):
        raise HTTPException(status_code=400, detail="Keyword already exists")

    # Create keyword
    # TODO: Get created_by from current_user when auth is integrated
    keyword_repo.create_keyword(
        keyword=keyword_data.keyword,
        created_by=1,  # Temporary: use admin user ID
        category=keyword_data.category,
        description=keyword_data.description,
    )

    return """
    <div class="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded">
        Keyword created successfully!
    </div>
    """


@router.put("/{keyword_id}", response_class=HTMLResponse)
async def update_keyword(
    keyword_id: int,
    keyword_data: KeywordUpdate,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Update a keyword."""

    # Get existing keyword
    keyword = keyword_repo.get_keyword_by_id(keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Update keyword
    keyword_repo.update_keyword(
        keyword_id=keyword_id,
        keyword=keyword_data.keyword or keyword.get("keyword"),
        category=keyword_data.category,
        description=keyword_data.description,
    )

    return """
    <div class="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded">
        Keyword updated successfully!
    </div>
    """


@router.delete("/{keyword_id}", response_class=HTMLResponse)
async def delete_keyword(
    keyword_id: int,
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Delete a keyword."""

    # Get keyword
    keyword = keyword_repo.get_keyword_by_id(keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Delete keyword
    keyword_repo.delete_keyword(keyword_id)

    # Redirect to keywords list
    from fastapi.responses import Response

    response = Response(status_code=200)
    response.headers["HX-Redirect"] = "/keywords"
    return response
