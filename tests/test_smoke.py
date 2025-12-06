from fastapi.testclient import TestClient

from src.jea_meeting_web_scraper.main import app


def test_app_starts_and_login_route_loads():
    """Basic smoke test to ensure the FastAPI app loads."""
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200
