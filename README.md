# RONradar — Malaysia Fuel Price Dashboard

Malaysia fuel price dashboard. Tracks the government's weekly RON95/RON97/Diesel announcements, compares prices across ASEAN, and surfaces the latest subsidy news.

**Live → [malaysia-fuel-dashboard.onrender.com](https://malaysia-fuel-dashboard.onrender.com)**

---

![Hero](docs/screenshots/01-hero.png)

---

## Features

| | |
|---|---|
| **Weekly prices** | RON 95 (BUDI95 subsidised + market ceiling), RON 97, Diesel — sourced from data.gov.my every Wednesday |
| **Pump prices** | Shell Malaysia live pump grades (Peninsular + Sabah & Sarawak) scraped weekly |
| **ASEAN comparison** | Bar chart + table: MY · SG · TH · ID · BN · PH, converted to MYR via live FX |
| **Trend chart** | 12-week rolling price history |
| **BUDI95 calculator** | Estimate monthly fuel spend by car model, daily distance, and quota |
| **Berita Terkini** | Latest Malaysia fuel & subsidy headlines via NewsAPI.org |

---

## Screenshots

### Fuel price cards
![Price cards](docs/screenshots/02-price-cards.png)

### ASEAN comparison
![ASEAN comparison](docs/screenshots/04-asean.png)

### BUDI95 calculator
![Calculator](docs/screenshots/06-calculator.png)

### Berita Terkini
![News](docs/screenshots/07-news.png)

### Mobile
![Mobile](docs/screenshots/mobile-02-cards.png)

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
