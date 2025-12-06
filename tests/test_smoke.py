from fastapi.testclient import TestClient

from src.jea_meeting_web_scraper.main import app


def test_app_starts_and_health_route_loads():
    """Basic smoke test to ensure the FastAPI app loads and health route responds."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
