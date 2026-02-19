# Codebase Structure

**Analysis Date:** 2026-02-19

## Directory Layout

```
elliotAI/
├── .planning/                    # Planning documents
│   └── codebase/                 # Generated architecture docs
├── .venv/                        # Python virtual environment (auto-created)
├── backend/                      # FastAPI REST + WebSocket API layer
│   ├── main.py                   # FastAPI app setup, CORS, route registration
│   ├── requirements.txt          # Backend dependencies (fastapi, uvicorn, websockets)
│   ├── routes/                   # API route handlers
│   │   ├── audit.py              # POST /audit/start, WS /audit/stream/{id}, GET /audit/{id}/status
│   │   └── health.py             # GET /health health check
│   └── services/
│       └── audit_runner.py       # Subprocess wrapper, stdout parsing, WebSocket event conversion
├── frontend/                     # Next.js 15 React web application
│   ├── package.json              # Frontend dependencies (next, react, framer-motion, Zustand)
│   ├── tsconfig.json             # TypeScript configuration
│   ├── components.json           # shadcn/ui component configuration
│   ├── public/                   # Static assets
│   └── src/
│       ├── app/                  # Next.js App Router pages
│       │   ├── layout.tsx        # Root layout with fonts, theme
│       │   ├── globals.css       # Tailwind CSS + custom Veritas theme
│       │   ├── page.tsx          # Landing page (Hero, Signals, Carousel, Grid)
│       │   ├── audit/[id]/       # Live audit view (WebSocket streaming)
│       │   │   └── page.tsx      # Three-column agent pipeline visualization
│       │   ├── report/[id]/      # Forensic report view
│       │   │   └── page.tsx      # Trust score findings, entity details, recommendations
│       │   └── v2/               # Alternative UI (experimental)
│       │       └── page.tsx
│       ├── components/           # React components organized by area
│       │   ├── ambient/           # Background effects
│       │   │   └── ParticleField.tsx
│       │   ├── audit/            # Live audit components
│       │   │   ├── AgentCard.tsx          # Individual agent status card
│       │   │   ├── AgentPipeline.tsx      # Multi-column agent visualization
│       │   │   ├── AuditHeader.tsx        # Audit info header
│       │   │   ├── CompletionOverlay.tsx  # Success/error completion screen
│       │   │   ├── EvidencePanel.tsx      # Screenshot carousel
│       │   │   ├── ForensicLog.tsx        # Log entry feed
│       │   │   └── NarrativeFeed.tsx      # AI-generated narrative stream
│       │   ├── data-display/     # Charts, badges, counters
│       │   │   ├── RiskBadge.tsx          # Risk level colored badge
│       │   │   ├── SeverityBadge.tsx      # Finding severity badge
│       │   │   ├── SignalBar.tsx          # Signal score progress bar
│       │   │   ├── SignalRadarChart.tsx   # Radar chart for 6 signals
│       │   │   ├── StatCounter.tsx        # Statistic counter with icon
│       │   │   └── TrustGauge.tsx         # Circular trust score gauge
│       │   ├── landing/          # Landing page sections
│       │   │   ├── DarkPatternCarousel.tsx  # Dark pattern examples carousel
│       │   │   ├── HeroSection.tsx          # Hero with description
│       │   │   ├── HowItWorks.tsx           # Step-by-step explanation
│       │   │   ├── SignalShowcase.tsx       # Signal feature showcase
│       │   │   └── SiteTypeGrid.tsx         # Site type classification grid
│       │   ├── layout/           # Navigation and layout
│       │   │   └── Navbar.tsx
│       │   └── report/           # Report page components
│       │       ├── AuditMetadata.tsx       # Audit metadata (tier, pages, duration)
│       │       ├── DarkPatternGrid.tsx     # Dark patterns findings grid
│       │       ├── EntityDetails.tsx       # Entity verification details
│       │       ├── Recommendations.tsx      # Actionable recommendations list
│       │       └── ReportHeader.tsx        # Report title with trust score
│       ├── hooks/                # Custom React hooks
│       │   └── useAuditStream.ts           # WebSocket connection + store handling
│       └── lib/                  # Shared utilities
│           ├── types.ts          # TypeScript interfaces (Phase, Finding, Screenshot, AuditResult)
│           ├── store.ts          # Zustand global store (audit info, phases, findings, logs)
│           └── education.ts      # Educational content data (dark patterns, site types)
├── veritas/                      # Python forensic auditing engine
│   ├── __main__.py               # CLI entry point (python -m veritas)
│   ├── .env                      # Environment variables (NVIDIA_API_KEY, endpoints, tuning)
│   ├── requirements.txt          # Python dependencies (langgraph, playwright, openai, etc.)
│   ├── agents/                   # AI agent implementations
│   │   ├── __init__.py
│   │   ├── scout.py              # StealthScout (Playwright browser, screenshots, metadata)
│   │   ├── vision.py             # VisionAgent (NIM VLM dark pattern detection)
│   │   ├── graph_investigator.py # GraphInvestigator (WHOIS, DNS, SSL, entity verification)
│   │   └── judge.py              # JudgeAgent (trust score, narrative, verdict)
│   ├── analysis/                 # Zero-AI security and structural analysis modules
│   │   ├── __init__.py
│   │   ├── dom_analyzer.py       # DOM structure analysis, element detection
│   │   ├── form_validator.py     # Form security validation (HTTPS, cross-domain checks)
│   │   ├── js_analyzer.py        # JavaScript behavior detection
│   │   ├── meta_analyzer.py      # Meta tag and SEO analysis
│   │   ├── pattern_matcher.py    # Dark pattern keyword matching
│   │   ├── phishing_checker.py   # Phishing indicator analysis
│   │   ├── redirect_analyzer.py  # Redirect chain tracing
│   │   ├── security_headers.py   # HTTP security header checks
│   │   └── temporal_analyzer.py  # Time-based content change detection
│   ├── config/                   # Configuration and tuning
│   │   ├── __init__.py
│   │   ├── settings.py           # Global settings: paths, NIM endpoints, audit tiers
│   │   ├── trust_weights.py      # Signal weight definitions, trust score computation
│   │   ├── dark_patterns.py      # Dark pattern categories and prompts
│   │   └── site_types.py         # Site type classification rules
│   ├── core/                     # Core infrastructure services
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # LangGraph state machine, audit node execution
│   │   ├── nim_client.py         # NVIDIA NIM API client (4-level fallback)
│   │   ├── evidence_store.py     # LanceDB vector evidence storage
│   │   ├── web_searcher.py       # Tavily search integration
│   │   └── tor_client.py         # Tor network client (.onion support)
│   ├── reporting/                # Report generation
│   │   ├── __init__.py
│   │   └── report_generator.py   # Markdown/JSON report builder
│   ├── ui/                       # Alternative Streamlit UI
│   │   ├── app.py                # Streamlit main app
│   │   └── app_v1_backup.py      # Backup version
│   ├── tests/                    # Test suite
│   │   ├── __init__.py
│   │   └── test_veritas.py       # Unit tests (20 tests)
│   └── data/                     # Runtime data (auto-created)
│       ├── cache/                # NIM response cache (24h TTL)
│       ├── evidence/             # Screenshot images
│       ├── reports/              # Generated reports
│       └── vectordb/             # LanceDB vector store
└── base models projects/         # Base model projects (reference/legacy)
    └── glass-box-portal/
        └── backend/
            └── main.py           # Reference: mobile viewport, stealth screenshot pattern
```

## Directory Purposes

**backend/**:
- Purpose: FastAPI application providing REST endpoints and WebSocket streaming
- Contains: route handlers, audit subprocess wrapper, health check
- Key files: `main.py` (FastAPI app), `routes/audit.py` (audit API), `services/audit_runner.py` (subprocess execution)

**frontend/**:
- Purpose: Next.js 15 web application for landing page, live audit view, forensic report
- Contains: App Router pages, React components, hooks, utilities, static assets
- Key files: `src/app/page.tsx` (landing), `src/app/audit/[id]/page.tsx` (live audit), `src/app/report/[id]/page.tsx` (report), `src/hooks/useAuditStream.ts` (WebSocket), `src/lib/store.ts` (state)

**veritas/**:
- Purpose: Core Python forensic auditing engine with LangGraph orchestration and 5 AI agents
- Contains: Agent implementations, analysis modules, core services, configuration
- Key files: `__main__.py` (CLI entry), `core/orchestrator.py` (state machine), `agents/scout.py` (browser), `agents/vision.py` (VLM), `agents/graph_investigator.py` (entity verification), `agents/judge.py` (scoring), `core/nim_client.py` (NIM API), `config/settings.py` (configuration)

## Key File Locations

**Entry Points:**
- `veritas/__main__.py`: Python CLI entry point for direct execution or subprocess invocation
- `backend/main.py`: FastAPI application setup, CORS, route registration
- `frontend/src/app/page.tsx`: Next.js root page (landing)
- `frontend/src/app/audit/[id]/page.tsx`: Live audit view with WebSocket streaming

**Configuration:**
- `veritas/.env`: Environment variables (NVIDIA_API_KEY, NIM endpoints, tuning)
- `veritas/config/settings.py`: Global configuration (paths, audit tiers, timeouts, weights)
- `veritas/config/trust_weights.py`: Signal weight definitions and trust score computation
- `veritas/config/dark_patterns.py`: Dark pattern categories, prompts, thresholds
- `veritas/config/site_types.py`: Site type classification profiles
- `frontend/package.json`: Frontend dependencies and npm scripts

**Core Logic:**
- `veritas/core/orchestrator.py`: LangGraph state machine, sequential node execution, routing logic
- `veritas/agents/scout.py`: StealthScout browser automation (Playwright, screenshots, metadata)
- `veritas/agents/vision.py`: VisionAgent VLM integration for dark pattern detection
- `veritas/agents/graph_investigator.py`: GraphInvestigator WHOIS, DNS, SSL, Tavily verification
- `veritas/agents/judge.py`: JudgeAgent trust scoring, narrative generation, verdict decision
- `veritas/core/nim_client.py`: NIMClient with 4-level fallback, rate limiting, caching

**Web API:**
- `backend/routes/audit.py`: POST /api/audit/start, WS /api/audit/stream/{id}, GET /audit/{id}/status
- `backend/routes/health.py`: GET /api/health
- `backend/services/audit_runner.py`: AuditRunner class for subprocess execution and stdout parsing

**Testing:**
- `veritas/tests/test_veritas.py`: Unit test suite (20 tests)

**Data Storage:**
- `veritas/data/cache/`: NIM response cache (JSON files, 24h TTL)
- `veritas/data/evidence/`: Screenshot images (JPEG)
- `veritas/data/reports/`: Generated reports (Markdown, HTML)
- `veritas/data/vectordb/`: LanceDB vector database

## Naming Conventions

**Files:**
- Python: snake_case (e.g., `graph_investigator.py`, `dark_pattern_matcher.py`)
- TypeScript: PascalCase for components (e.g., `AgentCard.tsx`, `DarkPatternGrid.tsx`), camelCase for utilities (e.g., `useAuditStream.ts`, `types.ts`)

**Functions:**
- Python: snake_case (e.g., `build_audit_graph()`, `run_audit()`, `investigate()`)
- TypeScript React: camelCase (e.g., `useAuditStream()`, `handleEvent()`)

**Variables:**
- Python: snake_case (e.g., `audit_tier`, `trust_score_result`)
- TypeScript: camelCase (e.g., `auditId`, `trustScore`)

**Types:**
- Python: PascalCase for dataclasses/classes (e.g., `ScoutResult`, `VisionAgent`, `TrustScoreResult`)
- TypeScript: PascalCase for interfaces/types (e.g., `AuditEvent`, `Finding`, `Phase`)

**Constants:**
- Python: UPPER_SNAKE_CASE (e.g., `MAX_ITERATIONS`, `NIM_VISION_MODEL`)
- TypeScript: UPPER_SNAKE_CASE for constants (e.g., `WS_BASE`, `RISK_COLORS`)

**Directories:**
- Lowercase with underscores where needed (e.g., `data-display`, `graph_investigator`)

## Where to Add New Code

**New Feature - Agent:**
- Primary code: `veritas/agents/<agent_name>.py`
- Create dataclass result type: `veritas/agents/<agent_name>.py` (e.g., `<AgentName>Result`)
- Add node to orchestrator: `veritas/core/orchestrator.py` (add `async def <agent>_node(state: AuditState) -> dict`)
- Add routing: `veritas/core/orchestrator.py` (add routing function, conditional edges)
- Tests: `veritas/tests/test_veritas.py` (add new test cases)

**New Feature - Analysis Module:**
- Primary code: `veritas/analysis/<module_name>.py`
- Follow pattern: async `analyze()` method returning dataclass with score, findings, errors
- Integrate: Call from Scout or Security node in `veritas/core/orchestrator.py`

**New Frontend Page:**
- Route file: `frontend/src/app/<route>/page.tsx` (or `frontend/src/app/<route>/[id]/page.tsx` for dynamic routes)
- Components: `frontend/src/components/<area>/<ComponentName>.tsx`
- Types: Add to `frontend/src/lib/types.ts` if new interfaces needed

**New Backend Endpoint:**
- Route file: `backend/routes/<resource>.py`
- Register: Add to `backend/main.py` with `app.include_router()`
- Request models: Use Pydantic BaseModel in route file
- WebSocket events: Add event type in `backend/services/audit_runner.py`, add handler in `frontend/src/lib/store.ts`

**New Security Module:**
- Primary code: `veritas/analysis/<module_name>.py`
- Integration: Add module name to `settings.ENABLED_SECURITY_MODULES` or pass via request
- Call from: `security_node()` in `veritas/core/orchestrator.py`

**New Report Format:**
- Primary code: `veritas/reporting/report_generator.py`
- Add format support: Add new method `generate_<format>()` to ReportGenerator class

**Utilities:**
- Shared helpers: `frontend/src/lib/<utility>.ts`
- Shared Python utilities: `veritas/core/<utility>.py` or `veritas/analysis/<utility>.py`

## Special Directories

**.venv/**:
- Purpose: Python virtual environment (auto-created by `python -m venv .venv`)
- Generated: Yes (install dependencies via `pip install -r veritas/requirements.txt`)
- Committed: No (.gitignore)

**veritas/data/**:
- Purpose: Runtime data storage (cache, evidence, reports, vectordb)
- Generated: Yes (directories auto-created on first run via settings.py)
- Committed: No (.gitignore)

**veritas/data/cache/**:
- Purpose: NIM response cache (24h TTL, MD5 keys)
- Generated: Yes (by NIMClient.write_cache())
- Committed: No

**veritas/data/evidence/**:
- Purpose: Screenshot images (JPEG format)
- Generated: Yes (by StealthScout._take_screenshot())
- Committed: No

**veritas/data/vectordb/**:
- Purpose: LanceDB vector storage for evidence similarity search
- Generated: Yes (by EvidenceStore when LanceDB initialized)
- Committed: No

**frontend/.next/**:
- Purpose: Next.js build output
- Generated: Yes (by `npm run build`/`npm run dev`)
- Committed: No (.gitignore)

**frontend/node_modules/**:
- Purpose: npm packages
- Generated: Yes (by `npm install`)
- Committed: No (.gitignore)

**.planning/**:
- Purpose: Planning documents and generated architecture docs
- Generated: No (user-defined planning)
- Committed: Yes

**base models projects/**:
- Purpose: Reference legacy projects (glass-box-portal pattern for mobile screenshots)
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-02-19*
