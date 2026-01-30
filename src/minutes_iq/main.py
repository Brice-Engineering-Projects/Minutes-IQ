"""Main module for the JEA Meeting Web Scraper."""

from fastapi import APIRouter, FastAPI

from minutes_iq.admin import (
    auth_code_routes,
    client_routes,
    keyword_routes,
)
from minutes_iq.api import clients
from minutes_iq.auth import routes

app = FastAPI()
router = APIRouter()

# Register and mount routers from other modules (e.g., auth, meetings, nlp)
app.include_router(routes.router, prefix="/auth")
app.include_router(auth_code_routes.router)
app.include_router(client_routes.router)
app.include_router(keyword_routes.router)
app.include_router(clients.router)
# nlp = router.include_router(APIRouter(), prefix="/nlp")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/nlp_demo")
def nlp_demo():
    return {"message": "NLP demo endpoint"}
