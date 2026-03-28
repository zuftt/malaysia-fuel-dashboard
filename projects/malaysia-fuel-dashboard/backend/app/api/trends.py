"""
Trend Analysis API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from decimal import Decimal

from app.database import get_db
from app.models import PriceHistory, GlobalBenchmark
from app.schemas import TrendResponse, TrendData

router = APIRouter()


@router.get("/subsidy-gap")
async def analyze_subsidy_gap(
    days: int = Query(90, ge=7, le=365),
    fuel_type: Optional[str] = "RON95",
    db: Session = Depends(get_db)
):
    """
    Analyze historical subsidy gap (Local vs Global price)
    
    Parameters:
    - days: Period to analyze (7-365)
    - fuel_type: RON95, RON97, or Diesel
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    history = db.query(PriceHistory).filter(
        (PriceHistory.date >= cutoff_date) &
        (PriceHistory.fuel_type == fuel_type)
    ).order_by(desc(PriceHistory.date)).all()
    
    if not history:
        return {
            "data": [],
            "statistics": {
                "avg_gap": 0,
                "max_gap": 0,
                "min_gap": 0,
                "trend": "No data"
            }
        }
    
    # Calculate statistics
    gaps = [float(h.subsidy_gap) for h in history if h.subsidy_gap]
    
    stats = {
        "avg_gap": round(sum(gaps) / len(gaps), 2) if gaps else 0,
        "max_gap": round(max(gaps), 2) if gaps else 0,
        "min_gap": round(min(gaps), 2) if gaps else 0,
        "trend": "Increasing" if gaps[0] > gaps[-1] else "Decreasing" if gaps[0] < gaps[-1] else "Stable"
    }
    
    # Format response data
    trend_data = [
        {
            "date": h.date.date(),
            "subsidy_gap": float(h.subsidy_gap) if h.subsidy_gap else None,
            "fuel_type": h.fuel_type,
            "local_price": float(h.price),
            "global_price": float(h.mops_reference) if h.mops_reference else None,
            "government_cost_myr": float(h.subsidy_gap) * 1000000 if h.subsidy_gap else None  # Estimate
        }
        for h in history
    ]
    
    return {
        "data": trend_data,
        "statistics": stats
    }


@router.get("/volatility")
async def analyze_volatility(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """
    Analyze price volatility by fuel type
    Returns weekly changes and trend direction
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    history = db.query(PriceHistory).filter(
        PriceHistory.date >= cutoff_date
    ).order_by(desc(PriceHistory.date)).all()
    
    # Group by fuel type
    fuel_types = set(h.fuel_type for h in history)
    
    volatility_data: Dict = {}
    
    for fuel in fuel_types:
        fuel_history = [h for h in history if h.fuel_type == fuel]
        
        if len(fuel_history) < 2:
            continue
        
        # Get prices sorted by date (ascending for calculation)
        sorted_history = sorted(fuel_history, key=lambda x: x.date)
        prices = [float(h.price) for h in sorted_history]
        
        # Calculate weekly changes
        weekly_changes = []
        for i in range(0, len(prices)-1, 1):
            change = prices[i+1] - prices[i]
            weekly_changes.append(round(change, 4))
        
        # Calculate volatility (standard deviation)
        if len(weekly_changes) > 1:
            avg_change = sum(weekly_changes) / len(weekly_changes)
            variance = sum((x - avg_change) ** 2 for x in weekly_changes) / len(weekly_changes)
            std_dev = variance ** 0.5
            volatility_pct = (std_dev / prices[0] * 100) if prices[0] != 0 else 0
        else:
            volatility_pct = 0
        
        # Determine trend
        if len(prices) > 1:
            trend_direction = "Upward" if prices[-1] > prices[0] else "Downward" if prices[-1] < prices[0] else "Stable"
        else:
            trend_direction = "Stable"
        
        volatility_data[fuel] = {
            "weekly_changes": weekly_changes[-4:],  # Last 4 weeks
            "volatility_pct": round(volatility_pct, 2),
            "trend_direction": trend_direction
        }
    
    return {"data": volatility_data}


@router.get("/forecast")
async def price_forecast(
    fuel_type: str = Query("RON95"),
    days_ahead: int = Query(14, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Simple price forecast based on recent trends
    Note: This is a basic linear extrapolation. ML models recommended for production.
    
    Parameters:
    - fuel_type: RON95, RON97, Diesel
    - days_ahead: Days to forecast (1-30)
    """
    # Get last 30 days of data
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    history = db.query(PriceHistory).filter(
        (PriceHistory.date >= cutoff_date) &
        (PriceHistory.fuel_type == fuel_type)
    ).order_by(PriceHistory.date).all()
    
    if len(history) < 2:
        return {
            "data": [],
            "forecast_confidence": "Low - Insufficient data",
            "method": "Linear trend extrapolation"
        }
    
    # Linear regression on prices
    prices = [float(h.price) for h in history]
    days = list(range(len(prices)))
    
    # Calculate slope
    n = len(prices)
    sum_xy = sum(d * p for d, p in zip(days, prices))
    sum_x = sum(days)
    sum_y = sum(prices)
    sum_x2 = sum(d**2 for d in days)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2) if n > 1 else 0
    intercept = (sum_y - slope * sum_x) / n
    
    # Generate forecast
    last_date = history[-1].date
    forecast = []
    
    for i in range(1, days_ahead + 1):
        forecast_date = last_date + timedelta(days=i)
        forecast_value = intercept + slope * (len(prices) + i - 1)
        
        forecast.append({
            "date": forecast_date.date(),
            "fuel_type": fuel_type,
            "forecast_price": round(max(0, forecast_value), 2),  # Prevent negative prices
            "confidence": "Low" if days_ahead > 7 else "Medium"
        })
    
    return {
        "data": forecast,
        "forecast_confidence": "Medium" if len(history) >= 10 else "Low",
        "method": "Linear trend extrapolation",
        "trend": "Upward" if slope > 0 else "Downward" if slope < 0 else "Stable",
        "slope": round(slope, 4)
    }


@router.get("/comparison")
async def regional_comparison(
    fuel_type: str = Query("RON95"),
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """
    Compare prices across regions (Peninsular vs East Malaysia)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    peninsular = db.query(PriceHistory).filter(
        (PriceHistory.date >= cutoff_date) &
        (PriceHistory.fuel_type == fuel_type) &
        (PriceHistory.region == "Peninsular")
    ).order_by(desc(PriceHistory.date)).all()
    
    east_malaysia = db.query(PriceHistory).filter(
        (PriceHistory.date >= cutoff_date) &
        (PriceHistory.fuel_type == fuel_type) &
        (PriceHistory.region == "East Malaysia")
    ).order_by(desc(PriceHistory.date)).all()
    
    return {
        "fuel_type": fuel_type,
        "period_days": days,
        "peninsular": {
            "count": len(peninsular),
            "avg_price": round(sum(float(p.price) for p in peninsular) / len(peninsular), 2) if peninsular else 0,
            "latest": float(peninsular[0].price) if peninsular else None
        },
        "east_malaysia": {
            "count": len(east_malaysia),
            "avg_price": round(sum(float(p.price) for p in east_malaysia) / len(east_malaysia), 2) if east_malaysia else 0,
            "latest": float(east_malaysia[0].price) if east_malaysia else None
        }
    }
