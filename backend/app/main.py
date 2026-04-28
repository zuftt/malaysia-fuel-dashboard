"""
FastAPI Application Entry Point
Malaysia Fuel & Government News Intelligence Dashboard
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
import logging

# Initialize Sentry for error tracking (if enabled)
if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "development")
    )

from app.database import init_db, SessionLocal
from app.api import prices, news, trends, admin, auth
from app.data_fetcher import sync_fuel_prices
from app.webz_news_fetcher import sync_webz_news
from app.asean_scraper import sync_asean_prices

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="🇲🇾 Malaysia Fuel & Policy Intelligence Dashboard",
    description="Real-time fuel price monitoring and government policy tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,"
            "http://localhost:3001,http://127.0.0.1:3001",
        ).split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize database and sync fuel data on startup"""
    logger.info("🚀 Starting Malaysia Fuel Dashboard API...")
    try:
        init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return

    # Sync fuel prices from data.gov.my on startup
    db = SessionLocal()
    try:
        try:
            result = sync_fuel_prices(db)
            logger.info(f"✓ Fuel data sync: {result['created']} new, {result['skipped']} skipped")
        except Exception as e:
            logger.warning(f"⚠ Fuel data sync failed (non-fatal): {e}")

        # Webz.io news (fuel & subsidy news — skip in CI via NEWS_SYNC_ON_STARTUP=false)
        if os.getenv("NEWS_SYNC_ON_STARTUP", "true").lower() in ("1", "true", "yes"):
            try:
                ns = sync_webz_news(db)
                logger.info(
                    "✓ Webz.io news: %s new, %s updated, %s skipped",
                    ns.get("inserted", 0),
                    ns.get("updated", 0),
                    ns.get("skipped", 0),
                )
            except Exception as e:
                logger.warning(f"⚠ Webz.io news sync failed (non-fatal): {e}")

        if os.getenv("ASEAN_SYNC_ON_STARTUP", "true").lower() in ("1", "true", "yes"):
            try:
                ar = sync_asean_prices(db)
                logger.info("✓ ASEAN fuel sync: %s rows upserted", ar.get("upserted", 0))
            except Exception as e:
                logger.warning(f"⚠ ASEAN fuel sync failed (non-fatal): {e}")
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down Malaysia Fuel Dashboard API...")


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Malaysia Fuel Intelligence Dashboard"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint"""
    return {
        "message": "🇲🇾 Malaysia Fuel & Government News Intelligence Dashboard",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# API V1 Router
@app.get("/api/v1", tags=["API"])
async def api_v1_root():
    """API V1 Root"""
    return {
        "version": "1.0.0",
        "endpoints": {
            "prices": "/api/v1/prices",
            "news": "/api/v1/news",
            "trends": "/api/v1/trends",
            "admin": "/api/v1/admin"
        }
    }


# Include routers
app.include_router(
    prices.router,
    prefix="/api/v1/prices",
    tags=["Fuel Prices"]
)

app.include_router(
    news.router,
    prefix="/api/v1/news",
    tags=["Government News"]
)

app.include_router(
    trends.router,
    prefix="/api/v1/trends",
    tags=["Trend Analysis"]
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Admin"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "details": str(exc) if os.getenv("DEBUG") else "An error occurred",
            "request_id": request.headers.get("x-request-id", "unknown")
        }
    )


# Lambda handler via Mangum (optional — not required for local API or pytest)
try:
    from mangum import Mangum

    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None  # type: ignore[misc, assignment]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development"
    )
