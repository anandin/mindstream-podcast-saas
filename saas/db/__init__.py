"""
Database initialization and session management.
"""
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from contextlib import contextmanager
from typing import Generator, Optional, Type

from saas.db.models import Base, User, Podcast, Episode, APIKey, UsageLog, SubscriptionTier, init_db, get_engine

# Default database URL
DEFAULT_DATABASE_URL = "sqlite:///./saas_podcast.db"

_engine = None
_SessionLocal = None


def get_db_engine(url: str = DEFAULT_DATABASE_URL):
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            url,
            connect_args={"check_same_thread": False} if "sqlite" in url else {},
            pool_pre_ping=True,
        )
    return _engine


def init_database(url: str = DEFAULT_DATABASE_URL):
    """Initialize database tables."""
    engine = get_db_engine(url)
    Base.metadata.create_all(engine)
    return engine


def get_db_session_maker(url: str = DEFAULT_DATABASE_URL) -> Type[Session]:
    """Get a database session maker (factory)."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_db_engine(url)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


@contextmanager
def get_db(url: str = DEFAULT_DATABASE_URL) -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    SessionLocal = get_db_session_maker(url)
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_monthly_usage():
    """Reset monthly usage counters (should be called via cron job)."""
    from datetime import datetime, timezone
    with get_db() as db:
        users = db.query(User).all()
        for user in users:
            user.episodes_generated_this_month = 0
            user.api_calls_this_month = 0
        db.commit()


# Dependency for FastAPI
def get_db_dependency(url: str = DEFAULT_DATABASE_URL):
    """FastAPI dependency for database sessions."""
    SessionLocal = get_db_session(url)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
