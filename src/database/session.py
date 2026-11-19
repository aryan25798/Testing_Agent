"""
Database Engine and Session Configuration.
Supports SQLite for local development and PostgreSQL for production.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger("database")

# Handle SQLite concurrency connection options
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides an active database session for requests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initializes all database tables defined in SQLAlchemy models."""
    logger.info("Initializing database schema...")
    import src.models.entities  # Ensure models are loaded
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
