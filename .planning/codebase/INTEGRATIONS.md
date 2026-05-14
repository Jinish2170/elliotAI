# External Integrations
**Analysis Date:** 2026-05-14

## APIs & External Services

- **NVIDIA NIM** - VLM/LLM inference (vision forensics + judge agents); OpenAI-compatible API. SDK/Client: `openai` (`elliot/core/nim_client.py`). Base URL `https://integrate.api.nvidia.com/v1` (default). Auth: `NVIDIA_NIM_API_KEY`. Models configurable via `NIM_VISION_MODEL`, `NIM_VISION_FALLBACK`, `NIM_LLM_MODEL`.
- **Tavily** - External web search for entity verification. SDK/Client: `tavily-python` (`elliot/osint/sources/tavily_source.py`). Auth: `TAVILY_API_KEY`.
- **URLVoid** - Domain reputation / threat intelligence (free tier ~500 req/day). Client: `aiohttp` (`elliot/osint/sources/urlvoid.py`, endpoint `https://www.urlvoid.com/api/1000`). Auth: `URLVOID_API_KEY`.
- **AbuseIPDB** - IP reputation / abuse reports (free tier ~1000 req/day). Client: `aiohttp` (`elliot/osint/sources/abuseipdb.py`, endpoint `https://api.abuseipdb.com/api/v2/check`). Auth: `ABUSEIPDB_API_KEY`.
- **Google Safe Browsing** - Phishing/malware URL lookup (optional). Used by security modules (`elliot/config/security_rules.py`, `elliot/agents/security_agent.py`). Auth: `GOOGLE_SAFE_BROWSING_KEY`.
- **WHOIS registries** - Domain registration intelligence. SDK/Client: `python-whois` (`elliot/osint/sources/whois_lookup.py`). Auth: none.
- **DNS resolvers** - DNS record lookups. SDK/Client: `dnspython` (`elliot/osint/sources/dns_lookup.py`). Auth: none.
- **SSL/TLS certificate inspection** - Certificate verification (`elliot/osint/sources/ssl_verify.py`). Auth: none.
- **Darknet / TOR marketplaces** - `.onion` threat scraping across multiple market sources (`elliot/osint/sources/darknet_alpha.py`, `darknet_dream.py`, `darknet_empire.py`, `darknet_hansa.py`, `darknet_wallstreet.py`, `darknet_tor2web.py`; `elliot/darknet/`). Accessed via TOR SOCKS5h proxy (`PySocks`); `elliot/darknet/tor_client.py`, `elliot/core/tor_client.py`. Auth: none (proxy config via `TOR_*` env vars).
- **Target websites** - Audited sites loaded via Playwright headless Chromium (`elliot/agents/scout.py`, `elliot/agents/scout_nav/`).
- **Glass-box-portal (separate sub-project)** - `base models projects/glass-box-portal/backend/main.py` uses Google Generative AI (`GOOGLE_API_KEY`); not part of the main Elliot app.

## Data Storage

**Databases:**
- SQLite via SQLAlchemy 2.0 + aiosqlite (async, WAL mode). Config in `elliot/db/config.py` (`DATABASE_URL = sqlite+aiosqlite:///./data/elliot_audits.db`). Models/repos in `elliot/db/models.py`, `elliot/db/repositories.py`. Initialized on FastAPI startup (`backend/main.py` lifespan -> `init_database`).
- Database files observed: `data/veritas_audits.db`, `elliot_dev.db` (root), plus `.serena`/`.swarm` tooling DBs.
- PRAGMA tuning: `WAL` journal, `NORMAL` synchronous, 64MB cache, memory temp store.

**File Storage:**
- Local filesystem under `elliot/data/` and root `data/`: `evidence/`, `screenshots/`, `reports/`, `cache/`, `vectordb/` (auto-created by `elliot/config/settings.py`).
- Screenshots also at `elliot/screenshots/`. Generated reports via WeasyPrint/Jinja2 (`elliot/reporting/`, `elliot/reporters/`).

**Caching:**
- LanceDB disk-based vector store (`data/vectordb/`) with `sentence-transformers` embeddings (`all-MiniLM-L6-v2`).
- OSINT response caching in `elliot/osint/cache.py`.
- File-based cache directory `data/cache/`.

## Authentication & Identity

**Auth Provider:** Not detected. No end-user authentication/identity system. The backend is CORS-scoped to localhost origins (`ALLOWED_ORIGINS`, default `http://localhost:3000,http://127.0.0.1:3000`) with `allow_credentials=True` (`backend/main.py`). All "auth" is outbound API-key based for third-party services.

## Monitoring & Observability

**Error Tracking:** Not detected (no Sentry/Rollbar/etc.).

**Logs:** Python `logging` module (e.g., `logging.getLogger("elliot.settings")`); `psutil` for resource monitoring; progress events streamed over WebSocket (`elliot/core/progress/`, `elliot/core/ipc.py`). Ad-hoc debug artifacts present (`judge_debug.txt`, `frontend/ws_output*.log`). No structured/centralized observability stack.

## CI/CD & Deployment

**Hosting:** Not detected (no cloud hosting config). Local-first via `start.bat`/`stop.bat`; containerized backend via `Dockerfile` (uvicorn on port 8000, frontend served separately on port 3000).

**CI Pipeline:** Not detected (no `.github/workflows/`, GitLab CI, or other CI config in repo).

## Environment Configuration

**Required env vars:** (names only — values never read)
- NVIDIA NIM: `NVIDIA_NIM_API_KEY`, `NVIDIA_NIM_ENDPOINT`, `NIM_VISION_MODEL`, `NIM_VISION_FALLBACK`, `NIM_LLM_MODEL`, `NIM_TIMEOUT`, `NIM_RETRY_COUNT`, `NIM_REQUESTS_PER_MINUTE`
- Search/OSINT/CTI: `TAVILY_API_KEY`, `TAVILY_REQUESTS_PER_MINUTE`, `URLVOID_API_KEY`, `URLVOID_REQUESTS_PER_MINUTE`, `ABUSEIPDB_API_KEY`, `ABUSEIPDB_REQUESTS_PER_MINUTE`, `GOOGLE_SAFE_BROWSING_KEY`
- Graph intelligence: `GRAPH_PHASE_TIMEOUT_S`, `GRAPH_WHOIS_TIMEOUT_S`, `GRAPH_DNS_TIMEOUT_S`, `GRAPH_SSL_TIMEOUT_S`, `GRAPH_META_TIMEOUT_S`, `GRAPH_VERIFY_TIMEOUT_S`, `GRAPH_SEARCH_TIMEOUT_S`, `GRAPH_VERIFY_CONCURRENCY`, `GRAPH_SEARCH_FOLLOW_LINKS`, `GRAPH_ENABLE_OSINT`, `GRAPH_OSINT_TIMEOUT_S`, `GRAPH_OSINT_MAX_PARALLEL`, `GRAPH_ENABLE_CTI`, `GRAPH_CTI_MIN_CONFIDENCE`
- Audit budget/concurrency: `MAX_ITERATIONS`, `MAX_PAGES_PER_AUDIT`, `SCREENSHOT_TIMEOUT`, `TEMPORAL_DELAY`, `SCOUT_PREFETCH_LINKS`, `CONFIDENCE_THRESHOLD`, `MIN_EVIDENCE_COUNT`, `MAX_CONCURRENT_AUDITS`, `MAX_CONCURRENT_BROWSER_PAGES`, `INTER_REQUEST_DELAY_MS`, `DEFAULT_AUDIT_TIER`
- Browser/OCR: `BROWSER_HEADLESS`, `BROWSER_VIEWPORT_WIDTH`, `BROWSER_VIEWPORT_HEIGHT`, `MOBILE_VIEWPORT_WIDTH`, `MOBILE_VIEWPORT_HEIGHT`, `TESSERACT_CMD`, `EMBEDDING_MODEL`
- Security agent: `ENABLED_SECURITY_MODULES`, `USE_SECURITY_AGENT`, `SECURITY_AGENT_ROLLOUT`, `SECURITY_AGENT_TIMEOUT`, `SECURITY_AGENT_RETRY_COUNT`, `SECURITY_AGENT_FAIL_FAST`, `SECURITY_USE_TIER_EXECUTION`
- Persistence/verdict: `USE_DB_PERSISTENCE`, `DEFAULT_VERDICT_MODE`
- TOR: `TOR_ENABLED`, `TOR_SOCKS_HOST`, `TOR_SOCKS_PORT`
- Backend/IPC: `ALLOWED_ORIGINS`, `QUEUE_IPC_MODE`, `QUEUE_IPC_ROLLOUT`, `ELLIOT_SUBPROCESS`, `PYTHONIOENCODING`
- Separate sub-project only: `GOOGLE_API_KEY` (`base models projects/glass-box-portal/`)

**Secrets location:** `.env.example` template at repo root; runtime `.env` expected at `elliot/.env` (loaded by `elliot/config/settings.py` and `backend/main.py`). `.gitignore` present at root. No secrets manager/vault detected; secrets are local `.env` files only.

## Webhooks & Callbacks

**Incoming:** None (no webhook receiver endpoints). Backend exposes `POST /api/audit/start` and WebSocket `WS /api/audit/stream/{id}` for the frontend (`backend/routes/audit.py`), plus `GET /api/health` (`backend/routes/health.py`).

**Outgoing:** None. All outbound traffic is direct REST/HTTP calls to the third-party APIs listed above and Playwright/TOR browsing; no outbound webhook posts detected.

---
*Integration audit: 2026-05-14*
