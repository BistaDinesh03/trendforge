"""Smoke tests for ForgeFix."""

from fastapi.testclient import TestClient

from forgefix.main import app


def test_health_endpoint() -> None:
    """The service must answer /health with a JSON status."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
