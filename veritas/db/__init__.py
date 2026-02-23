"""
Database initialization and async engine setup.

Provides the SQLAlchemy engine, session factory, and initialization
function for the VERITAS audit persistence layer.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from veritas.db import models
from veritas.db.config import DATABASE_URL, Base

# Create async engine with SQLite and aiosqlite driver
# check_same_thread=False required for SQLite to allow cross-thread access
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Create async session factory
# expire_on_commit=False allows accessing relationships after commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency injection for database sessions.

    Yields a database session and ensures it's closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize the database with WAL mode and create all tables.

    Executes PRAGMA statements to enable Write-Ahead Logging mode
    for improved concurrent write support, then creates all tables
    defined in the Base metadata.

    PRAGMA settings:
    - journal_mode=WAL: Enables concurrent reads and writes
    - synchronous=NORMAL: Better performance with some safety guarantees
    - cache_size=-64000: 64MB cache for improved performance
    - temp_store=MEMORY: Store temp tables in RAM
    - wal_autocheckpoint=1000: Checkpoint every 1000 pages
    """
    async with engine.begin() as conn:
        # Enable WAL mode for concurrent writes
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        # Set synchronous mode to NORMAL (safer with some performance cost)
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        # Set 64MB cache
        await conn.execute(text("PRAGMA cache_size=-64000"))
        # Store temp tables in memory
        await conn.execute(text("PRAGMA temp_store=MEMORY"))
        # Auto-checkpoint every 1000 pages
        await conn.execute(text("PRAGMA wal_autocheckpoint=1000"))
        # Create all tables from models
        await conn.run_sync(Base.metadata.create_all)


# Export public API
__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_database",
    "Base",
]
