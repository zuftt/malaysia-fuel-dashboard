"""FX provider selection and Fixer daily disk cache."""

import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fixer_env(monkeypatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("FIXER_FX_API_KEY", "test-fix-key")
    cache = tmp_path / "fixer_fx_cache.json"
    monkeypatch.setenv("FIXER_FX_CACHE_PATH", str(cache))
    return cache


def test_fixer_second_call_same_day_uses_disk_cache_no_second_http(fixer_env: Path):
    # Fixer.io free tier: EUR base; MYR per USD = MYR_per_EUR / USD_per_EUR = 5.4 / 1.2 = 4.5
    body = {
        "success": True,
        "base": "EUR",
        "rates": {
            "USD": 1.2,
            "MYR": 5.4,
            "SGD": 1.62,
            "THB": 43.2,
            "IDR": 19800.0,
            "BND": 1.62,
            "PHP": 69.6,
        },
    }
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = body

    with patch("app.fx_rates.requests.get", return_value=resp) as m_get:
        from app.fx_rates import fetch_exchange_rates

        r1 = fetch_exchange_rates()
        assert m_get.call_count == 1
        r2 = fetch_exchange_rates()
        assert m_get.call_count == 1

    assert r1["MYR"] == Decimal("4.5")
    assert r2["MYR"] == Decimal("4.5")
    assert fixer_env.is_file()


def test_fixer_live_failure_uses_stale_cache(monkeypatch, fixer_env: Path):
    stale = {
        "utc_date": "1999-12-31",
        "source": "fixer",
        "rates": {
            "USD": "1",
            "MYR": "4.11",
            "SGD": "1.22",
            "THB": "35",
            "IDR": "16000",
            "BND": "1.22",
            "PHP": "55",
        },
    }
    fixer_env.write_text(json.dumps(stale), encoding="utf-8")

    def boom(*_a, **_k):
        raise ConnectionError("no network")

    monkeypatch.setenv("FIXER_FX_API_KEY", "test-fix-key")

    with patch("app.fx_rates.requests.get", side_effect=boom):
        from app.fx_rates import fetch_exchange_rates

        out = fetch_exchange_rates()

    assert out["MYR"] == Decimal("4.11")


def test_fixer_live_failure_no_cache_falls_back_static(monkeypatch, tmp_path: Path):
    cache = tmp_path / "missing.json"
    monkeypatch.setenv("FIXER_FX_API_KEY", "x")
    monkeypatch.setenv("FIXER_FX_CACHE_PATH", str(cache))

    with patch("app.fx_rates.requests.get", side_effect=ConnectionError("down")):
        from app.fx_rates import fetch_exchange_rates

        out = fetch_exchange_rates()

    assert out["MYR"] == Decimal("4.50")
    assert out["USD"] == Decimal("1")
