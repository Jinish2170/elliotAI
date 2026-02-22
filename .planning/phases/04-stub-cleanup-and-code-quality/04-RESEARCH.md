# Phase 4: Stub Cleanup & Code Quality - Research

**Researched:** 2026-02-22
**Domain:** Python error handling, stub replacement patterns, code quality analysis
**Confidence:** HIGH

## Summary

This phase investigates best practices for replacing empty return stubs with proper error handling mechanisms. The core challenge is eliminating silent failures by raising `NotImplementedError` (or context-specific exceptions) while ensuring existing callers are analyzed and updated if needed before the change. Research confirms standard Python error handling patterns, pytest exception testing conventions, and grep/ast-based approaches for caller analysis.

**Primary recommendation:** Use pytest.raises() exception testing pattern with appropriate exception types (NotImplementedError for incomplete features, ValueError for bad input, RuntimeError for state issues), search for existing method callers using grep patterns before modifying stubs, and create test fixtures for each stubbed method.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Error handling approach
- Use context-specific error types, not just `NotImplementedError` everywhere
- Common error types to use: `NotImplementedError`, `ValueError` (for bad input), `RuntimeError` (for state issues)
- Error messages should be informative with context + reason (e.g., "validate(): cannot run without initialization")
- Message format varies by method based on complexity — no rigid template, but all messages must be informative

#### Migration considerations
- Apply stub changes atomically (all at once, not gradual)
- Before making changes, search for existing callers of stub methods using grep/ruff
- If existing callers are found, update those callers first before modifying the stub
- If callers expect specific return values from stubs, research whether the method can be fully implemented now (turn stub into real implementation if feasible)

### Claude's Discretion
- Exact error message wording per method
- Which specific error type applies to each stub context
- Callers search methodology (grep patterns, ruff checks, etc.)
- How to present the caller analysis results before proceeding

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CORE-04 | Empty return stubs replaced with NotImplementedError or proper implementations | Standard Python error handling patterns documented below |
| CORE-04-2 | evidence_store.py stubs (lines 207, 250, 309, 327, 351, 362) raise NotImplementedError | FileNotFoundError and IOError appropriate for missing resources; ValueError for invalid input |
| CORE-04-3 | judge.py empty returns (lines 943, 960) raise NotImplementedError | RuntimeError for missing dependencies (vision_result, graph_result) |
| CORE-04-4 | dom_analyzer.py empty returns (lines 318, 345) raise NotImplementedError | Empty returns in conditional branches may be intentional — analyze context |
| CORE-04-5 | dark_patterns.py empty return (line 407) raise NotImplementedError | KeyError/ValueError for invalid category_id - validate input or raise |
| CORE-06-4 | Stub cleanup verified by tests that raise NotImplementedError | pytest.raises() pattern established in existing test suite |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.4.1 | Exception testing framework | Industry standard for Python testing, supports async tests |
| pytest-asyncio | 1.0.0 | Async exception testing | Needed for testing async methods in VERITAS codebase |

### Testing
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| coverage | 7.9.2 | Code coverage for modified stubs | Verify tests cover new exception paths |
| pylint | 3.0.3 | Static analysis for code quality | Option: Lint for unused variables after stub changes |

### Python Runtime
| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11.5 | Runtime environment (not 3.14 as originally documented) |

### Installed Analysis Tools
- ✓ **pylint** (3.0.3): Static code analysis
- ✓ **coverage** (7.9.2): Test coverage reporting
- ✗ **ruff**: Not installed (mentioned in CONTEXT.md but unavailable)
  - **Alternative**: Use grep patterns with Grep tool

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| grep-based caller search | AST analysis with ast module | More robust but higher complexity; grep sufficient for this phase |
| pytest.raises() | try/except in tests | pytest.raises() is idiomatic and test framework integrates |
| NotImplementedError | custom exception classes | NotImplementedError is Python standard; custom exceptions add boilerplate |

**Installation:**
```bash
# All required tools already installed:
# pytest 8.4.1
# pytest-asyncio 1.0.0
# coverage 7.9.2
# pylint 3.0.3
```

## Architecture Patterns

### Recommended Test Structure
```
veritas/tests/
├── test_stub_cleanup.py          # New: Tests for stub cleanup
│   ├── class TestEvidenceStoreStubs
│   │   ├── test_search_similar_table_not_exists
│   │   ├── test_get_all_audits_table_not_exists
│   │   ├── test_json_search_file_not_exists
│   │   ├── test_json_search_exception
│   │   ├── test_json_list_all_file_not_exists
│   │   └── test_json_list_all_exception
│   ├── class TestJudgeStubs
│   │   ├── test_summarize_dark_patterns_no_vision_result
│   │   └── test_summarize_entity_verification_no_graph_result
│   ├── class TestDOMAnalyzerStubs
│   │   ├── test_check_excessive_tracking_fallback
│   │   └── test_check_dark_patterns_css_fallback
│   └── class TestDarkPatternsStubs
│       └── test_get_prompts_for_category_invalid_id
```

### Pattern 1: pytest.raises() Exception Testing
**What:** Test context manager that verifies specific exceptions are raised
**When to use:** Testing that stub methods raise expected exceptions
**Example:**
```python
# Source: Existing pattern in test_security_dataclasses.py and test_ipc_queue.py
import pytest

def test_invalid_composite_score_raises_error(self):
    """Test that composite_score > 1.0 raises ValueError."""
    with pytest.raises(ValueError):
        SecurityResult(url="https://example.com", composite_score=1.5)

def test_queue_full_raises_on_overflow(self):
    """Test that queue.Full is raised when capacity exceeded."""
    with pytest.raises(q_module.Full):
        q.put(999, timeout=0.1)
```

### Pattern 2: Context-Specific Error Messages
**What:** Error messages that include method name, context, and reason for failure
**When to use:** All stub exceptions to aid debugging
**Example:**
```python
def search_similar(self, query: str, k: int = 5, table_name: str = "audits") -> list[dict]:
    """
    [docstring...]
    """
    self._ensure_init()

    if self._db and self._embedder:
        try:
            if table_name not in self._db.table_names():
                raise ValueError(
                    f"search_similar(): table '{table_name}' does not exist. "
                    f"Available tables: {self._db.table_names()}"
                )
            # ... rest of implementation
        except Exception as e:
            raise RuntimeError(f"search_similar(): LanceDB search failed: {e}") from e

    raise NotImplementedError(
        "search_similar(): JSON fallback not implemented. "
        "LanceDB required for similarity search."
    )
```

### Pattern 3: Callers Search with Grep
**What:** Search codebase for method calls before modifying stubs
**When to use:** Before raising exceptions in stub methods
**Example:**
```bash
# Search for all calls to specific methods
grep -rn "search_similar(" veritas/ --include="*.py"
grep -rn "get_all_audits(" veritas/ --include="*.py"
grep -rn "_summarize_dark_patterns(" veritas/ --include="*.py"
```

### Anti-Patterns to Avoid
- **Silent failures:** Empty returns that mask bugs instead of raising exceptions
- **Generic exceptions:** Using bare `raise Exception()` without context
- **Overzealous replacement:** Converting legitimate empty return patterns (like empty defaults) to exceptions
- **Missing caller analysis:** Raising exceptions without checking if callers exist and expect return values

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Method call analysis tool | Custom AST traverser for finding callers | grep patterns with Grep tool | Simpler for this phase; sufficient accuracy |
| Exception testing framework | Custom try/except helpers | `pytest.raises()` context manager | Standard pytest pattern; framework integration |
| Error message templates | Custom template system | F-strings with method name context | Python 3.6+ feature; readable and flexible |
| Coverage checking | Custom test execution wrapper | `pytest --cov veritas` | Built-in pytest integration |

**Key insight:** Python's standard library (inspect, ast) and pytest ecosystem provide all tools needed. Custom solutions add complexity without benefit for stub replacement.

## Common Pitfalls

### Pitfall 1: Misidentifying Valid Empty Returns as Stubs
**What goes wrong:** Converting legitimate empty return patterns (default values, no-op branches) to exceptions, causing regressions
**Why it happens:** Line numbers in requirements may shift; some `return []` or `return None` statements are intentional behavior
**How to avoid:**
1. Read full method context, not just the return line
2. Check if empty return is in a conditional branch (valid fallback)
3. Verify if docstring or comments indicate the behavior is intentional
4. Look at test files to see if empty returns are tested
**Warning signs:**
- Empty returns inside `if` condition checks (likely valid edge cases)
- Return statements within `try/except` blocks (likely error recovery)
- Returns after validation checks (likely "not applicable" scenarios, not bugs)

### Pitfall 2: Breaking Callers Without Analysis
**What goes wrong:** Raising exceptions in stubs breaks existing callers that expect return values
**Why it happens:** Skipping caller search phase as specified in migration considerations
**How to avoid:**
1. Always grep for method calls before modifying returns
2. Check if callers handle exceptions or expect return values
3. If callers exist, update them first OR implement the full method if feasible
**Warning signs:**
- Public methods (no leading underscore) are likely called by other code
- Methods with type hints and return types in signatures are part of public API
- Methods with detailed docstrings are likely intended for external use

### Pitfall 3: Wrong Exception Type for Context
**What goes wrong:** Using `NotImplementedError` everywhere instead of context-specific exceptions
**Why it happens:** Over-simplifying error handling to use one exception type
**How to avoid:**
1. Use `NotImplementedError` for incomplete features only
2. Use `ValueError` for invalid input (e.g., missing file, bad parameter)
3. Use `RuntimeError` for state issues (e.g., database offline, not initialized)
4. Use `IOError`/`FileNotFoundError` for filesystem issues (Python 2 compatibility removed, OSError preferred)
**Warning signs:**
- Validation code that checks parameters → Use ValueError
- Database connection code that checks state → Use RuntimeError
- File operations that check existence → Use FileExistsError/FileNotFoundError

### Pitfall 4: Uninformative Error Messages
**What goes wrong:** Generic error messages like "Not implemented" that don't help debugging
**Why it happens:** Treating exception messages as boilerplate
**How to avoid:**
1. Include method name in message
2. Provide context about what was expected vs. actual
3. Suggest how to fix or what the exception means
**Warning signs:**
- Generic messages like "error", "failed", "not implemented"
- No indication of which method threw the exception
- No suggestion of how to resolve the issue

## Code Examples

Verified patterns from official sources:

### Exception Testing Pattern
```python
# Source: Existing project pattern (test_security_dataclasses.py:187, test_ipc_queue.py:134)
def test_invalid_confidence_raises_error(self):
    """Test that invalid confidence raises ValueError."""
    with pytest.raises(ValueError):
        SecurityFinding(
            category="test",
            severity="medium",
            evidence="Test",
            source_module="test",
            timestamp="2026-02-21T00:00:00Z",
            confidence=1.5,  # Invalid: > 1.0
        )

def test_queue_full_raises_on_overflow(self):
    """Test that queue.Full is raised when capacity exceeded."""
    with pytest.raises(q_module.Full):
        q.put(999, timeout=0.1)
```

### Context-Specific Error Messages (Standard Pattern)
```python
# Source: Python documentation best practices (PEP 8, PEP 3151)
def database_query(self, query: str) -> list[dict]:
    """Execute database query and return results."""
    if not self._connection:
        raise RuntimeError(
            f"database_query(): No active database connection. "
            f"Call initialize() before querying."
        )

    if not self._is_valid_query(query):
        raise ValueError(
            f"database_query(): Invalid query syntax '{query[:50]}...'"
        )

    if self._feature_not_ready:
        raise NotImplementedError(
            "database_query(): Advanced query parsing not yet implemented. "
            "Use simple queries only (SELECT * FROM table)."
        )
```

### Stub Replacement Pattern
```python
# Before: Silent failure
def search_similar(self, query: str, k: int = 5, table_name: str = "audits") -> list[dict]:
    """Search for similar records by embedding similarity."""
    self._ensure_init()

    if self._db and self._embedder:
        if table_name not in self._db.table_names():
            return []  # SILENT FAILURE - BUG MASKING

    # JSON fallback
    return self._json_search(query, k, table_name)

# After: Explicit error
def search_similar(self, query: str, k: int = 5, table_name: str = "audits") -> list[dict]:
    """Search for similar records by embedding similarity."""
    self._ensure_init()

    if self._db and self._embedder:
        if table_name not in self._db.table_names():
            raise ValueError(
                f"search_similar(): Table '{table_name}' does not exist. "
                f"Available tables: {self._db.table_names()}"
            )
        # ... full implementation

    raise NotImplementedError(
        "search_similar(): JSON fallback not implemented. "
        "LanceDB (vector database) required for semantic search."
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Silent `return []` on errors | `raise NotImplementedError` or specific exception | Python 2.x to 3.x transition | Fail-fast debugging vs. masked bugs |
| Try-except with bare `except:` | Specific exception types (ValueError, RuntimeError, NotImplementedError) | PEP 8 guidelines | Better error handling and debugging |
| Generic assert statements | pytest.raises() context manager for exceptions | pytest 2.0+ | Better error messages and test clarity |
| Manual test discovery | pytest auto-discovery with `test_*.py` pattern | pytest standard | Standardized test organization |

**Deprecated/outdated:**
- **Python 2 exception syntax**: `raise ValueError, "message"` (use `raise ValueError("message")`)
- **Bare except clauses**: `except:` (use `except Exception:` for broader catching)
- **Assert statements for testing**: Use pytest.raises() instead of assert for exceptions in tests
- **String-only exception raising**: `raise "error message"` removed in Python 3 (use exception class)

## Open Questions

1. **Valid vs. Stub Empty Returns at Specific Lines**
   - What we know: Line numbers in requirements (e.g., evidence_store.py:207) need verification against current code
   - What's unclear: Whether documented empty returns are actual stubs or legitimate fallback behavior
   - Recommendation: Read each method's full context before deciding to replace return with exception

2. **Caller Search Scope**
   - What we know: Must search for callers before modifying return statements
   - What's unclear: Whether to search only in veritas/ directory or include backend/ and frontend/
   - Recommendation: Start with veritas/ only (backend should use APIs, frontend uses backend), expand if grep shows no veritas/ callers

3. **Test File Organization**
   - What we know: Separate test file (test_stub_cleanup.py) needed for exception tests
   - What's unclear: Whether to integrate with existing test files (test_veritas.py etc.) or keep separate
   - Recommendation: Create separate test_stub_cleanup.py following project pattern (test_ipc_queue.py, test_security_agent.py are separate)

## Sources

### Primary (HIGH confidence)
- Python 3.11 Built-in Exception Documentation - NotImplementedError, ValueError, RuntimeError, OSError hierarchy
- pytest 8.4.1 Documentation - pytest.raises() context manager, exception testing patterns
- pytest-asyncio 1.0.0 Documentation - async exception testing
- Existing project test files - Verified patterns in test_ipc_queue.py, test_security_dataclasses.py, test_security_agent.py

### Secondary (MEDIUM confidence)
- PEP 8 (Style Guide for Python Code) - Exception naming and raising conventions
- PEP 3151 (Reworking the OS and IO exception hierarchy) - OSError subclasses for filesystem errors
- pylint 3.0.3 Documentation - Static analysis for identifying potential issues

### Tertiary (LOW confidence)
- WebSearch for "Python stub cleanup best practices" - General guidance only (verify against project needs)
- WebSearch for "grep pattern for method calls" - Custom patterns may be needed for specific codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified with Python 3.11.5 runtime and pip list
- Architecture: HIGH - Verified with existing test patterns (test_ipc_queue.py, test_security_dataclasses.py)
- Pitfalls: HIGH - Derived from Python documentation best practices and common anti-patterns

**Research date:** 2026-02-22
**Valid until:** 60 days (Python error handling is stable; pytest patterns rarely change)
