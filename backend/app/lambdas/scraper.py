"""
Lambda handler: Scrape fuel prices from data.gov.my on a weekly schedule.
Triggered by EventBridge every Wednesday evening.
Publishes price change notifications to SNS.
"""

import json
import logging
import os
from decimal import Decimal

import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lazy imports — avoid cold start overhead if not needed
_db_session = None
_sns_client = None


def _get_db():
    """Create a database session (NullPool for Lambda — no persistent connections)."""
    global _db_session
    if _db_session is None:
        database_url = os.environ["DATABASE_URL"]
        engine = create_engine(database_url, poolclass=NullPool, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)
        _db_session = Session
    return _db_session()


def _get_sns():
    """Get SNS client."""
    global _sns_client
    if _sns_client is None:
        _sns_client = boto3.client("sns")
    return _sns_client


def _publish_price_change(old_prices: dict, new_prices: dict, date: str):
    """Publish price change notification to SNS topic."""
    topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if not topic_arn:
        logger.info("No SNS_TOPIC_ARN set, skipping notification")
        return

    changes = []
    for fuel, label in [("ron97", "RON 97"), ("diesel", "Diesel"), ("ron95", "RON 95")]:
        old_val = old_prices.get(fuel)
        new_val = new_prices.get(fuel)
        if old_val and new_val and old_val != new_val:
            diff = new_val - old_val
            direction = "naik" if diff > 0 else "turun"
            changes.append(f"  {label}: RM {new_val:.2f} ({direction} {abs(diff):.2f})")

    if not changes:
        logger.info("No price changes detected, skipping SNS notification")
        return

    message = f"Harga Minyak Malaysia — {date}\n\n"
    message += "Perubahan minggu ini:\n"
    message += "\n".join(changes)
    message += "\n\nSumber: data.gov.my"

    _get_sns().publish(
        TopicArn=topic_arn,
        Subject=f"Harga Minyak {date} — Perubahan Dikesan",
        Message=message,
    )
    logger.info(f"SNS notification published: {len(changes)} price changes")


def _run_asean_sync(db):
    """Refresh `asean_fuel_prices` (FX + regional sources); failures are logged only."""
    try:
        from app.asean_scraper import sync_asean_prices

        asean_result = sync_asean_prices(db)
        logger.info(
            "ASEAN sync complete: %s rows upserted",
            asean_result.get("upserted", 0),
        )
    except Exception as asean_err:
        logger.warning("ASEAN sync failed (non-fatal): %s", asean_err, exc_info=True)


def handler(event, context):
    """
    Lambda entry point. Triggered by EventBridge schedule.

    1. Fetch latest prices from data.gov.my
    2. Compare with last stored prices
    3. Upsert new records into RDS
    4. Publish changes to SNS
    """
    # Import here to avoid top-level DB dependency
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from app.data_fetcher import fetch_fuel_csv, _dec
    from app.models import FuelPrice, PriceHistory, Base
    from datetime import datetime

    db = _get_db()

    try:
        # Fetch latest data
        rows = fetch_fuel_csv()
        logger.info(f"Fetched {len(rows)} price records from data.gov.my")

        if not rows:
            return {"statusCode": 200, "body": "No data fetched"}

        # Get the most recent row
        latest_row = rows[-1]
        date_str = latest_row.get("date", "").strip()
        effective_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Check if we already have this date
        existing = db.query(FuelPrice).filter(
            FuelPrice.effective_date == effective_date,
            FuelPrice.region == "Peninsular",
        ).first()

        if existing:
            logger.info(f"Prices for {date_str} already exist, skipping")
            _run_asean_sync(db)
            return {"statusCode": 200, "body": f"Already up to date: {date_str}"}

        # Get previous latest prices for comparison
        prev = db.query(FuelPrice).filter(
            FuelPrice.region == "Peninsular"
        ).order_by(FuelPrice.effective_date.desc()).first()

        old_prices = {}
        if prev:
            old_prices = {
                "ron95": float(prev.ron95_subsidized) if prev.ron95_subsidized else None,
                "ron97": float(prev.ron97) if prev.ron97 else None,
                "diesel": float(prev.diesel_peninsular) if prev.diesel_peninsular else None,
            }

        # Parse new prices
        ron95 = _dec(latest_row.get("ron95"))
        ron97 = _dec(latest_row.get("ron97"))
        diesel = _dec(latest_row.get("diesel"))
        diesel_east = _dec(latest_row.get("diesel_eastmsia"))
        budi95 = _dec(latest_row.get("ron95_budi95"))

        new_prices = {
            "ron95": float(budi95 or ron95) if (budi95 or ron95) else None,
            "ron97": float(ron97) if ron97 else None,
            "diesel": float(diesel) if diesel else None,
        }

        # Insert new price record
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

        # Insert price history entries
        for fuel_type, price_val in [("RON95", budi95 or ron95), ("RON97", ron97), ("Diesel", diesel)]:
            if price_val is None:
                continue
            hist = PriceHistory(
                date=effective_date,
                fuel_type=fuel_type,
                price=price_val,
                region="Peninsular",
                subsidy_status="subsidized" if fuel_type == "RON95" and budi95 else "market",
            )
            db.add(hist)

        db.commit()
        logger.info(f"Stored new prices for {date_str}")

        _run_asean_sync(db)

        # Publish SNS notification if prices changed
        _publish_price_change(old_prices, new_prices, date_str)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Prices updated for {date_str}",
                "prices": {k: str(v) for k, v in new_prices.items() if v},
            }),
        }

    except Exception as e:
        logger.error(f"Scraper error: {e}", exc_info=True)
        raise
    finally:
        db.close()
