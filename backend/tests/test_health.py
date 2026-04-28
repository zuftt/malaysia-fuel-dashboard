"""Tests for GET /health."""

from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


def test_health_status_code_and_json_shape():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "healthy"
    assert body.get("service") == "Malaysia Fuel Intelligence Dashboard"
    assert "timestamp" in body
    assert isinstance(body["timestamp"], str)
    # Naive UTC ISO string from datetime.utcnow().isoformat()
    datetime.fromisoformat(body["timestamp"])
