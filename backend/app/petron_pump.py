"""
Optional Petron homepage scrape for RON 100 (Blaze 100) — ``MY_PUMP_PRICES2``.

Runs only when the pump pipeline performs a live fetch (same weekly rule as Shell;
see ``pump_station_cache.needs_live_scrape``), not on every browser refresh.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BLAZE_OR_RON100 = re.compile(r"BLAZE\s*100|RON\s*100", re.I)
_RM_PRICE = re.compile(r"RM\s*(\d+(?:\.\d+)?)", re.I)


def fetch_petron_ron100_row(url: str) -> dict[str, Any] | None:
    """
    Parse Petron Malaysia HTML for PETRON BLAZE 100 / RON 100 and an ``RM x.xx`` price
    in the same block of text.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=35)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup.find_all(["td", "div", "span", "p", "li", "h2", "h3", "h4", "strong"]):
        text = tag.get_text(" ", strip=True)
        if len(text) > 400:
            continue
        if not _BLAZE_OR_RON100.search(text):
            continue
        m = _RM_PRICE.search(text)
        if not m:
            continue
        try:
            price = float(m.group(1))
        except ValueError:
            continue
        if not (0 < price < 50):
            continue
        return {
            "station": "RON 100 (Petron Blaze 100)",
            "location": None,
            "ron95_budi": None,
            "ron95": None,
            "ron97": None,
            "vpower": None,
            "ron100": price,
            "diesel": None,
            "diesel_b7": None,
        }

    logger.warning("Petron page had no Blaze 100 / RON 100 price block at %s", url)
    return None


def append_petron_ron100_if_configured(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """If ``MY_PUMP_PRICES2`` is set, append one RON 100 row when the scrape succeeds."""
    from app.safe_url import assert_safe_url

    raw = os.getenv("MY_PUMP_PRICES2", "").strip()
    if not raw:
        return rows
    url = raw if raw.startswith("http") else "https://" + raw.lstrip("/")
    try:
        assert_safe_url(url)
        row = fetch_petron_ron100_row(url)
        if row:
            return [*rows, row]
    except ValueError as e:
        logger.warning("MY_PUMP_PRICES2 rejected by allowlist: %s", e)
    except Exception as e:
        logger.warning("MY_PUMP_PRICES2 Petron scrape failed: %s", e)
    return rows
