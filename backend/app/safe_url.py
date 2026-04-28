"""
SSRF-prevention helpers for env-controlled scrape URLs.

These URLs are set by operators in Render env vars, but a misconfigured or
compromised env could otherwise point requests.get at internal services
(e.g. cloud metadata, RDS internal endpoints). We require https + a host
in an explicit allowlist of public data sources we already use.
"""

from __future__ import annotations

from urllib.parse import urlparse

# Suffix-match allowlist. Adding www. or subdomains is fine — we match by
# trailing .domain. Keep this list minimal and tied to real upstreams.
ALLOWED_HOSTS: tuple[str, ...] = (
    # Pump-grade scrape (Shell Malaysia, Motorist aggregators, Petron).
    "shell.com.my",
    "motorist.my",
    "motorist.sg",
    "petron.com.my",
    # ASEAN per-country sources.
    "globalpetrolprices.com",
    "eppo.go.th",
    "thairath.co.th",
    "mypertamina.id",
    "pertamina.com",
    "oto.com",
    "paultan.org",
    "fuelprice.ph",
    "philstar.com",
    # Public Malaysian government / data sources.
    "data.gov.my",
    "treasury.gov.my",
    "kpdn.gov.my",
    # News RSS feeds.
    "bing.com",
)


def assert_safe_url(url: str, *, allowed: tuple[str, ...] = ALLOWED_HOSTS) -> str:
    """
    Raise ValueError if URL is not https or its host is not on the allowlist.
    Returns the URL unchanged on success so it can be used inline.
    """
    if not url:
        raise ValueError("URL is empty")
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"URL scheme must be https (got {parsed.scheme!r})")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL has no host")
    for allowed_host in allowed:
        if host == allowed_host or host.endswith("." + allowed_host):
            return url
    raise ValueError(f"Host {host!r} is not in the allowlist")
