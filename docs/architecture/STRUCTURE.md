# Codebase Structure
**Analysis Date:** 2026-05-14

## Directory Layout
```
elliotAI/
├── elliot/                  # Audit engine — Python package, the core product
│   ├── __main__.py          # CLI entry point (python -m elliot <url>)
│   ├── core/                # Orchestration: LangGraph, nodes, IPC, infra
│   │   ├── orchestrator.py  # build_audit_graph + ElliotOrchestrator + AuditState
│   │   ├── nodes/           # Graph node adapters (scout/security/vision/graph/judge/routing)
│   │   └── progress/        # WebSocket progress streaming (emitter, estimator, rate limiter)
│   ├── agents/              # The 5 domain specialist agents
│   │   ├── scout_nav/       # Scout sub-modules (link explorer, scroll, lazy-load)
│   │   ├── vision/          # Vision sub-modules (temporal analysis)
│   │   └── judge_core/      # Judge sub-modules (strategies, verdict)
│   ├── analysis/            # Stateless analyzers + security modules
│   │   └── security/        # Security module impls (owasp/, cookies, csp, tls_ssl, ...)
│   ├── osint/               # OSINT / threat intel orchestration
│   │   └── sources/         # Per-source adapters (whois, dns, ssl, urlvoid, darknet_*)
│   ├── darknet/             # TOR client, onion detection, threat scraping
│   ├── cwe/                 # CVSS / CWE scoring (cvss_v31, registry)
│   ├── quality/             # Confidence scoring, consensus, validation state
│   ├── config/              # settings.py, taxonomies, trust weights, rules
│   ├── db/                  # SQLAlchemy async persistence (models, repos, config)
│   ├── screenshots/         # Screenshot file storage
│   ├── reporting/           # PDF/HTML report generator + Jinja2 templates
│   ├── reporters/           # Specialized reporters (darknet)
│   ├── ui/                  # Streamlit UI (secondary/legacy front end)
│   ├── data/                # Runtime data (cache, evidence, reports, vectordb, sqlite)
│   └── tests/               # Engine test suite (unit/, integration/, sites/)
├── backend/                 # FastAPI REST + WebSocket gateway
│   ├── main.py              # FastAPI app, CORS, lifespan/DB init
│   ├── routes/              # audit.py (start + WS stream + history), health.py
│   ├── services/            # audit_runner.py — spawns engine subprocess, translates events
│   └── tests/               # Backend test suite (persistence, route contract, queue IPC)
├── frontend/                # Next.js (App Router) web UI
│   └── src/
│       ├── app/             # Routes: page.tsx, audit/[id], report/[id], compare, history, v2
│       ├── components/      # React components (audit/, terminal/, report/, landing/, ...)
│       ├── hooks/           # useAuditStream (WebSocket), useEventSequencer
│       ├── lib/             # store.ts (Zustand), types.ts, utils.ts, education.ts
│       └── config/          # agent_personalities.ts, agents.ts
├── tests/                   # Top-level engine tests (consensus, link explorer, scroll)
├── testing/                 # Ad-hoc test scaffolding / fixtures
├── docs/                    # Project docs (agent_config, analysis, bug_reports, planning)
├── .planning/               # GSD planning artifacts (this directory)
├── .backend-docs/           # Generated backend reference docs
├── data/                    # Top-level runtime data dir
├── start.bat / stop.bat     # Windows service launchers (ports 8000 + 3000)
├── Dockerfile               # Container build
├── pytest.ini               # Pytest config
└── .env.example             # Environment variable template
```

## Directory Purposes

### `elliot/`
- **Purpose:** The audit engine — a self-contained Python package that performs the entire SCOUT->SECURITY->VISION->GRAPH->JUDGE pipeline. Runs as a subprocess of the backend or standalone via CLI.
- **Contains:** Orchestration, agents, analyzers, OSINT, scoring, config, persistence, reporting.
- **Key files:** `elliot/__main__.py`, `elliot/core/orchestrator.py`, `elliot/config/settings.py`.

### `elliot/core/` and `elliot/core/nodes/`
- **Purpose:** Wire agents into the cyclic LangGraph state machine; host cross-cutting infra (IPC, timeouts, degradation, progress streaming).
- **Contains:** Graph builder, `AuditState`, node adapters, routing, `NIMClient`, complexity analyzer, circuit breaker.
- **Key files:** `elliot/core/orchestrator.py`, `elliot/core/nodes/__init__.py`, `elliot/core/nodes/routing.py`, `elliot/core/nim_client.py`, `elliot/core/ipc.py`.

### `elliot/agents/`
- **Purpose:** The five domain specialists doing the actual audit work; each returns a typed result dataclass.
- **Contains:** `scout.py`, `vision.py`, `graph_investigator.py`, `judge.py`, `security_agent.py` plus sub-packages.
- **Key files:** `elliot/agents/scout.py`, `elliot/agents/vision.py`, `elliot/agents/graph_investigator.py`, `elliot/agents/judge.py`, `elliot/agents/security_agent.py`.

### `elliot/analysis/`
- **Purpose:** Stateless analyzers and concrete security-module implementations consumed by agents.
- **Contains:** DOM/JS/meta/redirect/temporal analyzers, form validator, pattern matcher, `security/` (OWASP A01-A10, cookies, CSP, TLS/SSL, GDPR, PCI-DSS, darknet).
- **Key files:** `elliot/analysis/meta_analyzer.py`, `elliot/analysis/phishing_checker.py`, `elliot/analysis/security/owasp/`, `elliot/analysis/security/base.py`.

### `elliot/osint/` and `elliot/darknet/`
- **Purpose:** External reputation / CTI / IOC / darknet intelligence with a reputation feedback loop.
- **Contains:** OSINT orchestrator, CTI, IOC detector, reputation store, per-source adapters, TOR client.
- **Key files:** `elliot/osint/orchestrator.py`, `elliot/osint/reputation.py`, `elliot/osint/cti.py`, `elliot/osint/sources/`, `elliot/darknet/tor_client.py`.

### `elliot/config/`
- **Purpose:** Central configuration, taxonomies, weights, and rule sets — imported by every layer.
- **Contains:** `settings.py` (paths, NIM endpoints, `AUDIT_TIERS`, budgets, feature flags), dark-pattern taxonomy, trust weights, site types, security/darknet rules.
- **Key files:** `elliot/config/settings.py`, `elliot/config/trust_weights.py`, `elliot/config/dark_patterns.py`.

### `elliot/db/` and `elliot/screenshots/`
- **Purpose:** Optional SQLite persistence of audit history and screenshot files.
- **Contains:** Async engine + init, ORM models, repository, screenshot storage.
- **Key files:** `elliot/db/__init__.py`, `elliot/db/models.py`, `elliot/db/repositories.py`, `elliot/db/config.py`, `elliot/screenshots/storage.py`.

### `elliot/quality/` and `elliot/cwe/`
- **Purpose:** Confidence/consensus scoring and CVSS/CWE computation.
- **Contains:** Confidence scorer, consensus engine, validation state; CVSS v3.1 calculator + CWE registry.
- **Key files:** `elliot/quality/consensus_engine.py`, `elliot/quality/confidence_scorer.py`, `elliot/cwe/cvss_v31.py`, `elliot/cwe/registry.py`.

### `elliot/reporting/` and `elliot/reporters/`
- **Purpose:** Render audit result dicts into PDF/HTML reports.
- **Contains:** Report generator (Jinja2 + WeasyPrint), templates, darknet reporter.
- **Key files:** `elliot/reporting/report_generator.py`, `elliot/reporting/templates/`, `elliot/reporters/darknet_reporter.py`.

### `backend/`
- **Purpose:** FastAPI gateway exposing REST + WebSocket; spawns and streams the audit engine subprocess.
- **Contains:** App bootstrap, route handlers, the subprocess driver/event translator.
- **Key files:** `backend/main.py`, `backend/routes/audit.py`, `backend/routes/health.py`, `backend/services/audit_runner.py`.

### `frontend/`
- **Purpose:** Next.js (App Router, React 19) web UI for submitting audits and viewing live results, history, comparisons, and reports.
- **Contains:** Route pages, React components, WebSocket hook, Zustand store, shared TS types.
- **Key files:** `frontend/src/app/page.tsx`, `frontend/src/app/layout.tsx`, `frontend/src/hooks/useAuditStream.ts`, `frontend/src/lib/store.ts`, `frontend/src/lib/types.ts`.

### `tests/`, `backend/tests/`, `elliot/tests/`, `testing/`
- **Purpose:** Test suites split by component. Root `tests/` and `elliot/tests/` cover the engine; `backend/tests/` covers the API/runner; `testing/` holds ad-hoc scaffolding/fixtures.
- **Contains:** Pytest modules (`test_*.py`), `elliot/tests/integration/`, `elliot/tests/unit/`, `elliot/tests/sites/`.
- **Key files:** `pytest.ini`, `elliot/tests/test_veritas.py`, `backend/tests/test_audit_route_contract.py`, `tests/test_consensus_engine.py`.

## Key File Locations

**Entry Points:**
- Backend API server: `backend/main.py`
- Audit engine CLI: `elliot/__main__.py`
- Orchestrator API: `elliot/core/orchestrator.py` (`ElliotOrchestrator.audit`)
- Frontend root page: `frontend/src/app/page.tsx`, layout `frontend/src/app/layout.tsx`
- Streamlit UI (secondary): `elliot/ui/app.py`
- Service launchers: `start.bat`, `stop.bat`

**Configuration:**
- Engine settings + audit tiers + feature flags: `elliot/config/settings.py`
- Trust scoring weights/overrides: `elliot/config/trust_weights.py`
- Dark-pattern taxonomy + VLM prompts: `elliot/config/dark_patterns.py`
- Database config (URL, WAL pragmas): `elliot/db/config.py`
- Env template: `.env.example` (real `.env` lives in `elliot/.env` — not committed)
- Pytest: `pytest.ini`
- Frontend: `frontend/next.config.ts`, `frontend/tsconfig.json`, `frontend/package.json`, `frontend/components.json`, `frontend/eslint.config.mjs`
- Container: `Dockerfile`

**Core Logic:**
- Graph state machine + state shape: `elliot/core/orchestrator.py`
- Graph node adapters: `elliot/core/nodes/` (`scout.py`, `security.py`, `vision.py`, `graph.py`, `judge.py`)
- Routing + force-verdict: `elliot/core/nodes/routing.py`
- Agents: `elliot/agents/scout.py`, `vision.py`, `graph_investigator.py`, `judge.py`, `security_agent.py`
- Trust score computation: `elliot/config/trust_weights.py` (`compute_trust_score`)
- Inference client: `elliot/core/nim_client.py`
- Subprocess/event bridge: `backend/services/audit_runner.py`
- API routes: `backend/routes/audit.py`
- Frontend state + streaming: `frontend/src/lib/store.ts`, `frontend/src/hooks/useAuditStream.ts`

**Testing:**
- Engine unit/integration: `elliot/tests/`, `tests/`
- Backend: `backend/tests/test_audit_persistence.py`, `backend/tests/test_audit_route_contract.py`, `backend/tests/test_audit_runner_queue.py`
- IPC: `elliot/tests/test_ipc_queue.py`, `elliot/tests/test_ipc_integration.py`
- Config: `pytest.ini`

## Naming Conventions

**Files:**
- Python: `snake_case.py`. Agent files named by role (`scout.py`, `judge.py`). Node adapters mirror agent names under `elliot/core/nodes/`. Tests prefixed `test_*.py`.
- Result types are `@dataclass` named `<Agent>Result` (`ScoutResult`, `VisionResult`, `GraphResult`) or `<Domain>Decision` (`JudgeDecision`).
- TypeScript/React: components `PascalCase.tsx` (`AgentCard.tsx`, `VerdictReveal.tsx`); hooks `useCamelCase.ts`; lib/config modules `camelCase.ts` (`store.ts`, `types.ts`).
- Next.js routes: `page.tsx` per route folder; dynamic segments in brackets (`audit/[id]`, `compare/[ids]`).

**Directories:**
- Python packages: lowercase, single-word where possible (`agents`, `analysis`, `osint`, `quality`, `cwe`). Sub-packages group an agent's helpers (`scout_nav`, `judge_core`, `vision`).
- Frontend components grouped by feature/area (`audit/`, `terminal/`, `report/`, `landing/`, `data-display/`, `ui/`, `ambient/`, `layout/`, `providers/`).
- Planning/docs dirs are dotted or descriptive (`.planning/`, `.backend-docs/`, `docs/`).

## Where to Add New Code

**New Feature (a new audit capability / pipeline step):**
- New agent: add `elliot/agents/<name>.py` (an agent class returning a result dataclass), then a node adapter at `elliot/core/nodes/<name>.py`, re-export it in `elliot/core/nodes/__init__.py`, and wire it into both `build_audit_graph` and the explicit loop in `ElliotOrchestrator.audit` (`elliot/core/orchestrator.py`). Add any new `AuditState` fields to the `TypedDict`.
- New analyzer used by an existing agent: add to `elliot/analysis/` (or `elliot/analysis/security/` for a security module — follow `elliot/analysis/security/base.py`).
- New OSINT source: add `elliot/osint/sources/<source>.py` following `elliot/osint/sources/base.py`, register it in `elliot/osint/orchestrator.py`.
- New tier or budget knob: edit `AUDIT_TIERS` / `JUDGE_THRESHOLDS` in `elliot/config/settings.py` and the tier allow-lists in `backend/routes/audit.py` (`_VALID_TIERS`) and `elliot/core/nodes/security.py` (`_get_security_modules_for_tier`).

**New Component/Module:**
- New API endpoint: add to an existing router in `backend/routes/` (or a new `backend/routes/<name>.py` registered in `backend/main.py`). Long-running work belongs in `backend/services/`.
- New frontend page: add `frontend/src/app/<route>/page.tsx`; shared UI in `frontend/src/components/<area>/`; new streamed-event handling goes in `frontend/src/lib/store.ts` + a new type in `frontend/src/lib/types.ts`.
- New streamed event type: emit it from `ElliotOrchestrator._emit` or `ProgressEmitter`, translate it in `backend/services/audit_runner.py` (`_handle_progress` / `_handle_result`), then consume in `frontend/src/lib/store.ts`.
- New persisted entity: add an ORM model to `elliot/db/models.py` and CRUD to `elliot/db/repositories.py`.

**Utilities:**
- Engine-side cross-cutting infra: `elliot/core/` (e.g., a new timeout/IPC helper alongside `timeout_manager.py`, `ipc.py`).
- Scoring helpers: `elliot/quality/` or `elliot/cwe/`.
- Config constants / rules: `elliot/config/`.
- Frontend helpers: `frontend/src/lib/utils.ts`; UI-agnostic config in `frontend/src/config/`.

## Special Directories

### `elliot/data/`
- **Purpose:** Engine runtime data — `cache/`, `evidence/`, `reports/`, `vectordb/`, the SQLite DB (`elliot_audits.db` / `veritas_audits.db`), `marketplace_threat_feeds.json`.
- **Generated:** yes (created/written at runtime; `settings.py` auto-creates the subdirs on import).
- **Committed:** mostly no — DB files and cache/evidence are runtime artifacts; check `.gitignore`. Seed JSON feeds may be committed.

### `data/` (repo root)
- **Purpose:** Top-level runtime data directory used by the backend's relative `DATABASE_URL` (`sqlite+aiosqlite:///./data/elliot_audits.db`) and screenshot storage.
- **Generated:** yes.
- **Committed:** no (runtime artifacts).

### `.planning/`
- **Purpose:** GSD workflow artifacts — roadmap, requirements, phase plans, and this `codebase/` analysis set.
- **Generated:** yes (by GSD tooling/agents).
- **Committed:** yes.

### `.backend-docs/` and `docs/`
- **Purpose:** `.backend-docs/` holds generated backend reference docs (routes, services, events); `docs/` holds broader project docs (analysis, bug reports, planning, agent config).
- **Generated:** `.backend-docs/` largely generated; `docs/` mixed (hand-written + generated).
- **Committed:** yes.

### `node_modules/` (root and `frontend/`)
- **Purpose:** npm dependencies. Root `node_modules/` is minimal (root `package.json` is trivial); `frontend/node_modules/` holds the real frontend deps.
- **Generated:** yes (`npm install`).
- **Committed:** no (`.gitignore`).

### `.venv/`
- **Purpose:** Python virtual environment for the engine + backend; `AuditRunner` resolves `.venv/Scripts/python.exe` to spawn the engine.
- **Generated:** yes (`python -m venv .venv`).
- **Committed:** no.

### `__pycache__/`, `.pytest_cache/`, `.claude-flow/`, `.swarm/`, `.serena/`
- **Purpose:** Tooling/runtime caches (Python bytecode, pytest cache, claude-flow/serena agent tooling state).
- **Generated:** yes.
- **Committed:** no.

---
*Structure analysis: 2026-05-14*
