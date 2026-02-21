# Phase 2: Agent Architecture Refactor - Research

**Researched:** 2026-02-21
**Domain:** Python agent class architecture, dynamic module discovery, feature-flagged migration
**Confidence:** HIGH

## Summary

This phase creates a SecurityAgent class that matches VisionAgent and JudgeAgent patterns while introducing auto-discovery of security modules from the `veritas/analysis/` directory. The key technical challenge is implementing dynamic module discovery and method generation at runtime without hardcoding module implementations. The migration uses a feature flag pattern (USE_SECURITY_AGENT) for gradual rollout with automatic fallback to the existing `security_node` function.

The primary technical decision is using Python's `inspect` and `importlib` modules for runtime module discovery and `setattr` for dynamic method creation. This allows new security modules to be automatically available without code changes to SecurityAgent, while maintaining the familiar VisionAgent/JudgeAgent interface for consistency across the codebase.

**Primary recommendation:** Implement SecurityAgent with auto-discovery pattern using `importlib.import_module()` to dynamically load security modules from `veritas/analysis/`, create analyzer instances, and bind them to SecurityAgent as methods using `setattr()`. Feature flag defaults to new agent behavior with rollback to legacy `security_node` function.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Agent interface:**
- NIM client injection: Accept NIMClient in constructor, maintain as instance state (`self.nim_client`)
- Initialization pattern: Two-phase setup - `SecurityAgent.initialize()` for setup, then `SecurityAgent.analyze(url)` for analysis calls
- Async context manager: Support `async with SecurityAgent() as agent:` pattern for proper resource cleanup
- Configuration approach: Accept SecurityConfig dataclass in constructor for module settings (timeout, enabled_modules, etc.)
- Return behavior: `analyze()` always returns SecurityResult dataclass, never raises exceptions (errors captured in result.errors list)
- Input interface: `analyze()` accepts URL string only (agent handles fetching), returns SecurityResult
- Reusability: Single SecurityAgent instance reused across multiple analyze() calls (not created fresh for each analysis)

**Module structure:**
- Method per module: SecurityAgent has explicit methods for each security module: `analyze_headers()`, `check_phishing()`, `analyze_redirects()`, `analyze_js()`, `validate_forms()`
- Separate module classes: Security analysis modules exist as separate class files in `analysis/` directory (e.g., `SecurityHeaderAnalyzer`, `PhishingChecker`, `RedirectAnalyzer`)
- Auto-discovery: SecurityAgent auto-discovers module classes from `analysis/` directory (NOT hardcoded fixed list)
- Pattern-based invocation: Module classes follow naming convention (e.g., *Analyzer or *Checker), SecurityAgent inspects and invokes via reflection/pattern matching
- Dynamic method creation: At runtime, SecurityAgent auto-discovered modules and dynamically creates corresponding methods (analyze_headers() calls SecurityHeaderAnalyzer, etc.)
- Configuration by file discovery: No explicit enabled_modules list - discover modules from file system based on presence in analysis/ directory

**Migration flags:**
- Environment variable: `USE_SECURITY_AGENT=true/false` simple boolean to enable/disable SecurityAgent mode
- Default behavior: Agent first - SecurityAgent class is default, security_node function requires opt-out via USE_SECURITY_AGENT=false
- Gradual rollout: Percentage-based staged rollout controlled by `SECURITY_AGENT_ROLLOUT` environment variable (separate from USE_SECURITY_AGENT)
- Stage advancement: Same timing as Phase 1 Queue IPC rollout - 1 week per stage (10% -> 25% -> 50% -> 75% -> 100%)
- Auto fallback: If SecurityAgent raises error during analyze(), automatically fall back to security_node function for current audit
- Logging: Mode tracking - log which mode (agent/function) was used per audit for monitoring staged rollout success

**Result types:**
- Comprehensive SecurityResult: Include all relevant fields - not just minimal essentials
- Nested per-module results: top-level `modules_results` dict/field containing nested per-module results (e.g., `modules_results = {"security_headers": {...}, "phishing": {...}}`)
- Composite security score: Single composite score (0-1) calculated from all modules, not just list of per-module scores
- Structured SecurityFinding: SecurityFinding as dataclass with fields: `category`, `severity` (enum), `evidence`, `source_module`, `timestamp`, `confidence`
- Severity enum: Severity as enum type: `Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]`
- Full metadata: Include all metadata fields - `url`, `audit_id`, `timestamp`, `modules_run`, `modules_failed`, `analysis_time_ms`, total_time, etc.
- Serialization methods: SecurityResult has `to_dict()` and `from_dict()` class methods for JSON serialization/deserialization

### Claude's Discretion

**Module discovery pattern:**
- Exact mechanism for auto-discovery (inspecting analysis/ directory, matching naming patterns, dynamic method creation)

**Error handling specifics:**
- Which exceptions to catch, how to surface errors (log, store in SecurityResult.errors), severity mapping

**Module invocation order:**
- Which order to run modules, parallel or sequential execution, module-specific timeouts

**NIMClient lifecycle:**
- How NIMClient is created/managed within SecurityAgent, sharing with other agents if applicable

**Config file structure:**
- What fields SecurityConfig dataclass should have (beyond basic: timeout, enabled_modules, retry logic)

**Finding aggregation:**
- How to aggregate findings across modules into composite SecurityResult findings list

**Score calculation:**
- Exact algorithm for composite security score from per-module scores, weights if any

### Deferred Ideas (OUT OF SCOPE)

- Module-specific configuration beyond basic SecurityConfig (e.g., timeouts per module) - defer to Phase 5 or specific module upgrade
- Performance optimization (module pre-compilation, result caching) - out of scope for v1.0 stabilization
- Advanced metrics/dashboarding for module performance - Phase 1 queue IPC handles general rollout monitoring
- Module parallelization (run security modules in parallel for speed) - defer to v2 if requested
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CORE-01 | SecurityAgent class matches VisionAgent and JudgeAgent patterns | VisionAgent/JudgeAgent patterns analyzed (class-based, async analyze(), Result dataclass, NIMClient injection) |
| CORE-01-2 | SecurityAgent has async analyze() method returning SecurityResult dataclass | VisionAgent.analyze() → async method returning VisionResult dataclass; pattern verified |
| CORE-01-3 | SecurityAgent includes all security modules (headers, phishing, redirects, JS analysis, form validation) | All 5 security analysis modules confirmed in veritas/analysis/ directory: SecurityHeaderAnalyzer, PhishingChecker, RedirectAnalyzer, JSObfuscationDetector, FormActionValidator |
| CORE-01-4 | Feature flag enables gradual migration from function to class-based agent | Feature flag pattern from STABILIZATION.md (FEATURE_FLAG = os.getenv(...)), auto-fallback pattern documented |
| CORE-06-2 | SecurityAgent class follows same test pattern as VisionAgent/JudgeAgent | Test patterns documented in STABILIZATION.md (characterization, change detection, integration tests) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.14+ | Core language, dataclasses, asyncio, typing | Required by project constraint |
| importlib | stdlib | Dynamic module import at runtime | Official Python mechanism for runtime imports |
| inspect | stdlib | Runtime introspection of module structure | Official Python mechanism for reflection |
| asyncio | stdlib | Async/await for concurrent analysis | Project uses async/await throughout |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dataclasses | stdlib | SecurityResult, SecurityConfig, SecurityFinding dataclasses | Pythonic immutable data structures |
| typing | stdlib | Type hints (Optional, Literal, dataclass fields) | Type safety and IDE support |
| logging | stdlib | Mode tracking, error logging | Python standard for logging |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| importlib.import_module() | pkgutil.iter_modules() pkgutil.walk_packages() | iter_modules() only lists modules, doesn't import them - still need import_module() anyway |
| setattr() for dynamic methods | getattr() with function wrapper | setattr() is cleaner for method attachment; getattr() would require more boilerplate wrapper code |
| Literal for severity enum | StrEnum (Python 3.11+) | StrEnum is semantically clearer but Literal is more widely compatible; project uses Literal in other enums |

**Installation:**
No external dependencies required - all functionality uses Python standard library.

## Architecture Patterns

### Recommended Project Structure
```
veritas/
├── agents/
│   ├── security_agent.py        # NEW: SecurityAgent class with auto-discovery
│   ├── vision.py                # EXISTING: VisionAgent pattern reference
│   ├── judge.py                 # EXISTING: JudgeAgent pattern reference
│   └── __init__.py
├── analysis/                    # AUTO-DISCOVERY TARGET DIRECTORY
│   ├── __init__.py
│   ├── security_headers.py      # SecurityHeaderAnalyzer class
│   ├── phishing_checker.py      # PhishingChecker class
│   ├── redirect_analyzer.py     # RedirectAnalyzer class
│   ├── js_analyzer.py           # JSObfuscationDetector class
│   └── form_validator.py        # FormActionValidator class
├── core/
│   └── nim_client.py            # NIMClient injected into SecurityAgent
└── config/
    └── security_config.py       # NEW: SecurityConfig dataclass
```

### Pattern 1: Agent Class Pattern (from VisionAgent/JudgeAgent)
**What:** Class-based agent with NIMClient injection, async analyze() method, comprehensive Result dataclass.

**When to use:** All agent implementations requiring structured data return with error handling.

**Example (VisionAgent reference):**
```python
# Source: C:/files/coding dev era/elliot/elliotAI/veritas/agents/vision.py
class VisionAgent:
    """Agent: Visual forensics using VLM."""

    def __init__(self, nim_client: Optional[NIMClient] = None):
        self._nim = nim_client or NIMClient()

    async def analyze(
        self,
        screenshots: list[str],
        screenshot_labels: list[str],
        url: str = "",
        categories: Optional[list[str]] = None,
        site_type: str = "",
    ) -> VisionResult:
        """Full visual forensics analysis."""
        result = VisionResult()
        # ... analysis logic ...
        return result


@dataclass
class VisionResult:
    """Complete result from Visual Forensics."""
    dark_patterns: list[DarkPatternFinding] = field(default_factory=list)
    temporal_findings: list[TemporalFinding] = field(default_factory=list)
    visual_score: float = 1.0
    temporal_score: float = 1.0
    screenshots_analyzed: int = 0
    errors: list[str] = field(default_factory=list)
```

### Pattern 2: Dynamic Module Discovery with importlib
**What:** Use `importlib.import_module()` to load modules at runtime based on naming patterns, then use `inspect` to extract analyzer classes.

**When to use:** Need plugin architecture where new modules are automatically available without code changes.

**Example:**
```python
import importlib
import inspect
from pathlib import Path
from typing import Type, Dict

# Define naming patterns for auto-discovery
_MODULE_PATTERNS = [
    "security_headers.py", "phishing_checker.py", "redirect_analyzer.py",
    "js_analyzer.py", "form_validator.py",
]

_CLASS_PATTERNS = [
    "SecurityHeaderAnalyzer", "PhishingChecker", "RedirectAnalyzer",
    "JSObfuscationDetector", "FormActionValidator",
]

_ANALYSIS_DIR = Path(__file__).parent.parent / "analysis"


def discover_security_modules() -> Dict[str, Type]:
    """Discover and load security analyzer classes dynamically."""
    analyzers = {}

    for module_file in _ANALYSIS_DIR.glob("*.py"):
        if module_file.name.startswith("_"):
            continue  # Skip __init__.py

        module_name = f"veritas.analysis.{module_file.stem}"
        try:
            module = importlib.import_module(module_name)

            # Inspect module for analyzer classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module_name and name.endswith(("Analyzer", "Checker", "Validator")):
                    analyzers[name] = obj
                    logger.info(f"Discovered security module: {name}")

        except Exception as e:
            logger.warning(f"Failed to load module {module_name}: {e}")

    return analyzers


class SecurityAgent:
    """Agent 2: Security analysis coordinator."""

    def __init__(self, nim_client: Optional[NIMClient] = None):
        self._nim = nim_client or NIMClient()
        self._analyzers = discover_security_modules()
        self._analyzer_instances: Dict[str, object] = {}

    async def analyze(self, url: str, page=None) -> SecurityResult:
        """Run all discovered security modules against URL."""
        result = SecurityResult(url=url)

        # Run each discovered module
        for analyzer_name, analyzer_class in self._analyzers.items():
            try:
                # Lazy instantiation (only create when needed)
                if analyzer_name not in self._analyzer_instances:
                    self._analyzer_instances[analyzer_name] = analyzer_class()

                instance = self._analyzer_instances[analyzer_name]
                module_result = await self._run_module(instance, url, page)

                if module_result:
                    result.modules_run.append(analyzer_name)
                    result.module_results[analyzer_name] = module_result
                    result._aggregate_findings(analyzer_name, module_result)

            except Exception as e:
                logger.error(f"Security module {analyzer_name} failed: {e}")
                result.errors.append(f"{analyzer_name}: {e}")
                result.modules_failed.append(analyzer_name)

        # Compute composite score
        result.score = result._compute_composite_score()
        return result
```

### Pattern 3: Feature-Flagged Migration with Auto-Fallback
**What:** Wrap new implementation in environment variable toggle, with automatic fallback to legacy code on error.

**When to use:** High-risk refactoring where rollback must be instant and automatic.

**Example:**
```python
import os
import logging

logger = logging.getLogger("veritas.orchestrator")

# Feature flags
USE_SECURITY_AGENT = os.getenv("USE_SECURITY_AGENT", "true").lower() == "true"
SECURITY_AGENT_ROLLOUT = int(os.getenv("SECURITY_AGENT_ROLLOUT", "100"))  # 0-100%

async def security_node(state: AuditState) -> dict:
    """
    SECURITY node: Run security analysis modules.
    NEW: Feature-flagged migration to SecurityAgent class.
    """
    url = state.get("url", "")
    errors = state.get("errors", [])
    mode_used = "unknown"

    # Check staged rollout percentage (hash-based deterministic routing)
    if USE_SECURITY_AGENT:
        import hashlib
        rollout_check = int(hashlib.md5(url.encode()).hexdigest(), 16) % 100
        in_rollout = rollout_check < SECURITY_AGENT_ROLLOUT

        if in_rollout:
            try:
                # NEW PATH: Use SecurityAgent class
                from agents.security_agent import SecurityAgent
                agent = SecurityAgent()
                result = await agent.analyze(url)
                mode_used = "security_agent"
                logger.info(f"SecurityAgent completed for {url}, score={result.score:.2f}")
                return {"security_results": result.to_dict(), "_mode": mode_used}

            except Exception as e:
                logger.error(f"SecurityAgent failed for {url}: {e}, falling back to legacy")
                errors.append(f"SecurityAgent fallback: {e}")
                # Fallthrough to legacy path

    # LEGACY PATH: Direct module calls (original security_node logic)
    mode_used = "legacy_function"
    results = {}

    # Security headers
    if "security_headers" in state.get("enabled_security_modules", []):
        try:
            from analysis.security_headers import SecurityHeaderAnalyzer
            analyzer = SecurityHeaderAnalyzer()
            res = await analyzer.analyze(url)
            results["security_headers"] = res.to_dict()
        except Exception as e:
            results["security_headers"] = {"error": str(e)}

    # ... other modules ...

    logger.info(f"Legacy security_node completed for {url}, mode={mode_used}")
    return {"security_results": results, "_mode": mode_used}
```

### Anti-Patterns to Avoid
- **Hardcoded module list:** Instead of `self._analyzers = {"headers": SecurityHeaderAnalyzer, ...}`, use auto-discovery from filesystem
- **Creating analyzer instances in __init__:** Lazily instantiate only when analyze() is called - avoid triggering module imports during agent creation
- **Silent failure in module discovery:** If a module fails to load, log the error and continue - don't let one broken module disable the entire agent
- **Mixing async and sync module calls:** All module analyzer methods are async - wrap sync calls in `asyncio.run_in_executor()` if needed
- **Raising exceptions from analyze():** Return errors in result.errors list instead - callers should handle partial results gracefully

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Module discovery from package | Manual file parsing with glob + ast | `importlib.import_module()` + `inspect.getmembers()` | Handles all edge cases (lazy imports, relative imports, package resolution) |
| Dynamic method creation | Creating lambda functions or wrappers | `setattr(self, method_name, bound_method)` | Cleaner, Pythonic, works with method signature inspection |
| Feature flag rollout logic | Custom random/clickhouse router | Deterministic hash-based routing | Consistent routing per URL, easier debugging, no network calls |
| Async context manager | Manual `__aenter__`/`__aexit__` boilerplate | `@contextlib.asynccontextmanager` decorator | Less boilerplate, handles exceptions automatically |
| Configuration management | Parsing env vars manually | `pydantic.BaseSettings` or os.getenv() with defaults | Type-safe, validates, handles defaults cleanly |

**Key insight:** Dynamic module discovery is a common pattern in plugin systems - using importlib and inspect is battle-tested, whereas building it from scratch would introduce edge cases around Python's import system (lazy imports, package __path__, relative imports, etc.).

## Common Pitfalls

### Pitfall 1: Import Side Effects During Auto-Discovery
**What goes wrong:** Importing modules during discovery triggers their top-level code execution, which may attempt network calls, file I/O, or database connections.

**Why it happens:** Security modules may have `requests.get()` calls or file operations at module level (not inside classes/methods).

**Consequences:**
- Slow agent initialization
- Unexpected network activity during import
- Race conditions if multiple threads import simultaneously
- Import failures if resources (network, files) unavailable

**Prevention:**
1. Review all security modules for top-level side effects
2. Defer heavy initialization to `__init__()` or async `analyze()` methods
3. Use lazy imports inside methods for modules with side effects
4. Add timeout to import operations

**Warning signs:**
- Agent instantiation takes > 100ms
- Network activity during agent creation
- Import errors when network/files are unavailable

### Pitfall 2: Method Name Collisions with Existing Attributes
**What goes wrong:** Dynamic method creation uses `setattr()` with names that conflict with existing attributes or methods.

**Why it happens:** Module naming conventions may overlap with agent methods (e.g., `analyze()` vs module method named `analyze`).

**Consequences:**
- Overwrites critical methods (e.g., `self.analyze` gets replaced)
- AttributeError when calling expected methods
- Confusing debugging (method does something unexpected)

**Prevention:**
1. Prefix dynamic methods (e.g., `analyze_headers()`, `check_phishing()`)
2. Use blacklist of reserved names (`__dict__`, `__init__`, `analyze`, etc.)
3. Log warnings when name collisions detected
4. Use module name as prefix if uncertain

**Detection:**
```python
def _bind_module_method(self, method_name: str, method_func):
    """Bind method to agent after checking for conflicts."""
    if hasattr(self, method_name):
        existing = getattr(self, method_name)
        if callable(existing):
            logger.warning(
                f"Method name collision: '{method_name}' already exists. "
                f"Skipping dynamic binding for {method_func.__module__}"
            )
            return False
    setattr(self, method_name, method_func)
    return True
```

### Pitfall 3: Async/sync Interoperability in Module Calls
**What goes wrong:** Mixing async `analyze()` calls with sync module methods causes runtime errors or blocking.

**Why it happens:** Some security modules may be synchronous (e.g., urllib-based analyzers) while others use async.

**Consequences:**
- `RuntimeError: This event loop is already running` if sync code creates new loop
- Blocked event loop if sync code runs in async context
- Inconsistent error handling patterns

**Prevention:**
1. Inspect module methods with `inspect.iscoroutinefunction()` to detect async/sync
2. Wrap sync calls with `asyncio.run_in_executor(thread_pool, func, *args)`
3. Document expected async/sync signature for new modules
4. Provide both async and sync variants if module author supports both

**Detection:**
```python
async def _run_module(self, instance: object, url: str, page=None):
    """Run module method, handling both async and sync."""

    # Determine method name by convention
    method_name = "check" if instance.__class__.__name__.endswith("Checker") else "analyze"
    if hasattr(instance, "validate"):
        method_name = "validate"

    method = getattr(instance, method_name, None)
    if not method:
        logger.warning(f"No {method_name} method found for {instance.__class__.__name__}")
        return None

    # Call async or sync appropriately
    if inspect.iscoroutinefunction(method):
        args = (url, page) if method_name == "validate" else (url,)
        return await method(*args)
    else:
        # Wrap sync call in executor to avoid blocking
        loop = asyncio.get_running_loop()
        args = (page, url) if method_name == "validate" else (url,)
        return await loop.run_in_executor(None, method, *args)
```

### Pitfall 4: Stale Analyzer State Across analyze() Calls
**What goes wrong:** Reusing analyzer instances caches state from previous `analyze()` calls, producing incorrect results.

**Why it happens:** Security modules may store per-request state as instance attributes.

**Consequences:**
- Module uses wrong URL from previous call
- Cached results returned for different URLs
- Intermittent bugs only on 2nd+ analyze() call

**Prevention:**
1. Create fresh analyzer instances for each `analyze()` call (trade-off: performance)
2. Call explicit `reset()` or `clear()` method if module supports it
3. Document stateful vs stateful module classes
4. Add test that calls `analyze()` twice with different URLs

**Detection:**
```python
class SecurityAgent:
    async def analyze(self, url: str, page=None) -> SecurityResult:
        result = SecurityResult(url=url)

        for analyzer_name, analyzer_class in self._analyzers.items():
            # Create fresh instance for each call (avoid state leakage)
            instance = analyzer_class()

            module_result = await self._run_module(instance, url, page)
            # ...
```

### Pitfall 5: Feature Flag Rollout skewing A/B Test Results
**What goes wrong:** Random routing causes uneven distribution, inconsistent user experience, makes debugging harder.

**Why it happens:** Using `random.random() < rollout_percent` or similar non-deterministic routing.

**Consequences:**
- Same URL may use different modes on consecutive requests
- Cannot reproduce bugs consistently
- Metrics aggregation becomes noisy

**Prevention:**
1. Use deterministic routing (hash-based) for consistent per-URL behavior
2. Include request ID or user ID in rollout hash for per-user consistency
3. Log the rollot decision to enable after-the-fact analysis
4. Switch to 100% rollout for staging/production debugging

**Detection:**
```python
def _should_use_agent(self, url: str, rollout_percent: int) -> bool:
    """Deterministic rollout - same URL always uses same mode."""
    import hashlib
    hash_value = int(hashlib.md5(url.encode()).hexdigest(), 16) % 100
    in_rollout = hash_value < rollout_percent
    if in_rollout:
        logger.debug(f"URL {url} in {rollout_percent}% rollout (hash={hash_value})")
    return in_rollout
```

## Code Examples

Verified patterns from official sources and existing codebase:

### SecurityAgent Skeleton with Auto-Discovery
```python
# veritas/agents/security_agent.py
import asyncio
import importlib
import inspect
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Any, Literal, Type

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.nim_client import NIMClient
from config.security_config import SecurityConfig

logger = logging.getLogger("veritas.security_agent")


# ============================================================
# Data Structures
# ============================================================

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


@dataclass
class SecurityFinding:
    """Structured finding from security analysis."""
    category: str
    severity: Severity
    evidence: str
    source_module: str           # e.g., "security_headers", "phishing_checker"
    timestamp: str
    confidence: float = 0.5

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "severity": self.severity,
            "evidence": self.evidence,
            "source_module": self.source_module,
            "timestamp": self.timestamp,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class SecurityResult:
    """Complete result from security analysis."""
    url: str
    score: float = 0.5                      # 0.0 - 1.0, higher = more secure

    # Module results (nested per-module)
    module_results: Dict[str, Dict] = field(default_factory=dict)

    # Aggregated findings
    findings: List[SecurityFinding] = field(default_factory=list)

    # Execution metadata
    modules_run: List[str] = field(default_factory=list)
    modules_failed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Timing
    analysis_time_ms: float = 0.0

    def _aggregate_findings(self, module_name: str, module_dict: Dict) -> None:
        """Extract findings from module result and add to findings list."""
        # Pattern: look for 'flags', 'findings', 'details' keys
        for finding_dict in module_dict.get("findings", module_dict.get("flags", [])):
            self.findings.append(SecurityFinding(
                category=finding_dict.get("category", module_name),
                severity=finding_dict.get("severity", "INFO").upper(),
                evidence=finding_dict.get("evidence", finding_dict.get("description", "")),
                source_module=module_name,
                timestamp=__import__("datetime").datetime.utcnow().isoformat(),
                confidence=finding_dict.get("confidence", 0.5),
            ))

    def _compute_composite_score(self) -> float:
        """Compute composite security score from module results."""
        if not self.module_results:
            return 0.5  # No data = neutral score

        # Average module scores
        scores = [r.get("score", 0.5) for r in self.module_results.values()]
        composite = sum(scores) / len(scores) if scores else 0.5

        # Penalize for failed modules
        if self.modules_failed:
            composite = max(0.0, composite - (len(self.modules_failed) * 0.1))

        # Penalize for critical findings
        critical_count = sum(1 for f in self.findings if f.severity == "CRITICAL")
        if critical_count > 0:
            composite = max(0.0, composite - (critical_count * 0.2))

        return round(composite, 3)

    def to_dict(self) -> dict:
        """Serialize to dictionary for state persistence."""
        return {
            "url": self.url,
            "score": self.score,
            "module_results": self.module_results,
            "findings": [f.to_dict() for f in self.findings],
            "modules_run": self.modules_run,
            "modules_failed": self.modules_failed,
            "errors": self.errors,
            "analysis_time_ms": round(self.analysis_time_ms, 2),
        }


# ============================================================
# Security Agent
# ============================================================

class SecurityAgent:
    """
    Agent 2: Security analysis coordinator.

    Auto-discovers security modules from veritas/analysis/ directory.
    Modules must:
        - Be in veritas/analysis/*.py files
        - Contain classes ending in "Analyzer", "Checker", or "Validator"
        - Have async methods: analyze(url), check(url), or validate(page, url)

    Usage:
        agent = SecurityAgent()

        result = await agent.analyze("https://example.com")
        print(f"Score: {result.score}")
        print(f"Modules run: {result.modules_run}")

    With page object (for modules that need browser context):
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto("https://example.com")

            result = await agent.analyze("https://example.com", page=page)
    """

    # Directory to scan for security modules
    _ANALYSIS_DIR = Path(__file__).resolve().parent.parent / "analysis"

    def __init__(self, nim_client: Optional[NIMClient] = None, config: Optional[SecurityConfig] = None):
        self._nim = nim_client or NIMClient()
        self._config = config or SecurityConfig()
        self._analyzers: Dict[str, Type] = self._discover_modules()

        logger.info(f"SecurityAgent initialized with {len(self._analyzers)} modules: {list(self._analyzers.keys())}")

    def _discover_modules(self) -> Dict[str, Type]:
        """Auto-discover security analysis classes from analysis/ directory."""
        analyzers = {}

        if not self._ANALYSIS_DIR.exists():
            logger.warning(f"Analysis directory not found: {self._ANALYSIS_DIR}")
            return analyzers

        for module_file in self._ANALYSIS_DIR.glob("*.py"):
            if module_file.name.startswith("_"):
                continue  # Skip __init__.py, __pycache__

            module_name = f"veritas.analysis.{module_file.stem}"
            try:
                module = importlib.import_module(module_name)

                # Inspect for analyzer classes
                for class_name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ == module_name and class_name.endswith(("Analyzer", "Checker", "Validator")):
                        analyzers[class_name] = obj
                        logger.debug(f"Discovered security module: {class_name} from {module_name}")

            except Exception as e:
                logger.warning(f"Failed to load module {module_name}: {e}")

        return analyzers

    async def analyze(self, url: str, page=None) -> SecurityResult:
        """
        Run all discovered security modules against URL.

        Args:
            url: Target URL to analyze
            page: Optional Playwright Page object (for modules needing browser context)

        Returns:
            SecurityResult with composite score and per-module findings
        """
        import time
        start_time = time.time()

        result = SecurityResult(url=url)

        # Run each discovered module
        for analyzer_name, analyzer_class in self._analyzers.items():
            try:
                # Create fresh instance for each call (avoid state leakage)
                instance = analyzer_class()

                module_result = await self._run_module(instance, url, page)

                if module_result is not None:
                    result.modules_run.append(analyzer_name)
                    result.module_results[analyzer_name.lower()] = module_result
                    result._aggregate_findings(analyzer_name.lower(), module_result)

            except Exception as e:
                logger.error(f"Security module {analyzer_name} failed: {e}", exc_info=True)
                result.errors.append(f"{analyzer_name}: {e}")
                result.modules_failed.append(analyzer_name)

        # Compute composite score
        result.score = result._compute_composite_score()
        result.analysis_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"SecurityAgent completed for {url} | "
            f"score={result.score:.2f} | "
            f"modules_run={len(result.modules_run)} | "
            f"modules_failed={len(result.modules_failed)} | "
            f"findings={len(result.findings)} | "
            f"time={result.analysis_time_ms:.0f}ms"
        )

        return result

    async def _run_module(self, instance: object, url: str, page=None) -> Optional[Dict]:
        """
        Run module method, handling both async and sync implementations.

        Detects method by class name convention:
            *Analyzer -> analyze(url)
            *Checker -> check(url)
            *Validator -> validate(page, url)
        """
        class_name = instance.__class__.__name__

        if class_name.endswith("Checker"):
            method_name = "check"
            args = (url,)
        elif class_name.endswith("Validator"):
            method_name = "validate"
            args = (page, url) if page else (url,)
        else:  # Analyzer
            method_name = "analyze"
            # JSObfuscationDetector needs page, others need url
            if class_name == "JSObfuscationDetector" and page is None:
                logger.debug(f"Skipping JSObfuscationDetector for {url} (no page object provided)")
                return None
            args = (page, url) if class_name == "JSObfuscationDetector" else (url,)

        method = getattr(instance, method_name, None)
        if method is None:
            logger.warning(f"No {method_name} method found for {class_name}")
            return None

        # Call async or sync appropriately
        if inspect.iscoroutinefunction(method):
            return await method(*args)
        else:
            # Wrap sync call in executor (avoid blocking)
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, method, *args)

    # Dynamic convenience methods (bound if needed)
    async def analyze_headers(self, url: str):
        """Convenience: Run SecurityHeaderAnalyzer only."""
        analyzer_class = self._analyzers.get("SecurityHeaderAnalyzer")
        if analyzer_class:
            instance = analyzer_class()
            return await instance.analyze(url)
        raise RuntimeError("SecurityHeaderAnalyzer not found")

    async def check_phishing(self, url: str):
        """Convenience: Run PhishingChecker only."""
        analyzer_class = self._analyzers.get("PhishingChecker")
        if analyzer_class:
            instance = analyzer_class()
            return await instance.check(url)
        raise RuntimeError("PhishingChecker not found")

    async def analyze_redirects(self, url: str):
        """Convenience: Run RedirectAnalyzer only."""
        analyzer_class = self._analyzers.get("RedirectAnalyzer")
        if analyzer_class:
            instance = analyzer_class()
            return await instance.analyze(url)
        raise RuntimeError("RedirectAnalyzer not found")

    async def analyze_js(self, url: str, page=None):
        """Convenience: Run JSObfuscationDetector only."""
        analyzer_class = self._analyzers.get("JSObfuscationDetector")
        if analyzer_class:
            instance = analyzer_class()
            return await instance.analyze(page or url, url)
        raise RuntimeError("JSObfuscationDetector not found")

    async def validate_forms(self, url: str, page=None):
        """Convenience: Run FormActionValidator only."""
        analyzer_class = self._analyzers.get("FormActionValidator")
        if analyzer_class:
            instance = analyzer_class()
            return await instance.validate(page or url, url)
        raise RuntimeError("FormActionValidator not found")
```

### SecurityConfig Dataclass
```python
# veritas/config/security_config.py
import os
from dataclasses import dataclass, field


@dataclass
class SecurityConfig:
    """Configuration for SecurityAgent behavior."""

    # Module execution
    timeout: int = 30                       # Default timeout per module (seconds)
    parallel_execution: bool = False        # If True, run modules in parallel (deferred to v2)

    # Module discovery
    auto_discover: bool = True              # If False, only use hardcoded module list
    analysis_dir: str = "veritas/analysis"  # Directory to scan for modules

    # Rollout control
    use_agent: bool = True                  # Default to agent (can be overridden by env var)
    rollout_percent: int = int(os.getenv("SECURITY_AGENT_ROLLOUT", "100"))

    # NIMClient configuration (if needed for future modules)
    nim_endpoint: str = ""                  # Optional: NIM endpoint override
    nim_api_key: str = ""                   # Optional: NIM API key override

    # Logging
    log_mode: bool = True                   # Log which mode (agent/function) was used

    # Error handling
    auto_fallback: bool = True              # Auto-fallback to legacy on error
    fail_fast: bool = False                 # Stop on first module failure (if False, continue)
```

### Legacy security_node with Feature Flags (Modified)
```python
# veritas/core/orchestrator.py
import os
import hashlib
import logging

logger = logging.getLogger("veritas.orchestrator")

# Feature flags
USE_SECURITY_AGENT = os.getenv("USE_SECURITY_AGENT", "true").lower() == "true"
SECURITY_AGENT_ROLLOUT = int(os.getenv("SECURITY_AGENT_ROLLOUT", "100"))


async def security_node(state: AuditState) -> dict:
    """
    SECURITY node: Run enabled security analysis modules.

    FEATURE FLAGS:
        - USE_SECURITY_AGENT: Enable/disable SecurityAgent class (default: true)
        - SECURITY_AGENT_ROLLOUT: Percentage of requests using agent (0-100, default: 100)
    """
    url = state.get("url", "")
    errors = state.get("errors", [])
    mode_used = "legacy"
    result_data = {}

    # Check if SecurityAgent should be used
    if USE_SECURITY_AGENT and _should_use_agent(url, SECURITY_AGENT_ROLLOUT):
        try:
            # NEW PATH: SecurityAgent class with auto-discovery
            from agents.security_agent import SecurityAgent
            from config.security_config import SecurityConfig

            config = SecurityConfig()
            agent = SecurityAgent(config=config)
            result = await agent.analyze(url)

            mode_used = "security_agent"
            result_data = result.to_dict()

            logger.info(
                f"SecurityAgent completed for {url} | "
                f"mode={mode_used} | "
                f"rollout={SECURITY_AGENT_ROLLOUT}% | "
                f"score={result.score:.2f}"
            )

            return {
                "security_results": result_data,
                "_mode": mode_used,
                "_rollout": SECURITY_AGENT_ROLLOUT,
            }

        except Exception as e:
            logger.error(f"SecurityAgent failed for {url}: {e}", exc_info=True)
            errors.append(f"SecurityAgent fallback: {e}")
            mode_used = "legacy_fallback"
            # Fallthrough to legacy path

    # LEGACY PATH: Direct module calls (preserved for fallback)
    enabled = state.get("enabled_security_modules", [])
    if not enabled:
        enabled = ["security_headers", "phishing_db"]  # Default

    # Security headers
    if "security_headers" in enabled:
        try:
            from analysis.security_headers import SecurityHeaderAnalyzer
            analyzer = SecurityHeaderAnalyzer()
            res = await analyzer.analyze(url)
            result_data["security_headers"] = res.to_dict()
        except Exception as e:
            result_data["security_headers"] = {"error": str(e)}

    # Phishing check
    if "phishing_db" in enabled:
        try:
            from analysis.phishing_checker import PhishingChecker
            checker = PhishingChecker()
            res = await checker.check(url)
            result_data["phishing"] = res.to_dict()
        except Exception as e:
            result_data["phishing"] = {"error": str(e)}

    # Redirect analysis
    if "redirect_chain" in enabled:
        try:
            from analysis.redirect_analyzer import RedirectAnalyzer
            analyzer = RedirectAnalyzer()
            res = await analyzer.analyze(url)
            result_data["redirects"] = res.to_dict()
        except Exception as e:
            result_data["redirects"] = {"error": str(e)}

    # Note: JS and form validation need page object (handled by scout_node or separate)

    logger.info(f"Legacy security_node completed for {url} | mode={mode_used}")

    return {
        "security_results": result_data,
        "_mode": mode_used,
        "_rollout": 0,
    }


def _should_use_agent(url: str, rollout_percent: int) -> bool:
    """
    Deterministic rollout routing.

    Same URL always gets same decision, enabling consistent behavior
    and easier debugging. Uses MD5 hash for uniform distribution.
    """
    if rollout_percent >= 100:
        return True
    if rollout_percent <= 0:
        return False

    hash_value = int(hashlib.md5(url.encode()).hexdigest(), 16) % 100
    in_rollout = hash_value < rollout_percent

    if in_rollout:
        logger.debug(f"URL {url} in {rollout_percent}% rollout (hash={hash_value})")

    return in_rollout
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded module imports | Auto-discovery with importlib | This phase | New security modules available without code changes |
| security_node function | SecurityAgent class | This phase | Matches VisionAgent/JudgeAgent patterns, better testability |
| No feature flags | USE_SECURITY_AGENT + SECURITY_AGENT_ROLLOUT | This phase | Gradual rollout with instant rollback |
| Manual module result aggregation | Composite SecurityResult.score calculation | This phase | Single consistent security score across modules |
| Sync module calls | Async/sync interoperability | This phase | Non-blocking security analysis in async context |

**Deprecated/outdated:**
- **security_node as primary interface**: Still kept for fallback during migration, will be removed after validation period
- **Hardcoded module lists**: Auto-discovery pattern supersedes this approach
- **Random feature flag routing**: Deterministic hash-based routing is new standard

## Open Questions

1. **Composite score algorithm weighting**
   - What we know: Average of module scores with penalties for failures and critical findings
   - What's unclear: Should specific modules have higher weight (e.g., phishing > headers)?
   - Recommendation: Start with equal weighting, adjust empirically based on audit results during rollout

2. **Parallel module execution**
   - What we know: All modules are async, could run in parallel for speed
   - What's unclear: JSObfuscationDetector and FormActionValidator need page object - can they run in parallel?
   - Recommendation: Deferred to v2 as per context; implement sequential execution with asyncio.gather() only after validation

3. **Module-specific timeouts**
   - What we know: SecurityConfig has single timeout for all modules
   - What's unclear: Should phishing_check (network) have longer timeout than headers (local)?
   - Recommendation: Start with single timeout, add module-specific timeout dict if modules request it during rollout

## Sources

### Primary (HIGH confidence)
- **Python 3.14 importlib documentation** - Dynamic module import patterns, `import_module()` API
  - https://docs.python.org/3/library/importlib.html
- **Python 3.14 inspect documentation** - `getmembers()`, `iscoroutinefunction()`, `isclass()`
  - https://docs.python.org/3/library/inspect.html
- **Existing VisionAgent code** - C:/files/coding dev era/elliot/elliotAI/veritas/agents/vision.py
- **Existing JudgeAgent code** - C:/files/coding dev era/elliot/elliotAI/veritas/agents/judge.py
- **Existing security modules** - All 5 modules in veritas/analysis/ directory (headers, phishing, redirects, JS, forms)

### Secondary (MEDIUM confidence)
- **Phase research on feature flag patterns** - .planning/research/STABILIZATION.md (Strangler Fig pattern, gradual migration)
- **security_node implementation** - veritas/core/orchestrator.py lines 638-700 (current functionality to preserve)

### Tertiary (LOW confidence)
- **Rollout best practices** - General pattern for staged rollout (no specific source verified, but pattern is standard)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All imports and patterns are Python stdlib, well-documented
- Architecture: HIGH - Pattern verified against existing VisionAgent/JudgeAgent code
- Pitfalls: HIGH - Common issues with dynamic imports and async/sync mixing, documented in Python ecosystem

**Research date:** 2026-02-21
**Valid until:** 30 days (Python import patterns stable, unlikely to change)

---

*Phase: 02-agent-architecture-refactor*
*Research complete: 2026-02-21*
