# Codebase Concerns
**Analysis Date:** 2026-03-16

## Tech Debt

### Data Forwarding Issue in Frontend
**Issue:** Backend fields not forwarded to audit result event
**Files:** `frontend/src/lib/types.ts` (line 820)
**Impact:** Frontend cannot display dual_verdict and trust_score_result fields from judge_decision
**Fix approach:** Wire the missing fields from backend `judge_decision` to the `audit_result` WebSocket event emission in `backend/services/audit_runner.py`

### MarketPlace Feed Test Failures
**Issue:** Pytest fixture configuration errors for marketplace feed tests
**Files:** `veritas/tests/unit/test_marketplace_feeds.py`
**Impact:** 8+ marketplace and Tor2Web test failures due to "fixture 'mock_open' not found" - the `@patch("builtins.open", MagicMock())` decorator is not properly injected into pytest's fixture scope
**Fix approach:** Convert the patch decorator to a pytest fixture or use dependency injection in the test setup

### Database State Concurrency Issues
**Issue:** SQLite shared memory and write-ahead log files modified
**Files:** `backend/data/veritas_audits.db-shm`, `backend/data/veritas_audits.db-wal`
**Impact:** Database may have uncommitted transactions or corruption from concurrent access. These are binary artifacts that should not be tracked in git
**Fix approach:**
- Add `*.db-shm` and `*.db-wal` to `.gitignore`
- Implement proper database connection pooling or WAL mode handling
- Ensure all database operations use context managers or proper session lifecycle

## Known Bugs

### Tor2Web De-Anonymization Detection Failures
**Symptoms:** Multiple test failures in `test_marketplace_feeds.py` for Tor2Web detection:
- `test_is_tor2web_url_detects_gateway` - FAILED
- `test_query_detects_gateway` - FAILED
- `test_query_multiple_gateways` - FAILED
- `test_check_headers_with_referrer_gateway` - FAILED
- `test_check_headers_with_forwarded_for` - FAILED
**Files:** `veritas/tests/unit/test_marketplace_feeds.py`, `veritas/osint/sources/tor2web.py`, `veritas/osint/sources/tor2web_deanon.py`
**Trigger:** Running marketplace feed tests
**Workaround:** None identified - detection logic needs review

### Marketplace Threat Data Query Failures
**Symptoms:** Tests return ERROR for:
- `test_queries_known_onion` for AlphaBay, Hansa, Empire, Dream, WallStreet
- `test_marketplace_threat_data_creation` - FAILED
- `test_to_dict_conversion` - FAILED
**Files:** `veritas/tests/unit/test_marketplace_feeds.py`, `veritas/osint/sources/marketplace_feeds.py`
**Trigger:** Querying marketplace threat data sources
**Workaround:** Tests are failing at setup phase due to fixture issues

## Security Considerations

### Hardcoded API Key Handling
**Risk:** API keys potentially loaded from environment variables but no validation
**Files:** `veritas/config/settings.py`, `veritas/agents/graph_investigator.py`
**Current mitigation:** Uses settings module that loads from environment
**Recommendations:**
- Add runtime validation for required API keys (Tavily, OpenAI, etc.)
- Implement API key presence checks before attempting to use clients
- Add secrets rotation mechanism documentation
- Consider using a secrets manager service

### Network Requests to Third-Party Services
**Risk:** Multiple external API integrations (AbuseIPDB, Tavily, darknet marketplaces)
**Files:** `veritas/osint/sources/`, `veritas/agents/graph_investigator.py`
**Current mitigation:** Rate limiting implemented with exponential backoff in most sources
**Recommendations:**
- Add request validation/sanitization to prevent injection attacks
- Implement timeouts (some async timeouts configured, but not comprehensive)
- Add request logging for audit trail
- Consider implementing certificate pinning for known APIs

### Sensitive Form Detection
**Risk:** Agent detects and flags forms posting sensitive data (passwords, credit cards)
**Files:** `veritas/agents/graph_investigator.py` (lines 1254-1262)
**Current mitigation:** Detection logic exists but evidence storage may need encryption
**Recommendations:** Ensure evidence store uses encrypted file storage for sensitive indicators

## Performance Bottlenecks

### Multi-Agent Orchestration Overhead
**Problem:** LangGraph orchestration may have significant overhead for parallel agent execution
**Files:** `veritas/core/orchestrator.py`, `veritas/agents/graph_investigator.py`
**Cause:** Sequential agent execution with complex state management; no parallel execution optimization observed
**Improvement path:**
- Evaluate parallel agent execution where agents are independent
- Profile orchestrator overhead vs agent execution time
- Implement agent result caching to avoid redundant calls

### Vector Database Operations
**Problem:** LanceDB with sentence-transformers model loading (MiniLM-L6-v2 ~90MB)
**Files:** `veritas/agents/graph_investigator.py` (RAG implementation)
**Cause:** Loading large embedding model per request without caching
**Improvement path:**
- Implement persistent vector DB client pooling
- Add embedding result caching at query level
- Consider using GPU acceleration if available

### Adaptive Timeout Calculation
**Problem:** Complexity analyzer extracts 15 metrics per analysis - may add latency
**Files:** `veritas/core/complexity_analyzer.py`, `veritas/core/timeout_manager.py`
**Cause:** Running complexity analysis on every audit adds computational overhead
**Improvement path:**
- Cache complexity analysis results for repeated audits
- Implement lazy complexity evaluation (only when timeout issues occur)

## Fragile Areas

### Marketplace Feed Data Files
**Files:** `veritas/data/marketplace_threat_data.json`, `veritas/data/*.json`
**Why fragile:** JSON data files loaded at runtime; file not found or malformed JSON causes failures
**Safe modification:** Add error handling with fallback to empty result on file read failures; add JSON schema validation on load
**Test coverage:** Current tests mock the file I/O but don't test malformed JSON handling

### Tor2Web Detection Logic
**Files:** `veritas/osint/sources/tor2web_deanon.py`, `veritas/analysis/security/tor2web.py`
**Why fragile:** Relies on HTTP header patterns that change frequently (referrer, forwarded-for headers)
**Safe modification:** Make detection pattern matching configurable; add version tracking for pattern updates
**Test coverage:** Test failures indicate logic may need updates

### Darknet Marketplace Integration
**Files:** `veritas/osint/sources/darknet_alpha.py`, `veritas/osint/sources/darknet_hansa.py`, etc.
**Why fragile:** Direct HTTP requests to onion services without proxy rotation or error recovery
**Safe modification:** Implement persistent Tor proxy with circuit rotation; add retry with different guards
**Test coverage:** Tests currently use mock data; no real endpoint testing

## Scaling Limits

### WebSocket Progress Streaming
**Current capacity:** Based on token-bucket rate limiting in `ProgressEmitter`
**Limit:** Single broadcast to all connected clients; no per-client control demonstrated
**Scaling path:** Implement per-client subscription management with backpressure handling; add message batching for high-frequency updates

### Agent Result Storage
**Current capacity:** SQLite database for audit persistence; evidence in filesystem
**Limit:** Single-file SQLite will have write contention under concurrent audits; filesystem storage not designed for multi-node deployment
**Scaling path:** Implement PostgreSQL with connection pooling; use cloud object storage (S3) for evidence

## Dependencies at Risk

### LangChain/LangGraph
**Risk:** Both at >=0.3.0/0.2.0 respectively; these are fast-moving libraries with frequent breaking changes
**Impact:** Upgrades may break existing orchestrator or agent patterns
**Migration plan:**
- Pin to specific minor versions in requirements.txt
- Implement comprehensive integration tests to catch breaking changes early
- Monitor LangChain changelog for security patches

### Playwright
**Risk:** Browser automation library at >=1.40.0
**Impact:** Browser compatibility issues may cause test failures or security vulnerabilities
**Migration plan:**
- Regularly update to latest stable versions
- Implement browser binary caching strategy
- Monitor CVE notifications

### Sentence-Transformers
**Risk:** Model loading from cloud (HuggingFace); network dependency
**Impact:** If HuggingFace is unavailable, all RAG operations fail
**Migration plan:**
- Download and cache models locally
- Implement fallback to simpler embeddings if model unavailable

## Missing Critical Features

### Error Recovery for Partial Agent Failures
**Problem:** Full audit fails if single agent fails; no graceful degradation
**Files:** `veritas/core/orchestrator.py`
**Blocks:** Production use where resilience is critical

### Audit Result Diff/Calculation Logic
**Problem:** Audit delta calculation assumes valid data and proper sorting
**Files:** `backend/routes/audit.py` (lines 323-326)
**Blocks:** Historical audit comparison and trend analysis

### Comprehensive Health Checks
**Problem:** No health endpoint for verifying dependencies (DB, VectorDB, APIs)
**Blocks:** Production deployment monitoring and deployment automation

## Test Coverage Gaps

### MarketPlace Feed Integration Tests
**What's not tested:**
- Real marketplace endpoint connectivity
- Malformed JSON handling in data files
- Rate limiting behavior under load
**Files:** `veritas/tests/unit/test_marketplace_feeds.py`
**Risk:** Integration failures won't be caught until production
**Priority:** High

### Security Analysis Module Tests
**What's not tested:**
- Cross-site scripting (XSS) detection in JavaScript analyzer
- Form analysis validation
- OWASP-specific rule coverage
**Files:** `veritas/analysis/security/owasp/*.py`, `veritas/analysis/js_analyzer.py`
**Risk:** Security vulnerabilities may be undetected
**Priority:** High

### End-to-End Orchestration Tests
**What's not tested:**
- Full audit lifecycle without mocked components
- Database rollback on failure scenarios
- Concurrent audit execution
**Files:** `veritas/tests/`
**Risk:** Integration bugs causing audit failures in production
**Priority:** High

### Frontend Type Safety
**What's not tested:**
- Missing type wiring (the TODO at line 820)
- Type validation on WebSocket event payloads
**Files:** `frontend/src/lib/types.ts`
**Risk:** Runtime errors or silent data loss
**Priority:** Medium

---
*Concerns audit: 2026-03-16*