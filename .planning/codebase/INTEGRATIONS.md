# External Integrations

**Analysis Date:** 2026-02-19

## APIs & External Services

**AI/Vision:**
- NVIDIA NIM (NVIDIA Inference Microservices) - Vision language models and LLMs
  - SDK/Client: OpenAI-compatible API via `openai>=1.0.0`
  - Auth: `NVIDIA_NIM_API_KEY` env var
  - Endpoint: `https://integrate.api.nvidia.com/v1`
  - Primary Models:
    - `nvidia/neva-22b` - Vision model for dark pattern detection
    - `microsoft/phi-3-vision-128k-instruct` - Fallback vision model
    - `meta/llama-3.1-70b-instruct` - LLM for judge agent reasoning
  - Implementation: `veritas/core/nim_client.py`

**External Search:**
- DuckDuckGo HTML Search - Web search via Playwright scraping
  - Custom web scraper implementation (no external API key required)
  - Implementation: `veritas/core/web_searcher.py`
  - Anti-detection: Stealth browser mode with user agent rotation

**Phishing Detection:**
- Google Safe Browsing API v4 - Malware/phishing URL checking
  - Auth: `GOOGLE_SAFE_BROWSING_KEY` env var (optional, free tier 10K/day)
  - Implementation: `veritas/analysis/phishing_checker.py`
- PhishTank - Community phishing database
  - API: `https://checkurl.phishtank.com/checkurl/`
  - No API key required (keyless lookups supported)
  - Implementation: `veritas/analysis/phishing_checker.py`

## Data Storage

**Databases:**
- LanceDB (Disk-based vector database)
  - Connection: Local filesystem storage at `veritas/data/vectordb/`
  - Client: `lancedb` Python package with sentence-transformers embeddings
  - Persistence: Survives restarts, ~90MB embedding model in RAM
  - Tables: `audits` (audit results), `evidence` (individual evidence items)
  - Fallback: JSONL files when LanceDB unavailable
  - Implementation: `veritas/core/evidence_store.py`

**File Storage:**
- Local filesystem only
  - Evidence: `veritas/data/evidence/` - Screenshots, captured content
  - Reports: `veritas/data/reports/` - Generated PDF reports
  - Cache: `veritas/data/cache/` - API response caching (24h TTL)

**Caching:**
- Response cache - `veritas/data/cache/` for NIM API responses
  - TTL: 24 hours
  - Keys: MD5 hashed from request parameters
  - Reduces API credit usage

## Authentication & Identity

**Auth Provider:**
- Custom implementation via FastAPI
  - No external auth provider required
  - Uses WebSocket connections for real-time audit streaming
  - Implementation: `backend/main.py`
  - CORS enabled for all origins in development

**API Keys Required:**
- `NVIDIA_NIM_API_KEY` - Critical for AI/vision analysis (from build.nvidia.com)
- `TAVILY_API_KEY` - Optional (web search - now using custom DuckDuckGo scraper)
- `GOOGLE_SAFE_BROWSING_KEY` - Optional (phishing detection enhancement)

## Monitoring & Observability

**Error Tracking:**
- None (custom logging implementation)
- Logging: Python logging module with structured logging

**Logs:**
- Python logging framework
- Log entries streamed to frontend via WebSocket
  - Implementation: `backend/routes/audit.py`, `frontend/src/hooks/useAuditStream.ts`
- Progress markers via stdout (`##PROGRESS:` prefix)
- Implementation: `veritas/core/orchestrator.py`

## CI/CD & Deployment

**Hosting:**
- Frontend: Vercel/Netlify compatible (Next.js)
- Backend: Container platform recommended (Docker/Kubernetes)
- No specific CI pipeline configured

**Local Development:**
- Launch scripts:
  - `start.bat` - Start complete system (Python venv activation + processes)
  - `stop.bat` - Shutdown all processes
  - Scripts configured for Windows (using forward slashes for bash compatibility)

## Environment Configuration

**Required env vars:**
- `NVIDIA_NIM_API_KEY` - Nvidia API key for AI services (REQUIRED)
- `NVIDIA_NIM_ENDPOINT` - API endpoint (default: `https://integrate.api.nvidia.com/v1`)

**Optional env vars:**
- `GOOGLE_SAFE_BROWSING_KEY` - Safe Browsing API key
- `TAVILY_API_KEY` - Alternative web search (not currently used, DuckDuckGo active)
- `NIM_VISION_MODEL` - Primary vision model (default: `meta/llama-3.2-90b-vision-instruct`)
- `NIM_VISION_FALLBACK` - Fallback vision model (default: `microsoft/phi-3.5-vision-instruct`)
- `NIM_LLM_MODEL` - LLM model (default: `meta/llama-3.1-70b-instruct`)

**Budget Controls (env vars):**
- `MAX_ITERATIONS` - Hard cap on reasoning cycles (default: 5)
- `MAX_PAGES_PER_AUDIT` - Pages to scan per audit (default: 10)
- `SCREENSHOT_TIMEOUT` - Screenshot capture timeout seconds (default: 15)
- `TEMPORAL_DELAY` - Delay between temporal screenshots (default: 10)
- `CONFIDENCE_THRESHOLD` - Minimum confidence for evidence (default: 0.6)
- `NIM_REQUESTS_PER_MINUTE` - Rate limit (default: 10)

**Concurrency (env vars):**
- `MAX_CONCURRENT_AUDITS` - Max parallel audits (default: 2)
- `MAX_CONCURRENT_BROWSER_PAGES` - Max browser pages (default: 3)
- `INTER_REQUEST_DELAY_MS` - Delay between requests (default: 500)

**Browser Configuration (env vars):**
- `BROWSER_HEADLESS` - Run headless (default: true)
- `BROWSER_VIEWPORT_WIDTH` - Viewport width (default: 1920)
- `BROWSER_VIEWPORT_HEIGHT` - Viewport height (default: 1080)

**Experimental (env vars):**
- `TOR_ENABLED` - Enable Tor proxy for .onion sites (default: false)
- `TOR_SOCKS_HOST` - Tor SOCKS proxy host (default: 127.0.0.1)
- `TOR_SOCKS_PORT` - Tor SOCKS proxy port (default: 9050)
  - Implementation: `veritas/core/tor_client.py` (stub, requires local Tor daemon)

**Secrets location:**
- `veritas/.env` file (not committed to git, template provided)
- `.gitignore` explicitly excludes `.env`

## Webhooks & Callbacks

**Incoming:**
- None (no webhook endpoints defined)

**Outgoing:**
- None (no external webhooks triggered)
- All external communication via HTTPS requests to integrated APIs

**Internal Communication:**
- WebSocket:
  - Endpoint: `ws://localhost:8000/api/audit/stream/{audit_id}`
  - Implemented in: `backend/routes/audit.py`
  - Client implementation: `frontend/src/hooks/useAuditStream.ts`
  - Events: phase_start, phase_complete, phase_error, finding, screenshot, stats_update, log_entry, audit_result, audit_complete, audit_error

---

*Integration audit: 2026-02-19*
