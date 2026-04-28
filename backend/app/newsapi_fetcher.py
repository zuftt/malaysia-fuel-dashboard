"""
NewsAPI.org integration for Malaysia fuel & subsidy news.
Free tier: 100 requests/day, articles up to 1 month old.
Docs: https://newsapi.org/docs/endpoints/everything
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from app.models import GovernmentAnnouncement

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()

QUERIES = [
    ("fuel_en",  "Malaysia petrol RON95 fuel price"),
    ("fuel_bm",  "harga minyak Malaysia RON95 diesel"),
    ("subsidy",  "Malaysia fuel subsidy BUDI95"),
]


def _fetch(query: str, page_size: int = 10) -> list[dict]:
    """Call NewsAPI /v2/everything and return raw article dicts."""
    try:
        resp = requests.get(
            NEWSAPI_URL,
            params={
                "q": query,
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "apiKey": NEWSAPI_KEY,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            logger.warning("NewsAPI error for %r: %s", query, data.get("message"))
            return []
        return data.get("articles", [])
    except requests.RequestException as e:
        logger.error("NewsAPI fetch failed for %r: %s", query, e)
        return []


def sync_newsapi(session: Session) -> dict:
    """Fetch from NewsAPI and upsert into government_announcements."""
    if not NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY not set, skipping NewsAPI fetch")
        return {"inserted": 0, "updated": 0, "skipped": 0}

    stats = {"inserted": 0, "updated": 0, "skipped": 0}
    seen_urls: set[str] = set()  # dedup across multiple query results

    for feed_name, query in QUERIES:
        logger.info("NewsAPI [%s]: %r", feed_name, query)
        articles = _fetch(query)

        for article in articles:
            url = (article.get("url") or "").strip()
            if not url or url == "https://removed.com" or url in seen_urls:
                stats["skipped"] += 1
                continue
            seen_urls.add(url)

            title = (article.get("title") or "").strip()[:500]
            if not title or title == "[Removed]":
                stats["skipped"] += 1
                continue

            try:
                pub_dt = datetime.fromisoformat(
                    article["publishedAt"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
            except (KeyError, ValueError):
                pub_dt = datetime.utcnow()

            source_name = (article.get("source") or {}).get("name") or "NewsAPI"
            description = (article.get("description") or article.get("content") or "")[:8000]

            existing = (
                session.query(GovernmentAnnouncement)
                .filter(GovernmentAnnouncement.source_url == url)
                .first()
            )

            payload = dict(
                announcement_date=pub_dt,
                title=title,
                content=description,
                source=f"NewsAPI · {source_name}",
                source_url=url,
                announcement_type="News Feed",
                keywords=["newsapi", feed_name],
            )

            if existing:
                for k, v in payload.items():
                    setattr(existing, k, v)
                stats["updated"] += 1
            else:
                session.add(GovernmentAnnouncement(**payload))
                stats["inserted"] += 1

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception("NewsAPI sync commit failed: %s", e)
        raise

    logger.info("NewsAPI sync: %(inserted)s inserted, %(updated)s updated, %(skipped)s skipped", stats)
    return stats
