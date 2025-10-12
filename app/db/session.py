"""Database engine and session management."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)


def _ensure_sqlite_directory(database_url: str) -> None:
    """Create parent directories for SQLite database files when needed."""

    if not database_url.startswith("sqlite:///"):
        return

    db_path = database_url.replace("sqlite:///", "", 1)
    path = Path(db_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


connect_args: dict[str, object] = {}
db_url = settings.database_url
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    _ensure_sqlite_directory(db_url)


engine: Engine = create_engine(
    db_url,
    future=True,
    echo=False,
    connect_args=connect_args,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


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
