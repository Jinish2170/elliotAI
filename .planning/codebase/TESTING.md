# Testing Patterns

**Analysis Date:** 2026-02-19

## Test Framework

**Runner:**
- **pytest** [>=7.4.0] configured in `veritas/requirements.txt`

**Async Support:**
- **pytest-asyncio** [>=0.23.0] for async test cases

**Assertion Library:**
- Built-in pytest assertions

**Config:**
- No explicit `pytest.ini`, `pyproject.toml`, or `setup.cfg` found
- Default pytest configuration used

**Run Commands:**
```bash
# Run all tests
cd veritas && python -m pytest tests/ -v

# Direct file execution (from test file itself)
python veritas/tests/test_veritas.py

# With pytest-asyncio (no explicit config, relies on auto-detection)
pytest tests/ -v --tb=short
```

## Test File Organization

**Location:**
- Tests located in `veritas/tests/` directory

**Naming:**
- `test_*.py` pattern for test modules (e.g., `test_veritas.py`)

**Structure:**
```
veritas/
├── agents/
│   ├── scout.py
│   ├── vision.py
│   ├── judge.py
│   └── graph_investigator.py
├── analysis/
│   ├── dom_analyzer.py
│   ├── pattern_matcher.py
│   └── ...
├── config/
│   ├── dark_patterns.py
│   ├── trust_weights.py
│   └── settings.py
├── core/
│   ├── nim_client.py
│   ├── evidence_store.py
│   └── orchestrator.py
├── reporting/
│   └── report_generator.py
└── tests/
    ├── __init__.py
    └── test_veritas.py
```

**Co-location:**
- NOT co-located; tests are in separate `tests/` directory
- Test data files referenced: `test_sites_dir()` fixture points to `tests/sites` path

## Test Structure

**Suite Organization:**

Tests are organized into test class groups, with a mix of unit and integration tests:

```python
# ============================================================
# 1. Config Module Tests
# ============================================================

class TestDarkPatterns:
    """Test dark_patterns.py taxonomy integrity."""
    def test_taxonomy_structure(self):
        from config.dark_patterns import DARK_PATTERN_TAXONOMY
        assert len(DARK_PATTERN_TAXONOMY) == 5

    def test_vlm_prompts_present(self):
        from config.dark_patterns import get_all_vlm_prompts
        prompts = get_all_vlm_prompts()
        assert len(prompts) > 10

class TestSettings:
    """Test settings.py configuration."""
    def test_paths_exist(self):
        from config import settings
        assert settings.BASE_DIR.exists()

# ============================================================
# 2. Analysis Module Tests
# ============================================================

class TestPatternMatcher:
    """Test pattern_matcher.py logic."""
    def test_prompt_generation(self):
        from analysis.pattern_matcher import PatternMatcher
        pm = PatternMatcher()
        prompts = pm.get_screenshot_prompts()
        assert len(prompts) > 5

class TestTemporalAnalyzer:
    """Test temporal_analyzer.py (no screenshots needed for unit tests)."""
    def test_timer_to_seconds(self):
        from analysis.temporal_analyzer import TemporalAnalyzer
        ta = TemporalAnalyzer()
        assert ta._timer_to_seconds("05:30") == 330

# ============================================================
# 3. Core Module Tests
# ============================================================

class TestEvidenceStore:
    """Test evidence_store.py with JSON fallback."""
    def test_json_fallback(self, tmp_path):
        from core.evidence_store import EvidenceStore
        # test logic with patched settings

# ============================================================
# 4. Reporting Tests
# ============================================================

class TestReportGenerator:
    """Test report_generator.py."""
    def test_context_building(self):
        from reporting.report_generator import ReportGenerator
        gen = ReportGenerator()
        ctx = gen._build_context(mock_result, ...)
        assert ctx["trust_score"] == 35
```

**Patterns:**

**Setup pattern:**
- No explicit `setUp()` or `setup_method()` used
- Test fixtures used for setup (pytest features)
- Some tests use `tmp_path` fixture for temporary directories

**Teardown pattern:**
- Cleanup handled by pytest's `tmp_path` fixture (auto-cleanup)
- No manual cleanup code needed in tests

**Assertion pattern:**
- Direct assertions: `assert len(DARK_PATTERN_TAXONOMY) == 5`
- Type-specific: `assert category in DARK_PATTERN_TAXONOMY`
- Numeric range: `assert result.final_score >= 90`
- Collection assertions: `assert len(prompts) > 10`

## Mocking

**Framework:**
- `unittest.mock` (MagicMock, AsyncMock, patch)

**Patterns:**

**Mock fixture:**
```python
@pytest.fixture
def mock_nim_client():
    """Create a mock NIM client that returns controlled responses."""
    client = MagicMock()
    client.analyze_image = AsyncMock(return_value={
        "detected": True,
        "category": "false_urgency",
        "sub_type": "fake_countdown",
        "confidence": 0.85,
        "description": "Countdown timer detected that appears to reset",
    })
    client.generate_text = AsyncMock(return_value="This website shows signs of deceptive practices.")
    client.call_count = 0
    client.cache_hits = 0
    client.fallback_count = 0
    return client
```

**Patch settings:**
```python
def test_json_fallback(self, tmp_path):
    # Force JSON-only mode by using a temp directory
    with patch("config.settings.VECTORDB_DIR", tmp_path / "vectordb"), \
         patch("config.settings.EVIDENCE_DIR", tmp_path / "evidence"):
        (tmp_path / "evidence").mkdir()
        from core.evidence_store import EvidenceStore
        store = EvidenceStore()
        # test logic...
```

**What to Mock:**
- External APIs (NIM VLM/LLM): `mock_nim_client` fixture for `analyze_image`, `generate_text`
- File system paths: settings paths to use `tmp_path` for isolation
- Network-dependent operations: use `patch` to avoid actual calls

**What NOT to Mock:**
- Pure Python logic (e.g., `TrustScore.compute_trust_score()`) tested directly
- Data model serialization (tested with actual data)
- JSON parsing (use actual JSON strings)

## Fixtures and Factories

**Test Data:**

**Fixture-based data:**
```python
@pytest.fixture
def test_sites_dir():
    """Path to test HTML sites."""
    return Path(__file__).parent / "sites"
```

**Mock result construction:**
```python
mock_result = {
    "url": "https://test.com",
    "judge_decision": {
        "trust_score_result": {
            "final_score": 35,
            "risk_level": "high_risk",
            "sub_signals": {},
            "overrides_applied": [],
        },
        "narrative": "Test narrative",
        "recommendations": ["Stop using dark patterns"],
    },
    "vision_result": {"findings": []},
    "graph_result": {"verifications": [], "inconsistencies": [], "domain_intel": {}},
    "iteration": 1,
}
```

**Direct object construction:**
```python
def test_perfect_score(self):
    from config.trust_weights import SubSignal, compute_trust_score

    signals = {
        "visual": SubSignal(name="visual", raw_score=1.0, confidence=1.0),
        "structural": SubSignal(name="structural", raw_score=1.0, confidence=1.0),
        "temporal": SubSignal(name="temporal", raw_score=1.0, confidence=1.0),
        "graph": SubSignal(name="graph", raw_score=1.0, confidence=1.0),
        "meta": SubSignal(name="meta", raw_score=1.0, confidence=1.0),
        "security": SubSignal(name="security", raw_score=1.0, confidence=1.0),
    }
    result = compute_trust_score(signals)
    assert result.final_score >= 90
    assert result.risk_level.value == "trusted"
```

**Location:**
- Fixtures defined within test file (not in separate conftest.py)
- No dedicated fixtures directory found

## Coverage

**Requirements:** None enforced (no coverage tool configured)

**View Coverage:**
- No coverage command found in codebase
- No coverage badge or CI configuration found

**Test Types:**

**Unit Tests:**
- Scope: Individual module logic without external dependencies
- Examples:
  - Config validation (taxonomy structure, prompt availability)
  - Type conversion (timer string to seconds)
  - Score computation logic
  - JSON response parsing

**Integration Tests:**
- Scope: Module chains with mocked external dependencies
- Examples:
  - Evidence storage with path patches
  - Report generator context building with mock data

**End-to-End Tests:**
- Framework: None detected
- Browser automation tests not in test suite (would need Playwright)
- No e2e tests for full audit pipeline

## Common Patterns

**Async Testing:**
```python
# AsyncMock for async methods
client.analyze_image = AsyncMock(return_value={...})
client.generate_text = AsyncMock(return_value="Text response")
```

**Error Testing:**
```python
def test_override_no_ssl(self):
    signals = {...}
    result = compute_trust_score(signals, ssl_status=False)
    assert result.final_score <= 50
    assert len(result.overrides_applied) > 0
```

**Negative Testing:**
```python
def test_vlm_response_parsing_negative(self):
    pm = PatternMatcher()
    finding = pm.parse_vlm_response(
        "No dark patterns detected in this image.",
        "false_urgency", "fake_countdown",
    )
    assert finding is None
```

**Edge Case Testing:**
```python
def test_timer_to_seconds(self):
    ta = TemporalAnalyzer()
    assert ta._timer_to_seconds("05:30") == 330
    assert ta._timer_to_seconds("01:00:00") == 3600
    assert ta._timer_to_seconds("invalid") is None  # Invalid input
```

**Direct file execution:**
```python
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

### Known Testing Gaps (based on codebase exploration)

**Untested or Partially Tested Areas:**

1. **Agent orchestration (`orchestrator.py`)** - No tests for the full audit graph state machine
2. **Browser automation (`scout.py`)** - Tests would require Playwright fixture setup
3. **Vision agent temporal analysis** - Requires screenshot pairs for full testing
4. **Graph investigator network operations** - WHOIS, DNS, SSL checks would require mocking
5. **WebSocket streaming in backend** - No FastAPI WebSocket tests
6. **Frontend React components** - No Jest/React Testing Library setup found
7. **TypeScript store logic** - No unit tests for Zustand store

**Priority Considerations:**
- Higher priority: Core scoring logic (trust_weights), parsing logic (pattern_matcher, vision response parsing)
- Lower priority: Full integration tests (expensive to set up, fragile)

---

*Testing analysis: 2026-02-19*
