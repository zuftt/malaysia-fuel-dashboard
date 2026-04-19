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

## News (“Berita Terkini”)

Headlines come from **RSS** (default: Google News searches for Malaysia fuel / subsidy / RON), filtered for relevance, then stored in **`government_announcements`** with `announcement_type = News Feed`. The API refreshes when data is **stale** (~4 hours) or on startup (`sync_news_feeds` in `news_fetcher.py`).

- **Env:** `NEWS_SYNC_ON_STARTUP` (default `true`, set `false` in CI/tests). Optional `NEWS_RSS_URLS` — semicolon-separated `Label|https://...` entries to add or replace feeds.
- **Egress:** Lambda/API needs **outbound HTTPS** to `news.google.com` (and any custom RSS hosts you set).

## CI/CD

**GitHub Actions** (push to `main`) uses **OIDC** to assume an IAM role (no long-lived access keys). It builds **Docker** images for `linux/amd64`, pushes to **ECR**, updates both Lambdas, runs `npm run build` for the frontend, **syncs** `frontend/out/` to S3, and **invalidates** CloudFront.

## Security (short)

IAM least-privilege roles for Lambda and GitHub OIDC; secrets in **SSM** / env; encryption at rest on RDS and related services per Terraform; **CloudTrail** for audit API logs.

For deployment commands and pitfalls (RDS passwords, Buildx manifests), see **[DEPLOYMENT.md](../DEPLOYMENT.md)**.
