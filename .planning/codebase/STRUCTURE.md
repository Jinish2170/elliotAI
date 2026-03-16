# Codebase Structure
**Analysis Date:** 2026-03-16

## Directory Layout

```
[project-root]/
├── backend/                          # FastAPI backend application
│   ├── __init__.py
│   ├── main.py                       # FastAPI app entry point
│   ├── requirements.txt              # Python dependencies
│   ├── services/                     # Business logic services
│   │   ├── audit_runner.py           # Audit execution coordinator
│   │   └── __init__.py
│   ├── routes/                       # API route handlers
│   │   ├── __init__.py
│   │   ├── audit.py                  # Audit endpoints (REST + WebSocket)
│   │   ├── health.py                 # Health check endpoint
│   │   └── __pycache__/
│   ├── tests/                        # Backend tests
│   │   ├── __init__.py
│   │   ├── test_imports.py
│   │   ├── test_audit_persistence.py
│   │   ├── test_audit_route_contract.py
│   │   └── test_audit_runner_queue.py
│   └── data/                         # Database files
│       ├── veritas_audits.db         # SQLite database (WAL mode)
│       ├── veritas_audits.db-shm
│       └── veritas_audits.db-wal
│
├── frontend/                         # Next.js frontend application
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   │   ├── layout.tsx            # Root layout (Navbar + children)
│   │   │   ├── page.tsx              # Landing/home page
│   │   │   ├── globals.css           # Global Tailwind styles
│   │   │   ├── audit/
│   │   │   │   └── [id]/             # Dynamic audit run page
│   │   │   │       └── page.tsx      # Real-time audit page
│   │   │   ├── report/
│   │   │   │   └── [id]/             # Dynamic report page
│   │   │   │       └── page.tsx      # Findings/report page
│   │   │   ├── history/
│   │   │   │   └── page.tsx          # Audit history page
│   │   │   ├── compare/
│   │   │   │   ├── page.tsx          # Compare selection page
│   │   │   │   └── [ids]/
│   │   │   │       └── page.tsx      # Audit comparison page
│   │   │   └── v2/
│   │   │       └── page.tsx          # Experimental V2 UI
│   │   ├── components/               # React components
│   │   │   ├── ambient/
│   │   │   │   └── ParticleField.tsx # Background particles
│   │   │   ├── audit/
│   │   │   │   ├── AuditHeader.tsx
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   ├── AgentTile.tsx
│   │   │   │   ├── DataFeed.tsx
│   │   │   │   ├── EventLog.tsx
│   │   │   │   ├── MetricTicker.tsx
│   │   │   │   ├── ActiveIntel.tsx
│   │   │   │   ├── EvidenceStack.tsx
│   │   │   │   ├── FindingRow.tsx
│   │   │   │   ├── VerdictReveal.tsx
│   │   │   │   └── ScreenshotCarousel.tsx
│   │   │   ├── data-display/         # Visualization components
│   │   │   │   ├── RiskBadge.tsx
│   │   │   │   ├── SeverityBadge.tsx
│   │   │   │   ├── SignalBar.tsx
│   │   │   │   ├── SignalRadarChart.tsx
│   │   │   │   ├── StatCounter.tsx
│   │   │   │   ├── TrustGauge.tsx
│   │   │   │   ├── DataTable.tsx
│   │   │   │   ├── InlineSparkline.tsx
│   │   │   │   ├── JsonTreeViewer.tsx
│   │   │   │   └── TerminalBlock.tsx
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.tsx
│   │   │   │   └── PanelChrome.tsx   # Panel container component
│   │   │   ├── landing/              # Homepage components
│   │   │   │   ├── CommandInput.tsx  # URL input form
│   │   │   │   ├── AgentStatus.tsx  # Agent status display
│   │   │   │   ├── RecentAudits.tsx # Recent audits widget
│   │   │   │   └── CapabilitiesGrid.tsx
│   │   │   ├── report/               # Report page components
│   │   │   │   ├── EntityIntel.tsx
│   │   │   │   ├── EvidenceGallery.tsx
│   │   │   │   ├── ExecSummary.tsx
│   │   │   │   ├── FindingsPanel.tsx
│   │   │   │   ├── MetadataGrid.tsx
│   │   │   │   ├── RecommendationsPanel.tsx
│   │   │   │   ├── SectionNav.tsx
│   │   │   │   ├── SecurityMatrix.tsx
│   │   │   │   └── SignalTable.tsx
│   │   │   ├── terminal/             # Terminal-style components
│   │   │   │   ├── TerminalPanel.tsx
│   │   │   │   ├── KnowledgeGraph.tsx
│   │   │   │   ├── DarknetOsintGrid.tsx
│   │   │   │   ├── MitreGrid.tsx
│   │   │   │   ├── VerdictPanel.tsx
│   │   │   │   ├── ScoutImagery.tsx
│   │   │   │   ├── SysLogStream.tsx
│   │   │   │   ├── CvssRadar.tsx
│   │   │   │   └── AgentProcState.tsx
│   │   │   ├── ui/                   # Low-level UI primitives
│   │   │   │   ├── AgentIcon.tsx
│   │   │   │   └── SeverityBadge.tsx
│   │   │   └── providers/            # React context providers
│   │   │       └── ChromaticProvider.tsx
│   │   ├── hooks/                    # Custom React hooks
│   │   │   └── useAuditStream.ts     # WebSocket stream handler
│   │   ├── lib/                      # Utility libraries
│   │   │   ├── store.ts              # Zustand state store
│   │   │   ├── utils.ts              # Helper functions
│   │   │   └── education.ts          # Educational content
│   │   └── .next/                    # Generated build output
│   ├── public/                       # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   ├── eslint.config.mjs
│   └── README.md
│
├── veritas/                          # Core AI/orchestration module
│   ├── __init__.py
│   ├── agents/                       # AI agent implementations
│   │   ├── __init__.py
│   │   ├── scout.py                  # Scout agent (URL discovery)
│   │   ├── vision.py                 # Vision agent (screenshots)
│   │   ├── graph_investigator.py    # Graph investigator (relationships)
│   │   ├── judge.py                  # Judge agent (verdict/scoring)
│   │   ├── security_agent.py         # Security scanning agent
│   │   ├── scout_nav/                # Scout navigation submodule
│   │   ├── vision/                   # Vision processing submodule
│   │   └── judge/                    # Judge reasoning submodule
│   ├── core/                         # Core orchestration
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # LangGraph state machine
│   │   ├── nodes/                    # Graph node definitions
│   │   ├── progress/                 # Progress tracking
│   │   ├── nim_client.py             # NVIDIA NIM API client
│   │   ├── timeout_manager.py        # Timeout management
│   │   ├── complexity_analyzer.py    # Complexity scoring
│   │   ├── degradation.py            # Graceful degradation
│   │   └── ipc.py                    # Inter-process communication
│   ├── config/                       # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py               # Main settings
│   │   ├── trust_weights.py          # Trust score weights
│   │   ├── site_types.py             # Site classification
│   │   └── constants.py              # Constants
│   ├── db/                           # Database layer
│   │   ├── __init__.py
│   │   ├── models.py                 # SQLAlchemy models
│   │   ├── repositories.py           # Repository classes
│   │   └── storage.py                # Screenshot storage
│   ├── data/                         # Data files
│   │   ├── cache/                    # LLM response cache (JSON files)
│   │   ├── screenshots/              # Screenshot storage directory
│   │   ├── userdata/                 # User-specific data
│   │   └── logs/                     # Log files
│   ├── analysis/                     # Analysis modules
│   │   ├── security/                 # Security analysis
│   │   └── __pycache__/
│   ├── osint/                        # OSINT tools
│   │   ├── orchestrator.py
│   │   └── __pycache__/
│   ├── cwe/                          # CWE definitions
│   ├── darknet/                      # Dark web intelligence
│   ├── screenshots/                  # Screenshot generation
│   └── __pycache__/                  # Python cache
│
├── .planning/                        # GSD planning output
├── .venv/                            # Python virtual environment
├── .vscode/                          # VS Code settings
├── .git/                             # Git repository
├── .env                              # Environment variables (DO NOT COMMIT)
├── README.md                         # Main documentation
├── USER_GUIDE.md                     # User guide
├── VERITAS_IMPLEMENTATION.md         # Implementation details
├── _compile_test.py                  # Test utilities
├── _test_ws.py                       # WebSocket test utility
├── test_output.json                  # Test data
└── patch_graph.py                    # Graph utility script
```

---

## Directory Purposes

### Backend (`backend/`)
**Purpose:** FastAPI web server and audit coordination

**Contains:**
- REST/WebSocket API endpoints
- Service layer (AuditRunner)
- Test suite

**Key Files:**
- `backend/main.py` - FastAPI app startup
- `backend/routes/audit.py` - Audit endpoints
- `backend/services/audit_runner.py` - Audit execution
- `backend/data/veritas_audits.db` - SQLite database

---

### Frontend (`frontend/`)
**Purpose:** Next.js web application

**Contains:**
- Pages (using App Router)
- React components (organized by feature)
- Hooks for state management and streaming
- Configuration files (Tailwind, ESLint, PostCSS)

**Key Files:**
- `frontend/src/app/layout.tsx` - Root layout
- `frontend/src/app/audit/[id]/page.tsx` - Real-time audit view
- `frontend/src/app/report/[id]/page.tsx` - Report view
- `frontend/src/hooks/useAuditStream.ts` - WebSocket handler

---

### Veritas Core (`veritas/`)
**Purpose:** AI orchestration and agent framework

**Contains:**
- Multi-agent LangGraph implementation
- Database models and repositories
- Configuration and settings
- Caching and utilities

**Key Files:**
- `veritas/core/orchestrator.py` - State machine definition
- `veritas/agents/*.py` - Agent implementations
- `veritas/db/models.py` - Database schema
- `veritas/config/settings.py` - Feature flags

---

## Key File Locations

### Entry Points
- `backend/main.py` - FastAPI server start (run: `python backend/main.py`)
- `frontend/src/app/layout.tsx` - Frontend root (served via `npm run dev`)
- `frontend/src/app/page.tsx` - Home page route (`/`)
- `frontend/src/app/audit/[id]/page.tsx` - Audit run page (`/audit/:id`)
- `frontend/src/app/report/[id]/page.tsx` - Audit report (`/report/:id`)

### Core Logic
- `veritas/core/orchestrator.py` - LangGraph orchestration (lines 500+)
- `backend/services/audit_runner.py` - Audit entry point
- `backend/routes/audit.py` - API route definitions and handlers
- `veritas/agents/judge.py` - Verdict generation logic

### Data & State
- `backend/data/veritas_audits.db` - SQLite database (use SQLite viewer)
- `veritas/data/cache/` - LLM response cache (JSON files)
- `frontend/src/lib/store.ts` - Zustand audit state store

### Configuration
- `veritas/.env` - Environment variables (not committed)
- `veritas/config/settings.py` - Feature flags and configs
- `frontend/next.config.ts` - Next.js configuration
- `frontend/tailwind.config.ts` - Tailwind theme configuration

### Testing
- `backend/tests/` - Backend unit tests
- `frontend/` - Frontend tested via Playwright or manual testing

---

## Naming Conventions

### Files
- **Python:** `snake_case.py` (e.g., `audit_runner.py`, `orchestrator.py`)
- **TypeScript/React:** `PascalCase.tsx` (e.g., `AuditHeader.tsx`, `AgentCard.tsx`)
- **TypeScript utilities:** `camelCase.ts` (e.g., `useAuditStream.ts`, `utils.ts`)
- **Config:** `snake_case.json` or `kebab-case.config.ts`

### Directories
- **Python modules:** `snake_case/` (e.g., `backend/routes/`, `veritas/agents/`)
- **React component dirs:** `kebab-case/` (e.g., `components/audit/`)
- **Pages:** `camelCase.ts` or `[slug]/page.tsx` for dynamic routes

### TypeScript/React
- **Components:** `PascalCase` (e.g., `CommandInput`, `EventLog`)
- **Hooks:** `camelCase` starting with `use` (e.g., `useAuditStream`)
- **Utilities:** `camelCase` (e.g., `formatDate`, `calculateScore`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_PAGES`, `DEFAULT_TIER`)

### Python
- **Classes:** `PascalCase` (e.g., `AuditRunner`, `AuditState`)
- **Functions/methods:** `snake_case` (e.g., `get_by_id`, `run_audit`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_ITERATIONS`, `DEFAULT_TIMEOUT`)
- **Modules:** `snake_case` (e.g., `orchestrator`, `audit_runner`)

### Database Models
- **Table names:** `PascalCase` (e.g., `Audit`, `AuditFinding`)
- **Columns:** `snake_case` (e.g., `audit_id`, `trust_score`)
- **Enums:** `PascalCase` (e.g., `AuditStatus.COMPLETED`)

---

## Where to Add New Code

### New Feature (Full Stack)
- **Backend API route**: `backend/routes/audit.py` (add new endpoint)
- **Backend service**: `backend/services/` (create new service if needed)
- **Frontend page**: `frontend/src/app/feature/` (new directory)
- **Frontend components**: `frontend/src/components/feature/` (new directory)
- **State management**: `frontend/src/lib/store.ts` or new hook

### New Agent (AI Layer)
- **Agent file**: `veritas/agents/new_agent.py` (implement agent logic)
- **Orchestrator node**: Add to `veritas/core/orchestrator.py` (add graph node)
- **Result types**: Define dataclass for agent output
- **Integration**: Update `veritas/agents/__init__.py` to export

### New Page (Frontend)
- **Route**: `frontend/src/app/page-name/page.tsx` (App Router file-based)
- **Components**: `frontend/src/components/page-name/` (colocate components)
- **State**: Use existing store or create new hook (`usePageName.ts`)
- **Type definitions**: Add to `frontend/src/types/` if needed

### New Component (UI)
- **Location**: `frontend/src/components/[category]/ComponentName.tsx`
- **Category choices**: `audit/`, `data-display/`, `terminal/`, `report/`, `layout/`, `ui/`
- **Testing**: Add `ComponentName.test.tsx` or test in page

### New Utility Function
- **Location**: `frontend/src/lib/utils.ts` (general), `frontend/src/lib/education.ts` (content)
- **Pattern**: Export named functions, use TypeScript
- **Backend utilities**: `backend/utils/` or appropriate service module

### Database Changes
- **Models**: Add to `veritas/db/models.py` (SQLAlchemy models)
- **Repository**: Add to `veritas/db/repositories.py` (add methods)
- **Migration**: Not required for SQLite (schema managed by code)
- **Seed data**: Add to test fixtures or verification scripts

### Configuration Changes
- **Feature flags**: `veritas/config/settings.py` (add to Settings class)
- **Frontend config**: `frontend/next.config.ts` or `tailwind.config.ts`
- **Environment**: Add to `veritas/.env` (NEVER commit these)

---

## Special Directories

### `.planning/`
- **Purpose**: GSD planning documents and phase definitions
- **Generated**: Yes
- **Committed**: Yes (to share planning context)

### `.venv/`
- **Purpose**: Python virtual environment with dependencies
- **Generated**: Yes (by `python -m venv .venv`)
- **Committed**: No (in `.gitignore`)

### `frontend/.next/`
- **Purpose**: Next.js build output (transpiled and optimized)
- **Generated**: Yes (by `npm run build`)
- **Committed**: No

### `veritas/data/cache/`
- **Purpose**: LLM response cache (JSON files keyed by hash)
- **Generated**: Yes (at runtime)
- **Committed**: Yes (persist across restarts)

### `veritas/data/screenshots/`
- **Purpose**: Audit screenshot storage
- **Generated**: Yes (by Vision agent)
- **Committed**: Yes (persisted to disk)

### `__pycache__/`
- **Purpose**: Python bytecode cache
- **Generated**: Yes (automatic)
- **Committed**: No

---

## Project-Specific Patterns

### API Pattern (REST + WebSocket)
- REST for initial request/response cycle
- WebSocket for streaming events during audit
- Two-way communication via event types

### Agent Pattern (LangGraph)
- State machine with typed state (AuditState)
- Nodes return partial state updates
- Conditional edges for control flow

### Component Pattern (React)
- Feature-based organization (audit, report, terminal)
- Colocation of related files
- Composition over inheritance

### State Pattern (Zustand)
- Single store for audit state (`useAuditStore`)
- Actions for state mutations
- Persist partial state across page navigations

### Database Pattern (Repository)
- Async session management
- Repository classes per entity
- Cascade deletes for related entities (e.g., findings, screenshots)

---

*Structure analysis: 2026-03-16*