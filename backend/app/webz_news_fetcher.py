"""
Webz.io News API integration for Malaysia fuel & subsidy news.
Replaces Google News RSS (which blocks scrapers with 503 errors).

API: https://webz.io/newsapilite (1,000 calls/month free tier)
"""

import requests
import logging
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import GovernmentAnnouncement

logger = logging.getLogger(__name__)

WEBZ_API_URL = "https://api.webz.io/newsApiLite"
WEBZ_API_KEY = os.getenv("WEBZ_IO_API_KEY", "").strip()

# Search queries for different news feeds
QUERIES = {
    "fuel_prices_en": "Malaysia fuel price petrol diesel RON95 RON97",
    "fuel_prices_my": "harga minyak Malaysia petrol diesel RON95",
    "subsidies": "Malaysia subsidy fuel minyak subsidi",
}


def fetch_webz_news(query: str, language: str = "english") -> list[dict] | None:
    """Fetch news from Webz.io API."""
    if not WEBZ_API_KEY:
        logger.warning("WEBZ_IO_API_KEY not set, skipping news fetch")
        return None

    params = {
        "token": WEBZ_API_KEY,
        "q": query,
        "language": language,
        "sort": "recency",
        "pageSize": 10,
    }

    try:
        resp = requests.get(WEBZ_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("posts"):
            logger.info(f"No posts found for query: {query}")
            return []

        articles = []
        for post in data["posts"]:
            articles.append({
                "title": post.get("title", ""),
                "description": post.get("text", post.get("summary", "")),
                "url": post.get("url", ""),
                "source": post.get("source", ""),
                "published_at": post.get("published", datetime.now(timezone.utc).isoformat()),
                "image_url": post.get("image", ""),
            })

        return articles
    except requests.RequestException as e:
        logger.error(f"Webz.io fetch failed: {e}")
        return None


def sync_webz_news(session: Session) -> dict:
    """Fetch from Webz.io API and store to database."""
    if not WEBZ_API_KEY:
        logger.warning("WEBZ_IO_API_KEY not set")
        return {"inserted": 0, "updated": 0, "skipped": 0}

    stats = {"inserted": 0, "updated": 0, "skipped": 0}

    for feed_name, query in QUERIES.items():
        language = "malay" if "_my" in feed_name or feed_name == "subsidies" else "english"

        logger.info(f"Fetching Webz.io {feed_name} ({language}): {query}")
        articles = fetch_webz_news(query, language)

        if not articles:
            continue

        for article in articles:
            url = article.get("url", "")
            if not url:
                stats["skipped"] += 1
                continue

            # Check if article already exists
            existing = (
                session.query(GovernmentAnnouncement)
                .filter(GovernmentAnnouncement.source_url == url)
                .first()
            )

            try:
                pub_dt = datetime.fromisoformat(article.get("published_at", "").replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, AttributeError):
                pub_dt = datetime.utcnow()

            payload = {
                "announcement_date": pub_dt,
                "title": article.get("title", "")[:500],
                "content": article.get("description", "")[:8000],
                "source": f"Webz.io · {article.get('source', 'Unknown')}",
                "source_url": url,
                "announcement_type": "News Feed",
                "keywords": ["webz.io", feed_name.split("_")[0]],
            }

            if existing:
                existing.announcement_date = payload["announcement_date"]
                existing.title = payload["title"]
                existing.content = payload["content"]
                existing.source = payload["source"]
                existing.keywords = payload["keywords"]
                stats["updated"] += 1
            else:
                session.add(GovernmentAnnouncement(**payload))
                stats["inserted"] += 1

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception("Webz.io sync commit failed: %s", e)
        raise

    logger.info(f"Webz.io sync complete: {stats['inserted']} inserted, {stats['updated']} updated, {stats['skipped']} skipped")
    return stats
