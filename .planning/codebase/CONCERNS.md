# Codebase Concerns

**Analysis Date:** 2026-02-19

## Tech Debt

### Missing SecurityAgent Class
**Issue:** Security analysis is implemented as a function instead of a class-based agent, breaking the agent architecture pattern.

**Files:**
- `veritas/core/orchestrator.py` (lines 636-718): `security_node()` is a standalone async function
- `veritas/analysis/security_headers.py`: Contains `SecurityHeaderAnalyzer` class but used imperatively
- `veritas/analysis/phishing_checker.py`: Contains `PhishingChecker` class but used imperatively
- `veritas/analysis/redirect_analyzer.py`: Contains `RedirectAnalyzer` class but used imperatively

**Impact:** The security functionality doesn't follow the agent pattern used by Scout, Vision, GraphInvestigator, and Judge. This makes the codebase inconsistent, harder to extend, and harder to test. The security modules exist as classes but are instantiated and called directly within a function rather than being managed through a proper agent lifecycle.

**Fix approach:** Create a `SecurityAgent` class in `veritas/agents/security_agent.py` that follows the same pattern as `VisionAgent` and `JudgeAgent`, with an async `analyze()` method and proper results serialization. The `security_node()` function should then instantiate and call this agent.

---

### Fragile Subprocess Stdout Parsing
**Issue:** Communication between the backend and veritas subprocess depends on parsing stdout for a specific `##PROGRESS:` marker prefix. This is fragile, non-standard, and breaks easily if subprocess output includes unexpected content.

**Files:**
- `backend/services/audit_runner.py` (lines 133-139): Parses `##PROGRESS:` markers from subprocess stdout
- `veritas/ui/app.py` (line 610): Same pattern used in Streamlit UI
- `veritas/core/orchestrator.py` (line 985): Emits markers via `print(f"##PROGRESS:{_json.dumps(msg)}", flush=True)`

**Impact:** If the subprocess emits any JSON that happens to start with `{`, the parser can misinterpret it as result data. If any subprocess output contains the `##PROGRESS:` prefix naturally, it will cause parsing errors. The fallback JSON extraction (lines 489-511 of audit_runner.py) attempts to recover but is itself fragile. Any changes to logging output or subprocess behavior can break the entire audit pipeline.

**Fix approach:** Replace stdout marker parsing with a proper IPC mechanism. Options include:
1. Use a temporary JSON output file (already partially implemented with `--output` flag)
2. Use a SQLite database for progress/status updates
3. Use a named pipe or Unix socket for structured communication
4. Use a proper message queue like Redis

---

### Sequential Execution Instead of LangGraph State Machine
**Issue:** The `VeritasOrchestrator.audit()` method manually executes nodes sequentially instead of using the compiled LangGraph state machine, defeating the purpose of using LangGraph.

**Files:**
- `veritas/core/orchestrator.py` (lines 929-1113): The `audit()` method contains an explicit for-loop that calls `scout_node()`, `security_node()`, `vision_node()`, `graph_node()`, and `judge_node()` in sequence
- `veritas/core/orchestrator.py` (lines 861-906): The `build_audit_graph()` function builds a proper LangGraph StateGraph but it's never used via `ainvoke()`

**Impact:** The entire LangGraph infrastructure is dead code. The routing functions (`route_after_scout()`, `route_after_judge()`) are still called manually. This loses the benefits of LangGraph's state management, visualization, and debugging tools. It also makes it harder to support parallel execution or true graph-based workflows in the future.

**Fix approach:** Refactor `VeritasOrchestrator.audit()` to use the compiled graph's `ainvoke()` method. The current sequential execution was likely a workaround for Python 3.14 asyncio issues. The proper fix is to resolve the underlying async cancellation issue rather than abandoning LangGraph's execution model.

---

### v2 Page is Just a Redirect
**Issue:** The v2 page at `frontend/src/app/v2/page.tsx` contains only a redirect to the root page, serving no functional purpose.

**Files:**
- `frontend/src/app/v2/page.tsx`: Contains `redirect("/")` in a Next.js page component

**Impact:** The `/v2` route is non-functional. Users accessing it are silently redirected with no explanation. This pollutes the route structure and may indicate abandoned feature work.

**Fix approach:** either remove the `/v2` route entirely or implement the intended v2 functionality. If redirecting is desired, use HTTP-level redirects rather than page-level redirects.

---

### In-Memory Audit Storage
**Issue:** Audit results are stored only in a process-local dictionary, lost on restart or failure.

**Files:**
- `backend/routes/audit.py` (line 19): `_audits: dict[str, dict] = {}` is the only storage mechanism
- `backend/routes/audit.py` (lines 84-86): Results are only stored in memory during WebSocket session

**Impact:** No audit history persists between backend restarts. No way to review past audits or build analytics. Critical audit evidence is ephemeral.

**Fix approach:** Implement persistent storage using:
1. SQLite for simple persistence (easiest, file-based)
2. PostgreSQL for production deployments
3. Document schema for audit results, status, and metadata

---

### Empty Return Stubs
**Issue:** Multiple functions return empty lists/dicts with no implementation, indicating incomplete features.

**Files:**
- `veritas/agents/judge.py` (lines 943, 960): Returns `[]` in unimplemented code paths
- `veritas/agents/graph_investigator.py` (lines 706, 1068): Returns `[]` and `{}`
- `veritas/config/dark_patterns.py` (line 407): Returns `[]`
- `veritas/core/evidence_store.py` (lines 207, 250, 309, 327, 351, 362): Multiple `[]` returns
- `veritas/analysis/dom_analyzer.py` (lines 318, 345): Returns `[]`

**Impact:** These empty returns mask runtime issues and make debugging harder. Functions fail silently. May indicate incomplete dark pattern detection and evidence collection features.

**Fix approach:** Either implement the missing logic or raise `NotImplementedError` with clear messages to prevent silent failures.

---

## Security Considerations

### No Root .env File
**Issue:** The project root has no `.env` file. The main `.env` is at `veritas/.env` but the root-level directory structure expects environment variables at the project root.

**Files:**
- `.gitignore` (lines 44-45): `.env` and `.env.*` are ignored at the root level
- `veritas/.env`: Exists but may be overlooked
- Root directory: No `.env` file present

**Impact:** Developers must discover that `.env` should be created at the project root (not in `veritas/`). Configuration is unclear and error-prone. The `veritas/.env.template` exists but template files should be at the root for standard Python project conventions.

**Current mitigation:** `veritas/.env` file exists and is gitignored. `veritas/.env.template` provides example configuration.

**Recommendations:**
1. Create `veritas/.env.example` at project root with standard naming
2. Add README or CONTRIBUTING.md explaining environment setup
3. Consider consolidating configuration to root-level `.env.example`

---

### Hardcoded Secrets in Comments
**Issue:** Some files may contain comments or example code that hints at secret configuration.

**Files:** No immediate hardcoded secrets found, but `veritas/.env` contains actual secrets (NVIDIA_NIM_API_KEY, TAVILY_API_KEY, etc.)

**Risk:** Secrets are committed if `.env` is accidentally added to git. The `.gitignore` protects this, but there's no pre-commit hook to prevent accidental environment file commits.

**Current mitigation:** `.gitignore` excludes `.env` files. No pre-commit hooks enforce this.

**Recommendations:**
1. Add pre-commit hook to reject commits with environment files containing patterns like `API_KEY=`, `SECRET=`, `TOKEN=`
2. Use `.env.example` with placeholder values only
3. Document secret management in project README

---

### Subprocess Injection Risk
**Issue:** While the current implementation uses `subprocess.Popen` with proper argument lists (not shell strings), the stdout parsing pattern could be vulnerable if command arguments are ever user-controlled.

**Files:**
- `backend/services/audit_runner.py` (lines 72-81): Constructs subprocess command from URL input

**Impact:** Currently mitigated by using proper list-based argument passing, but any future migration to shell=True would introduce command injection. The URL validation is minimal.

**Current mitigation:** Uses `subprocess.Popen` with argument list, not shell string.

**Recommendations:**
1. Add URL validation regex before subprocess execution
2. Consider using `shlex.quote()` if URLs ever need shell escaping
3. Add integration tests with malicious URL patterns to ensure safety

---

## Performance Bottlenecks

### Sequential Node Execution
**Problem:** All agent runs happen sequentially with no parallelism possible.

**Files:**
- `veritas/core/orchestrator.py` (lines 995-1068): Each await blocks until completion

**Impact:** The audit process cannot take advantage of multiple cores or concurrent operations. Vision and Graph analysis could potentially run in parallel since they don't depend on each other's outputs. Total audit time is the sum of all phase times rather than the maximum of independent phases.

**Improvement path:** Use LangGraph's proper state machine to enable parallel execution of independent nodes. Consider running Vision and Graph in parallel once Scout and Security complete.

---

### Blocking stdout.readline() Calls
**Problem:** The audit runner uses blocking reads from subprocess stdout wrapped in thread pool executor.

**Files:**
- `backend/services/audit_runner.py` (lines 123-126): Each `readline()` blocks in thread pool

**Impact:** While execution is offloaded to threads, the blocking I/O pattern can limit throughput. High concurrency on the audit endpoint could lead to many thread pool threads waiting on subprocess I/O.

**Improvement path:** Use asyncio-native subprocess communication (though this requires Python 3.14 compatibility fix). Alternatively, use a proper message queue for non-blocking progress updates.

---

### No Caching of External API Calls
**Problem:** Phishing checks and other external API lookups happen on every audit with no caching.

**Files:**
- `veritas/analysis/phishing_checker.py` (lines 100-108): Makes API calls on every check
- `veritas/agents/graph_investigator.py`: Tavily search calls on every graph analysis

**Impact:** Repeated audits of the same URL waste API quota and time. The same phishing database results are fetched multiple times unnecessarily.

**Current state:** No caching mechanism detected.

**Improvement path:** Implement a URL-based cache with TTL (e.g., Redis or SQLite) for API results. Cache key should be normalized URL.

---

## Fragile Areas

### audit_runner.py - Subprocess Communication Pattern
**Files:** `backend/services/audit_runner.py`

**Why fragile:**
1. Depends on exact `##PROGRESS:` marker prefix (line 133)
2. Falls back to regex-based JSON extraction if streaming parse fails (lines 489-511)
3. Has to handle buffer management for multi-line JSON (lines 140-151)
4. Thread pool executor complexity for Windows compatibility (lines 94-100)

**Safe modification:**
1. Add comprehensive logging around all subprocess I/O operations
2. Add timeout to subprocess subprocess calls (currently exists but inconsistent)
3. Test with various subprocess outputs including edge cases (empty output, malformed JSON, mixed log lines)

**Test coverage gaps:** No unit tests for the stdout parsing logic. Integration testing depends on running actual subprocess which makes CI difficult.

---

### orchestrator.py - Manual State Machine Execution
**Files:** `veritas/core/orchestrator.py` (lines 929-1113)

**Why fragile:**
1. Manually replicates LangGraph routing logic
2. State updates are manual and error-prone
3. No graph visualization or debugging tools available
4. Budget checking logic embedded throughout (lines 1007-1009, 1071-1088)

**Safe modification:**
1. Add validation after each state update
2. Log state transitions comprehensively
3. Add metrics for each phase duration
4. Consider adding checkpointing for resume capability

**Test coverage gaps:** The manual execution path is not tested separately from the node implementations. Edge cases like max iteration exhaustion, page budget limits, and retry logic have limited coverage.

---

### Subprocess Python Discovery
**Files:** `backend/services/audit_runner.py` (lines 28-40), `veritas/ui/app.py` (lines 547-556)

**Why fragile:**
1. Platform-specific Python executable discovery
2. Multiple fallback paths that may point to wrong interpreter
3. No validation that discovered Python has required dependencies

**Safe modification:**
1. Add validation that discovered Python can import required modules
2. Cache discovered path after verification
3. Add clear error message if suitable Python cannot be found

**Test coverage gaps:** Not tested across different Python installation scenarios.

---

## Scaling Limits

### In-Memory Audit Storage
**Current capacity:** Memory only, limited by server RAM

**Limit:** Crash or out-of-memory with large number of concurrent/completed audits. Historical audits are lost on restart.

**Scaling path:** Implement database persistence (SQLite → PostgreSQL). This also enables history exploration and analytics.

---

### Single-Process Backend
**Current capacity:** One FastAPI process

**Limit:** Gunicorn/uWSGI worker processes would each have separate `_audits` dictionary, causing inconsistent state.

**Scaling path:** Use Redis or PostgreSQL for shared audit state. Enable multi-worker deployments.

---

### Blocking Subprocess per Audit
**Current capacity:** One subprocess per concurrent audit

**Limit:** Each audit spawns a Python subprocess, consuming significant memory and CPU. High concurrent audits (10+) would overwhelm system resources.

**Scaling path:**
1. Distribute audits to worker nodes (task queue architecture)
2. Use connection pooling for Playwright browsers
3. Limit per-server concurrency using a semaphore

---

## Dependencies at Risk

### Python 3.14 AsyncIO Compatibility
**Risk:** LangGraph `ainvoke()` raises `CancelledError` on Python 3.14

**Files:** Comment in `veritas/core/orchestrator.py` (line 939): "This bypasses LangGraph's ainvoke to avoid Python 3.14 asyncio CancelledError issues"

**Impact:** The documented workaround (sequential execution) sacrifices LangGraph benefits. This is a temporary fix that may become obsolete or worse with Python version updates.

**Migration plan:**
1. Monitor LangGraph for Python 3.14 compatibility fixes
2. Consider alternative state machine libraries if LangGraph doesn't resolve the issue
3. Consider pinning Python version if compatibility cannot be achieved

---

### Playwright Browser Driver Updates
**Risk:** Playwright browser binaries get out of sync with Python package

**Files:** `veritas/agents/scout.py` (lines 232-247): Browser launch configuration

**Impact:** If Playwright version mismatches occur, browser launches fail silently or with cryptic errors. Browser features may break.

**Migration plan:** Pin Playwright version in requirements. Add check on startup to verify browser driver availability.

---

### External API Dependencies (NVIDIA NIM, Tavily)
**Risk:** API quotas, rate limits, or service outages

**Files:**
- `veritas/core/nim_client.py`: NVIDIA NIM client
- `veritas/agents/graph_investigator.py`: Tavily search integration

**Impact:**
- NIM down: Vision analysis fails, entire audit degrades
- Tavily down: Entity verification fails, trust score may be incomplete
- API key revocation: Silent failures or partial results

**Current mitigation:** Graceful degradation with fallback scores (e.g., `visual_score = 0.5` on Vision failure)

**Migration plan:**
1. Implement circuit breaker pattern for API calls
2. Add cached fallback data for critical APIs
3. Provide clear error messages when APIs are unavailable

---

## Missing Critical Features

### Audit Result Persistence
**Problem:** All audit data is lost on backend restart. No historical audit capability.

**Blocks:**
- Audit history and comparison
- Analytics and trend analysis
- Regression testing of trust scores
- Investigating past suspicious sites

**Priority:** High - critical for production use

---

### User Authentication
**Problem:** No authentication system. Anyone can start audits and access results.

**Blocks:**
- Multi-tenant deployment
- Rate limiting per user
- Audit ownership and privacy
- API access control

**Priority:** Medium - needed for hosted deployment

---

### Webhook/Hook System
**Problem:** No way to integrate audit results with external systems.

**Blocks:**
- CI/CD integration (audit on deploy)
- Alerting on high-risk findings
- Result archival and compliance logging
- Custom report generation

**Priority:** Low - convenience feature

---

### Rate Limiting
**Problem:** No protection against abuse. Unlimited concurrent audits possible.

**Blocks:**
- Production stability
- Cost control (API usage)
- Fair resource allocation

**Priority:** Medium - production stability

---

## Test Coverage Gaps

### Subprocess Communication Tests
**What's not tested:**
- `##PROGRESS:` marker parsing with malformed JSON
- Fallback JSON extraction edge cases
- Multi-line JSON buffer handling
- stderr drain functionality with large error output
- Process timeout and cleanup

**Files:** `backend/services/audit_runner.py`

**Risk:** Bugs in stdout parsing logic cause silent audit failures or incorrect results.

**Priority:** High - critical for audit reliability

---

### Agent Logic Unit Tests
**What's not tested:**
- Judge decision logic edge cases
- Vision agent fallback mode behavior
- Graph investigator timeout handling
- Scout retry logic

**Files:** `veritas/agents/justice.py`, `veritas/agents/vision.py`, `veritas/agents/graph_investigator.py`, `veritas/agents/scout.py`

**Risk:** Incorrect trust scores, missed dark patterns, or crashes on edge cases.

**Priority:** High - affects audit accuracy

---

### Integration Tests
**What's not tested:**
- Full audit pipeline end-to-end
- WebSocket event sequence correctness
- Frontend-backend communication
- Error recovery and cleanup

**Risk:** Integration issues discovered only in production.

**Priority:** Medium - production readiness

---

*Concerns audit: 2026-02-19*
