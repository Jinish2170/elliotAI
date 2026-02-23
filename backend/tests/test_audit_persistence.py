"""
Concurrent Audit Persistence Tests

Tests for SQLite WAL mode concurrent write handling.
Verifies that the database layer supports true concurrent access -
multiple writes succeed without locking errors, reads don't block writes.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import tempfile

# Add backend root to path for imports
import sys
from pathlib import Path as Pathlib
backend_root = Pathlib(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_root))
sys.path.insert(0, str(backend_root / "veritas"))

from veritas.db.models import Audit, AuditStatus
from veritas.db.repositories import AuditRepository
from veritas.db.config import Base


@pytest_asyncio.fixture
async def test_engine():
    """
    Create a fresh database engine for each test.
    Uses file-based SQLite to properly test WAL mode.
    """
    # Create temporary file for database
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    # Use file-based database for WAL mode tests
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    # Create all tables and enable WAL mode
    async with test_engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine, db_path

    # Cleanup
    await test_engine.dispose()
    Path(db_path).unlink(missing_ok=True)
    # Also clean up WAL files
    Path(db_path + "-wal").unlink(missing_ok=True)
    Path(db_path + "-shm").unlink(missing_ok=True)


@pytest_asyncio.fixture
async def audit_session(test_engine):
    """
    Create a fresh database session for each test.
    Returns a session factory to allow creating separate sessions.
    """
    test_engine, _ = test_engine

    # Session factory for this test
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session

    # After test, cleanup any remaining sessions using TestSessionLocal
    # (handled by async context manager)


async def get_session(engine) -> AsyncSession:
    """Helper to create a new session for concurrent operations."""
    TestSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return TestSessionLocal()


@pytest.mark.asyncio
async def test_concurrent_audit_writes(test_engine):
    """
    Test SQLite WAL mode handles concurrent writes correctly.

    Creates N audits simultaneously via asyncio.gather() with separate sessions.
    Verifies all writes succeed and data persists correctly.
    """
    test_engine, _ = test_engine
    num_concurrent = 10

    async def create_audit(index: int) -> str:
        """Create audit in its own session."""
        async with await get_session(test_engine) as session:
            repo = AuditRepository(session)
            audit = Audit(
                id=f"vrts_test_{index:08d}",
                url=f"https://test-{index}.com",
                audit_tier="quick_scan",
                verdict_mode="expert",
                status=AuditStatus.COMPLETED,
                trust_score=50.0 + index,
                risk_level="low" if index > 5 else "suspicious",
                pages_scanned=1,
                elapsed_seconds=5.0,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            result = await repo.create(audit)
            return result.id

    # Run concurrent writes
    tasks = [create_audit(i) for i in range(num_concurrent)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verify all writes succeeded (no exceptions)
    assert all(isinstance(r, str) for r in results), \
        f"Some writes failed: {[type(r).__name__ for r in results if not isinstance(r, str)]}"

    # Verify all audits persisted using a fresh session
    async with await get_session(test_engine) as session:
        repo = AuditRepository(session)
        for i in range(num_concurrent):
            audit = await repo.get_by_id(f"vrts_test_{i:08d}")
            assert audit is not None, f"Audit {i} not persisted"
            assert audit.trust_score == 50.0 + i, f"Audit {i} has wrong score: {audit.trust_score}"
            assert audit.status == AuditStatus.COMPLETED


@pytest.mark.asyncio
async def test_concurrent_read_write(test_engine):
    """
    Test that reads don't block writes in WAL mode.

    Runs continuous reads while performing writes.
    Verifies reads don't timeout and writes complete.
    """
    test_engine, _ = test_engine

    # Create initial audit
    async with await get_session(test_engine) as session:
        repo = AuditRepository(session)
        audit = Audit(
            id="vrts_readwrite_test",
            url="https://test-concurrent.com",
            audit_tier="standard_audit",
            verdict_mode="expert",
            status=AuditStatus.RUNNING,
            trust_score=50.0,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
        )
        await repo.create(audit)

    async def read_task() -> None:
        """Continuous reads while writes happen."""
        async with await get_session(test_engine) as session:
            repo = AuditRepository(session)
            for i in range(20):
                a = await repo.get_by_id("vrts_readwrite_test")
                assert a is not None, f"Read task failed at iteration {i}"
                await asyncio.sleep(0.005)  # Small delay between reads

    async def write_task(task_id: int) -> None:
        """Update audit in loop with separate session."""
        async with await get_session(test_engine) as session:
            repo = AuditRepository(session)
            for i in range(10):
                # Get, update, save (need to refresh each time due to separate sessions)
                a = await repo.get_by_id("vrts_readwrite_test")
                if a is not None:
                    a.trust_score = 50.0 + (task_id * 10) + i
                    a.pages_scanned = (task_id * 10) + i + 1
                    await repo.update(a)
                await asyncio.sleep(0.01)

    # Run concurrent read + write with 1 read task and 3 write tasks
    await asyncio.gather(
        read_task(),
        write_task(0),
        write_task(1),
        write_task(2),
    )

    # Verify final state
    async with await get_session(test_engine) as session:
        repo = AuditRepository(session)
        final = await repo.get_by_id("vrts_readwrite_test")
        assert final is not None
        assert final.trust_score >= 50.0, f"Trust score {final.trust_score} < 50.0"
        assert final.pages_scanned > 0, f"Pages scanned must be positive, got {final.pages_scanned}"


@pytest.mark.asyncio
async def test_wal_mode_enabled(test_engine):
    """
    Verify WAL mode is enabled for the database.
    Confirms PRAGMA journal_mode returns 'wal'.
    """
    test_engine, _ = test_engine

    async with await get_session(test_engine) as session:
        result = await session.execute(text("PRAGMA journal_mode"))
        journal_mode = result.scalar_one()

    assert journal_mode == "wal", \
        f"WAL mode not enabled, got: {journal_mode}. Check test setup."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
