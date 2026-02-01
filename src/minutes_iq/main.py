"""Main module for the JEA Meeting Web Scraper."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from minutes_iq.admin import (
    auth_code_routes,
    client_routes,
    keyword_routes,
)
from minutes_iq.api import clients
from minutes_iq.auth import routes as auth_routes
from minutes_iq.scraper import routes as scraper_routes
from minutes_iq.templates_config import templates

app = FastAPI()

# Set up static files
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Register and mount routers from other modules (e.g., auth, meetings, nlp)
app.include_router(auth_routes.router, prefix="/auth")
app.include_router(auth_code_routes.router)
app.include_router(client_routes.router)
app.include_router(keyword_routes.router)
app.include_router(clients.router)
app.include_router(scraper_routes.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/nlp_demo")
def nlp_demo():
    return {"message": "NLP demo endpoint"}
