"""
Pydantic Schemas for Request/Response Validation
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal


# ============ Fuel Prices ============

class FuelPriceBase(BaseModel):
    date_announced: datetime
    effective_date: date
    ron95_subsidized: Optional[Decimal] = Field(None, decimal_places=2)
    ron95_market: Optional[Decimal] = Field(None, decimal_places=2)
    ron97: Decimal = Field(..., decimal_places=2)
    diesel_peninsular: Decimal = Field(..., decimal_places=2)
    diesel_east_malaysia: Optional[Decimal] = Field(None, decimal_places=2)
    diesel_b10: Optional[Decimal] = Field(None, decimal_places=2)
    diesel_b20: Optional[Decimal] = Field(None, decimal_places=2)
    region: str = Field(..., min_length=1, max_length=50)
    source: str = Field(..., min_length=1, max_length=100)


class FuelPriceCreate(FuelPriceBase):
    pass


class FuelPriceUpdate(BaseModel):
    ron95_subsidized: Optional[Decimal] = None
    ron95_market: Optional[Decimal] = None
    ron97: Optional[Decimal] = None
    diesel_peninsular: Optional[Decimal] = None
    diesel_east_malaysia: Optional[Decimal] = None
    notes: Optional[str] = None


class FuelPrice(FuelPriceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FuelPriceResponse(BaseModel):
    """Latest row plus provenance for the client (see CONTENT_RULES.md)."""

    data: FuelPrice
    timestamp: datetime  # when this snapshot was last written by our sync (row updated_at)
    source_url: str  # CSV endpoint we read
    source_catalogue_url: str  # Human-readable catalogue page on data.gov.my


# ============ ASEAN regional comparison ============

class AseanCompareRow(BaseModel):
    country: str
    country_name: str
    fuel_type: str
    local_name: str  # human-readable local product name (e.g. "Pertalite", "Gasohol 95")
    local_price: float
    currency: str
    usd_price: float
    is_subsidised: bool
    date: date
    source: str  # where the row came from (e.g. "data.gov.my", "seed+fallback")
    source_url: Optional[str] = None


class ExchangeRatesInfo(BaseModel):
    """How ``exchange_rates`` on the compare response were produced (Fixer, exchangerate.host, or static)."""

    provider: str = "none"
    used_static_fallback: bool = False
    message: str = ""


class AseanCompareResponse(BaseModel):
    """Cross-country retail prices normalised to USD per litre."""

    data: List[AseanCompareRow]
    exchange_rates: dict[str, float]
    updated_at: datetime
    exchange_rates_info: ExchangeRatesInfo = Field(default_factory=ExchangeRatesInfo)


class AseanHistoryRow(AseanCompareRow):
    """One dated snapshot; `usd_uses_latest_fx` when USD/litre was derived from MYR at response time."""

    usd_uses_latest_fx: bool = False


class AseanHistoryResponse(BaseModel):
    """Time series from `asean_fuel_prices` plus optional Malaysia weekly official rows."""

    data: List[AseanHistoryRow]
    days: int
    malaysia_usd_uses_latest_fx: bool = False
    note: str = ""


class PumpStationPriceRow(BaseModel):
    station: str
    location: Optional[str] = None
    ron95_budi: Optional[float] = None
    ron95: Optional[float] = None
    ron97: Optional[float] = None
    vpower: Optional[float] = None
    ron100: Optional[float] = None
    diesel: Optional[float] = None
    diesel_b7: Optional[float] = None
    updated_at: Optional[str] = None


class PumpStationPriceResponse(BaseModel):
    data: List[PumpStationPriceRow]
    count: int
    timestamp: datetime


# ============ Government Announcements ============

class AnnouncementBase(BaseModel):
    announcement_date: datetime
    title: str = Field(..., min_length=5, max_length=500)
    content: Optional[str] = Field(None, max_length=10000)
    source: str = Field(..., min_length=1, max_length=100)
    source_url: Optional[str] = Field(None, max_length=2000)
    announcement_type: str = Field(..., min_length=1, max_length=50)
    keywords: List[str] = Field(default_factory=list, max_length=20)


class AnnouncementCreate(AnnouncementBase):
    extracted_prices: Optional[dict] = None


class Announcement(AnnouncementBase):
    id: int
    extracted_prices: Optional[dict] = None
    sentiment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("keywords", mode="before")
    @classmethod
    def keywords_none_to_empty(cls, v):
        return v if v is not None else []


class AnnouncementResponse(BaseModel):
    data: List[Announcement]
    count: int
    timestamp: datetime


# ============ Price Alerts ============

class PriceAlertBase(BaseModel):
    fuel_type: str
    price_change: Decimal = Field(..., decimal_places=2)
    percentage_change: Decimal = Field(..., decimal_places=2)
    alert_type: str


class PriceAlert(PriceAlertBase):
    id: int
    triggered_at: datetime
    is_notified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceAlertResponse(BaseModel):
    data: List[PriceAlert]
    count: int


# ============ Policy Tags ============

class PolicyTagCreate(BaseModel):
    tag: str = Field(..., min_length=1, max_length=100)
    confidence: Decimal = Field(default=Decimal('1.0'), decimal_places=2)


class PolicyTag(PolicyTagCreate):
    id: int
    announcement_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Global Benchmarks ============

class BenchmarkBase(BaseModel):
    date: datetime
    mops_singapore: Optional[Decimal] = None
    wti_crude: Optional[Decimal] = None
    brent_crude: Optional[Decimal] = None


class BenchmarkCreate(BenchmarkBase):
    pass


class Benchmark(BenchmarkBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Price History / Trends ============

class PriceHistoryCreate(BaseModel):
    date: date
    fuel_type: str
    price: Decimal = Field(..., decimal_places=2)
    region: str
    subsidy_status: Optional[str] = None
    mops_reference: Optional[Decimal] = None
    subsidy_gap: Optional[Decimal] = None


class PriceHistory(PriceHistoryCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrendData(BaseModel):
    date: date
    fuel_type: str
    local_price: Decimal
    global_reference: Optional[Decimal] = None
    subsidy_gap: Optional[Decimal] = None
    region: str


class TrendResponse(BaseModel):
    data: List[TrendData]
    statistics: Optional[dict] = None
    period_days: Optional[int] = None


# ============ Comparison Data ============

class ComparisonResponse(BaseModel):
    date: date
    malaysia: dict
    global_benchmark: dict
    subsidy_metrics: dict


# ============ Admin Endpoints ============

class PriceValidateRequest(BaseModel):
    price_id: int
    ron95_subsidized: Optional[Decimal] = None
    ron97: Optional[Decimal] = None
    diesel_peninsular: Optional[Decimal] = None
    notes: Optional[str] = None


class ValidationResponse(BaseModel):
    success: bool
    price_id: int
    updated_at: datetime
    message: Optional[str] = None


class AlertConfigCreate(BaseModel):
    fuel_type: str
    alert_threshold_pct: Decimal = Field(..., gt=0, decimal_places=2)
    notify_channels: List[str] = Field(default_factory=lambda: ['dashboard'])


class AlertConfig(AlertConfigCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScraperStatusResponse(BaseModel):
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: str
    items_scraped: int
    errors: List[str] = Field(default_factory=list)


# ============ Authentication ============

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserLogin(BaseModel):
    email: str
    password: str


# ============ Error Responses ============

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    request_id: Optional[str] = None
