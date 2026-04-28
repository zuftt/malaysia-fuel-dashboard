"""
Database Configuration & Session Management
"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
import os
from pathlib import Path

from dotenv import load_dotenv

# Always load backend/.env (not only cwd) so FIXER_ACCESS_KEY / DB URL work from repo root.
_backend_root = Path(__file__).resolve().parent.parent
load_dotenv(_backend_root / ".env")

# Database URL from environment or use SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fuel_dashboard.db"
)

# Engine configuration - use appropriate pool for database type
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "False") == "True"
    )
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=os.getenv("SQL_ECHO", "False") == "True"
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Dependency for FastAPI
def get_db() -> Session:
    """
    FastAPI dependency to provide database session
    Usage: def endpoint(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper to create tables
def init_db():
    """Initialize database tables (idempotent - skips if tables exist)"""
    from app.models import Base

    # Check if tables already exist by inspecting the schema
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if existing_tables:
        print(f"✓ Database already initialized ({len(existing_tables)} tables found)")
        return

    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


if __name__ == "__main__":
    init_db()
