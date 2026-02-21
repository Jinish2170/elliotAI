# Brownfield Project Stabilization Research

**Project:** VERITAS Forensic Web Auditing Platform
**Domain:** Brownfield legacy code stabilization
**Researched:** 2026-02-20
**Overall Confidence:** MEDIUM

## Executive Summary

VERITAS is a functional forensic web auditing platform with significant technical debt accumulated during rapid development. The codebase exhibits classic brownfield stabilization challenges: architectural violations (security_node as function), fragile inter-process communication (stdout parsing), unused framework infrastructure (LangGraph ainvoke bypassed), and incomplete implementations masking bugs.

Stabilization should follow the **Strangler Fig pattern** with **feature-flagged refactoring**. The approach systematically replaces fragile components with robust alternatives while maintaining existing functionality through parallel implementations. This minimizes risk by keeping the old code working alongside new code until complete migration is verified.

The highest-impact stabilization sequence is: (1) Replace stdout IPC with SQLite-based message queue, (2) Create proper SecurityAgent class, (3) Enable LangGraph proper execution (or confirm the workaround is necessary), (4) Replace empty stubs with NotImplemented, (5) Add persistent audit storage. This order addresses the most brittle communications first, then corrects architectural violations, then improves observability and data persistence.

## Key Findings

**Stack:** Python 3.14 with LangGraph, FastAPI, Next.js 16, Playwright, NVIDIA NIM
**Architecture:** 3-tier async event-stream with LangGraph state machine (currently bypassed)
**Critical pitfall:** Subprocess stdout parsing - any subprocess output change breaks the entire audit pipeline

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Phase 1: IPC Stabilization** - Most fragile component, affects all downstream reliability
   - Addresses: Subprocess stdout parsing vulnerability
   - Avoids: Intermittent parse failures on subprocess output changes

2. **Phase 2: Architecture Pattern Consistency** - Corrects agent pattern, improves maintainability
   - Addresses: SecurityAgent missing class, inconsistent agent implementations
   - Avoids: Future refactoring pain, code style inconsistencies

3. **Phase 3: State Machine Proper Execution** - Investigate LangGraph compatibility
   - Addresses: Sequential manual execution, bypassing LangGraph benefits
   - Avoids: Dead code, lost debugging capabilities

4. **Phase 4: Stub Cleanup** - Unmask silent failures
   - Addresses: Empty return stubs in evidence collection
   - Avoids: Hidden bugs, false confidence from partial results

5. **Phase 5: Data Persistence** - Enable audit history
   - Addresses: In-memory audit storage, data loss on restart
   - Avoids: Losing critical forensic evidence, no historical record

**Phase ordering rationale:**
- IPC first because it's the most fragile component causing real failures
- Architecture pattern because it affects future development speed
- State machine because it unlocks LangGraph's debugging and visualization
- Stub cleanup because it improves error visibility and testability
- Persistence last because it's an enhancement, not a blocking issue

**Research flags for phases:**
- Phase 3 (LangGraph): Likely needs deeper research — Python 3.14 compatibility may be a real blocker requiring version pin or alternative approach
- Phase 1, 2, 4, 5: Standard patterns, unlikely to need additional research

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| IPC Replacement | MEDIUM | SQLite pattern verified in Python docs, but edge cases need testing |
| SecurityAgent Refactor | HIGH | Clear pattern from existing agents (VisionAgent, JudgeAgent) |
| LangGraph Execution | LOW | Python 3.14 compatibility not verified — may require version pin or work continues with sequential execution |
| Stub Replacement | HIGH | Python NotImplementedError pattern well-documented |
| Persistent Storage | MEDIUM | SQLite schema straightforward, but migration path needs planning |

## Gaps to Address

- LangGraph Python 3.14 CancelledError root cause not verified — may need to file issue with LangGraph or pin Python version
- SQLite IPC performance characteristics under concurrent load not tested — may need connection pooling
- Empty stub analysis incomplete — need to audit all `return []` occurrences for true implementations needed

---

# Stabilization Architecture Research

## Current System Overview

The VERITAS platform implements a **3-tier Async Event-Stream Architecture** with subprocess isolation for Python 3.14 compatibility:

```
┌────────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                           │
│                   Next.js 16 + React 19                          │
├────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Landing Page │  │ Live Audit   │  │ Report View  │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         └─────────────────┼─────────────────┘                    │
│                           │                                        │
├───────────────────────────┼──────────────────────────────────────┤
│                    WebSocket Connection                         │
│                           │                                        │
├───────────────────────────┼──────────────────────────────────────┤
│                      API Layer (FastAPI)                         │
│              REST Endpoints + Stream Events                       │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    AuditRunner                            │    │
│  │        Subprocess wrapper + stdout parser                │    │
│  │   (Fragile: depends on ##PROGRESS: marker prefix)        │    │
│  └──────────────────────────────────────────────────────────┘    │
└───────────────────────────┼──────────────────────────────────────┘
                            │
               subprocess.Popen()
                            │
├───────────────────────────┼──────────────────────────────────────┤
│              Orchestration Layer (Veritas Engine)                │
│        LangGraph StateGraph (manual execution, not ainvoke)      │
│  ┌────────┐ ┌──────────┐ ┌───────┐ ┌──────┐ ┌──────┐           │
│  │ Scout  │ │ Security │ │Vision │ │Graph │ │Judge │           │
│  │ (class)│ │ (fn ❌)  │ │(class)│ │(class)│ │(class)│           │
│  └────┬───┘ └────┬─────┘ └───┬───┘ └──┬───┘ └──┬───┘           │
└───────┼───────────┼──────────┼────────┼────────┼────────────────┘
        │           │          │        │        │
        ↓           ↓          ↓        ↓        ↓
    Playwright   Analysis   NIMVLM   Tavily   TrustScore
```

## Pattern 1: Strangler Fig for Gradual Migration

**What:** Incrementally replace legacy components by running new and old implementations in parallel, switching over slowly.

**When:** Brownfield systems with fragile components that cannot be replaced wholesale without high risk.

**Trade-offs:**
- **Pros:** Low risk, gradual migration, can rollback easily, continuous delivery enabled
- **Cons:** Longer total migration time, temporary code duplication, complexity during transition

**IPC Stabilization Example:**

```python
# Phase 1: Add SQLite IPC alongside stdout markers
class AuditRunner:
    def __init__(self, audit_id: str, ..., use_ipc_db: bool = False):
        self.audit_id = audit_id
        self._use_ipc_db = use_ipc_db  # Feature flag
        if use_ipc_db:
            self._ipc_db = IPCDatabase(audit_id)

    async def run(self, send):
        if self._use_ipc_db:
            # New path: SQLite-based poller
            await self._run_with_ipc_db(send)
        else:
            # Legacy path: stdout parsing
            await self._run_with_stdout(send)
```

## Pattern 2: Feature Flagging for Safe Deployment

**What:** Wrap new implementations in runtime toggles that default to old behavior, enabling gradual rollout.

**When:** Any refactor where failure would be catastrophic, or where A/B testing of implementations is needed.

**Trade-offs:**
- **Pros:** Ship incomplete code safely, canary releases, instant rollback, A/B testing
- **Cons:** Code complexity, test matrix explosion, flags accumulate over time

**SecurityAgent Refactor Example:**

```python
# veritas/core/orchestrator.py

USE_SECURITY_AGENT_CLASS = os.getenv("VERITAS_SECURITY_AGENT_CLASS", "false").lower() == "true"

async def security_node(state: AuditState) -> dict:
    url = state.get("url", "")
    errors = state.get("errors", [])

    if USE_SECURITY_AGENT_CLASS:
        # New path: Proper agent class
        from agents.security_agent import SecurityAgent
        try:
            agent = SecurityAgent()
            result = await agent.analyze(
                url=url,
                modules_enabled=state.get("enabled_security_modules", [])
            )
            return {"security_results": result.to_dict()}
        except Exception as e:
            logger.error(f"SecurityAgent failed: {e}, falling back to legacy")
            # Continue to legacy path

    # Legacy path: Direct module calls (will be removed after validation)
    results = {}
    # ... existing security_node logic ...
    return {"security_results": results}
```

## Pattern 3: Repository Pattern for Data Persistence

**What:** Abstract data access behind interfaces, enabling storage backend changes without affecting business logic.

**When:** Migrating from in-memory storage to persistent storage, or supporting multiple storage backends.

**Trade-offs:**
- **Pros:** Storage backend agnostic, easier testing, clear data ownership boundaries
- **Cons:** Initial boilerplate, abstraction layer overhead, overengineering for simple CRUD

**Audit Storage Refactor Example:**

```python
# backend/services/audit_repository.py
from abc import ABC, abstractmethod
from typing import Optional

class AuditRepository(ABC):
    """Abstract repository for audit result persistence."""

    @abstractmethod
    async def save_audit(self, audit_id: str, result: dict) -> None:
        """Persist audit result."""
        pass

    @abstractmethod
    async def get_audit(self, audit_id: str) -> Optional[dict]:
        """Retrieve audit result."""
        pass

    @abstractmethod
    async def list_audits(self, limit: int = 100) -> list[dict]:
        """List recent audits."""
        pass

class InMemoryAuditRepository(AuditRepository):
    """In-memory repository (current implementation)."""

    def __init__(self):
        self._audits: dict[str, dict] = {}

    async def save_audit(self, audit_id: str, result: dict) -> None:
        self._audits[audit_id] = result

    async def get_audit(self, audit_id: str) -> Optional[dict]:
        return self._audits.get(audit_id)

    async def list_audits(self, limit: int = 100) -> list[dict]:
        return sorted(self._audits.values(), key=lambda x: x.get("timestamp", 0))[:limit]

class SQLiteAuditRepository(AuditRepository):
    """SQLite-based repository (new implementation)."""

    def __init__(self, db_path: str = "audits.db"):
        import sqlite3
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                audit_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    async def save_audit(self, audit_id: str, result: dict) -> None:
        import json
        self._conn.execute(
            "INSERT OR REPLACE INTO audits (audit_id, url, result_json) VALUES (?, ?, ?)",
            (audit_id, result.get("url", ""), json.dumps(result))
        )
        self._conn.commit()

# In backend/routes/audit.py
repository: AuditRepository

if os.getenv("VERITAS_USE_SQLITE_STORAGE", "false").lower() == "true":
    repository = SQLiteAuditRepository()
else:
    repository = InMemoryAuditRepository()
```

## Critical Pitfalls

### Pitfall 1: Fragile Stdout Parsing

**What goes wrong:** The backend parses subprocess stdout for `##PROGRESS:` markers, but any subprocess output change (logging, prints, errors) can break parsing.

**Why it happens:** Stdout is not a structured communication channel. Developers often add print statements that inadvertently match the marker pattern.

**Consequences:**
- Parser gets confused if subprocess outputs `{` characters
- Progress markers get missed if subprocess output contains the prefix naturally
- The entire audit pipeline fails on unexpected subprocess output

**Prevention:**
1. Replace stdout parsing with SQLite IPC (documented below)
2. If keeping stdout, use structured logging module and mark messages with severity-specific handlers
3. Prefix subprocess output with null bytes or other unambiguous delimiters

**Detection:**
- Audit completes but frontend shows no progress updates
- Logs show "Audit finished but final result JSON could not be parsed"
- Fallback JSON extraction triggered in audit_runner.py

### Pitfall 2: Sequential Instead of State Machine

**What goes wrong:** The orchestrator manually executes nodes sequentially instead of using LangGraph's `ainvoke()`, losing debugging, visualization, and true state management.

**Why it happens:** Python 3.14 asyncio CancelledError compatibility issue with LangGraph's `ainvoke()` implementation.

**Consequences:**
- No LangGraph visualization tools available
- State management is manual and error-prone
- Cannot use LangGraph's check-pointing for resumable audits
- Parallel execution of independent nodes is blocked

**Prevention:**
1. LangGraph Python 3.14 compatible (LOW confidence, research needed)
2. Keep sequential execution AS TEMPORARY WORKAROUND with:
   - Clear comment tracking the issue
   - Minimal manual state changes
   - Add state validation after each transition
3. Monitor LangGraph releases for Python 3.14 fix

**Detection:**
- `orchestrator.py:audit()` method contains explicit for-loop calling nodes
- `build_audit_graph()` function exists but is never invoked via `ainvoke()`

### Pitfall 3: Empty Return Stubs Masking Bugs

**What goes wrong:** Multiple functions return empty lists/dicts instead of raising errors, causing silent failures and partial results.

**Why it happens:** Incomplete features or placeholders left without proper error handling.

**Consequences:**
- False confidence in partial results
- Difficult to diagnose missing functionality
- Tests pass for wrong reasons (empty results accepted)

**Prevention:**
1. Replace all `return []` with `raise NotImplementedError("TODO: implement X")`
2. Add explicit check-in code review for empty returns
3. Add tests that expect NotImplementedError for incomplete features

**Detection:**
- Search for `return []` patterns in agents and analysis modules
- Run audits and check for incomplete evidence collection

### Pitfall 4: In-Memory Storage Losing Data

**What goes wrong:** All audit data stored in process-local dict, lost on backend restart.

**Why it happens:** No persistence layer implemented; initial development prioritized speed.

**Consequences:**
- No audit history or comparison
- Lost forensic evidence on restart
- Cannot debug past audits after the fact

**Prevention:**
1. Implement SQLiteAuditRepository (see Repository pattern above)
2. Add migration script to backload any recent audits
3. Add cron job for archival of old audits

**Detection:**
- Backend restart loses all audit state
- No way to query past audits via API

## Component Responsibilities

| Component | Responsibility | Should Communicate With |
|-----------|----------------|------------------------|
| **AuditRunner** | Subprocess spawning, event serialization | LangGraph Orchestrator (via IPC) |
| **SecurityAgent** | Security module orchestration | Orchestrator, analysis modules |
| **SQLite IPC** | Structured message queue between backend and veritas | AuditRunner, Orchestrator |
| **AuditRepository** | Audit result persistence | Backend API routes |
| **LangGraph Graph** | State machine definition and execution | All agents, routing functions |

## Data Flow

### Request Flow (Stabilized)

```
[User submits URL]
          ↓
[Next.js: POST /api/audit/start]
          ↓
[AuditRunner.run() createsAuditRunner]
          ↓
[Spawn subprocess with unique audit_id]
          ↓
[SQLite IPC initialized for audit_id]
          ↓
[Backend creates SQLitePoller coroutine]
          ↑                    ↓
[AuditRunner] ←─────── SQLite poll reads messages ───────→ [Veritas CLI]
          ↓                    ↓
[WebSocket.send_json()] ←─ Type conversion ──────────────────┘
          ↓
[Frontend receives structured events]
          ↓
[UI updates in real-time]
```

### State Management Flow

```
[LangGraph AuditState TypedDict]
          ↓
[Scout → Security → Vision → Graph → Judge]
          ↓                ↓              ↓
[Each node] → [Update state] → [Emit progress to SQLite]
          ↓
[State serialized → SQLite messages table]
          ↓
[Backend poller reads → WebSocket event]
          ↓
[Frontend store.update()]
```

## Stabilization Sequence

### Phase 1: IPC Stabilization (Week 1)

**Goal:** Replace fragile stdout parsing with robust SQLite IPC.

**Implementation Steps:**

1. **Create SQLite IPC Schema:**
```python
# veritas/core/ipc_db.py
class IPCDatabase:
    def __init__(self, audit_id: str, db_path: str = "ipc"):
        self._audit_id = audit_id
        self._db_path = f"{db_path}/{audit_id}.db"
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._setup_schema()

    def _setup_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase TEXT NOT NULL,
                step TEXT NOT NULL,
                pct INTEGER NOT NULL,
                detail TEXT,
                payload JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)

    def emit_progress(self, phase: str, step: str, pct: int, detail: str = "", **payload):
        """Emit a progress message."""
        import json
        self._conn.execute("""
            INSERT INTO messages (phase, step, pct, detail, payload, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (phase, step, pct, detail, json.dumps(payload)))
        self._conn.commit()

    def poll_messages(self, since_id: int = 0, timeout: float = 1.0):
        """Poll for new messages."""
        rows = self._conn.execute("""
            SELECT id, phase, step, pct, detail, payload
            FROM messages
            WHERE id > ? AND status = 'pending'
            ORDER BY id
            LIMIT 100
        """, (since_id,)).fetchall()

        if rows:
            msg_ids = [r[0] for r in rows]
            self._conn.executemany(
                "UPDATE messages SET status = 'delivered' WHERE id = ?",
                [(mid,) for mid in msg_ids]
            )
            self._conn.commit()

        return [
            {
                "id": r[0],
                "phase": r[1],
                "step": r[2],
                "pct": r[3],
                "detail": r[4],
                "payload": json.loads(r[5]) if r[5] else {}
            }
            for r in rows
        ]
```

2. **Update Orchestrator to Emit to SQLite:**
```python
# veritas/core/orchestrator.py
class VeritasOrchestrator:
    def __init__(self, use_ipc_db: bool = False):
        self._use_ipc_db = use_ipc_db
        if use_ipc_db:
            from core.ipc_db import IPCDatabase
            self._ipc = IPCDatabase(audit_id=os.getenv("AUDIT_ID", "default"))

    async def audit(self, url: str, ...) -> AuditState:
        # ... initialization ...

        def _emit(phase: str, step: str, pct: int, detail: str = "", **extra):
            if self._use_ipc_db:
                self._ipc.emit_progress(phase, step, pct, detail, **extra)
            else:
                # Legacy stdout path
                msg = {"phase": phase, "step": step, "pct": pct, "detail": detail}
                msg.update(extra)
                print(f"##PROGRESS:{_json.dumps(msg)}", flush=True)
```

3. **Update AuditRunner to Poll SQLite:**
```python
# backend/services/audit_runner.py
class AuditRunner:
    def __init__(self, audit_id: str, ..., use_ipc_db: bool = False):
        self.audit_id = audit_id
        self._use_ipc_db = use_ipc_db
        if use_ipc_db:
            from veritas.core.ipc_db import IPCDatabase
            self._ipc_db = IPCDatabase(audit_id)

    async def run(self, send):
        if self._use_ipc_db:
            await self._run_with_ipc_poller(send)
        else:
            await self._run_with_stdout_parser(send)

    async def _run_with_ipc_poller(self, send):
        last_id = 0
        poll_interval = 0.1  # 100ms

        while self._process.poll() is None:
            messages = self._ipc_db.poll_messages(last_id)
            for msg in messages:
                last_id = msg["id"]
                await self._handle_ipc_message(msg, send)
            await asyncio.sleep(poll_interval)
```

4. **Add Feature Flag:**
```python
# backend/main.py
USE_SQLITE_IPC = os.getenv("VERITAS_USE_SQLITE_IPC", "false").lower() == "true"

# In audit start route
if USE_SQLITE_IPC:
    runner = AuditRunner(audit_id, url, tier, verdict_mode, security_modules, use_ipc_db=True)
else:
    runner = AuditRunner(audit_id, url, tier, verdict_mode, security_modules, use_ipc_db=False)
```

**Testing Strategy:**
1. Characterization test: Run multiple audits with both path, compare event sequences
2. Load test: Simulate 10 concurrent audits, verify no connection pool exhaustion
3. Fallback test: Intentionally corrupt SQLite file, verify graceful degradation to stdout

### Phase 2: Security Agent Class Refactor (Week 2)

**Goal:** Create proper SecurityAgent class following Vision/Judge agent patterns.

**Implementation Steps:**

1. **Create SecurityAgent class structure:**
```python
# veritas/agents/security_agent.py (new file)
@dataclass
class SecurityResult:
    """Result from security analysis."""
    url: str
    score: float = 0.5           # 0-1, higher = more secure
    modules_run: list[str] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    module_results: dict = field(default_factory=dict)  # Per-module detailed results

    def to_dict(self) -> dict:
        """Serialize for state storage."""
        return {
            "url": self.url,
            "score": round(self.score, 3),
            "modules_run": self.modules_run,
            "findings": self.findings,
            "errors": self.errors,
            "module_results": self.module_results,
        }


class SecurityAgent:
    """
    Agent: Security analysis coordinator.

    Usage:
        agent = SecurityAgent()
        result = await agent.analyze(url, modules_enabled=["security_headers", "phishing_db"])
    """

    def __init__(self):
        self._analyzers = {
            "security_headers": None,  # Lazy-loaded
            "phishing_check": None,
            "redirect_analysis": None,
        }

    async def analyze(
        self,
        url: str,
        modules_enabled: Optional[list[str]] = None,
        timeout: int = 30
    ) -> SecurityResult:
        """Run enabled security modules against URL."""
        result = SecurityResult(url=url)

        if not modules_enabled:
            modules_enabled = ["security_headers", "phishing_check"]

        logger.info(f"SecurityAgent analyzing {url} | modules={modules_enabled}")

        # Analyze headers
        if "security_headers" in modules_enabled:
            await self._analyze_headers(result)

        # Check phishing database
        if "phishing_db" in modules_enabled:
            await self._check_phishing(result)

        # Analyze redirect chain
        if "redirect_chain" in modules_enabled:
            await self._analyze_redirects(result)

        # Compute aggregate security score
        result.score = self._compute_score(result)

        return result

    async def _analyze_headers(self, result: SecurityResult):
        """Analyze HTTP security headers."""
        try:
            from analysis.security_headers import SecurityHeaderAnalyzer
            header_obj = SecurityHeaderAnalyzer()
            res = await header_obj.analyze(result.url)
            result.modules_run.append("security_headers")
            result.module_results["security_headers"] = res.to_dict()
            result.score = (result.score + res.score) / 2
        except Exception as e:
            logger.error(f"Header analysis failed: {e}")
            result.errors.append(f"security_headers: {e}")

    def _compute_score(self, result: SecurityResult) -> float:
        """Compute aggregate security score from module results."""
        if result.errors:
            # Penalize for failed modules
            return max(0.0, result.score - (len(result.errors) * 0.1))
        return result.score
```

2. **Update orchestrator security_node with feature flag:**
```python
USE_SECURITY_AGENT_CLASS = os.getenv("VERITAS_SECURITY_AGENT_CLASS", "false").lower() == "true"

async def security_node(state: AuditState) -> dict:
    url = state.get("url", "")
    errors = state.get("errors", [])

    if USE_SECURITY_AGENT_CLASS:
        # NEW PATH: Use proper agent class
        try:
            from agents.security_agent import SecurityAgent
            agent = SecurityAgent()
            result = await agent.analyze(
                url=url,
                modules_enabled=state.get("enabled_security_modules", [])
            )
            return {"security_results": result.to_dict()}
        except Exception as e:
            logger.error(f"SecurityAgent failure, falling back: {e}")
            errors.append(f"SecurityAgent: {e}")

    # LEGACY PATH: Direct module instantiation (existing code)
    results = {}
    # ... existing security_node logic ...
    return {"security_results": results}
```

**Testing Strategy:**
1. Integration test: Run security_agent.analyze() directly, compare results to legacy path
2. Output comparison: Verify to_dict() produces same structure as legacy
3. Error handling test: Force module to fail, verify graceful degradation

### Phase 3: LangGraph Execution Investigation (Week 3)

**Goal:** Investigate and resolve Python 3.14 asyncio CancelledError blocking LangGraph ainvoke.

**Investigation Steps:**

1. **Reproduce the issue in isolation:**
```python
# test_langgraph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    value: int

async def add_one(state: State) -> dict:
    return {"value": state["value"] + 1}

def route(state: State) -> str:
    return "continue" if state["value"] < 3 else END

graph = StateGraph(State)
graph.add_node("add_one", add_one)
graph.set_entry_point("add_one")
graph.add_conditional_edges("add_one", route, {"continue": "add_one", "end": END})

compiled = graph.compile()

# This is expected to fail on Python 3.14
import asyncio
async def main():
    try:
        result = await compiled.ainvoke({"value": 0})
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

2. **If bug confirmed, options:**
   - **Option A:** Pin Python version to 3.13 (safest, but requires env change)
   - **Option B:** File issue with LangGraph and wait for fix (longest time, may never be fixed)
   - **Option C:** Continue with sequential execution AS DOCUMENTED WORKAROUND (most pragmatic)

3. **If continuing sequential execution:**
   - Add clear docstring explaining the workaround
   - Add tracking issue in repo for LangGraph fix
   - Add state validation after each transition
   - Add metrics for each phase duration

**Testing Strategy:**
1. Reproduction script to verify bug exists
2. Test on different Python versions (3.12, 3.13)
3. If pinning Python, verify all test suite passes on pinned version

### Phase 4: Empty Stub Cleanup (Week 4)

**Goal:** Replace all silent-empty returns with explicit errors.

**Implementation Steps:**

1. **Audit all empty return statements:**
```bash
# Find all problematic patterns
grep -rn "return \[\]" veritas/agents/*.py
grep -rn "return \{\}" veritas/agents/*.py
grep -rn "return \[\]" veritas/analysis/*.py
grep -rn "return \{\}" veritas/analysis/*.py
grep -rn "return \[\]" veritas/core/evidence_store.py
```

2. **Create a helper for TODO features:**
```python
# veritas/utils.py
class NotYetImplementedError(NotImplementedError):
    """For features under active development."""
    pass

def raise_not_implemented(feature: str, context: str = ""):
    """Standardized error for incomplete features."""
    msg = f"Not yet implemented: {feature}"
    if context:
        msg += f" ({context})"
    raise NotYetImplementedError(msg)
```

3. **Replace empty returns systematically:**

**Example: veritas/agents/judge.py (Line 943, 960)**
```python
# BEFORE:
def _extract_verdict_from_vlm(self, prompt: str) -> JudgeDecision:
    # TODO: Integrate VLM for verdict generation
    return []

# AFTER:
def _extract_verdict_from_vlm(self, prompt: str) -> JudgeDecision:
    """Extract verdict from VLM (not yet implemented)."""
    raise_not_implemented(
        "VLM-based verdict extraction",
        "awaiting NIMClient integration for verdict synthesis"
    )
```

**Example: veritas/core/evidence_store.py (multiple locations)**
```python
# BEFORE:
def find_similar_cases(self, vector: list[float], top_k: int = 5) -> list[Evidence]:
    # TODO: Implement vector similarity search
    return []

# AFTER:
def find_similar_cases(self, vector: list[float], top_k: int = 5) -> list[Evidence]:
    """Find similar historical cases by vector similarity."""
    raise_not_implemented(
        "Vector similarity search",
        "requires LanceDB vector index configuration"
    )
```

4. **Add tests for NotImplementedError propagation:**
```python
# tests/test_not_implemented.py
import pytest
from agents.judge import JudgeAgent

def test_unimplemented_verdict_extraction_raises():
    judge = JudgeAgent()
    with pytest.raises(NotImplementedError):
        judge._extract_verdict_from_vlm("test prompt")
```

**Testing Strategy:**
1. Change review checklist: Verify no new empty returns introduced
2. Run test suite, expect failures at NotImplementedError points (fix or document)
3. Add monitoring to track NotImplementedError occurrences in production

### Phase 5: Persistent Audit Storage (Week 5)

**Goal:** Implement SQLite-based audit result persistence.

**Implementation Steps:**

1. **Create repository interface (pattern documented above)**
2. **Implement SQLiteAuditRepository**
3. **Add migration for existing audits:**
```python
# scripts/migrate_audits_to_sqlite.py
async def migrate_memory_audits_to_sqlite():
    """Migrate in-memory audits to SQLite."""
    # This runs once when enabled
    in_memory = InMemoryAuditRepository()
    sqlite_repo = SQLiteAuditRepository()

    for audit_id, result in in_memory._audits.items():
        await sqlite_repo.save_audit(audit_id, result)
        print(f"Migrated {audit_id}")
```

4. **Add feature flag:**
```python
# backend/main.py
USE_SQLITE_STORAGE = os.getenv("VERITAS_USE_SQLITE_STORAGE", "false").lower() == "true"

if USE_SQLITE_STORAGE:
    audit_repository = SQLiteAuditRepository()
else:
    audit_repository = InMemoryAuditRepository()
```

**Testing Strategy:**
1. Integration test: Save audit, restart backend, retrieve audit
2. Performance test: Measure query time with 10K audits
3. Concurrent test: Multiple auditors reading/writing simultaneously

## What Not To Do During Stabilization

### Anti-Pattern 1: Parallel Feature Development

**What people do:** Start implementing new features (5-pass Vision Agent, OSINT sources) while stabilizing existing code.

**Why it's wrong:** Increases attack surface, harder to attribute bugs to stabilization vs features, extends timeline for both.

**Do this instead:** Complete stabilization first, freeze feature work, then start feature implementation.

### Anti-Pattern 2: Big-Bang Replacements

**What people do:** Replace stdout parsing with SQLite in one commit, delete all old code immediately.

**Why it's wrong:** High risk, difficult to rollback, no fallback if issues arise.

**Do this instead:** Keep both paths via feature flags, run in parallel for 1-2 weeks, monitor metrics, then cut over.

### Anti-Pattern 3: Skipping Tests for "Just a Refactor"

**What people do:** No tests for IPC replacement, SecurityAgent refactor because "it's just renaming code."

**Why it's wrong:** Refactors introduce bugs that tests would catch; without tests, bugs propagate silently.

**Do this instead:** Write characterization tests before refactoring, verify behavior preserved, add new tests for refactored code.

### Anti-Pattern 4: Fixing Unrelated Issues

**What people do:** While stabilizing IPC, also fix unrelated lint errors, add comments, refactor other modules.

**Why it's wrong:** Increases scope, dilutes focus, harder to review, harder to rollback stabilization.

**Do this instead:** Scope creep control - only changes related to the stabilization concern, defer other improvements.

## Testing Strategy for Stabilization

### 1. Characterization Tests (Before Refactoring)

Create tests that document current behavior:

```python
# tests/test_security_node_characterization.py
import pytest
from veritas.core.orchestrator import security_node, AuditState

@pytest.mark.skipif(not os.getenv("RUN_CHARACTERIZATION_TESTS"), reason="expensive")
async def test_security_node_characterization():
    """Document current security_node behavior before refactoring."""
    state = AuditState(
        url="https://example.com",
        audit_tier="standard_audit",
        iteration=1,
        max_iterations=5,
        max_pages=5,
        status="running",
        scout_results=[],
        # ... required fields ...
    )

    result = await security_node(state)

    # Document current output structure
    assert "security_results" in result
    assert isinstance(result["security_results"], dict)

    # Document which modules currently run
    results = result["security_results"]
    assert "security_headers" in results or results == {}  # Current behavior
```

### 2. Change Detection Tests (After Refactoring)

Tests that verify behavior is preserved:

```python
# tests/test_security_agent_compatibility.py
@pytest.mark.asyncio
async def test_securityagent_produces_same_output_as_legacy():
    """Verify SecurityAgent produces output compatible with legacy path."""
    url = "https://example.com"

    # Run legacy path
    leg_state = create_test_state(url)
    legacy_result = await security_node(leg_state)

    # Run new path
    from agents.security_agent import SecurityAgent
    agent = SecurityAgent()
    new_result = await agent.analyze(url)

    # Structure must match
    assert set(new_result.module_results.keys()) == set(legacy_result["security_results"].keys())
```

### 3. Integration Tests (End-to-End)

Tests that verify entire flow works:

```python
# tests/test_audit_integration.py
@pytest.mark.asyncio
async def test_ipc_sqlite_audit_completes():
    """Full audit runs successfully with SQLite IPC."""
    from backend.services.audit_runner import AuditRunner
    from veritas.core.ipc_db import IPCDatabase
    import tempfile

    audit_id = "test_sqlite_ipc"
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup IPC
        ipc = IPCDatabase(audit_id, db_path=tmpdir)

        # Run audit
        events_received = []
        async def mock_send(event):
            events_received.append(event)

        runner = AuditRunner(audit_id, "https://example.com", "quick_scan", use_ipc_db=True)
        runner._ipc_db = ipc
        await runner.run(mock_send)

        # Verify events received
        assert len(events_received) > 0
        assert any(e["type"] == "audit_complete" for e in events_received)
```

### 4. Load Tests (Concurrent Scenarios)

Tests for concurrent operation:

```python
# tests/test_ipc_concurrent.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_audits_with_sqlite_ipc():
    """10 concurrent audits should not conflict."""
    tasks = []
    for i in range(10):
        runner = AuditRunner(f"audit_{i}", "https://example.com", "quick_scan", use_ipc_db=True)
        tasks.append(runner.run(lambda e: None))

    await asyncio.gather(*tasks)

    # Verify all audits completed
    for i in range(10):
        assert Path(f"ipc/audit_{i}.db").exists()
```

## Sources

- **SQLite IPC:** Python 3.14 sqlite3 official documentation (HIGH confidence)
- **Agent Patterns:** Existing VisionAgent, JudgeAgent codebase (HIGH confidence)
- **Strangler Fig:** Martin Fowler's blog on gradual system migration (MEDIUM confidence - WebFetch unavailable, based on knowledge)
- **Feature Flagging:** Martin Fowler's feature toggles article (HIGH confidence - verified via WebFetch)
- **LangGraph:** docs.langchain.com (LOW confidence - WebFetch redirected, ainvoke patterns not verified)
- **NotImplementedError:** PEP 8 Python style guide (HIGH confidence - verified via WebFetch)

---

*Stabilization research for: VERITAS Brownfield Forensic Auditing Platform*
*Researched: 2026-02-20*
