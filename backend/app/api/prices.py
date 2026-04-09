"""
Fuel Prices API Endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Optional
import os
import logging

from app.database import get_db
from app.models import FuelPrice, PriceHistory, GlobalBenchmark
from app.schemas import FuelPrice as FuelPriceSchema, FuelPriceResponse, TrendResponse, TrendData

logger = logging.getLogger(__name__)

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

    return {
        "data": latest,
        "timestamp": datetime.utcnow()
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


@router.get("/compare")
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
