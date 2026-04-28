"""
Foreign-exchange rates for ASEAN USD conversions.

When ``FIXER_ACCESS_KEY`` (or legacy ``FIXER_FX_API_KEY``) is set, rates come from **Fixer.io**
``GET https://data.fixer.io/api/latest?access_key=…`` with at most **one HTTP call per UTC day**;
responses are cached on disk and reused until the next calendar day (UTC), including across process restarts.

Without that env var, falls back to exchangerate.host (unchanged behaviour).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExchangeRatesBundle:
    """FX snapshot: rates (units of local currency per 1 USD) plus how they were obtained."""

    rates: dict[str, Decimal]
    provider: str
    used_static_fallback: bool
    message: str


HTTP_TIMEOUT = 25
USER_AGENT = (
    "MalaysiaFuelDashboard/1.0 (+https://github.com/zuftt/malaysia-fuel-dashboard; "
    "contact: data sync bot)"
)

FIXERIO_LATEST_URL = "https://data.fixer.io/api/latest"
FX_SYMBOLS = ("MYR", "SGD", "THB", "IDR", "BND", "PHP")


def _fixer_access_key() -> str:
    """Fixer.io ``access_key`` query param; prefer FIXER_ACCESS_KEY, else FIXER_FX_API_KEY."""
    return (os.environ.get("FIXER_ACCESS_KEY") or os.environ.get("FIXER_FX_API_KEY") or "").strip()


def _utc_today_str() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _default_cache_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".cache" / "fixer_fx_cache.json"


def _cache_path() -> Path:
    raw = os.environ.get("FIXER_FX_CACHE_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return _default_cache_path()


def _session_headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _static_fx_fallback() -> dict[str, Decimal]:
    return {
        "USD": Decimal("1"),
        "MYR": Decimal("4.50"),
        "SGD": Decimal("1.35"),
        "THB": Decimal("36.00"),
        "IDR": Decimal("16500"),
        "BND": Decimal("1.35"),
        "PHP": Decimal("58.00"),
    }


def _normalize_rates(rates: dict[str, Any]) -> dict[str, Decimal]:
    """Build currency -> units per 1 USD when ``rates`` are already vs USD (exchangerate.host / Fixer paid)."""
    out: dict[str, Decimal] = {"USD": Decimal("1")}
    for sym in FX_SYMBOLS:
        v = rates.get(sym)
        if v is not None:
            out[sym] = Decimal(str(v))
    if "BND" not in out and "SGD" in out:
        out["BND"] = out["SGD"]
    if len(out) < 4:
        raise ValueError("Too few FX rates after normalisation")
    return out


def _normalize_rates_from_fixer_eur(rates: dict[str, Any]) -> dict[str, Decimal]:
    """
    Fixer.io default base is EUR: ``rates[X]`` = X per 1 EUR. Convert to units of X per 1 USD.
    """
    usd_per_eur = rates.get("USD")
    if usd_per_eur is None:
        raise ValueError("Fixer.io EUR response missing USD rate")
    usd_per_eur_d = Decimal(str(usd_per_eur))
    if usd_per_eur_d <= 0:
        raise ValueError("Invalid USD vs EUR from Fixer.io")

    out: dict[str, Decimal] = {"USD": Decimal("1")}
    for sym in FX_SYMBOLS:
        if sym == "USD":
            continue
        per_eur = rates.get(sym)
        if per_eur is None:
            continue
        out[sym] = Decimal(str(per_eur)) / usd_per_eur_d
    if "BND" not in out and "SGD" in out:
        out["BND"] = out["SGD"]
    if len(out) < 4:
        raise ValueError("Too few FX rates after EUR→USD conversion")
    return out


def _load_cache_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("FX cache read failed (%s): %s", path, e)
        return None


def _write_cache_file(path: Path, utc_date: str, rates: dict[str, Decimal]) -> None:
    payload = {
        "utc_date": utc_date,
        "source": "fixer.io",
        "rates": {k: str(v) for k, v in rates.items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _fetch_fixer_live(access_key: str) -> dict[str, Decimal]:
    # Include USD so EUR-based (free-tier) responses can be converted to "per 1 USD".
    symbols = ",".join(["USD", *FX_SYMBOLS])
    r = requests.get(
        FIXERIO_LATEST_URL,
        params={
            "access_key": access_key,
            "symbols": symbols,
        },
        headers=_session_headers(),
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    body = r.json()
    if not body.get("success"):
        err = body.get("error")
        if isinstance(err, dict):
            info = err.get("info") or err.get("type") or err
        else:
            info = err or body.get("message") or "success=false"
        raise ValueError(f"Fixer.io API: {info}")
    rates = body.get("rates") or {}
    base = str(body.get("base") or "EUR").upper()
    if base == "USD":
        return _normalize_rates(rates)
    if base == "EUR":
        return _normalize_rates_from_fixer_eur(rates)
    raise ValueError(f"Unsupported Fixer.io base currency: {base}")


def _rates_from_cache_doc(doc: dict[str, Any]) -> dict[str, Decimal] | None:
    raw = doc.get("rates")
    if not isinstance(raw, dict):
        return None
    try:
        return _normalize_rates({k: raw[k] for k in raw})
    except Exception:
        return None


def _exchange_rates_via_fixer() -> ExchangeRatesBundle:
    access_key = _fixer_access_key()
    if not access_key:
        raise RuntimeError("FIXER_ACCESS_KEY (or FIXER_FX_API_KEY) not set")

    cache_path = _cache_path()
    today = _utc_today_str()

    cached = _load_cache_file(cache_path)
    if cached and cached.get("utc_date") == today:
        rates = _rates_from_cache_doc(cached)
        if rates:
            logger.debug("FX: using Fixer.io disk cache for %s", today)
            return ExchangeRatesBundle(
                rates=rates,
                provider="fixer.io",
                used_static_fallback=False,
                message=f"Fixer.io (data.fixer.io): same-day disk cache for UTC date {today}.",
            )

    try:
        rates = _fetch_fixer_live(access_key)
        _write_cache_file(cache_path, today, rates)
        logger.info("FX: refreshed Fixer.io rates for %s (cached at %s)", today, cache_path)
        return ExchangeRatesBundle(
            rates=rates,
            provider="fixer.io",
            used_static_fallback=False,
            message=(
                f"Fixer.io: live GET /api/latest (EUR base on free tier → converted to per 1 USD) "
                f"for UTC date {today} (written to disk cache)."
            ),
        )
    except Exception as e:
        logger.warning("Fixer FX fetch failed (%s)", e)
        if cached:
            rates = _rates_from_cache_doc(cached)
            if rates:
                stale_date = cached.get("utc_date", "?")
                logger.warning(
                    "FX: using stale Fixer.io cache (utc_date=%s) after live fetch failure",
                    stale_date,
                )
                return ExchangeRatesBundle(
                    rates=rates,
                    provider="fixer.io",
                    used_static_fallback=False,
                    message=(
                        f"Fixer.io: live request failed ({e!s}); using stale on-disk cache "
                        f"(UTC date {stale_date}). Not the bundled static table."
                    ),
                )
        logger.warning("FX: Fixer.io unavailable and no cache; using static fallback rates")
        fb = _static_fx_fallback()
        return ExchangeRatesBundle(
            rates=fb,
            provider="static",
            used_static_fallback=True,
            message=(
                "Built-in static fallback (MYR 4.50, SGD 1.35, …) because Fixer.io was unreachable "
                "and no cache file was available."
            ),
        )


def _exchange_rates_via_exchangerate_host() -> ExchangeRatesBundle:
    symbols = ",".join(FX_SYMBOLS)
    url = f"https://api.exchangerate.host/latest?base=USD&symbols={symbols}"
    try:
        r = requests.get(url, headers=_session_headers(), timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        body = r.json()
        if body.get("success") is False:
            raise ValueError("exchangerate.host reported success=false")
        rates = body.get("rates") or {}
        norm = _normalize_rates(rates)
        return ExchangeRatesBundle(
            rates=norm,
            provider="exchangerate.host",
            used_static_fallback=False,
            message="exchangerate.host: live /latest?base=USD (no Fixer.io access key set).",
        )
    except Exception as e:
        logger.warning("FX fetch failed (%s), using static fallback rates", e)
        fb = _static_fx_fallback()
        return ExchangeRatesBundle(
            rates=fb,
            provider="static",
            used_static_fallback=True,
            message=(
                f"Built-in static fallback because exchangerate.host failed ({e!s}). "
                "Set FIXER_ACCESS_KEY for Fixer.io (data.fixer.io) with daily disk cache."
            ),
        )


def fetch_exchange_rates_bundle() -> ExchangeRatesBundle:
    """
    FX rates (units per 1 USD) plus provenance for API/UI.

    If ``FIXER_ACCESS_KEY`` or ``FIXER_FX_API_KEY`` is set, uses **Fixer.io** with **at most one live
    request per UTC day** (subsequent calls the same day read the on-disk cache).

    Otherwise uses exchangerate.host on each call.
    """
    if _fixer_access_key():
        return _exchange_rates_via_fixer()
    return _exchange_rates_via_exchangerate_host()


def fetch_exchange_rates() -> dict[str, Decimal]:
    """Same rates as :func:`fetch_exchange_rates_bundle` (backward compatible)."""
    return fetch_exchange_rates_bundle().rates
