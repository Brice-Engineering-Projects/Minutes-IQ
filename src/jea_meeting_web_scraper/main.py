"""Main module for the JEA Meeting Web Scraper."""

from fastapi import APIRouter, FastAPI

from jea_meeting_web_scraper.auth import routes

app = FastAPI()
router = APIRouter()

# Register and mountrouters from other modules (e.g., auth, meetings, nlp)
app.include_router(routes.router, prefix="/auth")
# nlp = router.include_router(APIRouter(), prefix="/nlp")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/nlp_demo")
def nlp_demo():
    return {"message": "NLP demo endpoint"}
