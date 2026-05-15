# Domain Setup, Security & SEO Best Practices

Complete guide for deploying your Malaysia Fuel Dashboard with a custom domain on Render.

---

## **Part 1: Buy a Domain**

### **Where to Buy (Best Options)**

| Registrar | Pros | Cons | Price |
|-----------|------|------|-------|
| **Namecheap** | Cheap, reliable, WHOIS privacy | Limited support | $8-12/yr |
| **Google Domains** | Simple, Google integrated | No email | $12/yr |
| **Cloudflare** | Free WHOIS, auto DNS | Requires Cloudflare account | $8/yr |
| **1&1 IONOS** | Cheap, Malaysia-friendly | Upsell-heavy | $6-10/yr |
| **GoDaddy** | Popular, lots of features | Poor reputation | $10-15/yr |

### **Recommended: Cloudflare (Best Security)**
- Free WHOIS privacy (protects your info)
- Free SSL/TLS everywhere
- DDoS protection
- Automatic DNS management

**Steps:**
1. Go to https://www.cloudflare.com/products/registrar/
2. Search your domain
3. Buy ($8-10/yr, no markup)
4. Domain auto-manages DNS through Cloudflare

---

## **Part 2: Connect Domain to Render**

### **Step 1: Add Custom Domain to Render**

**Frontend (Static Site):**
1. Render Dashboard → **malaysia-fuel-dashboard** (static site)
2. Click **Settings** → **Custom Domains**
3. Add your domain: `fuel-dashboard.com`
4. Render gives you a CNAME: `fuel-dashboard.com.onrender.com`

**Backend (Web Service):**
1. Render Dashboard → **malaysia-fuel-api** (web service)
2. Click **Settings** → **Custom Domains**
3. Add subdomain: `api.fuel-dashboard.com`
4. Render gives you a CNAME: `api.fuel-dashboard.com.onrender.com`

### **Step 2: Update DNS Records**

**If using Cloudflare (recommended):**
1. Cloudflare Dashboard → Your Domain → **DNS**
2. Add **CNAME records**:

```
Type    Name                    Content
CNAME   fuel-dashboard.com      fuel-dashboard.com.onrender.com
CNAME   api                     api.fuel-dashboard.com.onrender.com
CNAME   www                     fuel-dashboard.com.onrender.com  (optional, for www)
```

3. Click **Save**
4. Wait 5-15 minutes for DNS to propagate

**Check if working:**
```bash
nslookup fuel-dashboard.com
nslookup api.fuel-dashboard.com
```

---

## **Part 3: Security Best Practices**

### **1. SSL/TLS (HTTPS)**

✅ **Automatic with Render + Cloudflare**
- Render auto-provisions Let's Encrypt certificate
- Cloudflare provides edge SSL
- No extra setup needed!

Verify:
```bash
curl -I https://api.fuel-dashboard.com/health
# Should show: HTTP/2 200 or HTTP/1.1 200
```

### **2. CORS (Cross-Origin Resource Sharing)**

**Current setup (GOOD):**
```python
# backend/app/main.py
allow_origins=[
    "https://fuel-dashboard.com",
    "https://www.fuel-dashboard.com"
]
```

**Update this in code:**
```python
allow_origins=[
    "https://fuel-dashboard.com",
    "https://www.fuel-dashboard.com",
    "http://localhost:3000",      # dev only
]
```

Or set via env var in Render:
```
CORS_ORIGINS=https://fuel-dashboard.com,https://www.fuel-dashboard.com
```

### **3. Security Headers**

Add to **backend/app/main.py** (after CORS middleware):
```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### **4. Rate Limiting (Prevent Abuse)**

Install: `pip install slowapi`

Add to **backend/app/main.py**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/prices/latest")
@limiter.limit("100/minute")
async def get_latest_prices(request: Request, db: Session = Depends(get_db)):
    # Your endpoint
    pass
```

### **5. Hide Sensitive Info**

✅ Already done:
- Don't expose API keys in responses
- Don't log passwords/tokens
- Error messages don't leak stack traces (in prod)

Verify in Render:
```bash
curl https://api.fuel-dashboard.com/docs
# Should NOT show DATABASE_URL or SECRET keys
```

### **6. HTTPS Redirect**

Cloudflare auto-does this (Set to "Always Use HTTPS").

Or in Render settings:
```
Redirect all requests to HTTPS: ON
```

---

## **Part 4: SEO Best Practices**

### **1. Meta Tags (Frontend)**

Add to **frontend/src/pages/_document.tsx**:
```typescript
<Head>
  <title>Malaysia Fuel Price Dashboard | Official Weekly RON95, RON97 & Diesel</title>
  <meta name="description" content="Official weekly Malaysia fuel prices (RON95, RON97, Diesel) set by the Ministry of Finance, with the BUDI95 subsidy explained and ASEAN context. An information hub, not a station price-comparison tool." />
  <meta name="keywords" content="Malaysia fuel price, BUDI95, RON95 subsidy, RON97, diesel, MOF weekly fuel price, APM, data.gov.my" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  
  {/* Open Graph (social sharing) */}
  <meta property="og:title" content="Malaysia Fuel Price Dashboard" />
  <meta property="og:description" content="Official weekly Malaysia fuel prices and BUDI95 subsidy explained" />
  <meta property="og:image" content="https://fuel-dashboard.com/og-image.png" />
  <meta property="og:url" content="https://fuel-dashboard.com" />
  
  {/* Twitter Card */}
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Malaysia Fuel Price Dashboard" />
</Head>
```

### **2. robots.txt**

Create **frontend/public/robots.txt**:
```
User-agent: *
Allow: /
Disallow: /admin
Disallow: /api

Sitemap: https://fuel-dashboard.com/sitemap.xml
```

### **3. Sitemap (for Google)**

Create **frontend/public/sitemap.xml**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://fuel-dashboard.com/</loc>
    <lastmod>2026-04-28</lastmod>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://fuel-dashboard.com/api/docs</loc>
    <lastmod>2026-04-28</lastmod>
    <priority>0.7</priority>
  </url>
</urlset>
```

### **4. Structured Data (Schema.org)**

Add to **frontend/src/pages/index.tsx**:
```typescript
<script type="application/ld+json">
{JSON.stringify({
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Malaysia Fuel Price Dashboard",
  "description": "Information hub for Malaysia's official weekly fuel prices and the BUDI95 subsidy",
  "url": "https://fuel-dashboard.com",
  "applicationCategory": "UtilityApplication"
})}
</script>
```

### **5. Performance (Core Web Vitals)**

- ✅ Next.js Image optimization (already done)
- ✅ Gzip compression (Render auto-enables)
- ✅ CDN caching (Render + Cloudflare)

Check score:
```
https://pagespeed.web.dev/
```

### **6. Submit to Search Engines**

1. **Google Search Console:**
   - Go to https://search.google.com/search-console
   - Add property: `https://fuel-dashboard.com`
   - Upload sitemap
   - Submit URL inspection

2. **Bing Webmaster Tools:**
   - Go to https://www.bing.com/webmasters
   - Add site
   - Upload sitemap

---

## **Part 5: Monitoring & Maintenance**

### **Health Checks**

```bash
# API health
curl https://api.fuel-dashboard.com/health

# Frontend loads
curl -I https://fuel-dashboard.com

# SSL certificate (should be valid)
openssl s_client -connect api.fuel-dashboard.com:443 -brief
```

### **Renewal Reminders**

- **Domain:** Auto-renew in Cloudflare (set it to ON)
- **SSL Certificate:** Auto-renewed by Let's Encrypt (Render handles)
- **Render:** Monitor logs for downtime alerts

### **Monitoring Tools**

Free services to monitor uptime:
- **UptimeRobot** (already recommended)
- **Statuscake**
- **Pingdom**

---

## **Quick Checklist**

- [ ] Buy domain (Cloudflare recommended)
- [ ] Add CNAME records to DNS
- [ ] Wait for DNS propagation (5-15 min)
- [ ] Test: `curl https://api.fuel-dashboard.com/health`
- [ ] Update CORS_ORIGINS in Render env vars
- [ ] Add security headers to backend
- [ ] Add meta tags to frontend
- [ ] Create robots.txt & sitemap.xml
- [ ] Submit to Google Search Console
- [ ] Set up uptime monitoring
- [ ] Enable auto-renewal on domain

---

## **Cost Estimate (Monthly)**

| Service | Cost |
|---------|------|
| Domain (annual) | $0.67/mo |
| Cloudflare (free tier) | $0 |
| Render API (free tier) | $0 |
| Render Frontend (free tier) | $0 |
| Render Database (free tier) | $0 |
| Monitoring (UptimeRobot free) | $0 |
| **TOTAL** | **~$0.67/mo** |

Upgrade to paid tiers if you need:
- Custom Cloudflare features ($20/mo)
- Render paid instances ($7-100+/mo)

---

## **Questions?**

Ask me about:
- Specific domain registrar setup
- SSL certificate issues
- DNS troubleshooting
- SEO optimization
- Security hardening

Ready to deploy? 🚀
