# Deployment Guide

## Local Development Setup

### Prerequisites
- Python 3.9+
- PostgreSQL (optional, SQLite for dev)
- Node.js 16+ (for frontend)
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python app/database.py

# Run development server
python -m uvicorn app.main:app --reload --port 8000
```

API will be available at: **http://localhost:8000**
Docs: **http://localhost:8000/docs**

### Frontend Setup (React/Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run dev server
npm run dev
```

Dashboard will be available at: **http://localhost:3000**

---

## Docker Deployment

### Build Docker Images

```bash
# Backend
docker build -t fuel-dashboard-api:latest ./backend

# Frontend
docker build -t fuel-dashboard-web:latest ./frontend
```

### Run with Docker Compose

```bash
docker-compose up -d
```

Services will be available at:
- API: http://localhost:8000
- Dashboard: http://localhost:3000
- PostgreSQL: localhost:5432

---

## Production Deployment

### Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@db-host:5432/fuel_dashboard
SQL_ECHO=False

# API Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=480
ENVIRONMENT=production
PORT=8000

# CORS
CORS_ORIGINS=https://yourdomain.com

# Scraper Configuration
MOF_SCRAPER_ENABLED=true
KPDN_SCRAPER_ENABLED=true
SCRAPER_INTERVAL_HOURS=24

# Notifications
NOTIFY_EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Redis (for caching & background tasks)
REDIS_URL=redis://redis-host:6379/0

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

### Kubernetes Deployment

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fuel-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fuel-api
  template:
    metadata:
      labels:
        app: fuel-api
    spec:
      containers:
      - name: api
        image: fuel-dashboard-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: secret-key
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

Deploy:
```bash
kubectl apply -f api-deployment.yaml
kubectl apply -f api-service.yaml
```

### Database Migration

```bash
# Using Alembic
cd backend
alembic upgrade head
```

### Monitoring & Logging

**With Prometheus + Grafana:**
```bash
# Metrics endpoint: /metrics

# Sample dashboard queries:
- api_request_duration_seconds
- fuel_price_update_lag_seconds
- database_connection_pool_utilization
```

**With ELK Stack:**
```bash
# Logs are structured JSON for easy parsing
# Index pattern: logs-fuel-dashboard-*
```

---

## Automated Scraping Setup

### Background Tasks (Celery)

```bash
# Start Celery worker
celery -A app.tasks worker --loglevel=info --schedule=/tmp/celerybeat-schedule

# Monitor with Flower
celery -A app.tasks flower
```

Available at: **http://localhost:5555**

### Scheduled Tasks

- **Every Wednesday 5 PM (Malaysia Time):** Scrape MOF APM announcement
- **Daily at 8 AM:** Sync global benchmarks (MOPS, WTI, Brent)
- **Every 6 hours:** Aggregate Bernama news feed
- **Daily at 11 PM:** Generate analytics snapshot

---

## Backup & Disaster Recovery

### Daily Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/fuel-dashboard"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > $BACKUP_DIR/backup_$TIMESTAMP.sql
gzip $BACKUP_DIR/backup_$TIMESTAMP.sql

# Upload to S3
aws s3 cp $BACKUP_DIR/backup_$TIMESTAMP.sql.gz s3://your-bucket/backups/
```

### Recovery Procedure

```bash
# From backup file
gunzip backup_TIMESTAMP.sql.gz
psql -h localhost -U user fuel_dashboard < backup_TIMESTAMP.sql
```

---

## Performance Tuning

### Database Indexes

All necessary indexes are defined in `models.py`. Verify:
```sql
-- Check indexes
SELECT * FROM pg_indexes WHERE tablename = 'fuel_prices';
```

### Caching Strategy

- **Redis:** Cache latest prices (TTL: 1 hour)
- **CDN:** Static assets (JavaScript, CSS)
- **Browser Cache:** Set Cache-Control headers for API responses

### API Rate Limiting

Configured per endpoint:
- Public: 100 req/hour per IP
- Authenticated: 1000 req/hour per user
- Admin: 500 req/hour per user

---

## Continuous Deployment

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test Backend
        run: cd backend && pytest
      - name: Test Frontend
        run: cd frontend && npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Kubernetes
        run: kubectl apply -f k8s/
```

---

## Health Checks & Monitoring

### Health Endpoint
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-28T17:00:00Z",
  "service": "Malaysia Fuel Intelligence Dashboard"
}
```

### Key Metrics to Monitor

1. **API Response Time:** p95 < 500ms
2. **Database Query Time:** p95 < 200ms
3. **Scraper Success Rate:** > 99%
4. **Uptime:** > 99.5%
5. **Cache Hit Ratio:** > 80%

---

## Troubleshooting

### API Won't Start
```bash
# Check logs
docker logs fuel-dashboard-api

# Verify database connection
python -c "from app.database import SessionLocal; SessionLocal()"
```

### Slow Price Queries
```bash
# Check query performance
EXPLAIN ANALYZE SELECT * FROM fuel_prices ORDER BY effective_date DESC LIMIT 10;
```

### Missing Price Updates
```bash
# Check scraper status
curl http://localhost:8000/api/v1/admin/scraper-status

# Check Celery tasks
celery -A app.tasks inspect active
```

---

## Support & Escalation

For production issues:
1. Check `/health` endpoint
2. Review logs: `docker logs fuel-dashboard-api`
3. Check database connectivity
4. Contact DevOps team

Emergency contact: devops@example.com
