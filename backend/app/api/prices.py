"""
Fuel Prices API Endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
import os
import logging

from app.database import get_db
from app.data_fetcher import FUEL_CSV_URL
from app.models import FuelPrice, PriceHistory, GlobalBenchmark, AseanFuelPrice
from app.schemas import (
    FuelPriceResponse,
    TrendData,
    AseanCompareResponse,
    AseanCompareRow,
    ExchangeRatesInfo,
    AseanHistoryRow,
    AseanHistoryResponse,
    PumpStationPriceResponse,
    PumpStationPriceRow,
)
from sqlalchemy import func
from app.asean_scraper import fetch_exchange_rates, _to_usd_per_litre
from app.fx_rates import fetch_exchange_rates_bundle
from app.api.scrape import fetch_my_pump_prices_from_env
from app.pump_station_cache import (
    needs_live_scrape,
    read_cache,
    response_from_blob,
    write_cache,
)

logger = logging.getLogger(__name__)


def _pump_station_label_is_ron100(station: str) -> bool:
    s = station or ""
    return re.search(r"\bron\s*100\b|\bron100\b", s, re.I) is not None


def _pump_response_without_ron100(resp: PumpStationPriceResponse) -> PumpStationPriceResponse:
    """Strip RON 100 rows (including stale disk cache from older scrapers)."""
    data = [r for r in resp.data if not _pump_station_label_is_ron100(r.station)]
    if len(data) == len(resp.data):
        return resp
    return resp.model_copy(update={"data": data, "count": len(data)})


DATA_GOV_MY_FUEL_CATALOGUE = "https://data.gov.my/data-catalogue/fuelprice"

# DynamoDB visitor counter (optional — only in AWS)
_dynamodb = None

def _increment_visitor_count():
    """Atomic counter in DynamoDB — tracks API usage."""
    global _dynamodb
    table_name = os.environ.get("DYNAMODB_TABLE")
    if not table_name:
        return
    try:
        if _dynamodb is None:
            import boto3
            _dynamodb = boto3.resource("dynamodb").Table(table_name)
        _dynamodb.update_item(
            Key={"email": "visitor_counter", "fuel_type": "api_hits"},
            UpdateExpression="ADD visit_count :inc",
            ExpressionAttributeValues={":inc": 1},
        )
    except Exception as e:
        logger.debug(f"Visitor counter skipped: {e}")

router = APIRouter()


@router.get("/latest", response_model=FuelPriceResponse)
async def get_latest_prices(db: Session = Depends(get_db)):
    """
    Get latest fuel prices
    Returns the most recent price update
    """
    _increment_visitor_count()

    latest = db.query(FuelPrice).order_by(desc(FuelPrice.effective_date)).first()

    if not latest:
        raise HTTPException(status_code=404, detail="No price data available")

    retrieved = latest.updated_at or latest.created_at or datetime.utcnow()
    return {
        "data": latest,
        "timestamp": retrieved,
        "source_url": FUEL_CSV_URL,
        "source_catalogue_url": DATA_GOV_MY_FUEL_CATALOGUE,
    }


@router.get("/history")
async def get_price_history(
    days: int = Query(30, ge=1, le=365),
    fuel_type: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get historical fuel prices
    
    Parameters:
    - days: Number of days to retrieve (1-365)
    - fuel_type: Filter by fuel type (RON95, RON97, Diesel)
    - region: Filter by region (Peninsular, East Malaysia)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(PriceHistory).filter(PriceHistory.date >= cutoff_date)
    
    if fuel_type:
        query = query.filter(PriceHistory.fuel_type == fuel_type)
    
    if region:
        query = query.filter(PriceHistory.region == region)
    
    history = query.order_by(desc(PriceHistory.date)).all()
    
    # Convert to TrendData schema
    trend_data = [
        TrendData(
            date=h.date.date(),
            fuel_type=h.fuel_type,
            local_price=h.price,
            global_reference=h.mops_reference,
            subsidy_gap=h.subsidy_gap,
            region=h.region
        )
        for h in history
    ]
    
    return {
        "data": trend_data,
        "count": len(trend_data),
        "period_days": days
    }


def _pump_response_from_payload(payload: dict) -> PumpStationPriceResponse:
    stamp_raw = payload.get("retrieved_at")
    try:
        ts = datetime.fromisoformat(str(stamp_raw).replace("Z", "+00:00"))
    except Exception:
        ts = datetime.now(timezone.utc)

    rows: list[PumpStationPriceRow] = []
    for r in payload.get("rows", []):
        if not isinstance(r, dict):
            continue
        st = str(r.get("station") or "Unknown")
        rows.append(
            PumpStationPriceRow(
                station=st,
                location=r.get("location"),
                ron95_budi=r.get("ron95_budi"),
                ron95=r.get("ron95"),
                ron97=r.get("ron97"),
                vpower=r.get("vpower"),
                ron100=r.get("ron100"),
                diesel=r.get("diesel"),
                diesel_b7=r.get("diesel_b7"),
                updated_at=stamp_raw if isinstance(stamp_raw, str) else None,
            )
        )

    return PumpStationPriceResponse(
        data=rows,
        count=len(rows),
        timestamp=ts,
    )


@router.get("/pump-stations", response_model=PumpStationPriceResponse)
async def get_pump_station_prices():
    """
    Pump grades from ``MY_PUMP_PRICES`` (Shell / Motorist + Firecrawl) and
    optional ``MY_PUMP_PRICES2`` (Petron RON 100). Live fetches are cached;
    reloads use disk cache on non-schedule days (see ``needs_live_scrape`` —
    e.g. Thursday Malaysia, at most once that day) so external sites are not
    hit on every page refresh.
    """
    blob, cached_at = read_cache()
    now = datetime.now(timezone.utc)

    if blob is not None and cached_at is not None and not needs_live_scrape(cached_at, now=now):
        return response_from_blob(blob)

    try:
        payload = fetch_my_pump_prices_from_env()
    except ValueError as e:
        if blob is not None:
            logger.info("Pump scrape skipped (env); serving disk cache: %s", e)
            return response_from_blob(blob)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.warning("Pump station scrape failed: %s", e)
        if blob is not None:
            logger.info("Serving stale pump cache after scrape failure")
            return response_from_blob(blob)
        raise HTTPException(status_code=502, detail="Failed to scrape MY_PUMP_PRICES source") from e

    resp = _pump_response_from_payload(payload)
    write_cache(resp)
    return resp


_LOCAL_PRODUCT_NAMES: dict[tuple[str, str], str] = {
    ("MY", "RON95"): "RON 95 (BUDI95 subsidised)",
    ("MY", "RON97"): "RON 97",
    ("MY", "Diesel"): "Diesel Euro 5",
    ("SG", "RON95"): "92 octane (approx. RON 92)",
    ("SG", "RON97"): "95/98 octane (approx. RON 95-98)",
    ("SG", "Diesel"): "Euro V Diesel",
    ("TH", "RON95"): "Gasohol 95 / E20",
    ("TH", "RON97"): "Gasohol 97 / Super",
    ("TH", "Diesel"): "Diesel B7",
    ("ID", "RON95"): "Pertalite (RON 90)",
    ("ID", "RON97"): "Pertamax (RON 92)",
    ("ID", "Diesel"): "Dexlite / Solar",
    ("BN", "RON95"): "Premium (RON 95-ish, controlled)",
    ("BN", "RON97"): "Super (RON 97-ish, controlled)",
    ("BN", "Diesel"): "Diesel (controlled)",
    ("PH", "RON95"): "Gasoline 91 (RON 91)",
    ("PH", "RON97"): "Gasoline 95/97 (RON 95-97)",
    ("PH", "Diesel"): "Diesel",
}


def _asean_local_product_name(country: str, fuel_type: str) -> str:
    return _LOCAL_PRODUCT_NAMES.get((country, fuel_type), fuel_type)


@router.get("/compare", response_model=AseanCompareResponse)
async def asean_fuel_compare(db: Session = Depends(get_db)):
    """
    ASEAN cross-country retail fuel comparison (USD per litre).
    Latest row per country + fuel_type from `asean_fuel_prices`.
    """
    rows = db.query(AseanFuelPrice).order_by(desc(AseanFuelPrice.date), desc(AseanFuelPrice.updated_at)).all()
    seen: set[tuple[str, str]] = set()
    latest: list[AseanFuelPrice] = []
    for r in rows:
        key = (r.country, r.fuel_type)
        if key in seen:
            continue
        seen.add(key)
        latest.append(r)

    data = [
        AseanCompareRow(
            country=r.country,
            country_name=r.country_name,
            fuel_type=r.fuel_type,
            local_name=_asean_local_product_name(r.country, r.fuel_type),
            local_price=float(r.local_price),
            currency=r.currency,
            usd_price=float(r.usd_price),
            is_subsidised=bool(r.is_subsidised),
            date=r.date.date() if isinstance(r.date, datetime) else r.date,
            source=r.source or "unknown",
            source_url=r.source_url,
        )
        for r in latest
    ]

    try:
        bundle = fetch_exchange_rates_bundle()
        exchange_rates = {k: float(v) for k, v in bundle.rates.items()}
        exchange_rates_info = ExchangeRatesInfo(
            provider=bundle.provider,
            used_static_fallback=bundle.used_static_fallback,
            message=bundle.message,
        )
    except Exception as e:
        logger.debug("FX for compare response: %s", e)
        exchange_rates = {}
        exchange_rates_info = ExchangeRatesInfo(
            provider="none",
            used_static_fallback=False,
            message=f"No FX rates returned: {e}",
        )

    updated_at = db.query(func.max(AseanFuelPrice.updated_at)).scalar()
    if updated_at is None:
        updated_at = datetime.utcnow()

    return AseanCompareResponse(
        data=data,
        exchange_rates=exchange_rates,
        updated_at=updated_at,
        exchange_rates_info=exchange_rates_info,
    )


def _fuel_price_to_myr(
    fp: FuelPrice, fuel_type: str
) -> tuple[Optional[Decimal], bool]:
    """Return (price MYR/litre, is_subsidised) for Peninsular snapshot."""
    if fuel_type == "RON95":
        if fp.ron95_subsidized is not None:
            sub = bool(
                fp.ron95_market is not None
                and fp.ron95_subsidized is not None
                and fp.ron95_subsidized < fp.ron95_market
            )
            return Decimal(str(fp.ron95_subsidized)), sub
        if fp.ron95_market is not None:
            return Decimal(str(fp.ron95_market)), False
        return None, False
    if fuel_type == "RON97" and fp.ron97 is not None:
        return Decimal(str(fp.ron97)), False
    if fuel_type == "Diesel" and fp.diesel_peninsular is not None:
        return Decimal(str(fp.diesel_peninsular)), False
    return None, False


@router.get("/asean/history", response_model=AseanHistoryResponse)
async def asean_fuel_history(
    days: int = Query(365, ge=1, le=730),
    fuel_type: Optional[str] = Query(
        None,
        description="Filter to RON95, RON97, or Diesel; omit for all grades",
    ),
    include_malaysia_official_weeks: bool = Query(
        True,
        description="Replace MY rows with weekly Peninsular prices from data.gov.my (accurate effective dates)",
    ),
    db: Session = Depends(get_db),
):
    """
    Historical ASEAN snapshots from `asean_fuel_prices` (one row per country, date, fuel).

    Malaysia: when `include_malaysia_official_weeks` is true, rows come from `fuel_prices`
    (data.gov.my weekly effective dates) instead of ASEAN sync rows, so dates match the
    official pump schedule. USD/litre for those MY rows uses **current** FX at request time
    (`usd_uses_latest_fx=true`); other countries use USD stored at sync time.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    q = db.query(AseanFuelPrice).filter(AseanFuelPrice.date >= cutoff)
    if fuel_type:
        if fuel_type not in ("RON95", "RON97", "Diesel"):
            raise HTTPException(
                status_code=400,
                detail="fuel_type must be RON95, RON97, Diesel, or omitted",
            )
        q = q.filter(AseanFuelPrice.fuel_type == fuel_type)

    orm_rows = q.order_by(AseanFuelPrice.date.asc(), AseanFuelPrice.country.asc()).all()

    if include_malaysia_official_weeks:
        orm_rows = [r for r in orm_rows if r.country != "MY"]

    out: list[AseanHistoryRow] = [
        AseanHistoryRow(
            country=r.country,
            country_name=r.country_name,
            fuel_type=r.fuel_type,
            local_name=_asean_local_product_name(r.country, r.fuel_type),
            local_price=float(r.local_price),
            currency=r.currency,
            usd_price=float(r.usd_price),
            is_subsidised=bool(r.is_subsidised),
            date=r.date.date() if isinstance(r.date, datetime) else r.date,
            source=r.source or "unknown",
            source_url=r.source_url,
            usd_uses_latest_fx=False,
        )
        for r in orm_rows
    ]

    malaysia_usd_uses_latest_fx = False
    if include_malaysia_official_weeks:
        try:
            rates = fetch_exchange_rates()
        except Exception as e:
            logger.debug("FX for MY history rows: %s", e)
            rates = {}
        if rates:
            fp_q = (
                db.query(FuelPrice)
                .filter(
                    FuelPrice.region == "Peninsular",
                    FuelPrice.source == "data.gov.my",
                    FuelPrice.effective_date >= cutoff,
                )
                .order_by(FuelPrice.effective_date.asc())
            )
            ft_list = [fuel_type] if fuel_type else ["RON95", "RON97", "Diesel"]
            for fp in fp_q:
                eff = fp.effective_date
                d = eff.date() if isinstance(eff, datetime) else eff
                for ft in ft_list:
                    myr, sub = _fuel_price_to_myr(fp, ft)
                    if myr is None:
                        continue
                    try:
                        usd = float(_to_usd_per_litre(myr, "MYR", rates))
                    except Exception:
                        continue
                    malaysia_usd_uses_latest_fx = True
                    out.append(
                        AseanHistoryRow(
                            country="MY",
                            country_name="Malaysia",
                            fuel_type=ft,
                            local_name=_asean_local_product_name("MY", ft),
                            local_price=float(myr),
                            currency="MYR",
                            usd_price=usd,
                            is_subsidised=sub,
                            date=d,
                            source="data.gov.my (weekly official)",
                            source_url=FUEL_CSV_URL,
                            usd_uses_latest_fx=True,
                        )
                    )

    out.sort(key=lambda r: (r.date.isoformat(), r.country, r.fuel_type))

    note_parts = [
        "Each point is one row in our database for that calendar date (or Malaysia weekly effective date). "
        "Other ASEAN countries only gain new dates when the sync runs and the source supplies that date."
    ]
    if malaysia_usd_uses_latest_fx:
        note_parts.append(
            "Malaysia USD/litre in history uses MYR pump prices from data.gov.my with **today's** USD/MYR rate "
            "(not the rate on the historical week); use local MYR for strict period accuracy."
        )

    return AseanHistoryResponse(
        data=out,
        days=days,
        malaysia_usd_uses_latest_fx=malaysia_usd_uses_latest_fx,
        note=" ".join(note_parts),
    )


@router.get("/malaysia-vs-global")
async def compare_with_global(db: Session = Depends(get_db)):
    """
    Compare Malaysia fuel prices with global benchmarks
    Returns local prices vs MOPS Singapore, WTI, and Brent
    """
    # Get latest prices
    latest_price = db.query(FuelPrice).order_by(desc(FuelPrice.effective_date)).first()
    
    # Get latest benchmark
    latest_benchmark = db.query(GlobalBenchmark).order_by(desc(GlobalBenchmark.date)).first()
    
    if not latest_price:
        raise HTTPException(status_code=404, detail="No price data available")
    
    benchmark_data = {}
    if latest_benchmark:
        benchmark_data = {
            "mops_singapore": float(latest_benchmark.mops_singapore) if latest_benchmark.mops_singapore else None,
            "wti_crude": float(latest_benchmark.wti_crude) if latest_benchmark.wti_crude else None,
            "brent_crude": float(latest_benchmark.brent_crude) if latest_benchmark.brent_crude else None
        }
    
    # Calculate subsidy metrics
    subsidy_metrics = {
        "ron95_subsidized": float(latest_price.ron95_subsidized) if latest_price.ron95_subsidized else None,
        "ron95_market": float(latest_price.ron95_market) if latest_price.ron95_market else None,
        "subsidy_gap": float(latest_price.ron95_market) - float(latest_price.ron95_subsidized) 
                      if latest_price.ron95_market and latest_price.ron95_subsidized else None
    }
    
    return {
        "date": latest_price.effective_date.date(),
        "malaysia": {
            "ron95": float(latest_price.ron95_subsidized) if latest_price.ron95_subsidized else None,
            "ron97": float(latest_price.ron97),
            "diesel": float(latest_price.diesel_peninsular)
        },
        "global_benchmark": benchmark_data,
        "subsidy_metrics": subsidy_metrics
    }


@router.get("/volatility")
async def price_volatility(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """
    Analyze price volatility over specified period
    Returns weekly changes and volatility metrics
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    history = db.query(PriceHistory).filter(
        PriceHistory.date >= cutoff_date
    ).order_by(desc(PriceHistory.date)).all()
    
    # Group by fuel type
    fuel_types = set(h.fuel_type for h in history)
    
    volatility_data = {}
    for fuel in fuel_types:
        fuel_history = [h for h in history if h.fuel_type == fuel]
        
        if len(fuel_history) < 2:
            continue
        
        # Calculate weekly changes
        prices = [float(h.price) for h in fuel_history]
        changes = [prices[i] - prices[i+1] for i in range(len(prices)-1)]
        
        # Calculate volatility
        if len(changes) > 0:
            avg_change = sum(changes) / len(changes)
            volatility = (sum((c - avg_change) ** 2 for c in changes) / len(changes)) ** 0.5
            volatility_pct = (volatility / prices[0] * 100) if prices[0] != 0 else 0
            
            trend = "Upward" if avg_change > 0 else "Downward" if avg_change < 0 else "Stable"
        else:
            volatility_pct = 0
            trend = "Stable"
        
        volatility_data[fuel] = {
            "weekly_changes": changes[:4],  # Last 4 weeks
            "volatility_pct": round(volatility_pct, 2),
            "trend_direction": trend
        }
    
    return {"data": volatility_data}
