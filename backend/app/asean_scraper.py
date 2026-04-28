"""
ASEAN retail fuel price ingestion: per-country fetchers, FX to USD, and DB sync.

Respects polite crawling: single request per source, identifiable User-Agent, timeouts.
Brunei / Philippines use curated seed rows until dedicated scrapers are added.
"""

from __future__ import annotations

import csv
import io
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.data_fetcher import FUEL_CSV_URL, _dec, fetch_fuel_csv
from app.fx_rates import fetch_exchange_rates
from app.models import AseanFuelPrice

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 25
USER_AGENT = (
    "MalaysiaFuelDashboard/1.0 (+https://github.com/zuftt/malaysia-fuel-dashboard; "
    "contact: data sync bot)"
)

# Approximate retail prices when live sources fail.
# Last verified: 20 Apr 2026 via globalpetrolprices.com + official sources.
# SG: globalpetrolprices.com 20-Apr-2026 (SGD 3.08 gasoline, SGD 2.42/L diesel est.)
# TH: globalpetrolprices.com 20-Apr-2026 (Gasohol 95 E20 ~42.95, diesel 40.72 THB/L)
# ID: Pertamina official (Pertalite IDR10,000, Pertamax IDR12,300, Solar IDR6,800)
# BN: paultan.org — Brunei controlled prices unchanged
# PH: DOE Philippines via globalpetrolprices.com 20-Apr-2026
SEED_FALLBACK: dict[str, list[dict[str, Any]]] = {
    "SG": [
        {"fuel_type": "RON95", "local": Decimal("3.08"), "currency": "SGD", "subsidised": False},
        {"fuel_type": "RON97", "local": Decimal("3.97"), "currency": "SGD", "subsidised": False},
        {"fuel_type": "Diesel", "local": Decimal("4.65"), "currency": "SGD", "subsidised": False},
    ],
    "TH": [
        {"fuel_type": "RON95", "local": Decimal("42.95"), "currency": "THB", "subsidised": False},
        {"fuel_type": "RON97", "local": Decimal("52.99"), "currency": "THB", "subsidised": False},
        {"fuel_type": "Diesel", "local": Decimal("40.72"), "currency": "THB", "subsidised": False},
    ],
    "ID": [
        {"fuel_type": "RON95", "local": Decimal("10000"), "currency": "IDR", "subsidised": True},
        {"fuel_type": "RON97", "local": Decimal("12300"), "currency": "IDR", "subsidised": False},
        {"fuel_type": "Diesel", "local": Decimal("6800"), "currency": "IDR", "subsidised": True},
    ],
    "BN": [
        {"fuel_type": "RON95", "local": Decimal("0.36"), "currency": "BND", "subsidised": True},
        {"fuel_type": "RON97", "local": Decimal("0.53"), "currency": "BND", "subsidised": True},
        {"fuel_type": "Diesel", "local": Decimal("0.31"), "currency": "BND", "subsidised": True},
    ],
    "PH": [
        {"fuel_type": "RON95", "local": Decimal("88.10"), "currency": "PHP", "subsidised": False},
        {"fuel_type": "RON97", "local": Decimal("103.00"), "currency": "PHP", "subsidised": False},
        {"fuel_type": "Diesel", "local": Decimal("82.00"), "currency": "PHP", "subsidised": False},
    ],
}


def _session_headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "text/html,application/json,text/csv,*/*"}


def _to_usd_per_litre(local: Decimal, currency: str, rates_to_usd: dict[str, Decimal]) -> Decimal:
    """
    Convert local currency / litre to USD / litre.
    rates_to_usd[currency] = how many units of `currency` equal 1 USD.
    """
    if currency == "USD":
        return local.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    rate = rates_to_usd.get(currency)
    if not rate or rate == 0:
        raise ValueError(f"Missing FX rate for {currency}")
    return (local / rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _utc_midnight_naive(dt: datetime) -> datetime:
    """Store dates as naive UTC midnight (matches FuelPrice / SQLite usage)."""
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc)
    d = dt.date()
    return datetime(d.year, d.month, d.day)


def fetch_malaysia(rates_to_usd: dict[str, Decimal]) -> list[dict[str, Any]]:
    rows = fetch_fuel_csv()
    if not rows:
        return []
    latest = rows[-1]
    date_str = (latest.get("date") or "").strip()
    if not date_str:
        return []
    eff = _utc_midnight_naive(datetime.strptime(date_str, "%Y-%m-%d"))
    ron95 = _dec(latest.get("ron95"))
    ron97 = _dec(latest.get("ron97"))
    diesel = _dec(latest.get("diesel"))
    budi95 = _dec(latest.get("ron95_budi95"))
    display_ron95 = budi95 or ron95
    out: list[dict[str, Any]] = []
    if display_ron95:
        out.append(
            {
                "country": "MY",
                "country_name": "Malaysia",
                "date": eff,
                "fuel_type": "RON95",
                "local_price": display_ron95,
                "currency": "MYR",
                "usd_price": _to_usd_per_litre(display_ron95, "MYR", rates_to_usd),
                "is_subsidised": bool(budi95),
                "source_url": FUEL_CSV_URL,
                "source": "data.gov.my",
            }
        )
    if ron97:
        out.append(
            {
                "country": "MY",
                "country_name": "Malaysia",
                "date": eff,
                "fuel_type": "RON97",
                "local_price": ron97,
                "currency": "MYR",
                "usd_price": _to_usd_per_litre(ron97, "MYR", rates_to_usd),
                "is_subsidised": False,
                "source_url": FUEL_CSV_URL,
                "source": "data.gov.my",
            }
        )
    if diesel:
        out.append(
            {
                "country": "MY",
                "country_name": "Malaysia",
                "date": eff,
                "fuel_type": "Diesel",
                "local_price": diesel,
                "currency": "MYR",
                "usd_price": _to_usd_per_litre(diesel, "MYR", rates_to_usd),
                "is_subsidised": False,
                "source_url": FUEL_CSV_URL,
                "source": "data.gov.my",
            }
        )
    return out


def _parse_decimal_prices(text: str) -> list[Decimal]:
    found = re.findall(r"\b([0-9]+\.[0-9]{2})\b", text)
    vals = []
    for f in found:
        try:
            d = Decimal(f)
        except Exception:
            continue
        if Decimal("2.0") <= d <= Decimal("6.0"):
            vals.append(d)
    return vals


def fetch_singapore(rates_to_usd: dict[str, Decimal]) -> list[dict[str, Any]]:
    """
    SG has 92, 95, 98, and diesel. We map:
      RON95 → lowest petrol grade (92 octane)
      RON97 → highest petrol grade (98 octane)
      Diesel → diesel
    """
    url = "https://www.motorist.sg/petrol-prices"
    eff = _utc_midnight_naive(datetime.now(timezone.utc))
    try:
        r = requests.get(url, headers=_session_headers(), timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        candidates = _parse_decimal_prices(text)
        # SG pump prices in 2024-2026: petrol ~3.2-4.3, diesel ~4.5-5.0.
        # Filter to plausible pump range to avoid picking discount/cashback numbers.
        petrol = sorted(set(c for c in candidates if Decimal("3.0") <= c < Decimal("4.5")))
        diesel_candidates = sorted(set(c for c in candidates if Decimal("4.5") <= c <= Decimal("5.5")))
        if len(petrol) < 2:
            raise ValueError(f"Not enough SG petrol candidates in 3.0-4.5 range ({len(petrol)} found)")
        ron92 = petrol[0]
        ron98 = petrol[-1]
        diesel = diesel_candidates[0] if diesel_candidates else ron92 * Decimal("1.36")

        def row(ft: str, loc: Decimal, sub: bool) -> dict[str, Any]:
            return {
                "country": "SG",
                "country_name": "Singapore",
                "date": eff,
                "fuel_type": ft,
                "local_price": loc,
                "currency": "SGD",
                "usd_price": _to_usd_per_litre(loc, "SGD", rates_to_usd),
                "is_subsidised": sub,
                "source_url": url,
                "source": "motorist.sg",
            }

        return [
            row("RON95", ron92, False),
            row("RON97", ron98, False),
            row("Diesel", diesel, False),
        ]
    except Exception as e:
        logger.warning("Singapore scrape failed (%s), using seed fallback", e)
        return _rows_from_seed("SG", "Singapore", eff, SEED_FALLBACK["SG"], rates_to_usd, url, "seed+fallback")


def _rows_from_seed(
    code: str,
    name: str,
    eff: datetime,
    seeds: list[dict[str, Any]],
    rates_to_usd: dict[str, Decimal],
    source_url: str | None,
    source: str,
) -> list[dict[str, Any]]:
    out = []
    for s in seeds:
        loc = s["local"]
        cur = s["currency"]
        out.append(
            {
                "country": code,
                "country_name": name,
                "date": eff,
                "fuel_type": s["fuel_type"],
                "local_price": loc,
                "currency": cur,
                "usd_price": _to_usd_per_litre(loc, cur, rates_to_usd),
                "is_subsidised": s["subsidised"],
                "source_url": source_url,
                "source": source,
            }
        )
    return out


def fetch_thailand(rates_to_usd: dict[str, Decimal]) -> list[dict[str, Any]]:
    """
    Try EPPO open CSV (Bangkok retail). Falls back to seed on failure.
    """
    eff = _utc_midnight_naive(datetime.now(timezone.utc))
    # Public petroleum statistics CSV (structure may change; wrapped in try).
    urls = [
        "https://data.eppo.go.th/trade_statistics/public_prices/download/public_prices.csv",
    ]
    for csv_url in urls:
        try:
            resp = requests.get(csv_url, headers=_session_headers(), timeout=HTTP_TIMEOUT)
            if resp.status_code != 200:
                continue
            reader = csv.DictReader(io.StringIO(resp.text))
            rows = list(reader)
            if not rows:
                continue
            last = rows[-1]
            # Try common column names (EPPO exports vary).
            date_col = next((c for c in last if "date" in c.lower()), None)
            d_raw = last.get(date_col) if date_col else None
            if d_raw:
                for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                    try:
                        eff = _utc_midnight_naive(datetime.strptime(str(d_raw).strip(), fmt))
                        break
                    except ValueError:
                        continue

            def pick(*names: str) -> Decimal | None:
                for n in names:
                    for k, v in last.items():
                        if k and n.lower() in k.lower() and v not in (None, ""):
                            d = _dec(str(v).replace(",", ""))
                            if d:
                                return d
                return None

            r95 = pick("gasohol 95", "95", "ron 95")
            r97 = pick("gasohol 97", "98", "ron 97")
            dsl = pick("diesel", "hsd")
            if not r95:
                continue
            if not r97:
                r97 = r95 * Decimal("1.05")
            if not dsl:
                dsl = r95 * Decimal("0.92")

            def row(ft: str, loc: Decimal, sub: bool) -> dict[str, Any]:
                return {
                    "country": "TH",
                    "country_name": "Thailand",
                    "date": eff,
                    "fuel_type": ft,
                    "local_price": loc,
                    "currency": "THB",
                    "usd_price": _to_usd_per_litre(loc, "THB", rates_to_usd),
                    "is_subsidised": sub,
                    "source_url": csv_url,
                    "source": "eppo.go.th",
                }

            return [
                row("RON95", r95, False),
                row("RON97", r97, False),
                row("Diesel", dsl, False),
            ]
        except Exception as e:
            logger.debug("TH CSV attempt failed for %s: %s", csv_url, e)
            continue

    logger.warning("Thailand EPPO fetch failed, using seed fallback")
    return _rows_from_seed(
        "TH",
        "Thailand",
        eff,
        SEED_FALLBACK["TH"],
        rates_to_usd,
        "https://www.eppo.go.th/",
        "seed+fallback",
    )


def fetch_indonesia(rates_to_usd: dict[str, Decimal]) -> list[dict[str, Any]]:
    url = "https://www.mypertamina.id/fuels-harga"
    eff = _utc_midnight_naive(datetime.now(timezone.utc))
    try:
        r = requests.get(url, headers=_session_headers(), timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        idr = [Decimal(m.group(1).replace(",", "").replace(".", ""))
               for m in re.finditer(r"\b([5-9]\d{3}|[1-2]\d{4})\b", text)]
        idr = [x for x in idr if Decimal("5000") <= x <= Decimal("25000")]
        if len(idr) < 2:
            raise ValueError("Not enough IDR candidates")
        idr = sorted(set(idr))
        pertalite = min(x for x in idr if x >= 9000) if any(x >= 9000 for x in idr) else idr[0]
        pertamax = min(x for x in idr if x > pertalite) if any(x > pertalite for x in idr) else pertalite * Decimal("1.23")
        diesel = min(x for x in idr if x < pertalite) if any(x < pertalite for x in idr) else Decimal("6800")

        def row(ft: str, loc: Decimal, sub: bool) -> dict[str, Any]:
            return {
                "country": "ID",
                "country_name": "Indonesia",
                "date": eff,
                "fuel_type": ft,
                "local_price": loc,
                "currency": "IDR",
                "usd_price": _to_usd_per_litre(loc, "IDR", rates_to_usd),
                "is_subsidised": sub,
                "source_url": url,
                "source": "mypertamina.id",
            }

        return [
            row("RON95", pertalite, True),
            row("RON97", pertamax, False),
            row("Diesel", diesel, True),
        ]
    except Exception as e:
        logger.warning("Indonesia scrape failed (%s), using seed fallback", e)
        return _rows_from_seed("ID", "Indonesia", eff, SEED_FALLBACK["ID"], rates_to_usd, url, "seed+fallback")


def fetch_brunei(rates_to_usd: dict[str, Decimal]) -> list[dict[str, Any]]:
    eff = _utc_midnight_naive(datetime.now(timezone.utc))
    return _rows_from_seed(
        "BN",
        "Brunei",
        eff,
        SEED_FALLBACK["BN"],
        rates_to_usd,
        "https://www.moe.gov.bn/",
        "manual-seed",
    )


def fetch_philippines(rates_to_usd: dict[str, Decimal]) -> list[dict[str, Any]]:
    eff = _utc_midnight_naive(datetime.now(timezone.utc))
    return _rows_from_seed(
        "PH",
        "Philippines",
        eff,
        SEED_FALLBACK["PH"],
        rates_to_usd,
        "https://www.doe.gov.ph/",
        "manual-seed",
    )


def sync_asean_prices(session: Session) -> dict[str, Any]:
    """
    Fetch all ASEAN sources and upsert into asean_fuel_prices.
    """
    rates = fetch_exchange_rates()
    batch: list[dict[str, Any]] = []
    batch.extend(fetch_malaysia(rates))
    batch.extend(fetch_singapore(rates))
    batch.extend(fetch_thailand(rates))
    batch.extend(fetch_indonesia(rates))
    batch.extend(fetch_brunei(rates))
    batch.extend(fetch_philippines(rates))

    upserted = 0
    for item in batch:
        day = _utc_midnight_naive(item["date"])
        existing = (
            session.query(AseanFuelPrice)
            .filter(
                AseanFuelPrice.country == item["country"],
                AseanFuelPrice.fuel_type == item["fuel_type"],
                AseanFuelPrice.date == day,
            )
            .first()
        )
        if existing:
            existing.country_name = item["country_name"]
            existing.local_price = item["local_price"]
            existing.currency = item["currency"]
            existing.usd_price = item["usd_price"]
            existing.is_subsidised = item["is_subsidised"]
            existing.source_url = item.get("source_url")
            existing.source = item["source"]
        else:
            session.add(
                AseanFuelPrice(
                    country=item["country"],
                    country_name=item["country_name"],
                    date=day,
                    fuel_type=item["fuel_type"],
                    local_price=item["local_price"],
                    currency=item["currency"],
                    usd_price=item["usd_price"],
                    is_subsidised=item["is_subsidised"],
                    source_url=item.get("source_url"),
                    source=item["source"],
                )
            )
        upserted += 1

    session.commit()
    return {
        "upserted": upserted,
        "currencies": list(rates.keys()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
