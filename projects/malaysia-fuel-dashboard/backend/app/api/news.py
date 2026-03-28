"""
Government News & Announcements API Endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import Optional, List

from app.database import get_db
from app.models import GovernmentAnnouncement, PolicyTag, PriceAlert
from app.schemas import Announcement, AnnouncementResponse, PriceAlertResponse, PriceAlert as PriceAlertSchema

router = APIRouter()


@router.get("/latest", response_model=AnnouncementResponse)
async def get_latest_news(
    limit: int = Query(10, ge=1, le=50),
    source: Optional[str] = None,
    announcement_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get latest government announcements
    
    Parameters:
    - limit: Number of results (1-50)
    - source: Filter by source (MOF, KPDN, PMO, Bernama)
    - announcement_type: Filter by type (Price Update, Policy Change, BUDI Rollout)
    """
    query = db.query(GovernmentAnnouncement).order_by(desc(GovernmentAnnouncement.announcement_date))
    
    if source:
        query = query.filter(GovernmentAnnouncement.source == source)
    
    if announcement_type:
        query = query.filter(GovernmentAnnouncement.announcement_type == announcement_type)
    
    announcements = query.limit(limit).all()
    
    return {
        "data": announcements,
        "count": len(announcements),
        "timestamp": datetime.utcnow()
    }


@router.get("/alerts", response_model=PriceAlertResponse)
async def get_price_alerts(
    days: int = Query(7, ge=1, le=365),
    min_change: float = Query(0.05, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get price change alerts
    
    Parameters:
    - days: Look back period (days)
    - min_change: Minimum price change in RM (default: 0.05)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    alerts = db.query(PriceAlert).filter(
        and_(
            PriceAlert.triggered_at >= cutoff_date,
            # Convert Decimal to float for comparison
        )
    ).order_by(desc(PriceAlert.triggered_at)).all()
    
    # Filter by min_change
    filtered_alerts = [
        a for a in alerts 
        if abs(float(a.price_change)) >= min_change
    ]
    
    return {
        "data": filtered_alerts,
        "count": len(filtered_alerts)
    }


@router.get("/search")
async def search_announcements(
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    keyword: Optional[str] = Query(None, description="Full-text search"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Search announcements by keywords and tags
    
    Parameters:
    - tags: Comma-separated tags (#BUDI95, #Rationalization, #FuelFloating)
    - keyword: Search in title and content
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    """
    query = db.query(GovernmentAnnouncement)
    
    # Filter by tags
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        query = query.join(PolicyTag).filter(PolicyTag.tag.in_(tag_list))
    
    # Filter by keyword
    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(
            (GovernmentAnnouncement.title.ilike(search_term)) |
            (GovernmentAnnouncement.content.ilike(search_term))
        )
    
    # Filter by date range
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            query = query.filter(GovernmentAnnouncement.announcement_date >= from_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to)
            query = query.filter(GovernmentAnnouncement.announcement_date <= to_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")
    
    results = query.order_by(desc(GovernmentAnnouncement.announcement_date)).limit(50).all()
    
    return {
        "data": results,
        "count": len(results),
        "query": {
            "tags": tags.split(",") if tags else [],
            "keyword": keyword,
            "date_range": f"{date_from} to {date_to}" if date_from or date_to else None
        }
    }


@router.get("/by-source/{source}")
async def get_announcements_by_source(
    source: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get announcements from specific source
    
    Parameters:
    - source: MOF, KPDN, PMO, or Bernama
    - limit: Number of results
    """
    announcements = db.query(GovernmentAnnouncement).filter(
        GovernmentAnnouncement.source == source
    ).order_by(desc(GovernmentAnnouncement.announcement_date)).limit(limit).all()
    
    if not announcements:
        raise HTTPException(status_code=404, detail=f"No announcements found for source: {source}")
    
    return {
        "data": announcements,
        "count": len(announcements),
        "source": source
    }


@router.get("/tags")
async def get_all_tags(db: Session = Depends(get_db)):
    """
    Get all available policy tags
    Returns unique tags and their frequency
    """
    tags = db.query(PolicyTag.tag).distinct().all()
    
    tag_data = []
    for (tag,) in tags:
        count = db.query(PolicyTag).filter(PolicyTag.tag == tag).count()
        tag_data.append({
            "tag": tag,
            "frequency": count
        })
    
    return {
        "tags": sorted(tag_data, key=lambda x: x["frequency"], reverse=True),
        "total_unique_tags": len(tag_data)
    }
