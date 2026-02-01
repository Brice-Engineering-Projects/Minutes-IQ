"""Main module for the JEA Meeting Web Scraper."""

from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from minutes_iq.admin import (
    auth_code_routes,
    client_routes,
    keyword_routes,
)
from minutes_iq.api import clients
from minutes_iq.auth import routes
from minutes_iq.scraper import routes as scraper_routes

app = FastAPI()
router = APIRouter()

# Set up templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Register and mount routers from other modules (e.g., auth, meetings, nlp)
app.include_router(routes.router, prefix="/auth")
app.include_router(auth_code_routes.router)
app.include_router(client_routes.router)
app.include_router(keyword_routes.router)
app.include_router(clients.router)
app.include_router(scraper_routes.router)
# nlp = router.include_router(APIRouter(), prefix="/nlp")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/nlp_demo")
def nlp_demo():
    return {"message": "NLP demo endpoint"}
