# db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
# USE_SQLITE_DEV = os.getenv("USE_SQLITE_DEV", "0") == "1"


def _appears_placeholder(url: str | None) -> bool:
    """Return True if the provided URL is missing or looks like a placeholder.

    This helps when a developer has the example/supabase placeholder value in their
    .env file (for example: "postgresql://postgres:password@db.<your-host>.supabase.co/..."),
    which will fail DNS resolution locally. In that case we fall back to a local
    SQLite file so `create_tables.py` and local development can proceed without a
    working remote database.
    """
    if not url:
        return True
    low = url.lower()
    # common signs of placeholder/templated values
    if "<your-host>" in low or "<" in url or "example" in low:
        return True
    return False



if _appears_placeholder(DATABASE_URL):
    raise ValueError(
        "DATABASE_URL is not set or appears to be a placeholder.\n"
        "Set DATABASE_URL in your .env to your Supabase direct DB URL, for example:\n"
        "postgresql://postgres:ALIMahdees205-f@db.ixvgtszvpdjfbcevpcec.supabase.co:5432/postgres"
    )

assert DATABASE_URL is not None, "DATABASE_URL must be set"
db_url: str = DATABASE_URL

# Engine (sync) - suitable for FastAPI long-lived backend
try:
    # Production-safe engine settings. Supabase/Postgres works with a normal URL.
    # If you need SSL, include `?sslmode=require` in the DATABASE_URL.
    engine = create_engine(db_url, future=True, pool_pre_ping=True)
except Exception as exc:
    raise RuntimeError(f"unable to create SQLAlchemy engine for DATABASE_URL={db_url!r}: {exc}") from exc
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base = declarative_base()
