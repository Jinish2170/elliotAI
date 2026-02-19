# Architecture

**Analysis Date:** 2026-02-19

## Pattern Overview

**Overall:** 3-tier Async Event-Stream Architecture with LangGraph State Machine Orchestration

**Key Characteristics:**
- **Sequential Phase-Based Pipeline**: 5 AI agents execute in order (Scout → Security → Vision → Graph → Judge) with cyclic reasoning loops back to Scout when more investigation is needed
- **State Machine Orchestration**: LangGraph StateGraph manages audit lifecycle, transitions, and budget controls (max_iterations, max_pages, nim_call_budget)
- **Subprocess Isolation**: Backend runs Veritas engine as detached subprocess via subprocess.Popen to avoid Py3.14 asyncio compatibility issues
- **Stdout Event Streaming**: Python CLI emits ##PROGRESS markers, Backend AuditRunner parses and converts to typed WebSocket events
- **4-Level AI Fallback**: Primary NIM VLM → Fallback NIM VLM → Tesseract OCR + Heuristics → Manual Review (no service dependencies)
- **Real-Time Progress Feedback**: WebSocket streams phased progress events (phase_start, phase_complete, finding, screenshot, stats_update, audit_complete)

## Layers

**Presentation Layer (Next.js 15):**
- Purpose: User interface for landing, live audit view, forensic report display
- Location: `frontend/src/`
- Contains: React App Router pages (landing, audit/[id], report/[id]), components, hooks, store
- Depends on: FastAPI Backend via REST + WebSocket
- Used by: End users (web browser)

**API Layer (FastAPI):**
- Purpose: REST endpoints for audit lifecycle, WebSocket streaming for real-time events
- Location: `backend/`
- Contains: FastAPI app, route handlers, audit subprocess wrapper
- Depends on: Veritas Python engine (subprocess execution)
- Used by: Next.js frontend via HTTP/WebSocket

**Orchestration Layer (Veritas Engine):**
- Purpose: LangGraph state machine managing all phases of forensic audit
- Location: `veritas/core/orchestrator.py`, `veritas/agents/`
- Contains: State graph definition, node functions (scout_node, security_node, vision_node, graph_node, judge_node), routing logic
- Depends on: All agents, analysis modules, core services (NIMClient, EvidenceStore)
- Used by: Backend via subprocess invocation

**Agent Layer (5 AI Agents):**
- Purpose: Specialized forensic analysis per phase
- Location: `veritas/agents/`
- Contains: Scout (StealthScout), Vision (VisionAgent), Graph Investigator (GraphInvestigator), Judge (JudgeAgent)
- Depends on: Analysis modules, NIMClient, Playwright, WHOIS/DNS/SSL APIs
- Used by: Orchestrator as graph nodes

**Analysis Layer (22+ Analysis Modules):**
- Purpose: Zero-AI rule-based checks for security, structure, patterns
- Location: `veritas/analysis/`
- Contains: DOMAnalyzer, FormActionValidator, JSAnalyzer, MetaAnalyzer, PatternMatcher, PhishingChecker, RedirectAnalyzer, SecurityHeaderAnalyzer, TemporalAnalyzer
- Depends on: BeautifulSoup, pyquery, httpx for HTTP inspection
- Used by: Scout (dom分析, form验证), Security node (headers, phishing检查, redirects)

**Core Infrastructure Layer:**
- Purpose: Shared services for AI API, evidence persistence, external lookups
- Location: `veritas/core/`
- Contains: NIMClient (4-level fallback), EvidenceStore (LanceDB), WebSearcher (Tavily), TorClient (.onion support)
- Depends on: OpenAI SDK (NIM async), LanceDB, httpx, Tavily API
- Used by: All agents and orchestrator

## Data Flow

**End-to-End Audit Flow:**

1. **User Request**: Frontend form submits URL to Backend `POST /api/audit/start`
   - Returns `audit_id` and WebSocket URL `/api/audit/stream/{audit_id}`

2. **Backend Subprocess Spawn**: AuditRunner.run() spawns `python -m veritas <url> --tier <tier> --json`
   - Uses subprocess.Popen + asyncio.run_in_executor for Windows compatibility
   - Reads stdout line-by-line for ##PROGRESS markers and final JSON result

3. **Orchestrator Sequential Execution**: VeritasOrchestrator.audit() runs graph nodes sequentially
   - START → scout_node → security_node → vision_node → graph_node → judge_node → [route decision]
   - If judge requests more investigation → back to scout_node with new URLs
   - Emits ##PROGRESS:{"phase":"scout","step":"done","pct":25,...} to stdout

4. **Agent Execution** (per iteration):
   - **Scout**: Playwright stealth browser captures t0 screenshot, waits TEMPORAL_DELAY, captures t+delay screenshot, full-page screenshot, extracts DOM metadata, detects CAPTCHA
   - **Security**: Runs enabled modules (security_headers, phishing_db, redirect_chain, js_analysis, form_validation) concurrently
   - **Vision**: All screenshots sent to NIM VLM for dark pattern detection with category-specific prompts
   - **Graph**: WHOIS, DNS, SSL, Tavily search for entity verification against website claims
   - **Judge**: Computes weighted trust score, generates forensic narrative, determines if more pages needed

5. **WebSocket Event Stream**: AuditRunner parses stdout and sends typed events
   - `phase_start`: agent beginning work
   - `phase_complete`: agent finished with summary stats
   - `screenshot`: base64-encoded image with label/index
   - `finding`: dark pattern detection with category, severity, evidence
   - `stats_update`: running counters (pages, screenshots, findings, ai_calls)
   - `audit_result`: final verdict with trust_score, risk_level, narrative, recommendations
   - `audit_complete`: audit_id and elapsed time

6. **Frontend State Update**: useAuditStream hook connects WebSocket to Zustand store
   - store.handleEvent() updates state based on event type
   - Components (AgentPipeline, EvidencePanel, NarrativeFeed, ForensicLog) reactively render

7. **Report Completion**: User navigates to `/report/{audit_id}` after audit completes
   - Displays trust score gauge, signal radar chart, dark patterns grid, entity details, recommendations

**State Management:**

- **LangGraph State**: TypedDict `AuditState` flows through all nodes containing scout_results, vision_result, graph_result, judge_decision, pending_urls, errors, budget counters
- **Frontend Store**: Zustand store with audit info, phase states, findings, screenshots, logs, final result
- **Evidence Persistence**: LanceDB vector store at `veritas/data/vectordb/` for similar-case lookup (implemented in EvidenceStore but not actively used in current flow)

## Key Abstractions

**AuditState (LangGraph TypedDict):**
- Purpose: Shared state passed between graph nodes, enables cyclic investigation loops
- Examples: `veritas/core/orchestrator.py:49-93`
- Pattern: TypedDict with serializable field types allowing JSON serialization and LangGraph checkpointing
- Key fields: url, audit_tier, iteration, max_iterations, max_pages, scout_results, vision_result, graph_result, judge_decision, pending_urls, investigated_urls, status, errors, nim_calls_used, site_type, verdict_mode, security_results

**Agent Result Dataclasses:**
- Purpose: Type-safe result containers with deserialization methods for state passage
- Examples: `ScoutResult` (veritas/agents/scout.py), `VisionResult` (veritas/agents/vision.py), `GraphResult` (veritas/agents/graph_investigator.py), `JudgeDecision` (veritas/agents/judge.py)
- Pattern: dataclass with typed fields; orchestrator serializes to dict for state, reconstructs for Judge deliberation
- Key fields: status, evidence (screenshots, findings, verifications), metadata, diagnostics

**SubSignal + TrustScoreResult (Weighted Scoring):**
- Purpose: Structured trust signal composition with site-type weight overrides
- Examples: `veritas/config/trust_weights.py:SubSignal`, `TrustScoreResult`
- Pattern: Each signal has raw_score (0-1), confidence (0-1), evidence_count, details; TrustScoreResult aggregates with overrides applied
- Signals: visual, structural, temporal, graph, meta, security (6 total)

**WebSocket Event Types:**
- Purpose: Typed contract between Backend AuditRunner and Frontend store
- Examples: `frontend/src/lib/types.ts:AuditEvent`, `backend/routes/audit.py:WebSocket handler`
- Pattern: JSON objects with `type` field determining handler; specific payloads per type (phase_start, finding, screenshot, audit_result)
- Key types: phase_start, phase_complete, phase_error, finding, screenshot, stats_update, site_type, security_result, audit_result, audit_complete

**Analysis Module Interface:**
- Purpose: Zero-AI checks that return structured results
- Examples: `DOMAnalyzer.analyze()`, `SecurityHeaderAnalyzer.analyze()`, `FormActionValidator.validate()`, `PhishingChecker.check()`
- Pattern: Async method returning dataclass with score, findings, errors; non-blocking with consistent timeout handling
- Consistent fields: score (float 0-1), findings (list), errors (list), timestamp

## Entry Points

**CLI Entry Point:**
- Location: `veritas/__main__.py`
- Triggers: `python -m veritas <url> --tier <tier> --verdict-mode <simple|expert> --json`
- Responsibilities: Argument parsing, VeritasOrchestrator instantiation, run_audit async execution, progress emission, JSON result output, optional report generation

**Backend API Entry Point:**
- Location: `backend/main.py`
- Triggers: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Responsibilities: FastAPI app setup, CORS middleware, route registration (health, audit), sys.path configuration for veritas import

**Frontend Web Entry Point:**
- Location: `frontend/src/app/page.tsx` (root), `frontend/src/app/audit/[id]/page.tsx` (live audit), `frontend/src/app/report/[id]/page.tsx` (report)
- Triggers: `npm run dev` (Next.js dev server on port 3000)
- Responsibilities: UI rendering, WebSocket connection via useAuditStream hook, store state management, component composition

**Streamlit UI Entry Point (Alternative):**
- Location: `veritas/ui/app.py`
- Triggers: `streamlit run veritas/ui/app.py`
- Responsibilities: Alternative web UI for manual CLI execution (not used in main flow)

## Error Handling

**Strategy: Graceful degradation with 4-level fallback**

**Patterns:**

1. **NIM AI Fallback Chain** (`veritas/core/nim_client.py`):
   - Level 1: Primary NVIDIA VLM model fails → try Level 2
   - Level 2: Fallback VLM model fails → try Level 3
   - Level 3: Tesseract OCR + heuristics fails → Level 4 (no AI, manual review)
   - All levels cache responses (24h TTL) to reduce retry burden

2. **Scout Navigation Retry** (`veritas/agents/scout.py:_safe_navigate`):
   - Tries wait_until strategies in order: networkidle → domcontentloaded → load → commit
   - Returns ScoutResult with status TIMEOUT if all strategies fail
   - Orchestrator tracks scout_failures; aborts after 3 consecutive failures with no successful results

3. **LangGraph Sequential Execution** (`veritas/core/orchestrator.py:audit`):
   - Each node wrapped in try/except, errors appended to state["errors"]
   - Failed nodes still emit ##PROGRESS with step="error"
   - Final status can be "completed", "error", or "aborted"

4. **Budget Protection** (`veritas/config/settings.py:AUDIT_TIERS`):
   - max_iterations: hard cap on agent cycles (default 5)
   - max_pages: hard cap on total pages scouted per tier (1-10)
   - nim_call_budget: soft cap tracked via NIMClient.call_count
   - force_verdict_node runs when budget exhausted but Judge wanted more investigation

5. **Windows Subprocess Compatibility** (`backend/services/audit_runner.py`):
   - Uses subprocess.Popen + asyncio.run_in_executor instead of asyncio.create_subprocess_exec
   - Avoids Python 3.14 asyncio.CancelledError incompatibility on Windows
   - Separate _drain_stderr task prevents pipe backpressure deadlocks

## Cross-Cutting Concerns

**Logging:**
- Python: `logging` module with level-based filtering; logger instances per module (veritas.scout, veritas.vision, etc.)
- Frontend: Browser console via log_entry WebSocket events; severity mapped to level key
- Progress: ##PROGRESS markers for structured event streaming

**Validation:**
- Pydantic models for FastAPI request/response (AuditStartRequest, AuditStartResponse)
- Type hints throughout Python codebase (TypedDict, dataclass)
- TypeScript type definitions in `frontend/src/lib/types.ts`

**Authentication:**
- Not implemented (public API)
- NVIDIA API key via environment variable (NVIDIA_NIM_API_KEY)
- Tavily API key optional (TAVILY_API_KEY)

---

*Architecture analysis: 2026-02-19*
