"""
Database Engine and Session Configuration.
Hardened for high-concurrency SQLite (WAL mode, busy timeout, connection pooling)
and scalable PostgreSQL production fleets.
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool
from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger("database")

# Resolve relative SQLite path to absolute BASE_DIR to prevent cwd contamination
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///.") or db_url.startswith("sqlite:///testing_platform.db"):
    # Strip sqlite:/// prefix and resolve relative to BASE_DIR
    rel_path = db_url.replace("sqlite:///", "")
    resolved_db = (settings.BASE_DIR / rel_path).resolve()
    db_url = f"sqlite:///{resolved_db.as_posix()}"

is_sqlite = db_url.startswith("sqlite")

# Configure driver parameters and connection pooling
if is_sqlite:
    connect_args = {
        "check_same_thread": False,
        "timeout": 30.0,  # 30-second driver timeout for acquiring locks
    }
    engine_kwargs = {
        "connect_args": connect_args,
        "echo": False,
        "future": True,
    }
else:
    # Production PostgreSQL connection pool configuration
    engine_kwargs = {
        "poolclass": QueuePool,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "echo": False,
        "future": True,
    }

engine = create_engine(db_url, **engine_kwargs)

# Inject high-concurrency PRAGMAs on every SQLite connection
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_concurrency_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            # 1. Enable Write-Ahead Logging (WAL) - readers do not block writers, writers do not block readers
            cursor.execute("PRAGMA journal_mode=WAL;")
            # 2. Set busy timeout to 30000ms (30s) so concurrent writes wait instead of throwing "database is locked"
            cursor.execute("PRAGMA busy_timeout=30000;")
            # 3. Synchronous NORMAL is crash-safe in WAL mode and drastically faster on disk I/O
            cursor.execute("PRAGMA synchronous=NORMAL;")
            # 4. In-memory page cache (approx 10MB) for ultra-fast query execution
            cursor.execute("PRAGMA cache_size=-10000;")
            # 5. Enforce relational foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON;")
            # 6. Store temporary tables and indices in memory
            cursor.execute("PRAGMA temp_store=MEMORY;")
        finally:
            cursor.close()

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
    """Initializes all database tables defined in SQLAlchemy models and verifies concurrency PRAGMAs."""
    logger.info("Initializing database schema...")
    import src.models.entities  # Ensure models are loaded
    Base.metadata.create_all(bind=engine)
    
    # Verify active SQLite journal mode
    if is_sqlite:
        with engine.connect() as conn:
            from sqlalchemy import text
            mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
            timeout = conn.execute(text("PRAGMA busy_timeout;")).scalar()
            logger.info(f"SQLite concurrency engine active: journal_mode={mode}, busy_timeout={timeout}ms")
            
    logger.info("Database schema initialized successfully.")
