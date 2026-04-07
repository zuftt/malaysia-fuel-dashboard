# Database Schema

## SQL Schema Design

```sql
-- Core Tables

CREATE TABLE fuel_prices (
    id SERIAL PRIMARY KEY,
    date_announced TIMESTAMP NOT NULL,
    effective_date DATE NOT NULL,
    ron95_subsidized DECIMAL(6,2),
    ron95_market DECIMAL(6,2),
    ron97 DECIMAL(6,2),
    diesel_peninsular DECIMAL(6,2),
    diesel_east_malaysia DECIMAL(6,2),
    diesel_b10 DECIMAL(6,2),
    diesel_b20 DECIMAL(6,2),
    region VARCHAR(50),  -- 'Peninsular' or 'East Malaysia'
    source VARCHAR(100),  -- 'MOF', 'KPDN', 'PMO'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(effective_date, region, source)
);

CREATE TABLE government_announcements (
    id SERIAL PRIMARY KEY,
    announcement_date TIMESTAMP NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source VARCHAR(100),  -- 'MOF', 'KPDN', 'PMO', 'Bernama'
    source_url VARCHAR(500),
    announcement_type VARCHAR(50),  -- 'Price Update', 'Policy Change', 'BUDI Rollout'
    extracted_prices JSONB,  -- Store parsed prices as JSON
    keywords TEXT[],  -- Array of tags: BUDI95, FuelFloating, Rationalization
    sentiment VARCHAR(20),  -- 'Positive', 'Negative', 'Neutral'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source, source_url)
);

CREATE TABLE price_alerts (
    id SERIAL PRIMARY KEY,
    fuel_type VARCHAR(50),  -- 'RON95', 'RON97', 'Diesel'
    price_change DECIMAL(6,2),
    percentage_change DECIMAL(5,2),
    alert_type VARCHAR(50),  -- 'Increase', 'Decrease', 'Subsidy_Change'
    triggered_at TIMESTAMP NOT NULL,
    is_notified BOOLEAN DEFAULT FALSE,
    notified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE policy_tags (
    id SERIAL PRIMARY KEY,
    announcement_id INTEGER REFERENCES government_announcements(id),
    tag VARCHAR(100),  -- '#BUDI95', '#Rationalization', '#FuelFloating', '#DieselSubsidy'
    confidence DECIMAL(3,2),  -- 0-1 confidence score
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE global_benchmarks (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    mops_singapore DECIMAL(6,2),  -- Mean of Platts Singapore
    wti_crude DECIMAL(8,2),  -- West Texas Intermediate
    brent_crude DECIMAL(8,2),  -- Brent Crude
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date)
);

CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    fuel_type VARCHAR(50),  -- 'RON95', 'RON97', 'Diesel'
    price DECIMAL(6,2),
    region VARCHAR(50),  -- 'Peninsular', 'East Malaysia'
    subsidy_status VARCHAR(50),  -- 'Subsidized', 'Market'
    mops_reference DECIMAL(6,2),  -- Reference global price
    subsidy_gap DECIMAL(6,2),  -- Local - Global
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, fuel_type, region, subsidy_status)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50),  -- 'Admin', 'Viewer'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for Performance

CREATE INDEX idx_fuel_prices_date ON fuel_prices(effective_date DESC);
CREATE INDEX idx_fuel_prices_region ON fuel_prices(region);
CREATE INDEX idx_announcements_date ON government_announcements(announcement_date DESC);
CREATE INDEX idx_announcements_source ON government_announcements(source);
CREATE INDEX idx_policy_tags_tag ON policy_tags(tag);
CREATE INDEX idx_price_alerts_triggered ON price_alerts(triggered_at DESC);
CREATE INDEX idx_price_history_date ON price_history(date DESC);
CREATE INDEX idx_benchmarks_date ON global_benchmarks(date DESC);
```

## Pydantic Models (Python)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

# Fuel Price Schema
class FuelPriceBase(BaseModel):
    date_announced: datetime
    effective_date: datetime.date
    ron95_subsidized: Optional[Decimal] = None
    ron95_market: Optional[Decimal] = None
    ron97: Decimal
    diesel_peninsular: Decimal
    diesel_east_malaysia: Optional[Decimal] = None
    diesel_b10: Optional[Decimal] = None
    diesel_b20: Optional[Decimal] = None
    region: str  # 'Peninsular' or 'East Malaysia'
    source: str  # 'MOF', 'KPDN', 'PMO'

class FuelPriceCreate(FuelPriceBase):
    pass

class FuelPrice(FuelPriceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Government Announcement Schema
class AnnouncementBase(BaseModel):
    announcement_date: datetime
    title: str
    content: Optional[str] = None
    source: str  # 'MOF', 'KPDN', 'PMO', 'Bernama'
    source_url: Optional[str] = None
    announcement_type: str  # 'Price Update', 'Policy Change', 'BUDI Rollout'
    keywords: List[str] = []

class AnnouncementCreate(AnnouncementBase):
    extracted_prices: Optional[dict] = None

class Announcement(AnnouncementBase):
    id: int
    extracted_prices: Optional[dict] = None
    sentiment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Price Alert Schema
class PriceAlertBase(BaseModel):
    fuel_type: str  # 'RON95', 'RON97', 'Diesel'
    price_change: Decimal
    percentage_change: Decimal
    alert_type: str  # 'Increase', 'Decrease', 'Subsidy_Change'

class PriceAlert(PriceAlertBase):
    id: int
    triggered_at: datetime
    is_notified: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Global Benchmark Schema
class BenchmarkBase(BaseModel):
    date: datetime
    mops_singapore: Optional[Decimal] = None
    wti_crude: Optional[Decimal] = None
    brent_crude: Optional[Decimal] = None

class Benchmark(BenchmarkBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Trend Analysis Schema
class TrendData(BaseModel):
    date: datetime.date
    fuel_type: str
    local_price: Decimal
    global_reference: Decimal
    subsidy_gap: Decimal
    region: str
```

## Database Relationships

```
fuel_prices (1) ←→ (Many) price_history
  └─ Tracks changes over time

government_announcements (1) ←→ (Many) policy_tags
  └─ Multiple keywords per announcement

government_announcements (1) ←→ (Many) price_alerts
  └─ Announcements trigger alerts

fuel_prices ←→ global_benchmarks
  └─ Compare local vs global prices
```

---

## Migration Strategy

Use Alembic for schema management:

```bash
# Initial migration
alembic init alembic

# Create migration after updating models.py
alembic revision --autogenerate -m "Add fuel_prices table"

# Apply migration
alembic upgrade head
```

---

## Performance Tuning

- **Partitioning:** Partition fuel_prices by year for faster queries
- **Materialized Views:** Pre-compute trend summaries for dashboard
- **Caching:** Redis for latest prices (TTL: 1 hour)
- **Archive:** Move old price history (>2 years) to archive schema

