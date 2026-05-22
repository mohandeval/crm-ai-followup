"""
src/db/connection.py
────────────────────
PostgreSQL connection manager for the AI CRM project.

Provides:
  - get_connection()       — raw psycopg2 connection (use for queries)
  - get_engine()           — SQLAlchemy engine (use for pandas read_sql)
  - test_connection()      — health-check, prints table list in sales_raw schema

Usage:
    from src.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sales_raw.leads_raw")
            print(cur.fetchone())
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from typing import Generator

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── Connection string ──────────────────────────────────────────────────────────
def _build_dsn() -> str:
    return (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )


# ── Raw psycopg2 connection ────────────────────────────────────────────────────
@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Context manager returning a psycopg2 connection.
    Auto-commits on success, rolls back on exception, always closes.

    Example:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM sales_raw.leads_raw LIMIT 5")
                rows = cur.fetchall()
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            connect_timeout=10,
        )
        logger.debug("PostgreSQL connection established")
        yield conn
        conn.commit()
    except psycopg2.OperationalError as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn and not conn.closed:
            conn.close()
            logger.debug("PostgreSQL connection closed")


# ── SQLAlchemy engine (for pandas / ORM) ──────────────────────────────────────
def get_engine():
    """
    Returns a SQLAlchemy engine.
    Use this with pandas.read_sql() for quick data exploration.

    Example:
        import pandas as pd
        from src.db.connection import get_engine

        df = pd.read_sql("SELECT * FROM sales_raw.leads_raw LIMIT 10", get_engine())
    """
    return create_engine(_build_dsn(), pool_pre_ping=True)


# ── Health check ──────────────────────────────────────────────────────────────
def test_connection() -> bool:
    """
    Connects to the DB, prints all tables in the sales_raw schema,
    and returns True if healthy.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Basic ping
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                logger.info(f"Connected to: {version[:60]}...")

                # 2. List tables in sales_raw schema
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    ORDER BY table_name
                    """,
                    (settings.postgres_schema,),
                )
                tables = [row[0] for row in cur.fetchall()]
                logger.info(f"Tables in '{settings.postgres_schema}' schema: {tables}")

                # 3. Quick row count on leads_raw
                cur.execute(f"SELECT COUNT(*) FROM {settings.postgres_schema}.leads_raw")
                count = cur.fetchone()[0]
                logger.info(f"leads_raw row count: {count:,}")

        return True

    except Exception as e:
        logger.error(f"Connection test FAILED: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    print(f"\n{'✅ Database OK' if success else '❌ Database FAILED'}")
