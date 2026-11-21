# Technology Stack
**Analysis Date:** 2026-05-14

## Languages

**Primary:**
- Python 3.11 (3.11.5 in dev venv; `Dockerfile` targets `python:3.12-slim`) - Agent orchestration core (`elliot/`), FastAPI backend (`backend/`), OSINT/darknet investigation, knowledge graph
- TypeScript 5.x - Next.js desktop/web frontend (`frontend/src/`)

**Secondary:**
- JavaScript (ESM) - Frontend tooling and WebSocket test harnesses (`frontend/run_ws.js`, `frontend/eslint.config.mjs`, `frontend/postcss.config.mjs`)
- Batch / Shell - Startup and install scripts (`start.bat`, `stop.bat`, `install_dependencies.bat`, `install_dependencies.sh`)

## Runtime

**Environment:**
- Python 3.11/3.12 backend run via `uvicorn` (`backend/main.py`, port 8000)
- Node.js 22.x (v22.22.0 in dev) for the Next.js frontend (port 3000)
- Note: PROJECT brief mentions Electron, but no Electron dependency was detected; the desktop UI is **Next.js 16** (`frontend/package.json`). A legacy Streamlit UI also exists (`elliot/ui/app.py`).

**Package Manager:**
- Python: `pip` with `requirements.txt` files (`elliot/requirements.txt`, `backend/requirements.txt`). No project-level `pyproject.toml` (only one inside `.venv/`). No pip lockfile present.
- Frontend: `npm` - lockfile present (`frontend/package-lock.json`); also a near-empty root `package.json` / `package-lock.json`.

## Frameworks

**Core:**
- FastAPI 0.115.0 - REST + WebSocket backend API (`backend/main.py`, `backend/routes/`)
- LangGraph 1.0.9 + LangChain 1.2.10 - Agent orchestration graph (`elliot/core/orchestrator.py`, `elliot/agents/`)
- Next.js 16.1.6 (React 19.2.3) - Frontend app-router UI (`frontend/src/app/`)
- Streamlit >=1.30.0 - Legacy/alternate UI (`elliot/ui/app.py`)

**Testing:**
- pytest >=7.4.0 with pytest-asyncio >=0.23.0 - Python tests (`pytest.ini`, `tests/`, `elliot/tests/`, `backend/tests/`); custom markers `integration`, `slow`
- httpx >=0.25.0 - Test HTTP client
- ESLint 9 (`eslint-config-next` 16.1.6) - Frontend linting (`frontend/eslint.config.mjs`)

**Build/Dev:**
- Next.js CLI (`next dev --webpack`, `next build`) - Frontend build (`frontend/package.json` scripts)
- Tailwind CSS 4 + `@tailwindcss/postcss` + shadcn 3.8.4 - Styling / UI components (`frontend/components.json`, `frontend/postcss.config.mjs`)
- TypeScript 5 compiler (`noEmit`, bundler resolution) - Type checking (`frontend/tsconfig.json`)
- Docker - Containerized backend (`Dockerfile`, installs Chromium for Playwright)

## Key Dependencies

**Critical:**
- openai 2.21.0 - Client for NVIDIA NIM (OpenAI-compatible API) for VLM/LLM calls (`elliot/core/nim_client.py`)
- playwright 1.58.0 - Headless browser automation for site capture/screenshots (`elliot/agents/scout.py`, `elliot/agents/scout_nav/`)
- networkx 3.6.1 - Knowledge graph construction (`elliot/agents/graph_investigator.py`)
- SQLAlchemy 2.0.48 + aiosqlite 0.22.1 - Async ORM persistence layer (`elliot/db/`)
- sentence-transformers >=2.2.0 + lancedb >=0.4.0 - Local embeddings (`all-MiniLM-L6-v2`) and disk-based vector store
- pydantic 2.9.0 - Data models / validation throughout `elliot/` and `backend/`
- tavily-python >=0.3.0 - External web search for entity verification (`elliot/osint/sources/tavily_source.py`)

**Infrastructure:**
- uvicorn[standard] 0.30.0 + websockets 12.0 - ASGI server and real-time audit event streaming
- tenacity >=8.2.0 - Retry with exponential backoff for NIM / external API calls
- aiohttp >=3.9.0 - Async HTTP for OSINT/CTI source clients
- PySocks >=1.7.1 - SOCKS5h proxy support for TOR/.onion access (`elliot/darknet/tor_client.py`, `elliot/core/tor_client.py`)
- python-whois >=0.9.0, dnspython >=2.4.0 - Domain/DNS intelligence (`elliot/osint/sources/whois_lookup.py`, `elliot/osint/sources/dns_lookup.py`)
- rank-bm25 >=0.2.2, numpy >=1.24.0 - RAG / keyword search ranking
- WeasyPrint >=60.0 + Jinja2 >=3.1.0 - PDF/HTML report generation (`elliot/reporting/`, `elliot/reporters/`)
- Pillow >=10.0.0, pytesseract >=0.3.10 - OCR fallback (requires external Tesseract binary)
- opencv-python >=4.8.0, scikit-image >=0.21.0 - Computer vision for temporal analysis
- matplotlib >=3.8.0 - Knowledge graph PNG visualization
- psutil >=5.9.0 - Resource monitoring
- Frontend: zustand 5 (state), framer-motion 12, recharts 3, radix-ui 1.4.3, lucide-react, ws 8.20 (WebSocket client)

## Configuration

**Environment:**
- `.env.example` present at repo root (template; not read per security rules). Runtime `.env` expected at `elliot/.env` — loaded by both `elliot/config/settings.py` and `backend/main.py` via `python-dotenv`.
- All runtime tuning is env-overridable in `elliot/config/settings.py` (NIM endpoints/models, timeouts, concurrency, browser viewport, security module toggles, TOR settings, audit tiers).
- Additional config modules: `elliot/config/` (`dark_patterns.py`, `darknet_rules.py`, `security_rules.py`, `site_types.py`, `trust_weights.py`); `elliot/db/config.py` (SQLite WAL settings).
- Frontend: `frontend/components.json`, `frontend/next.config.ts` (remote image patterns), `frontend/src/config/`.

**Build:**
- `Dockerfile` - Python 3.12-slim, installs Chromium + Playwright deps, runs `uvicorn main:app` on port 8000.
- `start.bat` / `stop.bat` - Local orchestration (kills ports 8000/3000, launches venv backend + frontend).
- `frontend/tsconfig.json`, `frontend/eslint.config.mjs`, `frontend/postcss.config.mjs` - Frontend build/lint config.
- `.mcp.json` - Claude-Flow MCP server config (dev tooling, not app runtime).

## Platform Requirements

**Development:**
- Windows 11 confirmed dev environment (paths like `C:\Program Files\Tesseract-OCR\tesseract.exe` defaulted in `settings.py`); cross-platform fallbacks present.
- Python venv at `.venv/`; Node.js 22.x with `frontend/node_modules/`.
- External binaries: Tesseract OCR (optional, OCR fallback); Tor daemon (optional, for `.onion`/darknet features, default SOCKS 127.0.0.1:9050).
- Tuned for 8GB RAM per `elliot/requirements.txt` header (concurrency limits in `settings.py`).

**Production:**
- Docker container (`Dockerfile`) for backend; Chromium bundled via `playwright install chromium`.
- Backend exposes port 8000; frontend (Next.js) served separately on port 3000.
- No CI/CD or cloud hosting configuration detected in-repo.

---
*Stack analysis: 2026-05-14*
