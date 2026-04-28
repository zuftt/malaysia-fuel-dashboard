"""
Admin API Endpoints (Protected)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.database import get_db
from app.models import FuelPrice, GovernmentAnnouncement, AlertConfig, ScraperStatus, User
from app.schemas import (
    PriceValidateRequest, ValidationResponse,
    AlertConfigCreate, AlertConfig as AlertConfigSchema,
    ScraperStatusResponse, AnnouncementCreate,
)
from app.api.auth import require_admin
from app.data_fetcher import sync_fuel_prices

router = APIRouter()


@router.post("/prices/validate", response_model=ValidationResponse)
async def validate_price(
    request: PriceValidateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Manually validate and correct fuel prices
    For fixing OCR errors or missed updates
    """
    price = db.query(FuelPrice).filter(FuelPrice.id == request.price_id).first()
    
    if not price:
        raise HTTPException(status_code=404, detail=f"Price ID {request.price_id} not found")
    
    # Update fields
    if request.ron95_subsidized is not None:
        price.ron95_subsidized = request.ron95_subsidized
    if request.ron97 is not None:
        price.ron97 = request.ron97
    if request.diesel_peninsular is not None:
        price.diesel_peninsular = request.diesel_peninsular
    
    price.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(price)
    
    return {
        "success": True,
        "price_id": price.id,
        "updated_at": price.updated_at,
        "message": f"Price {price.id} validated and updated"
    }


@router.post("/announcements/manual")
async def add_manual_announcement(
    announcement: AnnouncementCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Manually add announcement (for missed scrapes)
    """
    try:
        new_announcement = GovernmentAnnouncement(
            announcement_date=announcement.announcement_date,
            title=announcement.title,
            content=announcement.content,
            source=announcement.source,
            source_url=announcement.source_url,
            announcement_type=announcement.announcement_type,
            extracted_prices=announcement.extracted_prices,
            keywords=announcement.keywords,
        )

        db.add(new_announcement)
        db.commit()
        db.refresh(new_announcement)

        return {
            "success": True,
            "announcement_id": new_announcement.id,
            "created_at": new_announcement.created_at
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create announcement")


@router.get("/scraper-status")
async def get_scraper_status(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Check status of automated scraping tasks
    """
    statuses = db.query(ScraperStatus).order_by(desc(ScraperStatus.updated_at)).all()
    
    status_data = []
    for status in statuses:
        status_data.append({
            "source": status.source,
            "last_run": status.last_run,
            "next_run": status.next_run,
            "status": status.status,
            "items_scraped": status.items_scraped,
            "error": status.error_message
        })
    
    return {
        "statuses": status_data,
        "total_sources": len(status_data)
    }


@router.post("/alerts/config", response_model=AlertConfigSchema)
async def create_alert_config(
    config: AlertConfigCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Configure alert thresholds for fuel types
    """
    # Check if config exists
    existing = db.query(AlertConfig).filter(
        AlertConfig.fuel_type == config.fuel_type
    ).first()
    
    if existing:
        # Update existing
        existing.alert_threshold_pct = config.alert_threshold_pct
        existing.notify_channels = config.notify_channels
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        new_config = AlertConfig(
            fuel_type=config.fuel_type,
            alert_threshold_pct=config.alert_threshold_pct,
            notify_channels=config.notify_channels
        )
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        return new_config


@router.get("/alerts/config/{fuel_type}")
async def get_alert_config(
    fuel_type: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Get alert configuration for specific fuel type
    """
    config = db.query(AlertConfig).filter(
        AlertConfig.fuel_type == fuel_type
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"No alert configuration found for {fuel_type}"
        )
    
    return {
        "fuel_type": config.fuel_type,
        "alert_threshold_pct": float(config.alert_threshold_pct),
        "notify_channels": config.notify_channels,
        "is_active": config.is_active
    }


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Get dashboard statistics for admin overview
    """
    total_prices = db.query(FuelPrice).count()
    total_announcements = db.query(GovernmentAnnouncement).count()
    
    # Latest price
    latest_price = db.query(FuelPrice).order_by(desc(FuelPrice.effective_date)).first()
    
    # Price update sources
    sources = db.query(FuelPrice.source).distinct().count()
    
    return {
        "total_prices": total_prices,
        "total_announcements": total_announcements,
        "data_sources": sources,
        "latest_price_date": latest_price.effective_date if latest_price else None,
        "system_status": "Healthy"
    }


@router.post("/sync/global-benchmarks")
async def sync_global_benchmarks(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Trigger sync of global benchmarks (MOPS Singapore, WTI, Brent)
    Note: Currently a placeholder - integrate with a real data provider for production.
    """
    return {
        "success": False,
        "message": "Global benchmark sync not yet configured. Set up a data provider (e.g. commodity API) to enable this feature.",
    }


@router.post("/sync/fuel-prices")
async def sync_fuel_prices_endpoint(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Trigger sync of fuel prices from data.gov.my
    """
    try:
        result = sync_fuel_prices(db)
        return {
            "success": True,
            "message": f"Synced {result['created']} new records from data.gov.my",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/cleanup/old-data")
async def cleanup_old_data(
    days: int = 730,  # 2 years
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Archive or delete data older than specified days
    """
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Note: In production, archive to separate schema instead of deleting
    old_prices = db.query(FuelPrice).filter(
        FuelPrice.created_at < cutoff_date
    ).count()
    
    old_announcements = db.query(GovernmentAnnouncement).filter(
        GovernmentAnnouncement.created_at < cutoff_date
    ).count()
    
    return {
        "success": True,
        "old_prices_found": old_prices,
        "old_announcements_found": old_announcements,
        "recommendation": "Archive to historical schema before deletion"
    }
