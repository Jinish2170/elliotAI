# Testing Patterns
**Analysis Date:** 2026-03-16

## Test Framework

### Python Backend

**Runner:**
- Framework: `pytest` with `pytest-asyncio` for async tests
- Test runner command: `python -m pytest` (from project root or backend directory)
- Configuration: `pytest.ini` at project root

**Config File - `pytest.ini`:**
```ini
[pytest]
markers =
  integration: exercises multiple runtime components together
  slow: requires longer runtime or optional dependencies
```

**Additional Dependencies:**
- `pytest-asyncio` - For async test functions
- `aiosqlite` - For async SQL operations in tests
- `sqlalchemy` - ORM for database testing

**Assertion Library:**
- Built-in pytest assertions
- SQLAlchemy model assertions

**Example Test Execution:**
```bash
cd C:/files/coding\ dev\ era/elliot\elliotAI
python -m pytest backend/tests/
```

**Test File Structure:**
```
backend/tests/
├── __init__.py
├── test_audit_persistence.py      # Tests SQLite WAL mode concurrent writes
├── test_audit_route_contract.py    # Tests route handlers and Pydantic contracts
└── test_audit_runner_queue.py      # Tests IPC queue mechanism
```

### Frontend

**Status:** No test framework currently configured
- No `jest.config.js`, `vitest.config.ts`, or similar configuration found
- No test files in `frontend/src/` (no `.test.ts`, `.spec.ts`, `.test.tsx`, `.spec.tsx` files)
- This is a gap in testing coverage

**Recommendation:** Consider adding testing framework (Vitest recommended for Next.js projects)

## Test File Organization

### Location

**Python Backend:**
- Location: `backend/tests/`
- Structure: Flat structure with individual test files by feature
- Test file naming: `test_*.py` pattern
- Test modules include `__init__.py` for package recognition

**Frontend:**
- Not implemented yet
- Expected: Tests co-located with components or in `__tests__` directories

### Naming Convention

**Python Backend:**
- Test files: `test_audit_persistence.py`, `test_audit_route_contract.py`, `test_audit_runner_queue.py`
- Test functions: `test_<functionality>` (e.g., `test_on_audit_completed_persists_canonical_summary`)
- Test classes: Not heavily used; prefer functional tests

**Example:**
```python
# File: backend/tests/test_audit_route_contract.py
@pytest.mark.asyncio
async def test_on_audit_completed_persists_canonical_summary(db_session: AsyncSession):
    # Test implementation
```

### Test Structure

**Python Backend - Using Fixtures:**

```python
# backend/tests/test_audit_route_contract.py

@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()
```

```python
# backend/tests/test_audit_persistence.py

@pytest_asyncio.fixture
async def test_engine():
    """Create a fresh database engine for each test."""
    # Use file-based SQLite to properly test WAL mode
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    async with test_engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine, db_path

    # Cleanup
    await test_engine.dispose()
    Path(db_path).unlink(missing_ok=True)
    Path(db_path + "-wal").unlink(missing_ok=True)
    Path(db_path + "-shm").unlink(missing_ok=True)
```

### Test Patterns

#### Test 1: Route Contract Testing

**File:** `backend/tests/test_audit_route_contract.py`

```python
@pytest.mark.asyncio
async def test_on_audit_completed_persists_canonical_summary(db_session: AsyncSession):
    """Test that audit completion persists all data correctly."""
    audit_id = "vrts_testabcd"

    # Mock environment to enable DB persistence
    with patch("backend.routes.audit.should_use_db_persistence", return_value=True):
        # Start audit
        await on_audit_started(
            audit_id,
            {
                "url": "https://example.com",
                "tier": "standard_audit",
                "verdict_mode": "expert",
            },
            db_session,
        )

        # Complete audit
        await on_audit_completed(
            audit_id,
            {
                "trust_score": 67,
                "risk_level": "medium",
                "narrative": "Caution warranted.",
                "signal_scores": {"security": 55.0},
                "site_type": "login",
                "site_type_confidence": 0.82,
                "security_results": {"phishing_db": {"verdict": "suspicious"}},
                "pages_scanned": 3,
                "elapsed_seconds": 9.5,
                "dark_pattern_summary": {...},
            },
            db_session,
        )

    # Verify persistence
    repo = AuditRepository(db_session)
    audit = await repo.get_by_id(audit_id)

    assert audit is not None
    assert audit.status == AuditStatus.COMPLETED
    assert audit.trust_score == 67
    assert audit.risk_level == "medium"
```

#### Test 2: Concurrent Database Writes

**File:** `backend/tests/test_audit_persistence.py`

```python
@pytest.mark.asyncio
async def test_concurrent_writes():
    """Test that multiple concurrent writes succeed without locking errors."""
    # Pattern: Create separate sessions for concurrent operations
    # Run multiple writes in parallel
    # Verify all succeeded without SQLite locking errors
```

#### Test 3: Service/Queue Tests

**File:** `backend/tests/test_audit_runner_queue.py`

```python
def test_sample_result():
    """Helper function creating sample audit result data."""
    return {
        "status": "completed",
        "url": "https://example.com",
        "audit_tier": "standard_audit",
        # ... complete structure
    }
```

## Mocking

### Python Backend

**Framework:** Python's built-in `unittest.mock` with `patch` decorator

**Types of Mocks Used:**

1. **Function Patching:**
   ```python
   with patch("backend.routes.audit.should_use_db_persistence", return_value=True):
       # test code
   ```

2. **Async Mocking:**
   ```python
   from unittest.mock import AsyncMock, Mock
   # Using AsyncMock for async methods
   ```

3. **Temporary File Mocking:**
   ```python
   db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
   # ... use for database tests
   ```

### What to Mock

**Database Layer:**
- Use in-memory SQLite (`sqlite+aiosqlite:///:memory:`) for unit tests
- Use temporary files for tests that need WAL mode (concurrency tests)
- Mock repository methods when testing pure route logic

**External Services:**
- WebSocket messages (in-memory for testing)
- File system operations (use `tempfile`)
- Environment variables (mocked via `patch`)

**Example - Mocking Database Persistence Toggle:**
```python
with patch("backend.routes.audit.should_use_db_persistence", return_value=True):
    await on_audit_started(...)
```

### What NOT to Mock

- SQLAlchemy models (test against actual schema)
- Pydantic validation (test contract compliance)
- Route handlers when testing HTTP behavior
- Repository layer integration tests

## Fixtures and Factories

### Test Data Patterns

**Inline Fixture Data:**
```python
def _sample_result(screenshot_path: str) -> dict:
    """Sample audit result for testing."""
    return {
        "status": "completed",
        "url": "https://example.com",
        "audit_tier": "standard_audit",
        "verdict_mode": "expert",
        "elapsed_seconds": 12.4,
        # ... complete nested structure
    }
```

**Database Fixtures:**
```python
@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Create in-memory database session."""
    # Set up test database
    # Yield session for test use
    # Clean up after test
```

### Location

**Database Fixtures:**
- Defined inline in test files (e.g., `test_audit_persistence.py`, `test_audit_route_contract.py`)
- Not in shared fixture module

**Data Factories:**
- Helper functions in test files (`_sample_result()`)
- No centralized factory framework

### Fixture Scope

**Default:** Function-scoped (each test gets fresh instance)
```python
@pytest_asyncio.fixture
async def db_session() -> AsyncSession:  # Function scope by default
```

**Pattern:** Clean setup and teardown for each test
- `async with engine.begin() as conn:` for setup
- `await engine.dispose()` for cleanup

## Coverage

### Current Status

**Python Backend:**
- No coverage enforcement detected
- No `--cov` configuration in pytest
- No coverage report generation

**Frontend:**
- Not implemented - no tests exist

### View Coverage

Not currently set up. Recommended for future:
```bash
python -m pytest backend/tests/ --cov=backend --cov-report=html
```

## Test Types

### Unit Tests

**Scope:**
- Individual route handlers (`test_audit_route_contract.py`)
- Service methods (`test_audit_runner_queue.py`)
- Repository methods

**Example:**
```python
@pytest.mark.asyncio
async def test_on_audit_completed_persists_canonical_summary(db_session: AsyncSession):
    # Test single operation - repository persisting audit data
```

### Integration Tests

**Marker:** `@pytest.mark.integration`

**Criteria:** "exercises multiple runtime components together" (from `pytest.ini`)

**Example:**
- Database + Repository integration
- Full audit flow (start → progress → complete)
- WebSocket message handling

**Not used:** Markers exist but tests not explicitly marked as integration

### Persistence Tests

**Specific Focus:** SQLite WAL mode concurrent access
- Tests in `test_audit_persistence.py`
- Uses file-based SQLite with WAL mode enabled
- Tests verify no database locking errors

## Common Patterns

### Async Testing

```python
import pytest
import pytest_asyncio

@pytest.mark.asyncio
async def test_my_async_function():
    result = await my_async_function()
    assert result is not None
```

**Key Points:**
- Use `@pytest.mark.asyncio` decorator
- Use `pytest_asyncio.fixture` for async fixtures
- Async functions must be declared with `async def`

### Error Testing

```python
# Test route errors
from fastapi import HTTPException

async def test_audit_start_invalid_url():
    # Test with invalid URL
    # Expect HTTPException with 400/422 status
```

```python
# Test exception propagation
with pytest.raises(ExpectedException):
    await failing_function()
```

### Logging Tests

No explicit logging tests currently. Pattern would be:
```python
# Capture log output
with caplog.at_level(logging.ERROR):
    # trigger error
    assert "error message" in caplog.text
```

### Database Tests

**Key Pattern - In-Memory SQLite:**
```python
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

**Key Pattern - Temporary File with WAL:**
```python
db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
async with test_engine.begin() as conn:
    await conn.execute(text("PRAGMA journal_mode=WAL"))
    await conn.run_sync(Base.metadata.create_all)
```

## Import Testing

**File:** `backend/test_imports.py`

A utility script that tests all critical imports:
```python
# Test all imports one by one
errors = []
try:
    from routes import health
except Exception as e:
    errors.append(f'health route: {e}')
# ...

if errors:
    print('ERRORS FOUND:')
    sys.exit(1)
else:
    print('All imports successful!')
```

**Usage:** Run manually to verify dependencies are properly configured

---

*Testing analysis: 2026-03-16*