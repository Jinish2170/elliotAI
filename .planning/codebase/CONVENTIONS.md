# Coding Conventions

**Analysis Date:** 2026-02-19

## Naming Patterns

**Files:**

**Python:**
- `snake_case.py` for all modules (e.g., `scout.py`, `graph_investigator.py`, `pattern_matcher.py`)
- Directories use `snake_case` (e.g., `agents/`, `analysis/`, `config/`)
- Test files: `test_*.py` (e.g., `test_veritas.py`)

**TypeScript/JavaScript:**
- `camelCase.ts` or `kebab-case.ts` for files (mixed usage in codebase: `useAuditStream.ts`, `types.ts`)
- Directories use `kebab-case` (e.g., `hooks/`, `lib/`)

**Functions:**

**Python:**
- `snake_case` for all functions and methods
```python
def _safe_navigate(self, page: Page, url: str) -> bool:
    """Navigate with fallback wait strategies."""
    ...

async def investigate(self, url: str, tier: str = "standard_audit") -> AuditState:
    """Run a complete audit on a URL."""
    ...

def _generate_recommendations(self, trust_result: TrustScoreResult, evidence: AuditEvidence) -> list[str]:
    """Generate actionable recommendations based on the verdict."""
```

**TypeScript:**
- `camelCase` for functions
```typescript
export function useAuditStream(auditId: string | null, url?: string, tier?: string) {
  const connect = useCallback(() => { ... });
  const disconnect = useCallback(() => { ... });
}
```

**Variables:**

**Python:**
- `snake_case` for instance variables and locals
```python
self._nim = nim_client or NIMClient()
self._call_count = 0
url_to_investigate = url
```

**TypeScript:**
- `camelCase` for variables
```typescript
const wsRef = useRef<WebSocket | null>(null);
const auditId = event.audit_id as string;
const connect = useCallback(() => { ... });
```

**Types:**

**Python:**
- `CamelCase` (PascalCase) for classes and type names
```python
class StealthScout:
    pass

class ScoutResult:
    pass

@dataclass
class DarkPatternFinding:
    category_id: str
    pattern_type: str
    confidence: float

class AuditState(TypedDict):
    url: str
    audit_tier: str
```

**TypeScript:**
- `PascalCase` for interfaces and types
```typescript
export interface PhaseState {
  status: PhaseStatus;
  message: string;
  pct: number;
}

export type Phase = "init" | "scout" | "security" | "vision" | "graph" | "judge";

export type PhaseStatus = "waiting" | "active" | "complete" | "error";
```

**Constants:**

**Python:**
- `UPPER_SNAKE_CASE` for module-level constants
```python
_DESKTOP_USER_AGENTS = [...]
_MOBILE_USER_AGENTS = [...]
_CAPTCHA_CONTENT_INDICATORS = [...]
_STEALTH_SCRIPT = """..."""
AUDIT_TIERS: dict = {...}
```

**TypeScript:**
- `PascalCase` or `SCREAMING_SNAKE_CASE` (mixed in codebase)
```typescript
export const PHASE_META: Record<Phase, {...}> = {...}
export const RISK_COLORS: Record<string, string> = {...}
export const RISK_LABELS: Record<string, string> = {...}
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"
```

## Code Style

**Formatting:**

**Python:**
- No explicit formatter configuration detected (no `black`, `ruff`, or `isort` config files)
- Line length appears to be around 100-120 characters based on actual code
- 4-space indentation (standard Python)

**TypeScript:**
- ESLint configured: `"eslint": "^9"`, `"eslint-config-next": "16.1.6"`
- No explicit Prettier config detected

**Linting:**

**Python:**
- No linting config files found (no `.flake8`, `pyproject.toml`, `setup.cfg` with lint settings)
- Manual code review patterns observed instead

**TypeScript:**
- ESLint with Next.js config for linting

## Import Organization

**Python:**

**Order:**
1. Standard library imports
2. Third-party imports (langchain, openai, playwright, etc.)
3. Local imports (using absolute paths with sys.path modification)

```python
# Standard library
import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Third-party
from playwright.async_api import Browser, Page, async_playwright
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from langgraph.graph import END, StateGraph

# Path setup for local imports (appears at top of many files)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Local imports (absolute-style reference)
from config import settings
from agents.scout import ScoutResult, StealthScout
from core.nim_client import NIMClient
from analysis.pattern_matcher import PatternMatcher
```

**Path Aliases:**

**Python:**
- Uses `sys.path.insert(0, ...)` to enable absolute imports from project root
- Local imports never use relative imports (`from . import xxx` is rarely used)

**TypeScript:**
- Uses `@/` alias for project root (standard Next.js)
```typescript
import { useAuditStore } from "@/lib/store";
import type { AuditResult, AuditStats } from "@/lib/types";
import { useCallback, useEffect, useRef } from "react";
```

## Error Handling

**Patterns:**

**Python:**

**Try-except with logging:**
```python
try:
    vlm_result = await self._nim.analyze_image(
        image_path=screenshot_path,
        prompt=prompt,
        category_hint=cat_id,
    )
except Exception as e:
    error_msg = f"VLM analysis failed for {cat_id}: {e}"
    logger.error(error_msg)
    result.errors.append(error_msg)
```

**Return partial results on error:**
```python
try:
    dom_analyzer = DOMAnalyzer()
    dom_result = await dom_analyzer.analyze(page)
    if not isinstance(dom_result, dict):
        dom_result = dom_result.__dict__ if hasattr(dom_result, '__dict__') else {}
    logger.debug(f"DOM analysis complete: {len(dom_result.get('findings', []))} findings")
except Exception as e:
    logger.warning(f"DOM analysis failed (non-critical): {e}")
    # Continue execution without crashing
```

**Graceful degradation with fallback values:**
```python
try:
    confidence = float(data.get("confidence", 0.6))
    if confidence < 0.3:
        continue
except (ValueError, TypeError):
    confidence = 0.5
```

**Custom exceptions:**
```python
class NIMCreditExhausted(Exception):
    """NVIDIA NIM API credits are exhausted."""
    pass

class NIMUnavailable(Exception):
    """All NIM endpoints are unreachable."""
    pass
```

**Early returns on validation:**
```python
if not screenshots:
    logger.warning("VisionAgent.analyze called with no screenshots")
    return result
```

**TypeScript:**

**Silent error handling in WebSocket:**
```typescript
ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    store.handleEvent(data);
  } catch {
    // ignore malformed messages
  }
};
```

**Error states in store:**
```typescript
case "audit_error": {
  set({
    status: "error",
    error: (event.error as string) || "Unknown error",
  });
  break;
}
```

## Logging

**Framework:** Python `logging` module

**Patterns:**

**Get logger per module:**
```python
logger = logging.getLogger("veritas.scout")
logger = logging.getLogger("veritas.vision")
logger = logging.getLogger("veritas.nim")
logger = logging.getLogger("veritas.judge")
```

**Log levels:**
- `logger.debug()` for diagnostic details
- `logger.info()` for normal operations/milestones
- `logger.warning()` for non-critical issues
- `logger.error()` for failures with stack traces
- `logger.exception()` rarely used (explicit `exc_info=True` used instead)

**Examples:**
```python
logger.info(f"Starting visual analysis of {url}")
logger.debug(f"Cache hit for vision analysis: {cache_key[:8]}...")
logger.warning(f"Scout failed: {url} | status={result.status}")
logger.error(f"Graph node exception: {e}", exc_info=True)
```

**Structured logging in orchestrator:**
```python
def _emit(phase: str, step: str, pct: int, detail: str = "", **extra):
    """Emit a structured progress marker for UI streaming."""
    msg = {"phase": phase, "step": step, "pct": pct, "detail": detail}
    msg.update(extra)
    print(f"##PROGRESS:{_json.dumps(msg)}", flush=True)
```

**TypeScript logging:**
- Uses console.log/info/warning/error mainly for debugging
- No formal logging framework detected

## Comments

**When to Comment:**

**Module docstrings (triple-quoted):**
```python
"""
Veritas Agent 4 — The Judge (Orchestrator's Brain)

The "Brain" of Veritas. Synthesizes evidence from all other agents into
a final verdict with Trust Score, risk level, and actionable recommendations.

Responsibilities:
    1. Receive evidence from Scout (metadata), Vision (dark patterns), Graph (entity verification)
    2. Determine if more investigation is needed (request additional pages)
    3. Compute the final Trust Score via trust_weights.compute_trust_score()
    4. Generate a forensic narrative explaining the verdict
    5. Produce structured report data for the reporting module
"""
```

**Function and method docstrings:**
```python
async def investigate(
    self,
    url: str,
    temporal_delay: Optional[int] = None,
    viewport: str = "desktop",
) -> ScoutResult:
    """
    Full forensic investigation of a URL:
        1. Navigate with stealth browser
        2. Check for CAPTCHA
        3. Take Screenshot_A (t0) — viewport shot
        4. Simulate human behavior (scroll, mouse jitter)
        5. Wait temporal_delay seconds
        ...

    Args:
        url: Target URL to investigate
        temporal_delay: Seconds between Screenshot_A and B
        viewport: "desktop" or "mobile"

    Returns:
        ScoutResult with all screenshots, metadata, and status
    """
```

**Inline comments for complex logic:**
```python
# -----------------------------------------------------------
# Check: Do we need more investigation?
# -----------------------------------------------------------
if self._should_investigate_more(evidence):
    return await self._request_more_investigation(evidence)
```

**Code pattern comments:**
```python
# Patterns carried forward from:
#    - glass-box-portal/backend/main.py → capture_mobile_screenshot()
#      (mobile viewport, navigator.webdriver=undefined, networkidle wait)
```

**TODO/FIXME comments present** (per user description of known issues):
- Used to track incomplete features or known bugs

**JSDoc/TSDoc:**
- Minimal usage in TypeScript codebase
- Type annotations preferred over docstrings
```typescript
export function useAuditStream(auditId: string | null, url?: string, tier?: string) {
  // No JSDoc - types are self-documenting
}
```

## Function Design

**Size:** No strict limits observed. Functions range from small (10-30 lines) to large (200+ lines for complex orchestration).

**Parameters:**

**Python:**
- Use type hints for all parameters
- Optional parameters use `Optional[T]` or default values
- Dataclasses used for complex parameter sets

```python
async def audit(
    self,
    url: str,
    tier: str = "standard_audit",
    verdict_mode: str = "expert",
    enabled_security_modules: Optional[list[str]] = None,
) -> AuditState:
```

**TypeScript:**
- All parameters typed
- Optional parameters use `?:`
```typescript
export function useAuditStream(auditId: string | null, url?: string, tier?: string) {
```

**Return Values:**

**Python:**
- Always return typed values (dataclasses or TypedDict)
- Use `list[T]` for collections
- Use `Optional[T]` for nullable returns

```python
def lookup_severity(self, category: str, sub_type: str) -> Severity:
    category = DARK_PATTERN_TAXONOMY.get(category)
    if category:

async def _find_temporal_pair(
    self, screenshots: list[str], labels: list[str]
) -> tuple[Optional[str], Optional[str]]:
```

**TypeScript:**
- Explicit return type annotations
```typescript
export function useAuditStream(auditId: string | null, url?: string, tier?: string): ReturnType<typeof useAuditStore>
```

## Module Design

**Exports:**

**Python:**
- No explicit `__all__` declarations in most modules
- Use dataclasses as primary export mechanism

**TypeScript:**
- Explicit `export` for everything meant to be public
```typescript
export type Phase = "init" | "scout" | "security" | "vision" | "graph" | "judge";
export interface PhaseState {...}
export const PHASE_META: Record<Phase, {...}> = {...}
export function useAuditStream(auditId: string | null, url?: string, tier?: string) {}
export const useAuditStore = create<AuditStore>((set, get) => ({...}));
```

**Barrel Files:**
- Python uses `__init__.py` with minimal content for package organization
- No explicit barrel index files in TypeScript (using `@/lib/types.ts` as central type registry)

## Async Patterns

**Python:**

**Use `async/await` for all I/O operations:**
```python
async def investigate(self, url: str) -> ScoutResult:
    ...

async def analyze(self, page) -> DOMAnalysisResult:
    dom_data = await page.evaluate(...)
    return DOMAnalysisResult()
```

**Context managers for resources:**
```python
async with StealthScout() as scout:
    result = await scout.investigate(url)

async def __aenter__(self):
    self._playwright = await async_playwright().start()
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    if self._browser:
        await self._browser.close()
```

**Rate limiting with Semaphore:**
```python
async with self._semaphore:
    self._call_count += 1
    result = await asyncio.wait_for(
        self._client.chat.completions.create(...),
        timeout=settings.NIM_TIMEOUT,
    )
```

**Retry with exponential backoff (tenacity):**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((TimeoutError, ConnectionError, OSError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _rate_limited_call(self, ...) -> None:
```

**Timeout handling:**
```python
try:
    async with asyncio.timeout(graph_timeout_s):
        result = await agent.investigate(...)
except TimeoutError:
    timeout_msg = f"Graph phase timeout after {graph_timeout_s}s"
    logger.error(timeout_msg)
    return fallback_result
```

**Error handling with asyncio.CancelledError:**
```python
except asyncio.CancelledError:
    error_msg = (
        f"VLM call to {model} was cancelled; treating as recoverable and falling back"
    )
    logger.warning(error_msg)
    return None
```

**Parallel execution:** Not heavily used; sequential async patterns dominate

**TypeScript:**

**WebSocket async handling:**
```typescript
const ws = new WebSocket(`${WS_BASE}/api/audit/stream/${audit_id}`);

ws.onopen = () => {
  store.setStatus("running");
};

ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    store.handleEvent(data);
  } catch {
    // ignore malformed messages
  }
};
```

**React hooks with useEffect for async cleanup:**
```typescript
useEffect(() => {
  const ws = connect();
  return () => {
    if (ws && ws.readyState <= WebSocket.OPEN) {
      ws.close();
    }
  };
}, [connect]);
```

## Data Model Patterns

**Python Dataclasses:**

**Use `@dataclass` for structured data:**
```python
@dataclass
class ScoutResult:
    url: str
    status: str  # SUCCESS | CAPTCHA_BLOCKED | TIMEOUT | ERROR
    screenshots: list[str] = field(default_factory=list)
    page_title: str = ""
    trust_modifier: float = 0.0
```

**Use `TypedDict` for shared state (LangGraph):**
```python
class AuditState(TypedDict):
    url: str
    audit_tier: str
    iteration: int
    scout_results: list[dict]
    vision_result: Optional[dict]
    judge_decision: Optional[dict]
    pending_urls: list[str]
```

**Enum-like patterns (string literals preferred):**
```python
status: str  # "SUCCESS", "CAPTCHA_BLOCKED", "TIMEOUT", "ERROR"
severity: str  # "low", "medium", "high", "critical"
verdict_mode: str  # "simple" | "expert"
```

**TypeScript Interfaces:**

**Explicit interfaces for data shapes:**
```typescript
export interface Finding {
  id: string;
  category: string;
  pattern_type: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  description: string;
  plain_english: string;
  screenshot_index?: number;
}
```

**Union types for string literals:**
```typescript
export type Phase = "init" | "scout" | "security" | "vision" | "graph" | "judge";
export type PhaseStatus = "waiting" | "active" | "complete" | "error";
```

**Record types for indexed data:**
```typescript
export const PHASE_META: Record<Phase, { label: string; icon: string; description: string }> = {...}
```

---

*Convention analysis: 2026-02-19*
