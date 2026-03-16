# External Integrations
**Analysis Date:** 2026-03-16

## AI & LLM APIs

### NVIDIA NIM (Primary Inference Provider)
- **Purpose:** Vision Language Models for Agent 2 (Visual Forensics) + LLM for Agent 4 (Judge)
- **SDK/Client:** `openai>=1.0.0` Python library (OpenAI-compatible API)
- **Auth:** `NVIDIA_NIM_API_KEY` environment variable
- **Endpoint:** `NVIDIA_NIM_ENDPOINT` (default: https://integrate.api.nvidia.com/v1)
- **Models:**
  - Vision: `meta/llama-3.2-90b-vision-instruct` (primary), `microsoft/phi-3.5-vision-instruct` (fallback)
  - LLM: `meta/llama-3.1-70b-instruct`
- **Rate Limits:** Configurable via `NIM_REQUESTS_PER_MINUTE` (default: 40)
- **Timeout:** 90 seconds per request
- **Retry Logic:** Tenacity with exponential backoff (4 retries default)

### Tavily (External Search)
- **Purpose:** Search API for entity verification and OSINT
- **SDK/Client:** `tavily-python>=0.3.0`
- **Auth:** `TAVILY_API_KEY` environment variable
- **Features:** External search with rate limiting (5 requests/minute default)

## Data Storage

### SQLite Database
- **Type:** Local relational database (veritas_audits.db)
- **Connection:** `veritas.db` module with async SQLAlchemy
- **Mode:** WAL (Write-Ahead Logging) enabled
- **ORM:** SQLAlchemy 2.x (async)
- **Path:** `backend/data/veritas_audits.db`
- **Models:** Audit, AuditFinding, AuditScreenshot, AuditEvent

### Vector Database
- **Product:** LanceDB 0.4.0+
- **Purpose:** Disk-based vector store for embeddings (NOT in-memory)
- **Path:** `veritas/data/vectordb/`
- **Embedding Model:** all-MiniLM-L6-v2 (~90MB local model)

### File Storage
- **Screenshots:** `veritas/data/evidence/`
- **Reports:** `veritas/data/reports/`
- **Cache:** `veritas/data/cache/`
- **Implementation:** Custom ScreenshotStorage class

### Caching
- **Type:** Local disk cache
- **Location:** `veritas/data/cache/`
- **Purpose:** OSINT responses, domain analysis results

## Security & Threat Intelligence APIs

### URLVoid
- **Purpose:** Domain reputation and phishing detection
- **Auth:** `URLVOID_API_KEY` environment variable
- **Rate Limit:** 20 requests/minute (free tier: 500/day)
- **Usage:** Security module - phishing database checks

### AbuseIPDB
- **Purpose:** IP reputation and threat intelligence
- **Auth:** `ABUSEIPDB_API_KEY` environment variable
- **Rate Limit:** 15 requests/minute (free tier: 1000/day)
- **Usage:** OSINT/ CTI integration for malicious IP detection

### Google Safe Browsing
- **Purpose:** Phishing and malware URL checking
- **Auth:** `GOOGLE_SAFE_BROWSING_KEY` environment variable
- **Rate Limit:** 10,000 lookups/day (free tier)
- **Usage:** Security module toggle (disabled by default if not configured)

## Browser Automation

### Playwright
- **Version:** 1.40.0+
- **Purpose:** Headless browser for website scraping and screenshots
- **Configuration:**
  - Headless: `BROWSER_HEADLESS` (default: true)
  - Viewport: 1920x1080 (desktop), 390x844 (mobile)
  - Browser context per audit with custom settings
- **Timeouts:** Screenshot timeout (25s), page load timeout configurable

### Tesseract OCR (Optional Fallback)
- **Purpose:** Extract text from images if other methods fail
- **Binary:** Path from `TESSERACT_CMD` env var
- **Usage:** Level 3 fallback in vision analysis pipeline

## Authentication & Identity

**Auth Provider:** Custom/Future
- Current: No authentication on API endpoints (CORS enabled for all origins)
- Plan: Veritas authentication system (future)
- Implementation: CORS middleware allows all origins (`allow_origins=["*"]`)

## WebSocket & Real-Time Communication

### Backend WebSocket Server
- **Endpoint:** `ws://localhost:8000/api/audit/stream/{audit_id}`
- **Protocol:** JSON messages over WebSocket
- **Library:** FastAPI WebSocket + websockets 12.0
- **Usage:** Stream real-time audit progress, findings, and events to frontend

### Frontend WebSocket Client
- **Implementation:** Native WebSocket API in React hooks
- **Base URL:** `NEXT_PUBLIC_WS_URL` or `ws://localhost:8000`
- **Hooks:** `useAuditStream.ts` - manages connection lifecycle
- **State Management:** Zustand store for audit state

## Monitoring & Observability

**Error Tracking:** Not currently integrated
- Backend logs: Python logging (veritas config modules)
- Frontend logs: console.* - No external error tracking service

**Logs:**
- Python: Standard logging module with `__name__` loggers
- Location: Console output (uvicorn server logs)
- Frontend: Browser console

## CI/CD & Deployment

**Hosting:**
- Backend: FastAPI on uvicorn (local development)
- Frontend: Next.js 16 (local development)
- Production: Ready for containerization (Docker not configured)

**CI Pipeline:**
- Not currently configured
- Tests: pytest framework in `veritas/tests/` directory
- Frontend: ESLint for code quality

## Environment Configuration

### Required ENV Keys (Backend/Veritas)
- `NVIDIA_NIM_API_KEY` - AI inference (NVIDIA NIM credits)
- `TAVILY_API_KEY` - External search
- `URLVOID_API_KEY` - Domain reputation
- `ABUSEIPDB_API_KEY` - IP threat intel
- `GOOGLE_SAFE_BROWSING_KEY` - Phishing checks (optional)
- `TOR_ENABLED` - Enable TOR routing (default: false)
- `TOR_SOCKS_HOST`, `TOR_SOCKS_PORT` - TOR proxy config

### Derived from Backend
- `NEXT_PUBLIC_WS_URL` - Frontend WebSocket endpoint

### Configuration Hierarchy
1. Environment variables from `.env` (veritas/)
2. Defaults in `veritas/config/settings.py`
3. Runtime overrides in audit tiers

## Webhooks & Callbacks

**Incoming:**
- None currently configured

**Outgoing:**
- WebSocket streaming events to frontend during audit execution
- JSON events: audit progress, findings, screenshots, final report

## Inter-Process Communication

**Architecture:**
- Backend (FastAPI) → Veritas agents (Python) via direct imports
- Frontend (React) ↔ Backend via REST + WebSocket
- Agent orchestration: LangGraph state machine from `veritas/core/orchestrator.py`

**Key Files:**
- `backend/services/audit_runner.py` - Audit lifecycle management
- `veritas/core/orchestrator.py` - LangGraph workflow
- `backend/routes/audit.py` - REST + WebSocket endpoints

---
*Integration audit: 2026-03-16*