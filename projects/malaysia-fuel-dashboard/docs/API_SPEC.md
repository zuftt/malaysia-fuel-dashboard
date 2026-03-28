# API Specification

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All protected endpoints require JWT token in `Authorization: Bearer <token>` header.

---

## Endpoints

### 1. Fuel Prices

#### GET /prices/latest
**Description:** Get current fuel prices
**Auth:** None (public)

**Response:**
```json
{
  "data": {
    "date_announced": "2026-03-28T17:00:00Z",
    "effective_date": "2026-03-28",
    "ron95_subsidized": 2.35,
    "ron95_market": 3.10,
    "ron97": 3.25,
    "diesel_peninsular": 2.48,
    "diesel_east_malaysia": 2.50,
    "region": "Peninsular",
    "source": "MOF",
    "created_at": "2026-03-28T17:05:00Z"
  },
  "timestamp": "2026-03-28T17:05:00Z"
}
```

#### GET /prices/history
**Description:** Historical fuel prices with trend data
**Auth:** None
**Query Params:**
- `days` (int, default=30): Number of days to retrieve
- `fuel_type` (string): Filter by fuel type (RON95, RON97, Diesel)
- `region` (string): Filter by region (Peninsular, East Malaysia)

**Response:**
```json
{
  "data": [
    {
      "date": "2026-03-28",
      "fuel_type": "RON95",
      "local_price": 2.35,
      "global_reference": 3.50,
      "subsidy_gap": 1.15,
      "region": "Peninsular"
    },
    {
      "date": "2026-03-21",
      "fuel_type": "RON95",
      "local_price": 2.30,
      "global_reference": 3.45,
      "subsidy_gap": 1.15,
      "region": "Peninsular"
    }
  ],
  "count": 2,
  "period_days": 7
}
```

#### GET /prices/compare
**Description:** Compare Malaysia prices vs global benchmarks
**Auth:** None

**Response:**
```json
{
  "data": {
    "date": "2026-03-28",
    "malaysia": {
      "ron95": 2.35,
      "ron97": 3.25,
      "diesel": 2.48
    },
    "global": {
      "mops_singapore": 3.50,
      "wti_crude": 75.20,
      "brent_crude": 78.30
    },
    "subsidy_cost_estimate": {
      "ron95_gap": 1.15,
      "estimated_monthly_burden_myr": 450000000
    }
  }
}
```

---

### 2. Government News & Announcements

#### GET /news/latest
**Description:** Latest government announcements
**Auth:** None
**Query Params:**
- `limit` (int, default=10): Number of results
- `source` (string): Filter by source (MOF, KPDN, PMO, Bernama)
- `type` (string): Filter by type (Price Update, Policy Change, BUDI Rollout)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "announcement_date": "2026-03-28T17:00:00Z",
      "title": "APM: RON95 down to RM2.35, Diesel unchanged",
      "content": "...",
      "source": "MOF",
      "source_url": "https://mof.gov.my/...",
      "announcement_type": "Price Update",
      "keywords": ["#BUDI95", "#SubsidyAdjustment"],
      "sentiment": "Positive",
      "extracted_prices": {
        "ron95_subsidized": 2.35,
        "ron97": 3.25,
        "diesel": 2.48
      }
    }
  ],
  "count": 1,
  "timestamp": "2026-03-28T17:05:00Z"
}
```

#### GET /news/alerts
**Description:** Get price change alerts
**Auth:** None
**Query Params:**
- `days` (int, default=7): Look back period
- `min_change` (float, default=0.05): Minimum price change (RM)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "fuel_type": "RON95",
      "price_change": -0.05,
      "percentage_change": -2.08,
      "alert_type": "Decrease",
      "triggered_at": "2026-03-28T17:00:00Z",
      "is_notified": true
    }
  ],
  "count": 1
}
```

#### GET /news/search
**Description:** Search announcements by keywords
**Auth:** None
**Query Params:**
- `tags` (string, comma-separated): Filter by tags (#BUDI95, #Rationalization, #FuelFloating)
- `keyword` (string): Full-text search in title/content
- `date_from` (date): Start date (YYYY-MM-DD)
- `date_to` (date): End date (YYYY-MM-DD)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "title": "BUDI MADANI Phase 2 Rollout Announcement",
      "announcement_date": "2026-03-15T10:00:00Z",
      "keywords": ["#BUDI95", "#TargetedSubsidy"],
      "sentiment": "Neutral"
    }
  ],
  "count": 1,
  "query": {
    "tags": ["#BUDI95"],
    "date_range": "2026-01-01 to 2026-03-28"
  }
}
```

---

### 3. Trend Analysis

#### GET /trends/subsidy-gap
**Description:** Historical subsidy gap (Local vs Global)
**Auth:** None
**Query Params:**
- `days` (int, default=90): Period to analyze
- `fuel_type` (string): RON95, RON97, Diesel

**Response:**
```json
{
  "data": [
    {
      "date": "2026-03-28",
      "subsidy_gap": 1.15,
      "fuel_type": "RON95",
      "local_price": 2.35,
      "global_price": 3.50,
      "government_cost_myr": 150000000
    }
  ],
  "statistics": {
    "avg_gap": 1.12,
    "max_gap": 1.25,
    "min_gap": 1.05,
    "trend": "Stable"
  }
}
```

#### GET /trends/volatility
**Description:** Price volatility analysis
**Auth:** None

**Response:**
```json
{
  "data": {
    "ron95": {
      "weekly_changes": [-0.05, 0.00, 0.10],
      "volatility_pct": 2.5,
      "trend_direction": "Upward"
    },
    "ron97": {
      "weekly_changes": [0.00, 0.05, 0.15],
      "volatility_pct": 3.8,
      "trend_direction": "Upward"
    },
    "diesel": {
      "weekly_changes": [0.00, 0.00, 0.00],
      "volatility_pct": 0.0,
      "trend_direction": "Stable"
    }
  }
}
```

---

### 4. Admin Endpoints

#### POST /admin/prices/validate
**Description:** Manually validate and correct fuel prices
**Auth:** Required (Admin role)
**Body:**
```json
{
  "price_id": 1,
  "ron95_subsidized": 2.35,
  "ron97": 3.25,
  "diesel_peninsular": 2.48,
  "notes": "Corrected from OCR error"
}
```

**Response:**
```json
{
  "success": true,
  "updated_at": "2026-03-28T17:15:00Z",
  "price_id": 1
}
```

#### POST /admin/announcements/manual
**Description:** Manually add announcement (for missed scrapes)
**Auth:** Required (Admin role)
**Body:**
```json
{
  "announcement_date": "2026-03-28T17:00:00Z",
  "title": "APM Announcement",
  "content": "...",
  "source": "MOF",
  "announcement_type": "Price Update",
  "extracted_prices": {
    "ron95_subsidized": 2.35
  }
}
```

#### GET /admin/scraper-status
**Description:** Check status of automated scraping tasks
**Auth:** Required (Admin role)

**Response:**
```json
{
  "last_run": "2026-03-28T17:00:00Z",
  "next_run": "2026-04-04T17:00:00Z",
  "status": "Success",
  "items_scraped": 5,
  "errors": []
}
```

#### POST /admin/alerts/config
**Description:** Configure alert thresholds
**Auth:** Required (Admin role)
**Body:**
```json
{
  "fuel_type": "RON95",
  "alert_threshold_pct": 3.0,
  "notify_channels": ["email", "dashboard"]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid query parameters",
  "details": "days must be between 1 and 365"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required",
  "message": "Missing or invalid JWT token"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "resource": "price_id_999"
}
```

### 500 Internal Server Error
```json
{
  "error": "Database connection failed",
  "request_id": "req_1234567890"
}
```

---

## Rate Limiting

- **Public endpoints:** 100 requests/hour per IP
- **Authenticated endpoints:** 1000 requests/hour per user
- **Admin endpoints:** 500 requests/hour per user
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## WebSocket (Real-Time Updates)

**Connection:**
```
ws://localhost:8000/ws/prices/live
```

**Subscribe to price updates:**
```json
{
  "action": "subscribe",
  "channels": ["prices.ron95", "prices.diesel", "news.alerts"]
}
```

**Receive updates:**
```json
{
  "channel": "prices.ron95",
  "data": {
    "price": 2.35,
    "timestamp": "2026-03-28T17:00:00Z",
    "change": -0.05
  }
}
```

