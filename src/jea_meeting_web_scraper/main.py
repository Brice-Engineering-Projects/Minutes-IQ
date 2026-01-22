"""Main module for the JEA Meeting Web Scraper."""

from fastapi import APIRouter, Depends, FastAPI

from jea_meeting_web_scraper.auth import routes
from jea_meeting_web_scraper.db.client import get_db
from jea_meeting_web_scraper.db.user_repository import UserRepository

app = FastAPI()
router = APIRouter()

# Register and mountrouters from other modules (e.g., auth, meetings, nlp)
app.include_router(routes.router, prefix="/auth")
# nlp = router.include_router(APIRouter(), prefix="/nlp")


# Added # noqa: B008 to bypass the Ruff linting error for FastAPI dependencies
def get_user_repo(conn=Depends(get_db)):  # noqa: B008
    return UserRepository(conn)


@app.get("/users/{user_id}")
def read_user(user_id: int, repo: UserRepository = Depends(get_user_repo)):  # noqa: B008
    user = repo.get_user_by_id(user_id)
    if not user:
        return {"error": "User not found"}
    return user


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/nlp_demo")
def nlp_demo():
    return {"message": "NLP demo endpoint"}
