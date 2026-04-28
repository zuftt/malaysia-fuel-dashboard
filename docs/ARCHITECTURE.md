# Architecture

RONradar runs on [Render](https://render.com) free tier across three services.

## Services

```
Browser
  └─ Static Site (Render CDN)
       └─ Next.js static export  ─────────────────────────────────────────┐
                                                                           │ HTTPS
  Web Service (Render, Singapore)                                          │
       └─ FastAPI + Gunicorn/Uvicorn ◄────────────────────────────────────┘
            ├─ GET /api/v1/prices/*     (fuel prices, ASEAN compare, pump stations)
            ├─ GET /api/v1/news/latest  (NewsAPI.org → Bing RSS fallback)
            ├─ GET /api/v1/trends/*     (12-week price history)
            └─ POST /api/v1/auth/*      (admin JWT auth, rate-limited)
                 └─ PostgreSQL (Render Managed DB)
```

## Data sources

| Data | Source | Cadence |
|---|---|---|
| Fuel prices (MY) | [data.gov.my CSV](https://storage.data.gov.my/commodities/fuelprice.csv) | Synced on startup; effective weekly Thursday |
| ASEAN prices | motorist.sg scrape + seed fallback | Synced on startup |
| FX rates | Fixer.io (disk-cached daily) | Once per UTC day |
| Pump grades | Shell Malaysia `.xlsx` via Firecrawl | Weekly (Thursday) |
| News | NewsAPI.org → Bing News RSS | Refreshed on stale read (4h TTL) |

## Frontend caching

The static frontend caches API responses in `localStorage` with TTLs aligned to the weekly price cycle:

- **Prices / history / pump stations** — expire next Thursday 00:00 MYT (when MOF publishes new prices)
- **ASEAN comparison** — 24 hours
- **News** — 30 minutes

On page load, cached data is painted immediately. The live fetch runs in the background and replaces it silently.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push to `main`:
1. Backend: `pytest -q` (21 tests)
2. Frontend: `npm run lint && npm run build`

Render auto-deploys both services on push to `main`.
