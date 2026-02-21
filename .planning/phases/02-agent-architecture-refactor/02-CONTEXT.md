# Phase 2: Agent Architecture Refactor - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

## Phase Boundary

Refactor security analysis from function-based approach to class-based SecurityAgent that matches VisionAgent and JudgeAgent patterns. Create SecurityAgent class with async analyze() method, encapsulating all security modules (headers, phishing, redirects, JS analysis, form validation), with feature-flaged migration from existing security_node function.

## Implementation Decisions

### Agent interface

- **NIM client injection**: Accept NIMClient in constructor, maintain as instance state (`self.nim_client`)
- **Initialization pattern**: Two-phase setup - `SecurityAgent.initialize()` for setup, then `SecurityAgent.analyze(url)` for analysis calls
- **Async context manager**: Support `async with SecurityAgent() as agent:` pattern for proper resource cleanup
- **Configuration approach**: Accept SecurityConfig dataclass in constructor for module settings (timeout, enabled_modules, etc.)
- **Return behavior**: `analyze()` always returns SecurityResult dataclass, never raises exceptions (errors captured in result.errors list)
- **Input interface**: `analyze()` accepts URL string only (agent handles fetching), returns SecurityResult
- **Reusability**: Single SecurityAgent instance reused across multiple analyze() calls (not created fresh for each analysis)

### Module structure

- **Method per module**: SecurityAgent has explicit methods for each security module: `analyze_headers()`, `check_phishing()`, `analyze_redirects()`, `analyze_js()`, `validate_forms()`
- **Separate module classes**: Security analysis modules exist as separate class files in `analysis/` directory (e.g., `SecurityHeaderAnalyzer`, `PhishingChecker`, `RedirectAnalyzer`)
- **Auto-discovery**: SecurityAgent auto-discovers module classes from `analysis/` directory (NOT hardcoded fixed list)
- **Pattern-based invocation**: Module classes follow naming convention (e.g., *Analyzer or *Checker), SecurityAgent inspects and invokes via reflection/pattern matching
- **Dynamic method creation**: At runtime, SecurityAgent auto-discovered modules and dynamically creates corresponding methods (analyze_headers() calls SecurityHeaderAnalyzer, etc.)
- **Configuration by file discovery**: No explicit enabled_modules list - discover modules from file system based on presence in analysis/ directory

### Migration flags

- **Environment variable**: `USE_SECURITY_AGENT=true/false` simple boolean to enable/disable SecurityAgent mode
- **Default behavior**: Agent first - SecurityAgent class is default, security_node function requires opt-out via USE_SECURITY_AGENT=false
- **Gradual rollout**: Percentage-based staged rollout controlled by `SECURITY_AGENT_ROLLOUT` environment variable (separate from USE_SECURITY_AGENT)
- **Stage advancement**: Same timing as Phase 1 Queue IPC rollout - 1 week per stage (10% → 25% → 50% → 75% → 100%)
- **Auto fallback**: If SecurityAgent raises error during analysis(), automatically fall back to security_node function for current audit
- **Logging**: Mode tracking - log which mode (agent/function) was used per audit for monitoring staged rollout success

### Result types

- **Comprehensive SecurityResult**: Include all relevant fields - not just minimal essentials
- **Nested per-module results**: top-level `modules_results` dict/field containing nested per-module results (e.g., `modules_results = {"security_headers": {...}, "phishing": {...}}`)
- **Composite security score**: Single composite score (0-1) calculated from all modules, not just list of per-module scores
- **Structured SecurityFinding**: SecurityFinding as dataclass with fields: `category`, `severity` (enum), `evidence`, `source_module`, `timestamp`, `confidence`
- **Severity enum**: Severity as enum type: `Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]`
- **Full metadata**: Include all metadata fields - `url`, `audit_id`, `timestamp`, `modules_run`, `modules_failed`, `analysis_time_ms`, total_time, etc.
- **Serialization methods**: SecurityResult has `to_dict()` and `from_dict()` class methods for JSON serialization/deserialization

### Claude's Discretion

- **Module discovery pattern**: Exact mechanism for auto-discovery (inspecting analysis/ directory, matching naming patterns, dynamic method creation)
- **Error handling specifics**: Which exceptions to catch, how to surface errors (log, store in SecurityResult.errors), severity mapping
- **Module invocation order**: Which order to run modules, parallel or sequential execution, module-specific timeouts
- **NIMClient lifecycle**: How NIMClient is created/managed within SecurityAgent, sharing with other agents if applicable
- **Config file structure**: What fields SecurityConfig dataclass should have (beyond basic: timeout, enabled_modules, retry logic)
- **Finding aggregation**: How to aggregate findings across modules into composite SecurityResult findings list
- **Score calculation**: Exact algorithm for composite security score from per-module scores, weights if any

## Specific Ideas

- "Make SecurityAgent match VisionAgent and JudgeAgent patterns for consistency"
- "Use auto-discovery so new modules are automatically available without code changes"
- "Gradual rollout like Phase 1 (10% staged rollout with environment variables)"
- "Safe migration with auto-fallback ensures audits never fail due to agent architecture changes"
- "SecurityResult should be comprehensive with all metadata for forensic investigation"

## Deferred Ideas

- Module-specific configuration beyond basic SecurityConfig (e.g., timeouts per module) - defer to Phase 5 or specific module upgrade
- Performance optimization (module pre-compilation, result caching) - out of scope for v1.0 stabilization
- Advanced metrics/dashboarding for module performance - Phase 1 queue IPC handles general rollout monitoring
- Module parallelization (run security modules in parallel for speed) - defer to v2 if requested

---

*Phase: 02-agent-architecture-refactor*
*Context gathered: 2026-02-21*
