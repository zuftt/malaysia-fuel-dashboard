# 🇲🇾 Malaysia Fuel & Government News Intelligence Dashboard

A real-time single pane of glass for fuel price monitoring, government policy tracking, and subsidy intelligence for Malaysia.

**Live Data Sources:**
- Weekly APM announcements (Ministry of Finance)
- KPDN price bulletins
- PMO & Government policy releases
- Bernama news aggregation
- Global benchmarks (MOPS Singapore)

**Key Features:**
- Real-time fuel price tracking (RON95, RON97, Diesel)
- Historical trend analysis vs. global benchmarks
- Policy intelligence & BUDI MADANI rollout tracking
- Smart alerts for price changes & legislative updates
- Tag-based filtering (#BUDI95, #Rationalization, #FuelFloating)
- Admin panel for manual data validation

---

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:3000
API Docs: http://localhost:8000/docs

---

## Project Structure

```
malaysia-fuel-dashboard/
├── backend/
│   ├── app/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic validation
│   │   ├── crud.py            # Database operations
│   │   ├── api/
│   │   │   ├── prices.py
│   │   │   ├── news.py
│   │   │   └── trends.py
│   │   └── scraper/
│   │       ├── mof_scraper.py
│   │       ├── kpdn_scraper.py
│   │       └── news_aggregator.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── PriceHistory.tsx
│   │   │   ├── PolicyNews.tsx
│   │   │   └── Alerts.tsx
│   │   ├── components/
│   │   │   ├── PriceCard.tsx
│   │   │   ├── TrendChart.tsx
│   │   │   └── NewsWidget.tsx
│   │   └── hooks/
│   │       └── useFuelData.ts
│   ├── package.json
│   └── next.config.js
│
└── docs/
    ├── ARCHITECTURE.md
    ├── SCHEMA.md
    └── API_SPEC.md
```

---

## Data Architecture

**Data Pipeline:**
```
Gov Sources (MoF, KPDN, PMO)
         ↓
[Weekly Scheduler + News Feed Parser]
         ↓
FastAPI Ingestion Endpoints
         ↓
PostgreSQL (Prices, News, Policies, Alerts)
         ↓
React Dashboard + Analytics
```

---

Built with ❤️ for Malaysia's fuel intelligence community.
