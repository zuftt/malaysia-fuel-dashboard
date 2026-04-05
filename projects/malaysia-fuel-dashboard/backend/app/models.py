"""
SQLAlchemy Models for Malaysia Fuel & Policy Intelligence Dashboard
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, JSON, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Use JSON instead of ARRAY for SQLite compatibility.
# PostgreSQL ARRAY(String) is not supported by SQLite.


class FuelPrice(Base):
    __tablename__ = "fuel_prices"

    id = Column(Integer, primary_key=True, index=True)
    date_announced = Column(DateTime, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    ron95_subsidized = Column(DECIMAL(6, 2), nullable=True)
    ron95_market = Column(DECIMAL(6, 2), nullable=True)
    ron97 = Column(DECIMAL(6, 2), nullable=False)
    diesel_peninsular = Column(DECIMAL(6, 2), nullable=False)
    diesel_east_malaysia = Column(DECIMAL(6, 2), nullable=True)
    diesel_b10 = Column(DECIMAL(6, 2), nullable=True)
    diesel_b20 = Column(DECIMAL(6, 2), nullable=True)
    region = Column(String(50), nullable=False)
    source = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    price_alerts = relationship("PriceAlert", back_populates="fuel_price")
    price_history = relationship("PriceHistory", back_populates="price_snapshot")

    __table_args__ = (
        UniqueConstraint('effective_date', 'region', 'source', name='uq_effective_region_source'),
        Index('idx_fuel_prices_date', 'effective_date'),
        Index('idx_fuel_prices_region', 'region'),
    )


class GovernmentAnnouncement(Base):
    __tablename__ = "government_announcements"

    id = Column(Integer, primary_key=True, index=True)
    announcement_date = Column(DateTime, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(String, nullable=True)
    source = Column(String(100), nullable=False)
    source_url = Column(String(500), nullable=True)
    announcement_type = Column(String(50), nullable=False)
    extracted_prices = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    sentiment = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    policy_tags = relationship("PolicyTag", back_populates="announcement")
    alerts = relationship("PriceAlert", back_populates="announcement")

    __table_args__ = (
        UniqueConstraint('source', 'source_url', name='uq_source_url'),
        Index('idx_announcements_date', 'announcement_date'),
        Index('idx_announcements_source', 'source'),
    )


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    fuel_type = Column(String(50), nullable=False)
    price_change = Column(DECIMAL(6, 2), nullable=False)
    percentage_change = Column(DECIMAL(5, 2), nullable=False)
    alert_type = Column(String(50), nullable=False)
    triggered_at = Column(DateTime, nullable=False)
    is_notified = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Foreign Keys
    fuel_price_id = Column(Integer, ForeignKey('fuel_prices.id'), nullable=True)
    announcement_id = Column(Integer, ForeignKey('government_announcements.id'), nullable=True)

    # Relationships
    fuel_price = relationship("FuelPrice", back_populates="price_alerts")
    announcement = relationship("GovernmentAnnouncement", back_populates="alerts")

    __table_args__ = (
        Index('idx_price_alerts_triggered', 'triggered_at'),
    )


class PolicyTag(Base):
    __tablename__ = "policy_tags"

    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(Integer, ForeignKey('government_announcements.id'), nullable=False)
    tag = Column(String(100), nullable=False)
    confidence = Column(DECIMAL(3, 2), nullable=False, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    announcement = relationship("GovernmentAnnouncement", back_populates="policy_tags")

    __table_args__ = (
        Index('idx_policy_tags_tag', 'tag'),
    )


class GlobalBenchmark(Base):
    __tablename__ = "global_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    mops_singapore = Column(DECIMAL(6, 2), nullable=True)
    wti_crude = Column(DECIMAL(8, 2), nullable=True)
    brent_crude = Column(DECIMAL(8, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('date', name='uq_benchmark_date'),
        Index('idx_benchmarks_date', 'date'),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    fuel_type = Column(String(50), nullable=False)
    price = Column(DECIMAL(6, 2), nullable=False)
    region = Column(String(50), nullable=False)
    subsidy_status = Column(String(50), nullable=True)
    mops_reference = Column(DECIMAL(6, 2), nullable=True)
    subsidy_gap = Column(DECIMAL(6, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Foreign Keys (optional reference to snapshot)
    fuel_price_id = Column(Integer, ForeignKey('fuel_prices.id'), nullable=True)

    # Relationships
    price_snapshot = relationship("FuelPrice", back_populates="price_history")

    __table_args__ = (
        UniqueConstraint('date', 'fuel_type', 'region', 'subsidy_status', name='uq_price_history'),
        Index('idx_price_history_date', 'date'),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScraperStatus(Base):
    __tablename__ = "scraper_status"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    items_scraped = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_scraper_status_source', 'source'),
    )


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, index=True)
    fuel_type = Column(String(50), nullable=False)
    alert_threshold_pct = Column(DECIMAL(5, 2), nullable=False)
    notify_channels = Column(JSON, default=['dashboard'])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('fuel_type', name='uq_fuel_type'),
    )
