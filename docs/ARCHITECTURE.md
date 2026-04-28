# Architecture

High-level view of what runs in production (aligned with [infra/aws_architecture.png](../infra/aws_architecture.png)).

## Traffic

1. **Users** hit **CloudFront** (optional **WAF** in front).
2. Static assets (`/*`) come from **S3** (Next.js export).
3. API requests (`/api/*`, `/health`) go to **API Gateway HTTP** → **API Lambda** (FastAPI + Mangum).

## Data

- **Fuel prices:** Pulled from the official **CSV** on data.gov.my (`data_fetcher.py`). The API Lambda syncs on startup when running locally; in AWS the **scraper Lambda** runs on an **EventBridge** schedule and writes to **RDS PostgreSQL**.
- **RDS** sits in **private subnets**; Lambdas run in the VPC with security-group access to PostgreSQL.
- **DynamoDB** holds subscription / visitor-counter style state used by the API.
- **SNS** sends price-alert notifications when the scraper detects changes.

## ASEAN fuel comparison

- **Table:** `asean_fuel_prices` — one row per `country`, effective `date`, and `fuel_type` (RON95, RON97, Diesel), with `local_price`, `currency`, `usd_price`, `is_subsidised`, `source`, `source_url`.
- **Ingestion:** `asean_scraper.py` — Malaysia reuses the data.gov.my CSV; Singapore (motorist.sg HTML heuristic), Thailand (EPPO CSV attempt + seed fallback), Indonesia (mypertamina scrape + seed), Brunei & Philippines (manual seed in Phase 1). FX to USD via **exchangerate.host** (`USD` base) with static fallback if the API fails.
- **API:** `GET /api/v1/prices/compare` returns `{ data, exchange_rates, updated_at }`. The previous Malaysia-vs-global benchmark response is at **`GET /api/v1/prices/malaysia-vs-global`** (same payload as the old `/compare` route).
- **When it runs:** FastAPI startup calls `sync_asean_prices` when **`ASEAN_SYNC_ON_STARTUP`** is true (default). The **scraper Lambda** runs ASEAN sync on every schedule tick (including when Malaysia prices are already up to date) so FX and regional rows refresh weekly.
- **Env:** `ASEAN_SYNC_ON_STARTUP` — set `false` in CI (see `.github/workflows/ci.yml`) and tests (`backend/tests/conftest.py`) to avoid outbound calls.

## News (“Berita Terkini”)

Headlines come from **RSS** (default: Google News searches for Malaysia fuel / subsidy / RON), filtered for relevance, then stored in **`government_announcements`** with `announcement_type = News Feed`. The API refreshes when data is **stale** (~4 hours) or on startup (`sync_news_feeds` in `news_fetcher.py`).

- **Env:** `NEWS_SYNC_ON_STARTUP` (default `true`, set `false` in CI/tests). Optional `NEWS_RSS_URLS` — semicolon-separated `Label|https://...` entries to add or replace feeds.
- **Egress:** Lambda/API needs **outbound HTTPS** to `news.google.com` (and any custom RSS hosts you set).

## CI/CD

**GitHub Actions** (push to `main`) uses **OIDC** to assume an IAM role (no long-lived access keys). It builds **Docker** images for `linux/amd64`, pushes to **ECR**, updates both Lambdas, runs `npm run build` for the frontend, **syncs** `frontend/out/` to S3, and **invalidates** CloudFront.

## Security (short)

IAM least-privilege roles for Lambda and GitHub OIDC; secrets in **SSM** / env; encryption at rest on RDS and related services per Terraform; **CloudTrail** for audit API logs.

For deployment commands and pitfalls (RDS passwords, Buildx manifests), see **[DEPLOYMENT.md](../DEPLOYMENT.md)**.
