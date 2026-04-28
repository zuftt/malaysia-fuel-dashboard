"""
Data fetcher for Malaysia fuel prices from data.gov.my

Source: https://data.gov.my/data-catalogue/fuelprice
CSV: https://storage.data.gov.my/commodities/fuelprice.csv

Fields: series_type, date, ron95, ron97, diesel, diesel_eastmsia, ron95_budi95
- series_type: "level" (actual price) or "change_weekly" (week-over-week change)
- date: effective date (YYYY-MM-DD)
- ron95, ron97, diesel, diesel_eastmsia: price per litre in RM
- ron95_budi95: RON95 BUDI subsidized price
"""

import csv
import io
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

import requests
from sqlalchemy.orm import Session

from app.models import FuelPrice, PriceHistory

logger = logging.getLogger(__name__)

FUEL_CSV_URL = "https://storage.data.gov.my/commodities/fuelprice.csv"


def fetch_fuel_csv() -> list[dict]:
    """Download and parse the fuel price CSV from data.gov.my."""
    resp = requests.get(FUEL_CSV_URL, timeout=30)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    return [row for row in reader if row.get("series_type") == "level"]


def _dec(value: str) -> Decimal | None:
    """Convert string to Decimal, returning None for empty/invalid values."""
    if not value or not value.strip():
        return None
    try:
        return Decimal(value.strip())
    except InvalidOperation:
        return None


def sync_fuel_prices(db: Session) -> dict:
    """
    Fetch fuel prices from data.gov.my and upsert into the database.
    Returns a summary of what was synced.
    """
    rows = fetch_fuel_csv()
    logger.info(f"Fetched {len(rows)} price records from data.gov.my")

    created = 0
    skipped = 0

    for row in rows:
        date_str = row.get("date", "").strip()
        if not date_str:
            skipped += 1
            continue

        effective_date = datetime.strptime(date_str, "%Y-%m-%d")
        ron95 = _dec(row.get("ron95"))
        ron97 = _dec(row.get("ron97"))
        diesel = _dec(row.get("diesel"))
        diesel_east = _dec(row.get("diesel_eastmsia"))
        budi95 = _dec(row.get("ron95_budi95"))

        if ron97 is None or diesel is None:
            skipped += 1
            continue

        # Check if this date+region already exists
        existing = db.query(FuelPrice).filter(
            FuelPrice.effective_date == effective_date,
            FuelPrice.region == "Peninsular",
            FuelPrice.source == "data.gov.my"
        ).first()

        if existing:
            skipped += 1
            continue

        price = FuelPrice(
            date_announced=effective_date,
            effective_date=effective_date,
            ron95_subsidized=budi95 or ron95,
            ron95_market=ron95,
            ron97=ron97,
            diesel_peninsular=diesel,
            diesel_east_malaysia=diesel_east,
            region="Peninsular",
            source="data.gov.my",
        )
        db.add(price)

        # Also create price history entries for trend tracking
        for fuel_type, price_val, mops_ref in [
            ("RON95", budi95 or ron95, ron95),
            ("RON97", ron97, None),
            ("Diesel", diesel, None),
        ]:
            if price_val is None:
                continue

            existing_hist = db.query(PriceHistory).filter(
                PriceHistory.date == effective_date,
                PriceHistory.fuel_type == fuel_type,
                PriceHistory.region == "Peninsular",
            ).first()

            if existing_hist:
                continue

            subsidy_gap = None
            if fuel_type == "RON95" and ron95 and budi95 and ron95 != budi95:
                subsidy_gap = ron95 - budi95

            hist = PriceHistory(
                date=effective_date,
                fuel_type=fuel_type,
                price=price_val,
                region="Peninsular",
                subsidy_status="subsidized" if fuel_type == "RON95" and budi95 else "market",
                mops_reference=mops_ref if fuel_type == "RON95" else None,
                subsidy_gap=subsidy_gap,
            )
            db.add(hist)

        created += 1

    db.commit()
    logger.info(f"Sync complete: {created} new records, {skipped} skipped")
    return {"created": created, "skipped": skipped, "total_fetched": len(rows)}
