# Testing Patterns
**Analysis Date:** 2026-03-16

## Test Framework
- **Backend:** pytest 7+ with pytest-asyncio for async tests
- **Testing Approach:** Class-based test organization using unittest.mock
- **Configuration:** `pytest.ini` at project root defines markers: `integration` and `slow`

## Test File Organization
- **Location:** `backend/tests/`
- **Naming:** `test_*.py` pattern
- **Structure:** Classes encapsulate related tests (e.g., `TestIpcModeDetermination`, `TestQueueReader`)

## Test Structure
- **Async Tests:** Use `@pytest.mark.asyncio` decorator
- **Fixtures:** `pytest_asyncio.fixture` for async setup; `tmp_path` for temporary files
- **Test Classes:** Group related test cases for clarity

## Mocking Approach
- **Framework:** Python `unittest.mock` (AsyncMock, Mock, patch)
- **Pattern:** Patch external dependencies at module level
- **Example:** `with patch("backend.services.audit_runner.mp.Manager", side_effect=RuntimeError(...))`

## Test Types
- **Unit Tests:** Direct testing of component logic
- **Integration Tests:** Multi-component testing with `pytest.mark.integration`
- **Async Tests:** Full async/await support via pytest-asyncio

## Running Tests
```bash
pytest backend/tests/           # All tests
pytest -m integration           # Integration tests only
pytest -m slow                  # Slow-running tests
```

## Coverage
- No explicit coverage tool detected
- Markers allow selective test runs for coverage analysis

---

*Testing analysis: 2026-03-16*