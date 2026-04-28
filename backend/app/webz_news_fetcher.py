"""
Webz.io News API integration for Malaysia fuel & subsidy news.
Replaces Google News RSS (which blocks scrapers with 503 errors).

API: https://webz.io/newsapilite (1,000 calls/month free tier)
"""

import requests
import logging
import os
from datetime import datetime, timezone

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


def sync_webz_news(db = None) -> dict:
    """Fetch news from Webz.io (database storage not yet implemented)."""
    if not WEBZ_API_KEY:
        logger.warning("WEBZ_IO_API_KEY not set")
        return {"inserted": 0, "updated": 0, "skipped": 0}

    stats = {"inserted": 0, "updated": 0, "skipped": 0}

    for feed_name, query in QUERIES.items():
        language = "malay" if "_my" in feed_name or feed_name == "subsidies" else "english"

        logger.info(f"Fetching {feed_name} ({language}): {query}")
        articles = fetch_webz_news(query, language)

        if articles:
            stats["inserted"] += len(articles)
            logger.info(f"  → {len(articles)} articles found")

    logger.info(
        f"Webz.io sync complete: {stats['inserted']} articles fetched"
    )
    return stats
