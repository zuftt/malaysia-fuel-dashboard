# RONradar — Malaysia Fuel Price Dashboard

Real-time weekly fuel price tracker for Malaysia. Pulls official prices from [data.gov.my](https://data.gov.my/), compares them across ASEAN, and surfaces the latest government subsidy news.

**Live:** [malaysia-fuel-dashboard.onrender.com](https://malaysia-fuel-dashboard.onrender.com)

---

## Features

| | |
|---|---|
| **Weekly prices** | RON 95 (BUDI95 subsidised + market ceiling), RON 97, Diesel — sourced from data.gov.my every Wednesday |
| **Pump prices** | Shell Malaysia live pump grades (Peninsular + Sabah & Sarawak) scraped weekly |
| **ASEAN comparison** | Bar chart + table: MY · SG · TH · ID · BN · PH, converted to MYR via live FX |
| **Trend chart** | 12-week rolling price history |
| **BUDI95 calculator** | Estimate monthly fuel spend by car model, daily distance, and quota |
| **Berita Terkini** | Latest Malaysia fuel & subsidy headlines via NewsAPI.org (Bing RSS fallback) |

---

## Stack

**Frontend** — Next.js 14 (static export) · TypeScript · Tailwind CSS · Recharts
→ Deployed on **Render Static Site**

**Backend** — FastAPI · SQLAlchemy · Gunicorn + Uvicorn workers
→ Deployed on **Render Web Service** (Singapore region, free tier)

**Database** — PostgreSQL on **Render Managed Database**

**News** — [NewsAPI.org](https://newsapi.org) (primary, 100 req/day free) · Bing News RSS (fallback, no key needed)

**FX rates** — [Fixer.io](https://fixer.io) (once per UTC day, disk-cached)

**Monitoring** — [Sentry](https://sentry.io) for error tracking

---

## Quick start (local)

```bash
git clone https://github.com/zuftt/malaysia-fuel-dashboard.git
cd malaysia-fuel-dashboard

# Backend — http://localhost:8000/docs
cp backend/.env.example backend/.env   # fill in SECRET_KEY (required)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend — http://localhost:3000 (new terminal)
cd frontend
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' > .env.local
npm install && npm run dev
```

### Required env vars

| Variable | Where | Notes |
|---|---|---|
| `SECRET_KEY` | backend | JWT signing key — min 32 chars, high-entropy. Generate: `python -c 'import secrets; print(secrets.token_urlsafe(32))'` |
| `NEWSAPI_KEY` | backend | [newsapi.org](https://newsapi.org) free key — falls back to Bing RSS if unset |
| `FIXER_ACCESS_KEY` | backend | [fixer.io](https://fixer.io) — optional, falls back to exchangerate.host |
| `NEXT_PUBLIC_API_URL` | frontend | Backend URL, e.g. `http://localhost:8000` |

See `backend/.env.example` for the full list.

---

## Testing

```bash
# Backend (21 tests)
cd backend
NEWS_SYNC_ON_STARTUP=false ASEAN_SYNC_ON_STARTUP=false pytest -q

# Frontend
cd frontend
npm run lint && npm run build
```

CI runs both on every push to `main` (see `.github/workflows/ci.yml`).

---

## Deploy (Render)

Three resources, all on free tier:

| Resource | Type | Root dir |
|---|---|---|
| `malaysia-fuel-api` | Web Service (Python) | `backend/` |
| `malaysia-fuel-dashboard` | Static Site | `frontend/` |
| `malaysia-fuel-db` | PostgreSQL | — |

**Build command (backend):** `pip install -r requirements.txt`
**Start command:** `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT`
**Build command (frontend):** `npm install && npm run build`
**Publish path:** `out/`

Set `DATABASE_URL`, `SECRET_KEY`, `NEWSAPI_KEY`, `CORS_ORIGINS`, and `ENVIRONMENT=production` in Render environment variables.

---

## Project layout

```
.
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers (prices, news, trends, admin, auth)
│   │   ├── main.py         # App entry point, CORS, security headers
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── data_fetcher.py # data.gov.my CSV sync
│   │   ├── asean_scraper.py# ASEAN regional prices + FX
│   │   ├── newsapi_fetcher.py # NewsAPI.org integration
│   │   ├── news_fetcher.py # Bing RSS fallback
│   │   └── safe_url.py     # SSRF host allowlist
│   └── tests/              # 21 pytest tests
├── frontend/
│   └── src/
│       ├── pages/index.tsx # Main dashboard page
│       ├── components/     # FuelCard, AseanComparison, TrendChart, BudiCalculator, NewsGrid…
│       └── lib/            # Types, formatters, constants
├── docs/                   # Architecture notes
└── .github/workflows/ci.yml
```

---

## Content rules

All user-facing copy, disclaimers, and data labelling follow **[CONTENT_RULES.md](CONTENT_RULES.md)**.

---

## License

MIT — see [LICENSE](LICENSE).
