# Testing Patterns
**Analysis Date:** 2026-05-14

## Test Framework

**Runner:** `pytest` (8.4.1 installed; `elliot/requirements.txt` pins `pytest>=7.4.0`). Async tests use `pytest-asyncio` (`pytest-asyncio>=0.23.0`) via the explicit `@pytest.mark.asyncio` decorator and `@pytest_asyncio.fixture` for async fixtures. HTTP-level testing uses `httpx>=0.25.0`. Config lives in `pytest.ini` at repo root — it only registers markers; there is **no `asyncio_mode = auto`**, so every async test must be decorated explicitly.

**Assertion Library:** Plain `assert` statements (pytest rewriting). Assertions almost always carry an explanatory message — `assert audit is not None`, `assert route_after_scout(state) == "vision", "Should route to vision on success"`.

**Run Commands:**
```bash
# All tests
python -m pytest

# A package / directory
python -m pytest elliot/tests/unit/
python -m pytest backend/tests/
python -m pytest tests/

# A single file or test
python -m pytest elliot/tests/unit/test_onion_detector.py
python -m pytest elliot/tests/unit/test_onion_detector.py::TestValidateOnion::test_validate_onion_v2_valid

# By marker (registered in pytest.ini)
python -m pytest -m integration
python -m pytest -m "not slow"

# Verbose with stdout shown
python -m pytest -v -s elliot/tests/langgraph_investigation/
```

## Test File Organization

**Location:** Three separate test roots, all with `__init__.py`:
- `elliot/tests/` — core/agent tests, with subdirs `unit/`, `integration/`, `langgraph_investigation/`. Many tests also sit directly in `elliot/tests/` (`test_security_agent.py`, `test_judge_early_exit.py`, `test_vlm_caching.py`).
- `backend/tests/` — FastAPI route + service tests (`test_audit_route_contract.py`, `test_audit_runner_queue.py`, `test_audit_persistence.py`).
- `tests/` (repo root) — cross-cutting component tests (`test_consensus_engine.py`, `test_link_explorer.py`, `test_scroll_orchestrator.py`).
- `testing/scripts/` — manual/ad-hoc scripts, **not** pytest-collected.

**Naming:** Files are `test_<subject>.py`. Test classes are `Test<Subject>` (`TestOnionDetectorPatterns`, `TestRunnerResultContract`, `TestScoutDataFlow`). Test functions are `test_<behavior>` with descriptive snake_case names (`test_pattern_v3_rejects_55_char`, `test_on_audit_completed_persists_canonical_summary`).

**Structure:** Mirror the source layout loosely — unit tests for `elliot/darknet/onion_detector.py` live in `elliot/tests/unit/test_onion_detector.py`; route tests for `backend/routes/audit.py` live in `backend/tests/test_audit_route_contract.py`. Shared fixtures go in a `conftest.py` next to the tests that use them (`elliot/tests/integration/conftest.py`, `elliot/tests/langgraph_investigation/conftest.py`). There is no root-level `conftest.py`.

## Test Structure

**Suite Organization:** Group related cases into `Test*` classes, each with a one-line docstring describing the area. Real example from `elliot/tests/unit/test_onion_detector.py`:
```python
class TestValidateOnion:
    """Test .onion URL validation."""

    def test_validate_onion_v2_valid(self):
        """Verify validate_onion() accepts valid v2 addresses."""
        detector = OnionDetector()
        valid_urls = [
            "abcdefghijklmnop.onion",
            "3g2upl4pq6kufc4m.onion",  # DuckDuckGo v2 (real example)
        ]
        for url in valid_urls:
            result = detector.validate_onion(url)
            assert result is True, f"URL: {url}"
```
Standalone module-level `test_*` functions are also acceptable, especially for pure routing/logic functions (`test_route_after_scout_routing` in `elliot/tests/langgraph_investigation/test_02_full_audit_mocked.py`).

**Patterns:** Every test function has a docstring starting with "Verify..." or "Test...". Tests loop over lists of inputs with an f-string assertion message identifying the failing case. Arrange-act-assert is followed without explicit comment markers. Async tests carry `@pytest.mark.asyncio`.

## Mocking

**Framework:** `unittest.mock` from the stdlib — `MagicMock`, `AsyncMock`, `Mock`, `patch`, `patch.dict`. No third-party mocking library.

**Patterns:** Patch where the name is *used*, not where it is defined, via `with patch(...)` blocks. Real example from `backend/tests/test_audit_route_contract.py`:
```python
@pytest.mark.asyncio
async def test_on_audit_completed_persists_canonical_summary(db_session: AsyncSession):
    audit_id = "vrts_testabcd"
    with patch("backend.routes.audit.should_use_db_persistence", return_value=True):
        await on_audit_started(audit_id, {...}, db_session)
        await on_audit_completed(audit_id, {...}, db_session)
```
For full-graph tests, many patches are stacked in one `with` using line-continuations (`elliot/tests/langgraph_investigation/test_02_full_audit_mocked.py` lines 70-79). Async methods are mocked with `AsyncMock(side_effect=async_fn)` so call args/counts can be asserted (`mock_scout.investigate.call_count > 0`). Env vars are mocked with `patch.dict("os.environ", {...})`.

**What to Mock:** External/expensive dependencies — the NVIDIA NIM API client (`NIMClient.analyze_image`/`generate_text`), Playwright browser automation (`StealthScout`), agent classes (`VisionAgent`, `GraphInvestigator`, `JudgeAgent`, `SecurityAgent`), subprocess/multiprocessing (`subprocess.Popen`, `mp.Manager`), and config gate functions (`should_use_db_persistence`).

**What NOT to Mock:** The system under test itself and the LangGraph orchestration logic — graph build/compile, routing functions, and node dispatch run for real. The database is **not mocked**; tests use a real in-memory SQLite engine (see Fixtures). Pure logic (`OnionDetector`, `route_after_scout`) is exercised directly with no mocks.

## Fixtures and Factories

**Test Data:** Fixtures defined with `@pytest.fixture` return canonical dict/state shapes; async resources use `@pytest_asyncio.fixture` with `yield` + teardown. Real example — in-memory DB fixture from `backend/tests/test_audit_route_contract.py`:
```python
@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
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
Factory-style module helper functions build large result payloads — e.g. `_sample_result(screenshot_path)` in `backend/tests/test_audit_runner_queue.py` and the `mock_scout_result_dict` / `base_audit_state` fixtures in `elliot/tests/integration/conftest.py`. The langgraph `conftest.py` provides a full set of mock-agent fixtures (`mock_nim_client`, `mock_scout`, `mock_vision_agent`, `mock_graph_investigator`, `mock_judge_agent`, `audit_state`).

**Location:** Co-located `conftest.py` per test directory (`elliot/tests/integration/conftest.py`, `elliot/tests/langgraph_investigation/conftest.py`). One-off factory helpers live as private `_name` functions inside the test file that uses them. `tmp_path` (pytest built-in) is used for filesystem fixtures (`backend/tests/test_audit_runner_queue.py`).

## Coverage

**Requirements:** No coverage tooling configured — `pytest-cov` is not in `elliot/requirements.txt` or `backend/requirements.txt`, and there is no `.coveragerc` or coverage config in `pytest.ini`. There is no enforced coverage threshold.

**View Coverage:** Not available out of the box. If needed, install and run: `pip install pytest-cov` then `python -m pytest --cov=elliot --cov=backend --cov-report=term-missing`.

## Test Types

**Unit Tests:** Pure-logic tests with no I/O or mocks — `elliot/tests/unit/test_onion_detector.py`, `elliot/tests/unit/test_tor_client.py`, `tests/test_link_explorer.py`. Instantiate the class and assert on outputs directly.

**Integration Tests:** Multi-component data-flow and tier-workflow tests under `elliot/tests/integration/` (`test_data_flow.py`, `test_tier_workflows.py`) and the route+DB contract tests in `backend/tests/`. Mark cross-component tests with `@pytest.mark.integration` (registered in `pytest.ini`). These exercise real orchestration/DB with external services mocked.

**E2E Tests:** No automated browser/end-to-end suite. The closest is `elliot/tests/langgraph_investigation/test_02_full_audit_mocked.py`, which runs the *entire* compiled LangGraph (`build_audit_graph().compile().ainvoke(...)`) with all external agents mocked. Truly manual end-to-end checks live as scripts in `testing/scripts/` and are run by hand, not via pytest.

## Common Patterns

**Async Testing:** Decorate with `@pytest.mark.asyncio`, `await` the call, and guard long-running graph executions with `asyncio.wait_for(..., timeout=...)`, calling `pytest.skip(...)` on `asyncio.TimeoutError` rather than failing. Real example from `elliot/tests/langgraph_investigation/test_02_full_audit_mocked.py`:
```python
@pytest.mark.asyncio
async def test_ainvoke_full_audit_mocked(mock_scout, mock_judge_agent, audit_state):
    with patch("elliot.core.orchestrator.NIMClient", return_value=mock_nim_client), \
         patch("elliot.agents.scout.StealthScout", return_value=mock_scout):
        compiled = build_audit_graph().compile()
        try:
            result = await asyncio.wait_for(compiled.ainvoke(audit_state.copy()), timeout=30.0)
            assert result["status"] in ("completed", "error", "aborted")
        except asyncio.TimeoutError:
            pytest.skip("ainvoke() exceeded 30-second timeout.")
```
Background tasks are tested by creating the task, `await asyncio.sleep(0.2)`, then `task.cancel()` / `await task` and asserting on recorded `send.await_args_list` (`backend/tests/test_audit_runner_queue.py::test_reader_maps_progress_events`).

**Error Testing:** Two styles. (1) Inject a failing dependency and assert graceful degradation rather than a raised exception — real example from `test_02_full_audit_mocked.py`:
```python
@pytest.mark.asyncio
async def test_node_error_propagation():
    state = {"url": "https://example.com", "pending_urls": ["https://example.com"],
             "scout_results": [], "scout_failures": 0, "errors": []}
    async def failing_aenter(*args):
        raise ValueError("Simulated Scout initialization failure")
    mock_scout_failing = MagicMock()
    mock_scout_failing.__aenter__ = AsyncMock(side_effect=failing_aenter)
    with patch("elliot.core.orchestrator.StealthScout", return_value=mock_scout_failing):
        result = await scout_node(state)
        assert isinstance(result, dict)  # node catches the error, returns a dict
```
(2) For input validators and config that *should* raise, use `pytest.raises(...)` (e.g. `CircuitBreakerConfig.__post_init__` raising `ValueError`). Prefer asserting on the returned error-status result object when testing agent/orchestrator code, since that layer is designed to catch and report rather than raise.

---
*Testing analysis: 2026-05-14*
