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

from app.models import News

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


def sync_webz_news(db: Session) -> dict:
    """Sync news from Webz.io into database."""
    if not WEBZ_API_KEY:
        logger.warning("WEBZ_IO_API_KEY not set")
        return {"inserted": 0, "updated": 0, "skipped": 0}

    stats = {"inserted": 0, "updated": 0, "skipped": 0}

    for feed_name, query in QUERIES.items():
        language = "malay" if "_my" in feed_name or feed_name == "subsidies" else "english"

        logger.info(f"Fetching {feed_name} ({language}): {query}")
        articles = fetch_webz_news(query, language)

        if not articles:
            continue

        for article in articles:
            try:
                existing = db.query(News).filter_by(url=article["url"]).first()

                if existing:
                    existing.title = article["title"]
                    existing.description = article["description"]
                    existing.updated_at = datetime.now(timezone.utc)
                    stats["updated"] += 1
                else:
                    news = News(
                        title=article["title"],
                        description=article["description"],
                        url=article["url"],
                        source=article["source"],
                        published_at=article["published_at"],
                        image_url=article["image_url"],
                        category="fuel_policy",
                    )
                    db.add(news)
                    stats["inserted"] += 1
            except Exception as e:
                logger.error(f"Failed to process article: {e}")
                stats["skipped"] += 1

        db.commit()

    logger.info(
        f"Webz.io sync complete: {stats['inserted']} new, "
        f"{stats['updated']} updated, {stats['skipped']} skipped"
    )
    return stats
