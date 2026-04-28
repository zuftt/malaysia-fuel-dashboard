# ⛽ RONradar — Malaysia Fuel Price Dashboard

> Every Wednesday the government announces new fuel prices. Most Malaysians find out at the pump. RONradar shows you the full picture — the subsidised BUDI95 price, the unsubsidised market rate, how much the gap costs you every month, and how Malaysia compares to the rest of ASEAN.

![Hero](docs/screenshots/01-hero.png)

🔗 **[Live → malaysia-fuel-dashboard.onrender.com](https://malaysia-fuel-dashboard.onrender.com)**

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white" />
</p>

---

## The two things it does really well

### 1 · See exactly what you're paying — and why

![Price cards](docs/screenshots/02-price-cards.png)

RONradar pulls the official price data from [data.gov.my](https://data.gov.my/) every Thursday and breaks it down clearly:

- **BUDI95 (RM 1.99/L)** — what eligible Malaysians pay at the pump
- **RON 95 market (RM 3.87/L)** — the unsubsidised ceiling price
- **RON 97 & Diesel** — full market rates
- Week-on-week change with direction arrows so you always know if prices went up or down

Plus a 12-week trend chart and a live ASEAN comparison so you can see how Malaysia's prices stack up against Singapore, Thailand, Indonesia, Brunei, and the Philippines.

![ASEAN](docs/screenshots/04-asean.png)

---

### 2 · Calculate your actual BUDI95 savings

![Calculator](docs/screenshots/06-calculator.png)

The gap between RM 1.99 and RM 3.87 is **RM 1.88 per litre**. Over a month of daily commuting that adds up. The BUDI95 calculator tells you exactly how much:

1. Pick your car from a list of 20+ common Malaysian models (Myvi, Axia, Saga, City, Vios…) — tank size and fuel consumption pre-filled
2. Enter your daily distance
3. See your estimated monthly litres, cost, and **how much you save vs paying market rate**

It also tells you whether you'll hit the 200L monthly quota before the month ends — and what happens to the excess litres if you do.

---

## Screenshots

| Pump prices & trend | Latest news |
|---|---|
| ![Price cards](docs/screenshots/02-price-cards.png) | ![News](docs/screenshots/07-news.png) |

<p align="center">
  <img src="docs/screenshots/mobile-02-cards.png" alt="Mobile view" width="300" />
  <br/>
  <em>Mobile (iPhone)</em>
</p>

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (static export) · TypeScript · Tailwind CSS · Recharts |
| Backend | FastAPI · SQLAlchemy · Gunicorn + Uvicorn |
| Database | PostgreSQL |
| Hosting | [Render](https://render.com) — Static Site + Web Service + Managed DB |
| News | [NewsAPI.org](https://newsapi.org) · Bing News RSS (fallback) |
| FX rates | [Fixer.io](https://fixer.io) (daily disk cache) |
| Monitoring | [Sentry](https://sentry.io) |

---

## Project Layout

```
.
├── backend/
│   ├── app/
│   │   ├── api/               # Routers: prices, news, trends, admin, auth
│   │   ├── main.py            # FastAPI entry, CORS, security headers
│   │   ├── data_fetcher.py    # data.gov.my weekly sync
│   │   ├── asean_scraper.py   # ASEAN prices + FX conversion
│   │   └── newsapi_fetcher.py # NewsAPI.org integration
│   └── tests/                 # 21 pytest tests
└── frontend/
    └── src/
        ├── pages/index.tsx    # Dashboard
        ├── components/        # FuelCard, AseanComparison, TrendChart, BudiCalculator, NewsGrid
        └── lib/               # Types, formatters, constants, localStorage cache
```

---

## License

MIT — see [LICENSE](LICENSE).
