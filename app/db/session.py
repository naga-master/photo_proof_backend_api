"""Database engine and session management."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


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
    try:
        yield db
        db.commit()
    except Exception:  # pragma: no cover - re-raise for FastAPI error handling
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager variant for scripts and background tasks."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - re-raise to caller
        session.rollback()
        raise
    finally:
        session.close()
