"""Dashboard API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from minutes_iq.db.client_repository import ClientRepository
from minutes_iq.db.dependencies import get_client_repository, get_keyword_repository
from minutes_iq.db.keyword_repository import KeywordRepository

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_class=HTMLResponse)
async def get_dashboard_stats(
    request: Request,
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Get dashboard statistics."""
    # Query real data from database
    # Get active clients count
    clients = client_repo.list_clients()
    active_clients_count = len([c for c in clients if c.get("is_active", True)])

    # Get keywords count
    keywords = keyword_repo.list_keywords()
    keywords_count = len(keywords)

    # TODO: Get scrape jobs and results counts from their respective repositories
    # For now, return 0 as there's no data yet
    scrape_jobs_count = 0
    results_count = 0

    # Render stats cards
    html = f"""
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-600">Active Clients</p>
                <p class="mt-2 text-3xl font-semibold text-gray-900">{active_clients_count}</p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                </svg>
            </div>
        </div>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-600">Keywords Tracked</p>
                <p class="mt-2 text-3xl font-semibold text-gray-900">{keywords_count}</p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
                </svg>
            </div>
        </div>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-600">Scrape Jobs</p>
                <p class="mt-2 text-3xl font-semibold text-gray-900">{scrape_jobs_count}</p>
                <p class="mt-1 text-xs text-gray-500">No jobs yet</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
            </div>
        </div>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-600">Recent Results</p>
                <p class="mt-2 text-3xl font-semibold text-gray-900">{results_count}</p>
                <p class="mt-1 text-xs text-gray-500">Last 30 days</p>
            </div>
            <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
            </div>
        </div>
    </div>
    """

    return html


@router.get("/activity", response_class=HTMLResponse)
async def get_recent_activity(request: Request):
    """Get recent activity feed."""
    # TODO: Query real activity data from database
    # For now, return empty state since there's no data

    html = """
    <div class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No activity yet</h3>
        <p class="mt-1 text-sm text-gray-500">Start by creating your first scrape job to see activity here.</p>
        <div class="mt-6">
            <a
                href="/scraper/new"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
                <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                New Scrape Job
            </a>
        </div>
    </div>
    """

    return html
