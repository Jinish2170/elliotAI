# Architecture
**Analysis Date:** 2026-03-16

## Pattern Overview
**Overall:** Multi-tier Web Application with Agentic AI Backend
**Architecture Style:** REST + WebSocket API with LangGraph Orchestration

**Key Characteristics:**
- **Frontend**: Next.js 14+ with React Server Components and client-side state management
- **Backend**: FastAPI with async Python for high-concurrency request handling
- **AI Engine**: LangGraph-based state machine orchestration with specialized agents
- **Real-time**: WebSocket streaming for live audit progress and results
- **Data Persistence**: SQLite with async SQLAlchemy ORM and repository pattern

## Layers

### 1. Frontend Layer (Next.js Application)
**Location:** `frontend/src/app/` and `frontend/src/components/`
**Purpose:** User interface, visualization, and client-side state management

**Contains:**
- **Routing**: Next.js App Router with dynamic routes (`audit/[id]`, `report/[id]`, `compare/[ids]`)
- **Pages**:
  - `page.tsx` - Landing/home with command input and recent audits
  - `audit/[id]/page.tsx` - Real-time audit streaming and monitoring
  - `report/[id]/page.tsx` - Post-audit report with findings, evidence, recommendations
  - `history/page.tsx` - Audit history with pagination and filtering
  - `compare/page.tsx` and `compare/[ids]/page.tsx` - Multi-audit comparison
- **Components**:
  - Data display: `SignalBar`, `TrustGauge`, `RiskBadge`, `SeverityBadge`, `StatCounter`, `SignalRadarChart`
  - Audit: `EventLog`, `DataFeed`, `FindingRow`, `EvidenceStack`, `ScreenshotCarousel`
  - Terminal: `TerminalPanel`, `KnowledgeGraph`, `DarknetOsintGrid`, `SysLogStream`
  - Report: `FindingsPanel`, `SignalTable`, `SecurityMatrix`, `ExecSummary`, `MetadataGrid`
- **State Management**: Zustand store (`useAuditStore`) for audit state and WebSocket events
- **Stream Handling**: Custom hook `useAuditStream` for real-time audit event processing

**Key Dependencies:**
- `@tanstack/react-query` - Server state management
- `zustand` - Client state
- `recharts` and `chart.js` - Data visualization
- `@radix-ui/*` - UI primitives

**Depends on:** Backend API via REST/WebSocket

---

### 2. API Gateway Layer (FastAPI)
**Location:** `backend/main.py`, `backend/routes/`
**Purpose:** HTTP/WebSocket endpoint handling, request validation, and orchestration

**Entry Points:**
- `backend/main.py` - FastAPI application with CORS middleware and router registration
- `backend/routes/audit.py` - Audit endpoints (start, stream, status, history, compare)
- `backend/routes/health.py` - Health check

**Routes:**
- `POST /api/audit/start` - Initiate audit, returns audit_id
- `WS /api/audit/stream/{audit_id}` - WebSocket for real-time streaming
- `GET /api/audit/{audit_id}/status` - Poll audit status
- `GET /api/audits/history` - Paginated history with filtering
- `POST /api/audits/compare` - Compare multiple audits

**Dependencies:**
- `fastapi` - Framework
- `sqlalchemy.ext.asyncio` - Async ORM
- `pydantic` - Request/response validation

**Used by:** Frontend WebSocket and REST clients

---

### 3. Service Layer (Audit Runner)
**Location:** `backend/services/audit_runner.py`
**Purpose:** Coordinates the audit execution, bridges API to core logic

**Responsibilities:**
- Initialize audit execution
- Stream events back to WebSocket client
- Handle timeout and error management
- Generate audit IDs

**Pattern:** Singleton pattern with per-audit instantiation through `AuditRunner` class

**Depends on:** Veritas core orchestrator

---

### 4. Core AI Layer (LangGraph Orchestrator)
**Location:** `veritas/core/orchestrator.py`
**Purpose:** State machine managing the multi-agent audit workflow

**State Machine Flow:**
```
START → SCOUT → VISION → GRAPH → JUDGE → REPORT
  ↓                              ↓
  └────── More investigation? ───┘
```

**Budget Controls:**
- `max_iterations` - Hard cap on reasoning cycles
- `max_pages` - Hard cap on total pages scouted
- `nim_call_budget` - Soft cap tracked via NIMClient.call_count

**Key Classes:**
- `AuditState` (TypedDict) - Shared state flowing through graph nodes
- StateGraph compiled once, invoked per audit

**Depends on:** Agent modules (Scout, Vision, Judge, Graph)

---

### 5. Agent Layer (Specialized AI Agents)
**Location:** `veritas/agents/`

**Agents:**

**Scout Agent** (`veritas/agents/scout.py`, `veritas/agents/scout_nav/`)
- Purpose: URL exploration and page discovery
- Responsibilities: Crawl websites, extract links, identify site type
- Output: `ScoutResult` with discovered URLs and site classification

**Vision Agent** (`veritas/agents/vision.py`, `veritas/agents/vision/`)
- Purpose: Screenshot capture and visual analysis
- Responsibilities: Capture page screenshots, analyze visual patterns
- Output: `VisionResult` with captured screenshots and visual metadata

**Graph Investigator** (`veritas/agents/graph_investigator.py`)
- Purpose: Relationship mapping and link analysis
- Responsibilities: Analyze inter-page relationships, identify navigation patterns
- Output: `GraphResult` with relationship graph and insights

**Judge Agent** (`veritas/agents/judge.py`, `veritas/agents/judge/`)
- Purpose: Evidence evaluation and verdict generation
- Responsibilities: Assess findings, calculate trust scores, generate risk assessments
- Output: `JudgeDecision` with verdict, confidence, and recommendations

**Security Agent** (`veritas/agents/security_agent.py`)
- Purpose: Security vulnerability scanning
- Responsibilities: Run security checks, aggregate security results
- Output: Security analysis results

---

### 6. Data Layer (Persistence)
**Location:** `veritas/db/`, `backend/data/`
**Purpose:** Persistent storage and data access

**Database:** SQLite with WAL mode enabled

**Schema Models** (`veritas/db/models.py`):
- `Audit` - Main audit record (id, url, status, trust_score, risk_level, findings, screenshots)
- `AuditFinding` - Individual findings (pattern_type, category, severity, confidence, description)
- `AuditScreenshot` - Screenshot metadata (file_path, label, index_num, file_size_bytes)
- `AuditStatus` - Enum (QUEUED, RUNNING, COMPLETED, ERROR, DISCONNECTED)

**Repositories** (`veritas/db/repositories.py`):
- `AuditRepository` - CRUD operations for audits and related entities

**Storage:**
- Database: `backend/data/veritas_audits.db` (SQLite with WAL)
- Screenshots: `veritas/data/screenshots/` (filesystem)

**Configuration:** `veritas/config/settings.py` with `should_use_db_persistence()` flag

---

### 7. Configuration & Infrastructure
**Location:** `veritas/config/`, `veritas/core/`

**Configuration:**
- `settings.py` - Main settings (API keys, feature flags, persistence config)
- `trust_weights.py` - Trust score calculation weights
- `site_types.py` - Site classification definitions
- `constants.py` - Shared constants

**Core Utilities:**
- `nim_client.py` - NVIDIA NIM API client for LLM inference
- `timeout_manager.py` - Timeout and complexity management
- `complexity_analyzer.py` - Page/site complexity scoring
- `degradation.py` - Graceful degradation strategies
- `ipc.py` - Inter-process communication for progress events

**Error Handling:**
- Custom exception hierarchy
- Fallback mode management via `DegradedResult` and `FallbackManager`
- Error state propagation through orchestrator state

---

## Data Flow

### Primary Flow: Website Audit

```
1. USER ACTION
   └─> Frontend: Enter URL + tier → POST /api/audit/start

2. API GATEWAY
   └─> Backend: Generate audit_id → Store in-memory → Return audit_id + ws_url

3. WEBSOCKET CONNECTION
   └─> Frontend: WS /api/audit/stream/{audit_id}
   └─> Backend: Accept → Update audit_info["status"] → "running"

4. AUDIT EXECUTION
   └─> Backend: Create AuditRunner(...)
   └─> Runner: Orchestrator.run(send_event_callback)

5. ORCHESTRATION (LangGraph)
   ├─> SCOUT: Discover pages/links → ScoutResult
   ├─> VISION: Capture screenshots → VisionResult
   ├─> GRAPH: Analyze relationships → GraphResult
   └─> JUDGE: Evaluate evidence → JudgeDecision
   └─> Loop: Judge can request more investigation → back to SCOUT

6. EVENT STREAMING
   └─> Runner calls send_event(data) for each state transition
   └─> Backend: ws.send_json(event) → Frontend: ws.onmessage

7. COMPLETION
   └─> Runner: audit_info["result"] = final_result
   └─> Backend: on_audit_completed() → Database persistence
   └─> Frontend: Handle complete event → Show report page
```

### Secondary Flows

**History Retrieval:**
- Frontend: GET /api/audits/history?limit=20&offset=0
- Backend: AuditRepository.get_paginated() → SQLAlchemy query
- Response: Array of audit summaries

**Audit Comparison:**
- Frontend: POST /api/audits/compare with audit_ids[]
- Backend: Fetch all audits → Calculate deltas → Return comparison data

**Status Polling:**
- Frontend: GET /api/audit/{audit_id}/status
- Backend: Check DB (if persistence) → Fallback to in-memory

---

## Key Abstractions

### API Contracts (Pydantic Models)
- `AuditStartRequest` - url, tier, verdict_mode, security_modules
- `AuditStartResponse` - audit_id, status, ws_url
- Streaming events: `audit_started`, `scout_progress`, `vision_capture`, `graph_analyzed`, `judge_decision`, `audit_result`, `audit_error`

### Agent Interfaces (Protocols)
- Each agent has a result dataclass (ScoutResult, VisionResult, GraphResult, JudgeDecision)
- Standardized output formats for downstream processing
- Error handling integrated into result types

### Repository Pattern
- `AuditRepository(db: AsyncSession)` - Clean abstraction over SQLAlchemy
- Methods: `get_by_id()`, `create()`, `update()`, `get_paginated()`, `get_by_status()`

### Event-Based Communication
- WebSocket events with typed payloads
- Frontend store handles events to update UI reactively
- Screenshot events handled with base64 encoding → filesystem save

---

## Entry Points

### Backend Entry
- **Primary**: `backend/main.py` - FastAPI app initialization
  - Triggers: Application startup via `uvicorn.run("main:app")`
  - Initializes SQLite with WAL mode
  - Registers routes

### Frontend Entry
- **Primary**: `frontend/src/app/layout.tsx` - Root layout
  - Triggers: Any page load
  - Renders Navbar and children
- **Audit Flow Entry**: `frontend/src/app/page.tsx` (landing)/command input
- **Audit Page**: `frontend/src/app/audit/[id]/page.tsx` (dynamic route)

### API Entry Points
- POST /api/audit/start - Audit creation
- WS /api/audit/stream/{audit_id} - Real-time audit execution
- GET /api/audit/{audit_id}/status - Status check
- GET /api/audits/history - History listing
- POST /api/audits/compare - Audit comparison

---

## Error Handling

**Strategy:** Graceful degradation with fallback modes

**Patterns:**
1. **In-Memory Fallback**: If DB persistence disabled, audit state stored in `_audits` dict
2. **FallbackManager**: `FallbackMode.ORCHESTRATOR_LITE` - Simplified agent execution
3. **Timeout Management**: Per-stage timeouts with complexity-based calculation
4. **Error Propagation**: Errors accumulated in `AuditState.errors` list
5. **WebSocket Error Events**: Errors sent back to client for display

**Key Handlers:**
- `on_audit_error(audit_id, error, db)` - Database error persistence
- WebSocket exception handling with `ws.close()` in finally block

---

## Cross-Cutting Concerns

### Logging
- **Framework**: Python standard `logging` with module loggers
- **Pattern**: `logger = logging.getLogger("veritas.orchestrator")`
- **Levels**: INFO, WARNING, ERROR with context (audit_id)
- **Output**: Console (via uvicorn) + structured event streaming

### Validation
- **Framework**: Pydantic models for request/response validation
- **Pattern**: Type hints on route handlers with `Annotated[Type, Depends(...)]`
- **Example**: `DbSession = Annotated[AsyncSession, Depends(get_db)]`

### Authentication
- **Current**: None (CORS allows all origins in dev)
- **Production Note**: Would require auth middleware and token validation

### Environment Configuration
- **Method**: Python-dotenv with `.env` file
- **Location**: `veritas/.env` loaded by backend/main.py
- **Secrets**: API keys, database path, NIM configuration

### Caching
- **Method**: Filesystem cache in `veritas/data/cache/`
- **Pattern**: JSON files with hashed keys for LLM responses
- **Integration**: NIMClient uses cache for repeated queries

---

## Technology Stack Summary

| Component | Technology | Version |
|-----------|------------|---------|
| Frontend Framework | Next.js | 14+ |
| UI | React + Tailwind CSS | Latest |
| State | Zustand + React Query | Latest |
| Charts | Recharts + Chart.js | Latest |
| Backend Framework | FastAPI | Latest |
| Async ORM | SQLAlchemy 2.0+ (async) | Latest |
| Database | SQLite (WAL mode) | 3+ |
| LLM Orchestration | LangGraph | Latest |
| LLM Client | NVIDIA NIM | Latest |
| Agent Framework | Custom (LangChain primitives) | Latest |
| HTTP Client | httpx (async) | Latest |
| WebSocket | FastAPI native | Latest |
| Python | 3.11+ | Latest |

---

*Architecture analysis: 2026-03-16*