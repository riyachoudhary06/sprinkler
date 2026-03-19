"""
db/database.py — SQLAlchemy engine, session factory, and Base.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    """Create all tables if they don't exist."""
    from db import models  # noqa: F401 — ensure models are registered with Base
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a database session, always closes on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
