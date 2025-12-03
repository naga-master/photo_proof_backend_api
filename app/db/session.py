"""Database engine and session management - PostgreSQL Only."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)


# PostgreSQL-only engine configuration
engine_config: dict[str, object] = {
    "future": True,
    "echo": False,
    "pool_size": 20,              # Base connection pool
    "max_overflow": 10,            # Additional connections under load
    "pool_timeout": 30,            # Wait 30s for connection
    "pool_pre_ping": True,         # Verify connections before use
    "pool_recycle": 3600,          # Recycle connections after 1 hour
}

db_url = settings.database_url

if not db_url.startswith("postgresql"):
    raise ValueError(f"Only PostgreSQL is supported. Got: {db_url}")

logger.info("Using PostgreSQL with connection pooling")

engine: Engine = create_engine(db_url, **engine_config)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a transactional database session."""

    db = SessionLocal()
    logger.debug("Database session opened")
    try:
        yield db
        db.commit()
        logger.debug("Database session committed")
    except Exception:  # pragma: no cover - re-raise for FastAPI error handling
        db.rollback()
        logger.exception("Database session rolled back due to exception")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager variant for scripts and background tasks."""

    session = SessionLocal()
    logger.debug("Session scope opened")
    try:
        yield session
        session.commit()
        logger.debug("Session scope committed")
    except Exception:  # pragma: no cover - re-raise to caller
        session.rollback()
        logger.exception("Session scope rolled back due to exception")
        raise
    finally:
        session.close()
        logger.debug("Session scope closed")
