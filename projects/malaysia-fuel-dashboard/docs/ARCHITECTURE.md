# System Architecture

## High-Level Data Flow (Mermaid)

```mermaid
graph TB
    subgraph "Data Sources"
        A1["Ministry of Finance<br/>APM Announcements"]
        A2["KPDN Press Releases"]
        A3["PMO Statements"]
        A4["Bernama News Feed"]
        A5["Global Benchmarks<br/>MOPS Singapore"]
    end

    subgraph "Ingestion Layer"
        B1["Weekly Scheduler<br/>APM @ Wednesday 5 PM"]
        B2["PDF/Web Scraper<br/>OCR + Text Extraction"]
        B3["RSS/API Aggregator"]
        B4["Market Data Connector"]
    end

    subgraph "Processing & Validation"
        C1["FastAPI Ingestion Service"]
        C2["Pydantic Schema Validation"]
        C3["Duplicate Detection"]
        C4["Keyword Tagging Engine"]
    end

    subgraph "Data Layer"
        D1["PostgreSQL Database"]
        D2["Redis Cache<br/>Latest Prices"]
        D3["Time-Series Store<br/>Historical Trends"]
    end

    subgraph "API Layer"
        E1["/prices/latest<br/>Current fuel costs"]
        E2["/news/alerts<br/>Policy + price changes"]
        E3["/trends<br/>Historical analysis"]
        E4["/compare<br/>Local vs Global"]
    end

    subgraph "Frontend"
        F1["React Dashboard<br/>Real-time updates"]
        F2["Charts & Analytics<br/>Recharts/D3"]
        F3["Alert System<br/>Toast notifications"]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B3
    A5 --> B4

    B1 --> C1
    B2 --> C1
    B3 --> C1
    B4 --> C1

    C1 --> C2
    C2 --> C3
    C3 --> C4

    C4 --> D1
    D1 --> D2
    D1 --> D3

    D1 --> E1
    D1 --> E2
    D1 --> E3
    D1 --> E4

    E1 --> F1
    E2 --> F3
    E3 --> F2

    style A1 fill:#e1f5ff
    style D1 fill:#fff3e0
    style E1 fill:#f3e5f5
    style F1 fill:#e8f5e9
```

## Component Breakdown

### 1. Data Ingestion (Weekly Schedule)
- **Trigger:** Every Wednesday at 5:00 PM (Malaysia Standard Time)
- **Sources:**
  - MOF APM Bulletin (PDF + HTML)
  - KPDN Official Price List
  - PMO Press Release Feed
  - Bernama RSS (filtered: fuel-related)
- **Strategy:**
  - **PDF/HTML:** BeautifulSoup4 + PyPDF2 for text extraction, regex for price parsing
  - **RSS:** feedparser library with caching
  - **OCR Fallback:** Tesseract for image-based PDFs

### 2. Validation & Enrichment
- **Pydantic Models:** Strict schema validation (date, price format, decimal precision)
- **Duplicate Detection:** Hash-based deduplication (source + date + price)
- **Keyword Tagging:** Regex + NLP for tags (#BUDI95, #FuelFloating, #Rationalization)
- **Alert Generation:** Compare against last known price, flag significant changes (>5%)

### 3. Database Design
- **Fuel Prices Table:** Track RON95/RON97/Diesel across Peninsular & East Malaysia
- **News/Announcements:** Timestamp, source, content, extracted price deltas, policy keywords
- **Historical Snapshots:** Time-series data for trend analysis
- **Alert Rules:** Trigger thresholds for email/SMS notifications

### 4. API Endpoints
- **GET /prices/latest** → Current fuel prices + timestamp
- **GET /prices/history?days=30** → Historical data for charting
- **GET /news/alerts** → Recent price changes + policy updates
- **GET /news/search?tag=BUDI95** → Filter by keywords
- **GET /trends/vs-global** → Malaysia vs MOPS Singapore comparison
- **POST /admin/validate** → Manual data correction endpoint (auth required)

### 5. Frontend Real-Time Updates
- **WebSocket Connection:** Push price updates to connected clients
- **Chart Updates:** Recharts with real-time data binding
- **Toast Alerts:** Trigger notifications on significant price changes
- **Filter Sidebar:** Tag-based filtering (#BUDI95, #Rationalization, etc.)

---

## Deployment Strategy

**Development:**
- FastAPI on localhost:8000
- React dev server on localhost:3000
- SQLite for testing (or PostgreSQL locally)

**Production:**
- FastAPI: Docker container (Gunicorn + Uvicorn)
- React: Static build deployed to Vercel/Netlify
- PostgreSQL: Managed service (AWS RDS or similar)
- Celery + Redis: For background scraping tasks
- GitHub Actions: CI/CD pipeline for testing + deployment

---

## Security Considerations

- API authentication: JWT tokens for admin endpoints
- Rate limiting: Prevent scraper abuse
- HTTPS only: All external API calls
- Data validation: Pydantic strict mode on all inputs
- CORS: Whitelist frontend domain
- Secrets management: Environment variables for credentials

---

## Performance Metrics

- **Ingestion Latency:** < 5 minutes from MOF announcement to dashboard
- **API Response Time:** < 500ms for /prices/latest
- **Chart Rendering:** < 2s for 90-day historical view
- **Uptime SLA:** 99.5% (resilience to source outages)

---

## Future Enhancements

1. **Machine Learning:** Predictive models for price changes based on global oil trends
2. **SMS/Email Alerts:** Notifications for significant price changes
3. **Comparative Analysis:** Fuel subsidies vs regional neighbors (Singapore, Thailand)
4. **Mobile App:** React Native version for on-the-go alerts
5. **Integration:** Telegram bot for instant price alerts
6. **Analytics:** Dashboard usage analytics + user heatmaps

