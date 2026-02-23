"""
Database configuration for VERITAS audit persistence.

Configures SQLite database with WAL mode optimization settings for
concurrent write support and improved performance.
"""

# SQLite database URL with aiosqlite driver for async operations
DATABASE_URL = "sqlite+aiosqlite:///./data/veritas_audits.db"

# Base class for all SQLAlchemy models
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# PRAGMA constants for WAL mode optimization
# See: https://www.sqlite.org/wal.html
PRAGMA_JOURNAL_MODE = "WAL"  # Write-Ahead Logging for concurrent access
PRAGMA_SYNCHRONOUS = "NORMAL"  # Checkpoint does fsync, not each transaction
PRAGMA_CACHE_SIZE = -64000  # -64MB cache for better performance
PRAGMA_TEMP_STORE = "MEMORY"  # Keep temp tables in RAM
PRAGMA_WAL_AUTOCHECKPOINT = 1000  # Checkpoint every 1000 pages
