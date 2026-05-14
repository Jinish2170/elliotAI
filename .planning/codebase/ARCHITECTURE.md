# Architecture
**Analysis Date:** 2026-05-14

## Pattern Overview

**Overall:** Multi-agent forensic pipeline orchestrated as a LangGraph `StateGraph`, wrapped by a FastAPI REST + WebSocket backend, fronted by a Next.js (App Router) single-page UI. The backend does not run the audit in-process — it spawns the `elliot` package as a Python subprocess (CLI) and streams its progress events back over a WebSocket. The audit engine itself is a cyclic state machine: SCOUT -> SECURITY -> VISION -> GRAPH -> JUDGE, with JUDGE able to loop back to SCOUT for deeper investigation.

**Key Characteristics:**
- Agent-per-responsibility design: Scout (browser/evidence), Security (vuln modules), Vision (VLM dark-pattern detection), Graph (entity/OSINT/CTI verification), Judge (verdict synthesis).
- Graph nodes are thin adapters (`elliot/core/nodes/`) that call rich agent classes (`elliot/agents/`).
- Shared mutable state is a single `TypedDict` (`AuditState`) threaded through every node; nodes return partial-dict updates.
- Process isolation: backend (`backend/main.py`) <-> audit engine (`python -m elliot`) communicate via subprocess stdout markers (`##PROGRESS:`) or a `multiprocessing.Queue` (IPC mode selectable).
- Defensive/degradable: every agent has a registered fallback, circuit breakers, adaptive timeouts, and a "force verdict" escape hatch when budgets are exhausted.
- 4-level inference fallback chain in `NIMClient` (primary VLM -> fallback VLM -> Tesseract OCR -> no-AI stub).
- Feature-flagged behavior via environment variables and percentage rollouts (`should_use_db_persistence`, `should_use_security_agent`, IPC mode).

## Layers

### Presentation Layer (Frontend)
- **Purpose:** Live audit dashboard, history, comparison, and report views.
- **Location:** `frontend/src/`
- **Contains:** Next.js App Router pages (`frontend/src/app/`), React components (`frontend/src/components/`), Zustand global store (`frontend/src/lib/store.ts`), WebSocket streaming hook (`frontend/src/hooks/useAuditStream.ts`), event ordering hook (`frontend/src/hooks/useEventSequencer.ts`), shared types (`frontend/src/lib/types.ts`).
- **Depends on:** Backend REST API (`/api/audit/*`) and WebSocket (`/api/audit/stream/{id}`).
- **Used by:** End users (browser).

### API Layer (Backend)
- **Purpose:** HTTP/WebSocket gateway; audit lifecycle, persistence, and event streaming.
- **Location:** `backend/`
- **Contains:** FastAPI app + CORS + lifespan/DB init (`backend/main.py`), route handlers (`backend/routes/audit.py`, `backend/routes/health.py`), the subprocess driver/event translator (`backend/services/audit_runner.py`).
- **Depends on:** Audit Engine (spawned as subprocess), Persistence Layer (`elliot/db/`), screenshot storage (`elliot/screenshots/storage.py`), config (`elliot/config/settings.py`).
- **Used by:** Frontend.

### Orchestration Layer (Audit Engine core)
- **Purpose:** Wire agents into the cyclic audit state machine; manage budgets, iterations, timeouts, degradation, and progress emission.
- **Location:** `elliot/core/`
- **Contains:** LangGraph builder + `ElliotOrchestrator` (`elliot/core/orchestrator.py`), graph node adapters (`elliot/core/nodes/`), routing logic (`elliot/core/nodes/routing.py`), cross-cutting infra: `nim_client.py`, `ipc.py`, `complexity_analyzer.py`, `timeout_manager.py`, `degradation.py`, `circuit_breaker.py`, `evidence.py`/`evidence_store.py`, `progress/` (emitter, estimator, rate limiter).
- **Depends on:** Agent Layer, Config Layer, OSINT Layer, Quality Layer.
- **Used by:** CLI entry point (`elliot/__main__.py`), which is invoked by `backend/services/audit_runner.py`.

### Agent Layer
- **Purpose:** The five domain specialists that actually perform the audit work.
- **Location:** `elliot/agents/`
- **Contains:** `scout.py` (+ `scout_nav/` link explorer, scroll orchestrator, lazy-load detector), `vision.py` (+ `vision/temporal_analysis.py`), `graph_investigator.py`, `judge.py` (+ `judge_core/strategies/`, `judge_core/verdict/`), `security_agent.py`.
- **Depends on:** Analysis Layer, OSINT Layer, CWE Layer, Quality Layer, `NIMClient`, Config Layer.
- **Used by:** Orchestration Layer (`elliot/core/nodes/`).

### Analysis Layer
- **Purpose:** Stateless analyzers and security-module implementations consumed by agents.
- **Location:** `elliot/analysis/`
- **Contains:** `dom_analyzer.py`, `js_analyzer.py`, `meta_analyzer.py`, `phishing_checker.py`, `redirect_analyzer.py`, `temporal_analyzer.py`, `form_validator.py`, `pattern_matcher.py`, `exploitation_advisor.py`, `scenario_generator.py`, `security_headers.py`, and the `security/` subpackage (OWASP modules in `security/owasp/`, plus `cookies.py`, `csp.py`, `tls_ssl.py`, `gdpr.py`, `pci_dss.py`, `darknet.py`, `social_engineering.py`).
- **Depends on:** Config Layer, CWE Layer.
- **Used by:** Security Agent, Graph Investigator, Vision Agent.

### OSINT / Threat Intelligence Layer
- **Purpose:** External reputation, CTI, IOC detection, and darknet correlation with a reputation feedback loop.
- **Location:** `elliot/osint/` and `elliot/darknet/`
- **Contains:** `orchestrator.py` (OSINT fan-out), `cti.py`, `ioc_detector.py`, `reputation.py` (JSON-backed source reputation store), `attack_patterns.py`, `vulnerability_mapper.py`, `social_engineering.py`, `cache.py`, and `sources/` (per-source adapters: `whois_lookup.py`, `dns_lookup.py`, `ssl_verify.py`, `urlvoid.py`, `abuseipdb.py`, `tavily_source.py`, `darknet_*.py`). `elliot/darknet/` adds `onion_detector.py`, `threat_scraper.py`, `tor_client.py`.
- **Depends on:** Config Layer (API keys, feature flags), external APIs.
- **Used by:** Graph Investigator, Scout (IOC detection), Orchestrator (reputation grading).

### Quality / Scoring Layer
- **Purpose:** Confidence scoring, multi-source consensus, validation state, and trust-score computation.
- **Location:** `elliot/quality/`, `elliot/config/trust_weights.py`, `elliot/cwe/`
- **Contains:** `quality/confidence_scorer.py`, `quality/consensus_engine.py`, `quality/validation_state.py`; `config/trust_weights.py` (`compute_trust_score`, `SubSignal`, `RiskLevel`, override rules); `cwe/cvss_calculator.py`, `cwe/cvss_v31.py`, `cwe/registry.py`.
- **Depends on:** Config Layer.
- **Used by:** Judge Agent, Security Agent, Graph Investigator, routing `force_verdict_node`.

### Persistence Layer
- **Purpose:** SQLite-backed audit history (feature-flagged).
- **Location:** `elliot/db/` and `elliot/screenshots/`
- **Contains:** async engine + `init_database` + `get_db` dependency (`elliot/db/__init__.py`), `config.py` (DATABASE_URL, WAL pragmas, `Base`), `models.py` (`Audit`, `AuditFinding`, `AuditScreenshot`, `AuditStatus`), `repositories.py` (`AuditRepository`), screenshot file storage (`elliot/screenshots/storage.py`).
- **Depends on:** SQLAlchemy async + aiosqlite.
- **Used by:** Backend routes (`backend/routes/audit.py`) and health check.

### Config Layer
- **Purpose:** Central settings, taxonomies, weights, and rule definitions.
- **Location:** `elliot/config/`
- **Contains:** `settings.py` (paths, NIM endpoints, `AUDIT_TIERS`, budgets, `JUDGE_THRESHOLDS`, feature-flag helpers), `dark_patterns.py` (`DARK_PATTERN_TAXONOMY` + VLM prompts), `trust_weights.py`, `site_types.py`, `security_rules.py`, `darknet_rules.py`.
- **Depends on:** `.env` (via `python-dotenv`).
- **Used by:** Every other layer.

### Reporting Layer
- **Purpose:** Render audit results into PDF/HTML reports.
- **Location:** `elliot/reporting/` and `elliot/reporters/`
- **Contains:** `reporting/report_generator.py` (Jinja2 + WeasyPrint, HTML fallback), `reporting/templates/`, `reporters/darknet_reporter.py`.
- **Depends on:** Config Layer, audit result dicts.
- **Used by:** CLI (`elliot/__main__.py --report`).

## Data Flow

### 1. Audit request -> live stream (primary flow)
1. Frontend `CommandInput` posts `POST /api/audit/start` with `{url, tier, verdict_mode, security_modules}`.
2. `backend/routes/audit.py::start_audit` generates an `audit_id` (`vrts_<8hex>`), stores metadata in the in-memory `_audits` dict, returns `{audit_id, ws_url}`.
3. Frontend opens WebSocket `GET /api/audit/stream/{audit_id}`; `stream_audit` accepts the connection, persists a `RUNNING` `Audit` row (if `should_use_db_persistence()`), and constructs an `AuditRunner`.
4. `AuditRunner.run` does a pre-flight HEAD/GET reachability check, then spawns the audit engine: `python -m elliot <url> --tier ... --verdict-mode ... --json` (optionally `--use-queue-ipc`).
5. The subprocess emits `##PROGRESS:{json}` lines to stdout (or `ProgressEvent` objects to a `multiprocessing.Queue`); `AuditRunner._read_queue_and_stream` / stdout reader translates them into typed frontend events (`phase_start`, `phase_complete`, `finding`, `screenshot`, `security_result`, `knowledge_graph`, `verdict_*`, etc.) via `send_event`.
6. The subprocess's final stdout JSON (full `AuditState`) is parsed by `_handle_result`, which fans it out into ~30 enriched event types and a final `audit_result` event.
7. `stream_audit` persists the completed `Audit` (+ findings + screenshots) via `AuditRepository`, then closes the socket.

### 2. Audit engine pipeline (inside `python -m elliot`)
1. `elliot/__main__.py::main` parses args, calls `run_audit` -> `ElliotOrchestrator.audit(url, tier, ...)`.
2. `audit()` builds the initial `AuditState` dict (input, budgets from `AUDIT_TIERS[tier]`, iteration counters, empty result slots, V2/smart fields) and runs a manual `for` loop over `max_iterations` (it bypasses `LangGraph.ainvoke` to avoid Python 3.14 asyncio cancellation issues, but keeps node logic identical to `build_audit_graph`).
3. Per iteration: `scout_node` -> `route_after_scout` (abort if 3+ consecutive failures, else continue) -> `security_node_with_agent` -> `vision_node` -> `graph_node` -> `judge_node`.
4. Each node receives `AuditState`, reconstructs dataclasses from serialized dicts, calls the corresponding agent class, and returns a partial-dict update merged via `state.update(...)`.
5. `route_after_judge`: `end` (verdict rendered or status terminal), `scout` (Judge requested `REQUEST_MORE_INVESTIGATION` and page budget remains -> loop with new `pending_urls`), or `force_verdict` (budget exhausted -> `force_verdict_node` computes a trust score from partial evidence).
6. Finalization: status set, OSINT reputation feedback loop grades sources against the final verdict, accumulated quality penalty is applied to the trust score, security results are aggregated (MITRE/CVSS) for the frontend, completion progress emitted.
7. `main()` prints the final `AuditState` as JSON to stdout (the IPC data channel).

### 3. Graph topology (`build_audit_graph` in `elliot/core/orchestrator.py`)
`START -> scout -> [route_after_scout: vision|abort] -> security -> vision -> graph -> judge -> [route_after_judge: scout|force_verdict|end] -> END`; `force_verdict -> END`. The compiled graph is held by `ElliotOrchestrator._compiled` but the production path uses the explicit loop in `audit()`.

**State Management:**
- Engine: single `AuditState` `TypedDict` (`elliot/core/orchestrator.py`) — input fields, iteration/budget counters, accumulated evidence (`scout_results`, `vision_result`, `graph_result`, `judge_decision`, `security_results`), URL queues (`pending_urls`/`investigated_urls`), error list, NIM budget, V2 fields (`site_type`, `verdict_mode`, `security_mode`), and underscore-prefixed "smart" fields (`_quality_penalty`, `_degraded_agents`, `_timeout_config`, `_complexity_score`, `_progress_emitter`). Nodes never mutate in place across processes; they return dict deltas.
- Backend: ephemeral in-memory `_audits` dict in `backend/routes/audit.py` plus optional SQLite via `AuditRepository`.
- Frontend: Zustand store `frontend/src/lib/store.ts` accumulates all streamed events into typed collections; `useEventSequencer` enforces ordering via per-event `sequence` numbers added by `AuditRunner`.

## Key Abstractions

### AuditState (shared graph state)
- **Purpose:** Single contract passed through every audit node.
- **Examples:** `elliot/core/orchestrator.py` (definition), every file in `elliot/core/nodes/`.
- **Pattern:** LangGraph `TypedDict` state; nodes are `async (state) -> dict` partial updaters.

### Graph Node adapter
- **Purpose:** Thin async function bridging the graph to a heavyweight agent class; handles (de)serialization of dataclasses <-> dicts.
- **Examples:** `elliot/core/nodes/scout.py`, `vision.py`, `graph.py`, `judge.py`, `security.py`.
- **Pattern:** Adapter / boundary function; re-exported via `elliot/core/nodes/__init__.py`.

### Agent class
- **Purpose:** Encapsulates one domain of audit logic, often as an async context manager.
- **Examples:** `elliot/agents/scout.py::StealthScout`, `agents/vision.py::VisionAgent`, `agents/graph_investigator.py::GraphInvestigator`, `agents/judge.py::JudgeAgent`, `agents/security_agent.py`.
- **Pattern:** Strategy/specialist object returning a dataclass result (`ScoutResult`, `VisionResult`, `GraphResult`, `JudgeDecision`).

### Result dataclass
- **Purpose:** Typed agent output, serialized into `AuditState` as plain dicts.
- **Examples:** `ScoutResult`, `VisionResult`/`DarkPatternFinding`/`TemporalFinding`, `GraphResult`, `JudgeDecision`/`AuditEvidence`, `TrustScoreResult`/`SubSignal` (`elliot/config/trust_weights.py`).
- **Pattern:** `@dataclass` value objects with `asdict`-based serialization.

### IPC / ProgressEvent channel
- **Purpose:** Cross-process progress streaming between audit subprocess and backend.
- **Examples:** `elliot/core/ipc.py` (`ProgressEvent`, `determine_ipc_mode`, `serialize_queue`, `safe_put`), `elliot/core/progress/emitter.py`.
- **Pattern:** Message-passing over `multiprocessing.Queue` or stdout markers; mode selected by env/CLI flag with rollout percentage.

### Degradation / circuit breaker
- **Purpose:** Keep audits producing a verdict when agents time out or crash.
- **Examples:** `elliot/core/degradation.py` (`FallbackManager`, `FallbackMode`, `DegradedResult`), `elliot/core/circuit_breaker.py`, `ElliotOrchestrator._register_fallback_functions`/`_execute_agent_smart`.
- **Pattern:** Circuit breaker + registered fallback functions + quality-penalty accumulation.

### Trust scoring engine
- **Purpose:** Convert per-signal sub-scores into a final 0-100 trust score with override rules.
- **Examples:** `elliot/config/trust_weights.py::compute_trust_score`, used by `agents/judge.py` and `core/nodes/routing.py::force_verdict_node`.
- **Pattern:** Weighted aggregation with rule-based overrides (`overrides_applied`).

### Feature flag / rollout helper
- **Purpose:** Toggle subsystems without code changes.
- **Examples:** `elliot/config/settings.py::should_use_db_persistence`, `should_use_security_agent`; `elliot/core/ipc.py::determine_ipc_mode`.
- **Pattern:** Env-var + hash-based percentage rollout.

## Entry Points

### Backend API server
- **Location:** `backend/main.py`
- **Triggers:** `python backend/main.py` / uvicorn (`start.bat`, `Dockerfile`); listens on `0.0.0.0:8000`.
- **Responsibilities:** Load `.env`, fix `sys.path`, configure CORS, run DB `init_database()` in lifespan, mount `routes/health.py` and `routes/audit.py` under `/api`.

### Audit engine CLI
- **Location:** `elliot/__main__.py` (`python -m elliot <url> ...`)
- **Triggers:** Invoked as a subprocess by `backend/services/audit_runner.py`; also runnable directly by users.
- **Responsibilities:** Parse args/tier/IPC flags, force UTF-8 stdio on Windows, run `ElliotOrchestrator.audit`, print human summary to stderr (subprocess mode) and final JSON `AuditState` to stdout, optionally generate a report.

### Orchestrator API
- **Location:** `elliot/core/orchestrator.py` (`ElliotOrchestrator.audit`)
- **Triggers:** Called by the CLI; importable for embedding/tests.
- **Responsibilities:** Build/compile the graph, run the iterative SCOUT->...->JUDGE loop, manage budgets/timeouts/degradation, emit progress, finalize state.

### Frontend app
- **Location:** `frontend/src/app/` (Next.js App Router; root `page.tsx`, `layout.tsx`, dynamic routes `audit/[id]`, `report/[id]`, `compare/[ids]`, `history`, `v2`)
- **Triggers:** `npm run dev` / `next start` (port 3000 via `start.bat`).
- **Responsibilities:** Submit audits, open the WebSocket stream, render live agent progress, screenshots, findings, knowledge graph, dual verdict, and history/comparison views.

### Streamlit UI (secondary)
- **Location:** `elliot/ui/app.py` (`streamlit run elliot/ui/app.py`)
- **Triggers:** Manual; alternative/legacy UI with darknet components (`elliot/ui/darknet_components.py`).
- **Responsibilities:** Local interactive auditing front end independent of the Next.js app.

## Error Handling

**Strategy:** Fail-soft and always produce a verdict. Every agent failure is caught, logged, recorded in `state["errors"]`, and converted into a quality penalty rather than aborting; only repeated Scout failures (3+ with no results) abort the audit. Budget exhaustion routes to `force_verdict_node` instead of erroring.

**Patterns:**
- Per-node try/except in `ElliotOrchestrator.audit` — each phase wrapped, errors appended to `state["errors"]`, `_emit(..., "error", ...)` sent.
- `_execute_agent_smart` wraps agents with `asyncio.wait_for` timeouts and circuit breakers; `asyncio.TimeoutError` -> 0.5 penalty, generic exception -> 0.7 penalty.
- `FallbackManager` registers per-agent fallbacks (`vision_fallback`, `graph_fallback`, `security_fallback`, `judge_fallback`, `osint_fallback`) returning safe placeholder dicts.
- `NIMClient` 4-level fallback chain (primary VLM -> fallback VLM -> Tesseract OCR -> no-AI stub) with tenacity retry + exponential backoff.
- Routing escape hatches: `route_after_scout` -> `abort`, `route_after_judge` -> `force_verdict`.
- Backend: `AuditRunner` pre-flight reachability check fails fast on unreachable URLs; `stream_audit` catches `WebSocketDisconnect` and generic exceptions, maps timeouts to friendly messages, persists `ERROR` status, guards against sending on closed sockets.
- Top-level `except BaseException` in `audit()` sets `status="aborted"` and flushes buffered progress events so the UI is not left mid-progress.

## Cross-Cutting Concerns

**Logging:** Python `logging` throughout, namespaced loggers (`elliot.orchestrator`, `elliot.scout`, `elliot.nim`, `elliot.routes.audit`, `elliot.audit_runner`, etc.). CLI binds handlers explicitly to `stderr` (`elliot/__main__.py::setup_logging`) so stdout stays a clean IPC channel. Backend uses module-level loggers; `stderr` of the audit subprocess is drained and tail-logged by `AuditRunner`. Progress events double as a structured "log" stream to the UI (`log_entry` events).

**Validation:** Pydantic models with `field_validator` for API input (`AuditStartRequest` in `backend/routes/audit.py` — regex URL validation, tier/verdict-mode allow-lists). Audit tier/IPC choices constrained by `argparse` `choices` in the CLI. `AuditState` is a `TypedDict` (structural, not runtime-enforced). Internal quality/consensus validation via `elliot/quality/` (`validation_state.py`, `consensus_engine.py`, `confidence_scorer.py`).

**Authentication:** None. No auth/authz layer on the backend API; CORS is the only access control (`ALLOWED_ORIGINS`, default `localhost:3000`). The product is a local desktop-style tool. API keys (NVIDIA NIM, Tavily, URLVoid, AbuseIPDB) are loaded from `.env` via `python-dotenv` and used only for outbound calls.

---
*Architecture analysis: 2026-05-14*
