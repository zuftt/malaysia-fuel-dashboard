# RONradar

Malaysia fuel price dashboard. Tracks the government's weekly RON95/RON97/Diesel announcements, compares prices across ASEAN, and surfaces the latest subsidy news.

**Live → [malaysia-fuel-dashboard.onrender.com](https://malaysia-fuel-dashboard.onrender.com)**

---

## What it does

**Weekly fuel prices** — RON 95 (BUDI95 subsidised + market ceiling), RON 97, and Diesel pulled directly from [data.gov.my](https://data.gov.my/) every Thursday.

**ASEAN comparison** — Bar chart showing how Malaysia's pump prices stack up against Singapore, Thailand, Indonesia, Brunei, and the Philippines, converted to MYR via live exchange rates.

**Trend chart** — 12-week rolling price history.

**Pump prices** — Shell Malaysia live grades (Peninsular + Sabah & Sarawak), scraped weekly.

**BUDI95 calculator** — Enter your car and daily commute; see your estimated monthly fuel spend and how much of your 200L quota you use.

**Berita Terkini** — Latest Malaysia fuel & subsidy headlines via NewsAPI.org.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (static export) · TypeScript · Tailwind CSS · Recharts |
| Backend | FastAPI · SQLAlchemy · Gunicorn + Uvicorn |
| Database | PostgreSQL |
| Hosting | [Render](https://render.com) — Static Site + Web Service + Managed DB |
| News | [NewsAPI.org](https://newsapi.org) · Bing News RSS (fallback) |
| FX rates | [Fixer.io](https://fixer.io) (daily cache) |
| Monitoring | [Sentry](https://sentry.io) |

---

## Project layout

```
.
├── backend/
│   ├── app/
│   │   ├── api/               # Routers: prices, news, trends, admin, auth
│   │   ├── main.py            # FastAPI entry, CORS, security headers
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── data_fetcher.py    # data.gov.my weekly sync
│   │   ├── asean_scraper.py   # ASEAN prices + FX conversion
│   │   ├── newsapi_fetcher.py # NewsAPI.org integration
│   │   └── safe_url.py        # SSRF host allowlist
│   └── tests/                 # 21 pytest tests
└── frontend/
    └── src/
        ├── pages/index.tsx    # Dashboard
        ├── components/        # FuelCard, AseanComparison, TrendChart, BudiCalculator, NewsGrid…
        └── lib/               # Types, formatters, constants, cache
```

---

## License

MIT — see [LICENSE](LICENSE).
