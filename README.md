<p align="center">
  <img src="frontend/public/file.svg" width="80" alt="Veritas Logo" />
</p>

<h1 align="center">VERITAS</h1>
<p align="center">
  <strong>Autonomous Multi-Modal Forensic Web Auditor</strong>
</p>

<p align="center">
  <a href="#features">Features</a> · 
  <a href="#architecture">Architecture</a> · 
  <a href="#quick-start">Quick Start</a> · 
  <a href="#api-reference">API</a> · 
  <a href="#testing">Testing</a> · 
  <a href="#configuration">Configuration</a>
</p>

---

Veritas is an AI-powered forensic web auditing platform that analyzes websites for trust, safety, dark patterns, and security vulnerabilities. It combines **5 specialized AI agents** with **visual analysis**, **graph investigation**, and **multi-signal scoring** to produce comprehensive trust reports.

---

## Features

- **5-Phase Autonomous Pipeline** — Scout → Security → Vision → Graph Investigation → Judge  
- **NVIDIA NIM Integration** — LLM reasoning + Vision Language Model for screenshot analysis  
- **22 Analysis Modules** — DOM parsing, form validation, dark pattern detection, phishing checks, redirect tracing, temporal analysis, security headers, meta tag analysis, JavaScript behavior analysis  
- **Real-Time WebSocket Streaming** — Live progress, findings, and screenshots streamed to the browser  
- **Trust Score Engine** — Weighted multi-signal scoring (0–100) with risk classification  
- **Dark Pattern Detection** — 5 categories: Urgency, Misdirection, Social Proof, Obstruction, Sneaking  
- **Next.js 15 Frontend** — Animated three-column live audit view, interactive report with Simple/Expert modes  
- **LanceDB Vector Store** — Evidence persistence and similarity search  
- **Playwright Browser Automation** — Headless screenshot capture, DOM extraction, interaction testing  

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  Landing ──→ Live Audit (WebSocket) ──→ Report           │
│  Port 3000                                               │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP + WebSocket
┌────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                         │
│  POST /api/audit/start   WS /api/audit/stream/{id}       │
│  GET  /api/audit/{id}/status   GET /api/health            │
│  Port 8000                                               │
└────────────────────┬────────────────────────────────────┘
                     │ Subprocess + stdout
┌────────────────────▼────────────────────────────────────┐
│                  Veritas Python Engine                    │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌───────────┐  │
│  │  Scout   │→│ Security │→│ Vision │→│   Graph    │   │
│  │  Agent   │  │  Agent   │  │ Agent  │  │Investigator│  │
│  └─────────┘  └──────────┘  └────────┘  └─────┬─────┘  │
│                                                 │        │
│  ┌──────────────────────────────────────────────▼─────┐  │
│  │                  Judge Agent                        │  │
│  │  Weighted scoring · Risk classification · Report    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  NVIDIA NIM (LLM + VLM) · Playwright · LanceDB          │
└──────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Requirement | Minimum Version | Recommended |
|-------------|----------------|-------------|
| **Python** | 3.12 | 3.13+ |
| **Node.js** | 20.x | 22+ |
| **npm** | 9.x | 10+ |
| **Git** | 2.x | Latest |
| **NVIDIA NIM API Key** | — | Required |

> **Windows users**: Use PowerShell or CMD. Git Bash works too.  
> **Linux/macOS users**: All commands work as-is.

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/veritas.git
cd veritas
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install Python engine dependencies
pip install -r veritas/requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure Environment Variables

Create the file `veritas/.env`:

```env
# ── NVIDIA NIM ──────────────────────────────
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_NIM_ENDPOINT=https://integrate.api.nvidia.com/v1
NIM_VISION_MODEL=nvidia/llama-3.2-nv-vision-90b-instruct
NIM_VISION_FALLBACK=nvidia/llama-3.2-nv-vision-11b-instruct
NIM_LLM_MODEL=nvidia/llama-3.3-nemotron-super-49b-v1

# ── API Keys (optional) ────────────────────
TAVILY_API_KEY=                       # Leave empty to disable web search

# ── Tuning ──────────────────────────────────
NIM_TIMEOUT=30
NIM_RETRY_COUNT=2
NIM_REQUESTS_PER_MINUTE=10
MAX_ITERATIONS=5
MAX_PAGES_PER_AUDIT=10
TEMPORAL_DELAY=10
CONFIDENCE_THRESHOLD=0.6
BROWSER_HEADLESS=true
```

### 4. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 6. Run (Development)

Open **two terminals**:

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## Production Deployment

### Frontend Production Build

```bash
cd frontend
npm run build
npm start
```

### Backend with Gunicorn (Linux/macOS)

```bash
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (Optional)

```dockerfile
# backend/Dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY veritas/ ./veritas/
COPY backend/ ./backend/
COPY veritas/requirements.txt ./veritas/
COPY backend/requirements.txt ./backend/
RUN pip install -r veritas/requirements.txt -r backend/requirements.txt
RUN playwright install chromium --with-deps
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:22-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build
CMD ["npm", "start"]
```

```yaml
# docker-compose.yml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    env_file: veritas/.env

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
```

---

## API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Service health check |
| `POST` | `/api/audit/start` | Start a new audit |
| `GET` | `/api/audit/{id}/status` | Get audit status |

#### POST /api/audit/start

**Request Body:**
```json
{
  "url": "https://example.com",
  "tier": "standard"
}
```

**Response:**
```json
{
  "audit_id": "vrts_a1b2c3d4",
  "status": "queued",
  "ws_url": "/api/audit/stream/vrts_a1b2c3d4"
}
```

### WebSocket

Connect to `ws://localhost:8000/api/audit/stream/{audit_id}` to receive real-time events.

**Event Types:**

| Type | Payload | Description |
|------|---------|-------------|
| `phase_start` | `{ phase, name }` | Agent phase begins |
| `phase_complete` | `{ phase, name }` | Agent phase finishes |
| `finding` | `{ category, severity, title, description, evidence }` | Dark pattern or issue found |
| `screenshot` | `{ url, data, timestamp }` | Base64 screenshot captured |
| `stats_update` | `{ pages_crawled, patterns_found, ... }` | Live statistics |
| `log_entry` | `{ level, message, timestamp, source }` | Technical log line |
| `site_type` | `{ site_type, confidence }` | Detected site category |
| `security_result` | `{ header, present, value }` | Security header check |
| `audit_result` | `{ trust_score, risk_level, signals, ... }` | Final scored result |
| `audit_complete` | `{ audit_id }` | Audit finished |

---

## Project Structure

```
veritas/
├── veritas/                        # Python auditing engine
│   ├── __main__.py                 # CLI entry point
│   ├── .env                        # Environment config
│   ├── requirements.txt            # Python dependencies
│   ├── agents/                     # AI agent modules
│   │   ├── scout.py                # Phase 1: URL crawling & DOM extraction
│   │   ├── vision.py               # Phase 3: VLM screenshot analysis
│   │   ├── graph_investigator.py   # Phase 4: Entity graph & link analysis
│   │   └── judge.py                # Phase 5: Scoring & verdict
│   ├── analysis/                   # Analysis modules
│   │   ├── dom_analyzer.py         # HTML structure analysis
│   │   ├── form_validator.py       # Form security checks
│   │   ├── js_analyzer.py          # JavaScript behavior detection
│   │   ├── meta_analyzer.py        # Meta tag & SEO checks
│   │   ├── pattern_matcher.py      # Dark pattern detection
│   │   ├── phishing_checker.py     # Phishing indicator analysis
│   │   ├── redirect_analyzer.py    # Redirect chain tracing
│   │   ├── security_headers.py     # HTTP security headers
│   │   └── temporal_analyzer.py    # Time-based content changes
│   ├── config/                     # Configuration
│   │   ├── settings.py             # App settings & env loading
│   │   ├── trust_weights.py        # Signal weight definitions
│   │   ├── dark_patterns.py        # Pattern category definitions
│   │   └── site_types.py           # Site classification rules
│   ├── core/                       # Core infrastructure
│   │   ├── orchestrator.py         # LangGraph pipeline orchestrator
│   │   ├── nim_client.py           # NVIDIA NIM API client
│   │   ├── evidence_store.py       # LanceDB evidence storage
│   │   ├── web_searcher.py         # External search integration
│   │   └── tor_client.py           # Tor network client
│   ├── reporting/                  # Report generation
│   │   └── report_generator.py     # Markdown/JSON report builder
│   └── tests/                      # Test suite
│       └── test_veritas.py         # 20 unit tests
│
├── backend/                        # FastAPI API layer
│   ├── main.py                     # CORS, routers, sys.path setup
│   ├── requirements.txt            # fastapi, uvicorn, websockets
│   ├── routes/
│   │   ├── audit.py                # REST + WebSocket endpoints
│   │   └── health.py               # Health check
│   └── services/
│       └── audit_runner.py         # Subprocess wrapper for engine
│
├── frontend/                       # Next.js 15 UI
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx          # Root layout (fonts, theme)
│   │   │   ├── globals.css         # Veritas dark theme + animations
│   │   │   ├── page.tsx            # Landing page
│   │   │   ├── audit/[id]/page.tsx # Live audit view
│   │   │   └── report/[id]/page.tsx# Forensic report view
│   │   ├── components/
│   │   │   ├── ambient/            # ParticleField background
│   │   │   ├── landing/            # Hero, Signals, Carousel, Timeline, Grid
│   │   │   ├── audit/              # AgentPipeline, Narrative, Evidence, Log
│   │   │   ├── report/             # Score, Signals, Patterns, Security
│   │   │   ├── data-display/       # Gauges, badges, charts, counters
│   │   │   └── layout/             # Navbar
│   │   ├── hooks/
│   │   │   └── useAuditStream.ts   # WebSocket hook
│   │   └── lib/
│   │       ├── types.ts            # TypeScript interfaces
│   │       ├── store.ts            # Zustand global state
│   │       └── education.ts        # Educational content data
│   └── package.json                # Next.js + React + deps
│
├── USER_GUIDE.md                   # Local quick-start guide
└── README.md                       # This file
```

---

## Tech Stack

### Backend

| Technology | Purpose |
|-----------|---------|
| **Python 3.12+** | Core engine runtime |
| **LangChain** | LLM orchestration framework |
| **LangGraph** | Multi-agent state machine |
| **NVIDIA NIM** | LLM + Vision Language Model API |
| **Playwright** | Headless browser automation |
| **LanceDB** | Vector database for evidence |
| **sentence-transformers** | Text embeddings |
| **NetworkX** | Entity relationship graphs |
| **FastAPI** | REST + WebSocket API |
| **Uvicorn** | ASGI server |
| **BeautifulSoup4** | HTML parsing |

### Frontend

| Technology | Purpose |
|-----------|---------|
| **Next.js 15** | React meta-framework (App Router, Turbopack) |
| **React 19** | UI library |
| **TypeScript 5** | Type safety |
| **Tailwind CSS 4** | Utility-first styling |
| **shadcn/ui** | Component library (New York style) |
| **Framer Motion** | Animations & transitions |
| **Zustand** | Global state management |
| **Recharts** | Radar & bar charts |
| **Lucide React** | Icon library |

---

## Testing

### Python Engine Tests

```bash
# Activate venv first
python -m pytest veritas/tests/test_veritas.py -v
```

Expected output: **20 passed**.

### Frontend Build Verification

```bash
cd frontend
npm run build
```

Expected output: 3 routes generated (`/`, `/audit/[id]`, `/report/[id]`), 0 errors.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NVIDIA_API_KEY` | **Yes** | — | NVIDIA NIM API key |
| `NVIDIA_NIM_ENDPOINT` | No | `https://integrate.api.nvidia.com/v1` | NIM API base URL |
| `NIM_VISION_MODEL` | No | `nvidia/llama-3.2-nv-vision-90b-instruct` | Primary VLM model |
| `NIM_VISION_FALLBACK` | No | `nvidia/llama-3.2-nv-vision-11b-instruct` | Fallback VLM model |
| `NIM_LLM_MODEL` | No | `nvidia/llama-3.3-nemotron-super-49b-v1` | LLM model for reasoning |
| `TAVILY_API_KEY` | No | — | Web search API key |
| `NIM_TIMEOUT` | No | `30` | API request timeout (seconds) |
| `NIM_RETRY_COUNT` | No | `2` | API retry attempts |
| `NIM_REQUESTS_PER_MINUTE` | No | `10` | Rate limiter |
| `MAX_ITERATIONS` | No | `5` | Max LangGraph iterations |
| `MAX_PAGES_PER_AUDIT` | No | `10` | Max pages to crawl per audit |
| `TEMPORAL_DELAY` | No | `10` | Delay between temporal snapshots (seconds) |
| `CONFIDENCE_THRESHOLD` | No | `0.6` | Minimum confidence for findings |
| `BROWSER_HEADLESS` | No | `true` | Run browser headlessly |

### Audit Tiers

| Tier | Duration | Description |
|------|----------|-------------|
| `quick` | ~60s | Basic checks — DNS, headers, visible patterns |
| `standard` | ~3min | Full pipeline — all 5 agents, screenshots, scoring |
| `deep` | ~5min | Deep forensic — temporal analysis, extended crawl, graph investigation |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: veritas` | Run backend from the `backend/` directory — `main.py` adds parent path automatically |
| `playwright._impl._errors.Error` | Run `playwright install chromium` inside the venv |
| NVIDIA NIM 401/403 | Verify `NVIDIA_API_KEY` in `veritas/.env` |
| NVIDIA NIM 404 | Model name may have changed. Check [NVIDIA NIM Catalog](https://build.nvidia.com/explore/discover) |
| Port already in use | Kill existing process or change port: `uvicorn main:app --port 8001` |
| WebSocket fails to connect | Ensure backend is running before accessing the audit page |
| Frontend blank page | Check browser console. Ensure `npm install` completed without errors |
| Python 3.14 `CancelledError` | Already patched in orchestrator.py — uses `asyncio.exceptions.CancelledError` |
| `UnicodeEncodeError` on Windows | Already patched — engine uses `utf-8` encoding explicitly |
| LanceDB lock errors | Delete `veritas/data/vectordb/` and restart |

---

## How It Works

1. **Scout Agent** — Navigates to the target URL using Playwright, captures screenshots, extracts full DOM, follows links up to `MAX_PAGES_PER_AUDIT`

2. **Security Agent** — Checks HTTP response headers (CSP, HSTS, X-Frame-Options, etc.), analyzes forms for HTTPS/autocomplete, runs phishing heuristics, traces redirect chains

3. **Vision Agent** — Sends screenshots to NVIDIA NIM VLM for visual analysis — detects fake urgency banners, misleading buttons, hidden elements, deceptive layouts

4. **Graph Investigator** — Builds entity relationship graph (domain ↔ registrar ↔ hosting ↔ certificates), identifies inconsistencies, checks domain age and reputation

5. **Judge Agent** — Aggregates all signals with configurable weights, applies site-type-specific scoring adjustments, classifies risk level, generates natural-language verdict and actionable recommendations

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

Please ensure all 20 Python tests pass and `npm run build` succeeds before submitting.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with NVIDIA NIM · LangGraph · Next.js · FastAPI
</p>
