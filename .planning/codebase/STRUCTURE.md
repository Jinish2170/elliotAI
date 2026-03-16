# Codebase Structure
**Analysis Date:** 2026-03-16

## Directory Layout
```
C:\files\coding dev era\elliot\elliotAI/
├── backend/                          # FastAPI backend
│   ├── main.py                       # FastAPI app entry point
│   ├── __init__.py                   # Package marker
│   ├── routes/
│   │   ├── audit.py                  # Audit start & WebSocket endpoints
│   │   └── health.py                 # Health check
│   ├── services/
│   │   ├── audit_runner.py           # Orchestration bridging to veritas
│   │   └── (other services if any)
│   ├── data/
│   │   └── veritas_audits.db*        # SQLite database (WAL mode)
│   ├── requirements.txt              # Python dependencies
│   └── tests/                        # Backend unit tests
│
├── frontend/                         # Next.js frontend
│   └── src/
│       └── app/
│           ├── layout.tsx            # Root layout
│           ├── page.tsx              # Home dashboard
│           ├── v2/page.tsx           # V2 interface
│           ├── audit/
│           │   └── [id]/page.tsx     # Live audit terminal
│           ├── history/page.tsx      # Audit history list
│           ├── report/[id]/page.tsx  # Audit detail report
│           ├── compare/
│           │   ├── page.tsx          # Comparison list
│           │   └── [ids]/page.tsx    # Side-by-side view
│           └── globals.css           # Tailwind + terminal styles
│
├── veritas/                          # Core audit engine
│   ├── __main__.py                   # CLI entry point
│   ├── .env                          # Environment configuration
│   ├── config/
│   │   ├── settings.py               # Global settings + audit tiers
│   │   ├── trust_weights.py          # Trust score calculation
│   │   └── site_types.py             # Site classification
│   ├── core/
│   │   ├── orchestrator.py           # LangGraph orchestrator
│   │   ├── nodes/                    # LangGraph node functions
│   │   │   ├── __init__.py
│   │   │   ├── scout_node.py
│   │   │   ├── vision_node.py
│   │   │   ├── graph_node.py
│   │   │   ├── judge_node.py
│   │   │   └── security.py
│   │   ├── ipc.py                    # Inter-process communication
│   │   ├── progress.py               # ProgressEmitter for WebSocket
│   │   ├── nim_client.py             # NIM API client
│   │   ├── timeout_manager.py        # Adaptive timeouts
│   │   ├── complexity_analyzer.py    # Page complexity scoring
│   │   └── degradation.py            # FallbackManager, circuit breaker
│   ├── agents/                       # 5 forensic agents
│   │   ├── scout.py                  # Browser automation (screenshots)
│   │   ├── vision.py                 # NIM-based visual analysis
│   │   ├── graph_investigator.py     # OSINT + entity verification
│   │   ├── judge.py                  # Verdict synthesis
│   │   └── security_agent.py         # Security scanning
│   ├── db/
│   │   └── veritas.db                # SQLite audit storage
│   ├── osint/                        # OSINT integrations
│   │   ├── ioc_detector.py           # IOC analysis
│   │   ├── virus_total.py            # VirusTotal client
│   │   ├── abuseipdb.py              # AbuseIPDB client
│   │   └── (other OSINT sources)
│   ├── darknet/                      # Darknet intelligence
│   ├── cwe/                          # CWE vulnerability database
│   ├── analysis/                     # Analysis utilities
│   ├── quality/                      # Quality metrics
│   ├── reporting/                    # Report generation
│   └── requirements.txt              # Python dependencies
│
├── .planning/                        # GSD planning (generated)
│   ├── codebase/                     # Codebase mapping docs
│   │   ├── ARCHITECTURE.md
│   │   ├── STRUCTURE.md
│   │   ├── CONCERNS.md (if concerns focus)
│   │   └── (other focus docs)
│   └── phases/                       # GSD phase planning
│
└── package.json                      # Frontend dependencies
```

## Directory Purposes

### Backend (`backend/`)
- **Purpose:** FastAPI REST + WebSocket server for frontend
- **Contains:**
  - FastAPI application setup with CORS middleware
  - Audit API routes (start, stream, status)
  - Services bridging HTTP to veritas orchestration
  - SQLite database with WAL mode for concurrency

### Frontend (`frontend/`)
- **Purpose:** Next.js 14 web application with Bloomberg Terminal UI
- **Contains:**
  - Real-time audit terminal with WebSocket streaming
  - History, reporting, and comparison features
  - Darkmode terminal-styled interface
  - Dark pattern visualization components

### Core Engine (`veritas/`)
- **Purpose:** Autonomous forensic web auditor engine
- **Contains:**
  - LangGraph orchestration with state machine
  - 5 specialized agents (Scout, Vision, Graph, Judge, Security)
  - OSINT, CWE, and darknet integrations
  - Trust score calculation and verdict generation

### Planning (`.planning/`)
- **Purpose:** GSD methodology planning documents
- **Contains:** Architecture, structure, concerns, and implementation plans

## Key File Locations

### Entry Points
- `backend/main.py` — FastAPI server (uvicorn)
- `veritas/__main__.py` — CLI entry (`python -m veritas`)
- `backend/routes/audit.py` — Audit API endpoints
- `frontend/src/app/page.tsx` — Frontend home

### Core Logic
- `veritas/core/orchestrator.py` — LangGraph orchestration (897 lines)
- `backend/services/audit_runner.py` — Process execution bridge (737 lines)
- `veritas/agents/judge.py` — Verdict computation
- `veritas/config/trust_weights.py` — Trust score algorithm

### Agent Implementations
- `veritas/agents/scout.py` — Browser automation (+300 lines)
- `veritas/agents/vision.py` — Visual analysis with NIM
- `veritas/agents/graph_investigator.py` — Entity/OSINT analysis
- `veritas/agents/judge.py` — Evidence synthesis + scoring
- `veritas/agents/security_agent.py` — Security module orchestration

### Frontend Components
- `frontend/src/app/audit/[id]/page.tsx` — Live audit terminal
- `frontend/src/app/report/[id]/page.tsx` — Report display
- `frontend/src/components/terminal/` — Terminal UI components

### Configuration
- `veritas/config/settings.py` — Settings + audit tier configs
- `veritas/.env` — Environment variables
- `backend/.env` — Backend environment variables
- `package.json` — Frontend dependencies

## Naming Conventions

### Files
- **Python:** snake_case (e.g., `orchestrator.py`, `audit_runner.py`)
- **TypeScript/TSX:** kebab-case (e.g., `audit-page.tsx`)
- **Config:** snake_case (e.g., `settings.py`, `trust_weights.py`)

### Directories
- **Python packages:** snake_case (e.g., `veritas/core/`, `veritas/agents/`)
- **Frontend routes:** kebab-case matching URL pattern (e.g., `audit/[id]/`)

### Classes/Functions
- **Classes:** PascalCase (e.g., `VeritasOrchestrator`, `AuditRunner`, `StealthScout`)
- **Functions:** snake_case (e.g., `build_audit_graph()`, `_execute_agent_smart()`)
- **Async functions:** Prefix with `_` for internal (e.g., `_handle_result()`)

### TypedDict/State Fields
- **AuditState:** camelCase for fields (e.g., `audit_tier`, `scout_failures`, `nim_calls_used`)

## Where to Add New Code

### New Feature
- **Primary code:** Add to corresponding agent in `veritas/agents/`, or new module in `veritas/core/`
- **Tests:** Add to agent's test file or create `veritas/tests/test_feature.py`
- **Integration:** If needs orchestrator update → modify node in `veritas/core/nodes/`

### New Agent
- **Implementation:** Create new file in `veritas/agents/` (e.g., `new_agent.py`)
- **Orchestrator:** Add node to `veritas/core/nodes/` and update `orchestrator.py`'s graph
- **Tests:** Create `veritas/tests/test_new_agent.py`

### New Frontend Page/Feature
- **Implementation:** Create route in `frontend/src/app/` (e.g., `dashboard/`)
- **Components:** Create in `frontend/src/components/` or co-locate
- **API Integration:** Add WebSocket or REST call in page component

### Utilities
- **Backend:** Add to `backend/services/` or `veritas/analysis/`
- **Frontend:** Add to `frontend/src/lib/` or `frontend/src/utils/`

### Configuration
- **Global settings:** Edit `veritas/config/settings.py`
- **Trust weights:** Edit `veritas/config/trust_weights.py`
- **Environment:** Update `veritas/.env` (DO NOT commit secrets)

## Special Directories

### `.planning/` (Created by GSD)
- **Purpose:** Store architecture, structure, and implementation planning
- **Generated:** Yes
- **Committed:** Yes (tracked in git)

### `.venv/` (Virtual Environment)
- **Purpose:** Python virtual environment for dependencies
- **Generated:** Yes (during setup)
- **Committed:** No (ignored in .gitignore)

### `veritas/screenshots/` (Artifacts)
- **Purpose:** Store captured screenshots during audits
- **Generated:** Yes (during execution)
- **Committed:** No (ignored)

### `backend/data/` (Database)
- **Purpose:** SQLite database files with WAL mode
- **Generated:** Yes (during init)
- **Committed:** No (though .db-wal and .db-shm are in git status)

---

*Structure analysis: 2026-03-16*