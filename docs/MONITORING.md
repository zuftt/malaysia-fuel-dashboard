# Monitoring & Alerts Setup (Render)

Simple 3-step monitoring for your Render backend.

## Step 1: Sentry (Error Tracking) - 2 minutes

### What it does:
- 🟢 Auto-captures all errors/exceptions
- 🟢 Sends you email alerts on new errors
- 🟢 Free tier: 5,000 errors/month

### Setup:
```bash
1. Go to https://sentry.io/signup/
2. Create account (free tier)
3. Create project → select "FastAPI"
4. Copy DSN (looks like: https://abc123@sentry.io/9999)
5. Add to your Render env vars:
   SENTRY_DSN=https://abc123@sentry.io/9999
   ENVIRONMENT=production
```

Done! All backend errors now send you an alert.

---

## Step 2: Render Health Checks - 1 minute

### What it does:
- 🟢 Checks `/health` endpoint every 5 minutes
- 🟢 Auto-restarts if service is down
- ⚠️ Render restarts silently (monitor logs manually)

### Setup in Render Dashboard:
```
Your Service → Settings → Health Check
  URL: https://your-api.onrender.com/health
  Protocol: HTTP
  Period: 5 minutes
  Timeout: 30 seconds
```

Click **Enable**.

---

## Step 3: Manual Health Check (Optional but recommended)

### Quick status check:
```bash
curl https://your-api.onrender.com/health

# Response:
# {"status":"healthy","timestamp":"2026-04-28T...","service":"Malaysia Fuel..."}
```

---

## Viewing Alerts

### Sentry Dashboard:
- Go to https://sentry.io/organizations/your-org/
- Click your project
- All errors appear with stack traces, trends, and email notifications

### Render Logs:
- Render dashboard → Your Service → Logs
- Search for `ERROR` to find crash logs
- Logs show for 24 hours

---

## Example: What triggers alerts?

✅ **You get notified:**
- Database connection fails
- API returns 500 error
- Unhandled exception in code
- Missing environment variable crashes app

❌ **You don't get notified:**
- 404 errors (normal)
- API returns 400 (client error)
- Slow requests (only in logs)

---

## Cost

| Tool | Free Tier | What you get |
|------|-----------|-------------|
| Sentry | ✅ YES | 5,000 errors/month, email alerts |
| Render Health | ✅ Built-in | Health checks, auto-restart |
| **Total** | **$0** | **Full monitoring** |

---

## Database Issues?

If your API crashes due to database:
1. Check Sentry for error details
2. Check Render Logs for connection messages
3. Verify `DATABASE_URL` in Render env vars
4. Test locally: `psql $DATABASE_URL -c "SELECT 1"`

---

## Cron Job (Weekly Fuel Sync) Monitoring

Currently just logs. To add alerts:

```python
# backend/app/lambdas/scraper.py (optional - add at end)
if success:
    logger.info("✓ Fuel sync completed successfully")
else:
    logger.error("✗ Fuel sync failed - check error logs")
    # Optional: send Slack webhook here
```

Logs appear in Render dashboard even for cron jobs.

