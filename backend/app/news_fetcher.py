"""
Live news ingestion from RSS feeds (fuel / subsidy / Malaysia policy related).

Uses feedparser + keyword relevance scoring so the dashboard stays useful without noise.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import feedparser
import requests
from sqlalchemy.orm import Session

from app.models import GovernmentAnnouncement

logger = logging.getLogger(__name__)

# Try to import Webz.io fetcher (optional dependency)
try:
    from app.webz_news_fetcher import sync_webz_news
    HAS_WEBZ = True
except ImportError:
    HAS_WEBZ = False

# Malaysia / fuel context — article must match at least one gate term
_GATE_TERMS = re.compile(
    r"\b(malaysia|malaysian|my\b|petronas|putrajaya|kuala|apm|kpdn|mof|sinar|"
    r"kerajaan|subsidi|subsidy|madani|budi)\b",
    re.I,
)

# Topic relevance — must match at least one
_TOPIC_TERMS = re.compile(
    r"\b(fuel|petrol|diesel|minyak|ron\s*95|ron\s*97|gasoline|petroleum|oil\s+price|"
    r"harga\s+minyak|price\s+cap|retail\s+fuel|energy|oem|apm|subsidi|subsidy|"
    r"inflation|budget)\b",
    re.I,
)

DEFAULT_RSS_FEEDS: tuple[tuple[str, str], ...] = (
    (
        "Google News — Malaysia fuel",
        "https://news.google.com/rss/search?q=Malaysia+%28fuel+OR+petrol+OR+diesel+OR+RON+OR+subsidi+minyak%29&hl=en-MY&gl=MY&ceid=MY:en",
    ),
    (
        "Google News — BM minyak",
        "https://news.google.com/rss/search?q=minyak+RON+subsidi+harga+Malaysia&hl=ms&gl=MY&ceid=MY:ms",
    ),
)

HEADERS = {
    "User-Agent": (
        "MalaysiaFuelDashboard/1.0 (+https://github.com/zuftt/malaysia-fuel-dashboard)"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def _parse_feed_datetime(entry: Any) -> datetime:
    """Best-effort published date from feedparser entry."""
    if getattr(entry, "published_parsed", None):
        t = entry.published_parsed
        return datetime(*t[:6], tzinfo=timezone.utc).replace(tzinfo=None)
    if getattr(entry, "updated_parsed", None):
        t = entry.updated_parsed
        return datetime(*t[:6], tzinfo=timezone.utc).replace(tzinfo=None)
    return datetime.utcnow()


def _is_relevant(title: str, summary: str) -> bool:
    blob = f"{title}\n{summary or ''}"
    if not _TOPIC_TERMS.search(blob):
        return False
    # Malaysia-focused feeds often omit "Malaysia" in title — allow global oil pieces only if gate matches
    if _GATE_TERMS.search(blob):
        return True
    # Strong fuel headline without country name (short titles)
    if len(title) < 120 and _TOPIC_TERMS.search(title):
        return True
    return False


def _rss_urls() -> tuple[tuple[str, str], ...]:
    raw = os.getenv("NEWS_RSS_URLS", "").strip()
    if not raw:
        return DEFAULT_RSS_FEEDS
    pairs: list[tuple[str, str]] = []
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if "|" in chunk:
            label, url = chunk.split("|", 1)
            pairs.append((label.strip(), url.strip()))
        elif chunk.startswith("http"):
            pairs.append(("Custom RSS", chunk))
    return tuple(pairs) if pairs else DEFAULT_RSS_FEEDS


def sync_news_feeds(session: Session, max_total: int = 24) -> dict[str, Any]:
    """
    Fetch news from primary source (Webz.io API if available, else RSS feeds).
    Filter by relevance, upsert into government_announcements.

    Uses (source, source_url) uniqueness from the model.
    """
    # Try Webz.io first (more reliable than Google News RSS which blocks)
    if HAS_WEBZ and os.getenv("WEBZ_IO_API_KEY", "").strip():
        try:
            logger.info("Syncing from Webz.io (primary source)...")
            result = sync_webz_news(session)
            logger.info(f"Webz.io sync result: {result}")
            return result
        except Exception as e:
            logger.warning(f"Webz.io sync failed, falling back to RSS: {e}")

    # Fall back to RSS feeds
    logger.info("Using RSS feeds (fallback)...")
    inserted = 0
    updated = 0
    skipped = 0
    errors: list[str] = []
    seen_urls: set[str] = set()
    stop = False

    for feed_label, feed_url in _rss_urls():
        if stop:
            break
        try:
            resp = requests.get(feed_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            errors.append(f"{feed_label}: {e}")
            logger.warning("RSS fetch failed %s: %s", feed_label, e)
            continue

        parsed = feedparser.parse(resp.content)
        for entry in getattr(parsed, "entries", [])[:30]:
            title = (getattr(entry, "title", "") or "").strip()
            link = (getattr(entry, "link", "") or "").strip()
            summary = ""
            if getattr(entry, "summary", None):
                summary = re.sub(r"<[^>]+>", "", entry.summary)[:2000]
            elif getattr(entry, "description", None):
                summary = re.sub(r"<[^>]+>", "", str(entry.description))[:2000]

            if not title or not link:
                skipped += 1
                continue
            if link in seen_urls:
                continue
            seen_urls.add(link)

            if not _is_relevant(title, summary):
                skipped += 1
                continue

            pub_dt = _parse_feed_datetime(entry)
            host = urlparse(link).netloc or "news"

            existing = (
                session.query(GovernmentAnnouncement)
                .filter(GovernmentAnnouncement.source_url == link)
                .first()
            )

            payload = dict(
                announcement_date=pub_dt,
                title=title[:500],
                content=summary[:8000] if summary else None,
                source=f"RSS · {feed_label}",
                source_url=link,
                announcement_type="News Feed",
                keywords=["rss", host.split(".")[-2] if "." in host else host],
            )

            if existing:
                existing.announcement_date = pub_dt
                existing.title = payload["title"]
                existing.content = payload["content"]
                existing.source = payload["source"]
                existing.keywords = payload["keywords"]
                updated += 1
            else:
                session.add(GovernmentAnnouncement(**payload))
                inserted += 1

            if inserted + updated >= max_total:
                stop = True
                break
        if stop:
            break

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception("news sync commit failed: %s", e)
        raise

    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


def news_feeds_stale(session: Session, max_age_hours: float = 4.0) -> bool:
    """True if we should refresh RSS (no rows or oldest News Feed older than max_age_hours)."""
    q = (
        session.query(GovernmentAnnouncement)
        .filter(GovernmentAnnouncement.announcement_type == "News Feed")
        .order_by(GovernmentAnnouncement.created_at.desc())
    )
    latest = q.first()
    if latest is None:
        return True
    if latest.created_at is None:
        return True
    age = datetime.utcnow() - latest.created_at.replace(tzinfo=None)
    return age > timedelta(hours=max_age_hours)


def maybe_refresh_news(session: Session) -> None:
    """Refresh RSS when data is stale (safe no-op on failure)."""
    try:
        if news_feeds_stale(session):
            sync_news_feeds(session)
    except Exception as e:
        logger.warning("maybe_refresh_news skipped: %s", e)
