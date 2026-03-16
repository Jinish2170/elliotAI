# Architecture
**Analysis Date:** 2026-03-16

## Pattern Overview
**Overall:** Multi-agent LangGraph Pipeline with WebSocket Streaming

**Key Characteristics:**
- Agent-based orchestration using LangGraph's StateGraph with TypedDict
- Cyclic reasoning loop: Scout → Security → Vision → Graph → Judge → (loop or end)
- WebSocket real-time progress streaming to frontend
- Multiprocessing-based IPC for event queuing
- Adaptive timeout management with circuit breakers for resilience

## Layers

### 1. API/Entry Layer (FastAPI)
- **Purpose:** Expose REST endpoints and WebSocket streaming
- **Location:** `backend/main.py`, `backend/routes/audit.py`
- **Contains:**
  - `GET /api/health` — Health check
  - `POST /api/audit/start` — Initiate audit, returns audit_id
  - `WS /api/audit/stream/{id}` — Real-time event streaming
- **Depends on:** AuditRunner service
- **Used by:** Frontend Next.js application

### 2. Orchestration Layer
- **Purpose:** Coordinate multi-agent audit workflow with state management
- **Location:** `veritas/core/orchestrator.py`, `backend/services/audit_runner.py`
- **Contains:**
  - LangGraph StateGraph with AuditState TypedDict
  - Sequential node execution for each agent phase
  - Progress streaming via WebSocket
  - Quality penalty tracking and adaptive timeouts
- **Depends on:** All agent nodes (scout, security, vision, graph, judge)
- **Used by:** API layer (audit.py)

### 3. Agent Layer
- **Purpose:** Perform specific forensic analysis tasks
- **Location:** `veritas/agents/` (5 agents)
- **Contains:**
  - **Scout** (`scout.py`) — Browser automation, screenshot capture, metadata extraction
  - **Vision** (`vision.py`) — NIM-based visual analysis for dark patterns
  - **Graph** (`graph_investigator.py`) — WHOIS, DNS, SSL, OSINT, entity verification
  - **Judge** (`judge.py`) — Evidence synthesis and trust scoring
  - **Security** (`security_agent.py`) — OWASP vulnerability scanning
- **Depends on:** NIMClient, config settings, database
- **Used by:** Orchestrator

### 4. Data/Infrastructure Layer
- **Purpose:** Persist audit data, serve configuration, manage OSINT sources
- **Location:**
  - `veritas/db/` — SQLite database operations
  - `veritas/config/` — Settings and trust weights
  - `veritas/osint/` — External OSINT source integration
  - `veritas/darknet/` — Darknet marketplace intelligence
  - `veritas/cwe/` — CWE vulnerability database
- **Contains:**
  - SQLite with WAL mode for concurrent access
  - Trust score calculation engine
  - IOC detection and OSINT aggregation
  - CWE/CVSS vulnerability mappings
- **Depends on:** External APIs (OSINT, Darknet, CWE)
- **Used by:** All upper layers

### 5. Frontend Layer (Next.js)
- **Purpose:** Present real-time audit results in Bloomberg Terminal UI
- **Location:** `frontend/src/app/`
- **Contains:**
  - `page.tsx` — Main dashboard
  - `audit/[id]/page.tsx` — Live audit terminal with WebSocket streaming
  - `history/page.tsx` — Audit history
  - `report/[id]/page.tsx` — Audit detail view
  - `compare/[ids]/page.tsx` — Side-by-side comparison
- **Depends on:** API endpoints via WebSocket and REST
- **Used by:** End users

## Data Flow

### Primary Audit Flow
1. **Frontend:** User submits URL → POST `/api/audit/start`
2. **API:** Creates audit_id, returns immediately → WebSocket connection established
3. **Orchestrator:** Instantiates VeritasOrchestrator, executes `audit()` method
4. **Agent Execution Loop:**
   - **Scout:** Navigate URL, capture screenshots, collect metadata
   - **Security:** Run modular security scans (OWASP, darknet, phishing)
   - **Vision:** Analyze screenshots for dark patterns via NIM VLM
   - **Graph:** WHOIS lookup, DNS analysis, SSL verification, OSINT aggregation
   - **Judge:** Synthesize evidence, compute trust score, generate verdict
5. **Progress Streaming:** Real-time events sent via WebSocket
6. **Result Delivery:** Final audit_result sent to frontend, stored in SQLite

### State Management
- **AuditState TypedDict:** Shared state object flows through all nodes
  - URL, audit_tier, iteration, max_iterations
  - scout_results, vision_result, graph_result, judge_decision
  - pending_urls, investigated_urls (for cyclic investigation)
  - Timing, error tracking, NIM budget tracking

### Budget Controls
- **max_iterations:** Hard cap on reasoning cycles (set in settings)
- **max_pages:** Hard cap on total pages scouted
- **nim_call_budget:** Soft cap tracked via NIMClient.call_count (Phase 3 feature)

## Key Abstractions

### 1. AuditState TypedDict
- Purpose: Schema for shared state across all LangGraph nodes
- Examples: `veritas/core/orchestrator.py` (lines 51-97)
- Pattern: TypedDict for LangGraph state management

### 2. VeritasOrchestrator Class
- Purpose: High-level orchestrator API with smart features
- Examples: `veritas/core/orchestrator.py` (lines 173-897)
- Pattern: Adaptive timeout management, circuit breakers, fallback execution

### 3. AuditRunner Class
- Purpose: Bridge between FastAPI and veritas CLI/module execution
- Examples: `backend/services/audit_runner.py` (lines 31-737)
- Pattern: Subprocess execution with progress streaming via IPC

### 4. Agent Node Functions
- Purpose: Individual agent execution as LangGraph nodes
- Examples: `veritas/core/nodes/scout.py`, `vision.py`, `graph.py`, `judge.py`
- Pattern: Pure async functions receiving and updating AuditState

### 5. ProgressEmitter
- Purpose: Rate-limited WebSocket streaming with token-bucket algorithm
- Examples: `veritas/core/progress.py`
- Pattern: Buffering and throttling for smooth frontend updates

## Entry Points

### Backend Entry
- **Location:** `backend/main.py`
- **Triggers:** Uvicorn server starts
- **Responsibilities:** Initialize FastAPI, CORS, database, register routers

### Audit Execution Entry
- **Location:** `backend/routes/audit.py`
- **Triggers:** POST `/api/audit/start`
- **Responsibilities:** Accept URL, tier, security modules → instantiate AuditRunner → return audit_id

### WebSocket Stream Entry
- **Location:** `backend/routes/audit.py` (WebSocket endpoint)
- **Triggers:** WS connection to `/api/audit/stream/{id}`
- **Responsibilities:** Bridge AuditRunner events to frontend via asyncio

### Veritas CLI Entry
- **Location:** `veritas/__main__.py`
- **Triggers:** `python -m veritas <url> [options]`
- **Responsibilities:** Parse CLI arguments → run VeritasOrchestrator.audit() directly

## Error Handling

**Strategy:** Graceful degradation with fallback modes and circuit breakers

**Patterns:**
1. **Adaptive Timeouts:** TimeoutManager calculates per-agent timeouts based on page complexity
2. **Circuit Breakers:** FallbackManager wraps agent execution with failure detection
3. **Fallback Modes:**
   - Simplified: Return default scores when agent fails
   - Alternative: Use cached data or alternative sources
   - None: Return empty results
4. **Quality Penalty:** Accumulated quality degradation applied to final trust score
5. **Abort Conditions:** Too many consecutive scout failures or unrecoverable errors

## Cross-Cutting Concerns

### Logging
- Framework: Python standard logging
- Patterns: One logger per module (veritas.scout, veritas.orchestrator, etc.)
- Outputs: Console, file, and event stream

### Validation
- Approach: URL validation at API layer, tier/verdict_mode enum validation at orchestrator
- Location: audit.py routes, orchestrator.audit()

### Authentication
- Approach: None (open API for demo), can add auth middleware later
- Current: CORS allows all origins (for development)

---

*Architecture analysis: 2026-03-16*