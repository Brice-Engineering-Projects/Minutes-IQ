"""Main module for the Minutes IQ application."""

from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from minutes_iq.admin import (
    auth_code_routes,
    client_routes,
    keyword_routes,
)
from minutes_iq.api import admin_ui as admin_ui_api
from minutes_iq.api import clients
from minutes_iq.api import clients_ui as clients_ui_api
from minutes_iq.api import dashboard as dashboard_api
from minutes_iq.api import keywords_ui as keywords_ui_api
from minutes_iq.api import profile_ui as profile_ui_api
from minutes_iq.api import scraper_jobs_ui as scraper_jobs_ui_api
from minutes_iq.auth import routes as auth_routes
from minutes_iq.auth.dependencies import get_current_user
from minutes_iq.error_handlers import (
    forbidden_handler,
    internal_server_error_handler,
    not_found_handler,
    unauthorized_handler,
)
from minutes_iq.scraper import routes as scraper_routes
from minutes_iq.templates_config import templates
from minutes_iq.ui import admin_routes as admin_ui_routes
from minutes_iq.ui import client_routes as client_ui_routes
from minutes_iq.ui import keyword_routes as keyword_ui_routes
from minutes_iq.ui import profile_routes as profile_ui_routes
from minutes_iq.ui import scraper_job_routes as scraper_job_ui_routes

app = FastAPI()

# Register exception handlers for custom error pages
app.add_exception_handler(401, unauthorized_handler)
app.add_exception_handler(404, not_found_handler)
app.add_exception_handler(403, forbidden_handler)
app.add_exception_handler(500, internal_server_error_handler)
app.add_exception_handler(
    StarletteHTTPException, not_found_handler
)  # Catch-all for other HTTP exceptions

# Set up static files
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Register and mount routers from other modules (e.g., auth, meetings, nlp)
# IMPORTANT: Register UI routes before API routes when they share the same prefix
# to ensure HTML pages are served instead of JSON responses
app.include_router(auth_routes.router, prefix="/auth")

# Register UI routes BEFORE REST API routes to prevent conflicts
# The admin UI route /admin/auth-codes must be registered before the REST API /admin/auth-codes
app.include_router(admin_ui_routes.router)
app.include_router(client_ui_routes.router)
app.include_router(keyword_ui_routes.router)
app.include_router(scraper_job_ui_routes.router)
app.include_router(profile_ui_routes.router)

# Now register REST API routers
app.include_router(auth_code_routes.router)
app.include_router(client_routes.router)
app.include_router(keyword_routes.router)
app.include_router(dashboard_api.router)

# Register API fragment routers
app.include_router(clients_ui_api.router)
app.include_router(clients.router)
app.include_router(keywords_ui_api.router)
app.include_router(scraper_jobs_ui_api.router)
app.include_router(scraper_routes.router)
app.include_router(admin_ui_api.router)
app.include_router(profile_ui_api.router)
app.include_router(profile_ui_routes.router)
app.include_router(profile_ui_api.router)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    """Render the landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Render the dashboard page (requires authentication)."""
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "current_user": current_user}
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/nlp_demo")
def nlp_demo():
    return {"message": "NLP demo endpoint"}


def run_dev():
    uvicorn.run(
        "minutes_iq.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
