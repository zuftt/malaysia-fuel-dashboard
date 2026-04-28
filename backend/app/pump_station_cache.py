"""
Disk cache for GET /api/v1/prices/pump-stations.

Refreshes from Firecrawl at most once per Malaysia calendar week: live scrape is
only attempted on Thursday (Asia/Kuala_Lumpur) and only if the last successful
cache write was before that Thursday's date. Other days always serve the last
cached payload so reloads do not hit Firecrawl.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.schemas import PumpStationPriceResponse

logger = logging.getLogger(__name__)

_MY = ZoneInfo("Asia/Kuala_Lumpur")
_THURSDAY = 3  # datetime.weekday(): Monday=0


def _default_cache_path() -> Path:
    base = Path(__file__).resolve().parent.parent / ".cache"
    return base / "pump_stations.json"


def cache_path() -> Path:
    raw = os.getenv("PUMP_STATIONS_CACHE_PATH", "").strip()
    return Path(raw) if raw else _default_cache_path()


def needs_live_scrape(last_cached_at: datetime, *, now: datetime | None = None) -> bool:
    """
    True when we should call Firecrawl again.

    Rules (Malaysia local date):
    - Not Thursday → never refresh (serve disk cache if present).
    - Thursday → refresh only if last cache was written on an earlier calendar day
      (at most one live scrape per Thursday).
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if last_cached_at.tzinfo is None:
        last_cached_at = last_cached_at.replace(tzinfo=timezone.utc)

    now_my = now.astimezone(_MY)
    if now_my.weekday() != _THURSDAY:
        return False

    last_my = last_cached_at.astimezone(_MY)
    return last_my.date() < now_my.date()


def read_cache() -> tuple[dict[str, Any] | None, datetime | None]:
    """Return (raw_blob, cached_at) or (None, None) if missing/invalid."""
    path = cache_path()
    if not path.is_file():
        return None, None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Pump cache read failed (%s): %s", path, e)
        return None, None

    if not isinstance(raw, dict) or raw.get("version") != 1:
        return None, None

    stamp = raw.get("cached_at")
    if not isinstance(stamp, str):
        return None, None
    try:
        cached_at = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None, None

    if cached_at.tzinfo is None:
        cached_at = cached_at.replace(tzinfo=timezone.utc)

    return raw, cached_at


def write_cache(response: PumpStationPriceResponse, *, cached_at: datetime | None = None) -> None:
    path = cache_path()
    when = cached_at or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)

    blob = {
        "version": 1,
        "cached_at": when.isoformat(),
        "response": response.model_dump(mode="json"),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(blob, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning("Pump cache write failed (%s): %s", path, e)


def response_from_blob(blob: dict[str, Any]) -> PumpStationPriceResponse:
    return PumpStationPriceResponse.model_validate(blob["response"])
