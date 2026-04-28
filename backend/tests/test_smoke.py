"""Smoke tests — startup hits SQLite + optional data.gov.my sync (needs network)."""

from fastapi.testclient import TestClient

from app.main import app


def test_api_v1_root():
    with TestClient(app) as client:
        response = client.get("/api/v1")
        assert response.status_code == 200
        assert "endpoints" in response.json()


def test_latest_prices_response_includes_provenance():
    """GET /api/v1/prices/latest includes source URLs and timestamp (CONTENT_RULES.md)."""
    with TestClient(app) as client:
        response = client.get("/api/v1/prices/latest")
        if response.status_code == 404:
            return  # empty DB in some environments
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "timestamp" in body
        assert "source_url" in body
        assert "source_catalogue_url" in body
        assert "storage.data.gov.my" in body["source_url"]
        assert "data.gov.my" in body["source_catalogue_url"]


def test_asean_compare_endpoint_shape():
    """GET /api/v1/prices/compare returns ASEAN comparison envelope (may be empty in CI)."""
    with TestClient(app) as client:
        response = client.get("/api/v1/prices/compare")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "exchange_rates" in body
        assert "updated_at" in body
        assert "exchange_rates_info" in body
        assert isinstance(body["data"], list)
        assert isinstance(body["exchange_rates"], dict)
        info = body["exchange_rates_info"]
        assert isinstance(info, dict)
        assert "provider" in info
        assert "used_static_fallback" in info
        assert "message" in info


def test_asean_history_endpoint_shape():
    """GET /api/v1/prices/asean/history returns dated rows envelope."""
    with TestClient(app) as client:
        response = client.get("/api/v1/prices/asean/history?days=30")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "days" in body
        assert body["days"] == 30
        assert "note" in body
        assert "malaysia_usd_uses_latest_fx" in body
        assert isinstance(body["data"], list)
