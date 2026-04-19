"""Smoke tests — startup hits SQLite + optional data.gov.my sync (needs network)."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body.get("status") == "healthy"


def test_api_v1_root():
    with TestClient(app) as client:
        response = client.get("/api/v1")
        assert response.status_code == 200
        assert "endpoints" in response.json()
