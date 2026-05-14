<p align="center">
  <img src="frontend/public/file.svg" width="80" alt="Elliot Logo" />
</p>

<h1 align="center">ELLIOT</h1>
<p align="center">
  <strong>Autonomous Multi-Modal Forensic Web Auditor</strong>
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#api-reference">API</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#testing">Testing</a>
</p>

---

Elliot is an AI-powered forensic web auditing platform that analyzes websites for trust, safety, dark patterns, and security vulnerabilities. It combines **5 specialized AI agents** with **visual analysis**, **graph investigation**, **OSINT/darknet intelligence**, and **multi-signal scoring** to produce comprehensive, real-time forensic reports.

---

## Features

- **5-Phase Autonomous Pipeline** — Scout → Security → Vision → Graph Investigation → Judge
- **4 Audit Tiers** — `quick_scan`, `standard_audit`, `deep_forensic`, `darknet_investigation`
- **Dual Verdict System** — Parallel Forensic Analysis (technical) + Executive Summary (non-technical), both rendered live with typewriter effects
- **NVIDIA NIM Integration** — LLM reasoning + Vision Language Models for screenshot analysis
- **22+ Analysis Modules** — DOM, form validation, dark pattern detection, phishing heuristics, redirect tracing, temporal analysis, security headers, JS behavior analysis, JS obfuscation detection, meta tag analysis
- **OSINT Intelligence Engine** — IOC detection, Cyber Threat Intelligence (CTI), reputation checking, attack pattern recognition, MITRE ATT&CK technique mapping, CVSS scoring
- **Darknet Integration** — Onion domain detector, Tor threat scraper, marketplace threat data
- **Quality Consensus Engine** — Multi-agent confidence scoring and validation consensus layer
- **Database Persistence** — SQLAlchemy async ORM (SQLite by default) with full audit history, findings, and screenshots stored
- **Real-Time WebSocket Streaming** — Live events with sequence-ordered delivery and at-least-once delivery guarantee
- **Audit History & Compare** — Browse past audits, compare trust scores / risk deltas between runs
- **Chromatic UI Theming** — Active agent context drives ambient UI color changes (ChromaticProvider)
- **16 Specialized Terminal Panels** — CVSS Radar, MITRE ATT&CK Grid, Knowledge Graph, Threat Matrix, Scout Imagery, Vision Intelligence, Scout Telemetry, Corporate Entities, Verdict Matrix, and more
- **Next.js 15 Frontend** — 5-route app with animated terminal-style live audit view, history browser, multi-audit comparison
- **LanceDB Vector Store** — Evidence persistence and similarity search
- **Playwright Browser Automation** — Headless screenshot capture, DOM extraction, interaction testing, CAPTCHA detection, form discovery

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Next.js 15 Frontend                       │
│  Landing  ──▶  Live Audit (WS)  ──▶  Final Report            │
│  History  ──▶  Compare (multi-audit diff)                     │
│  Port 3000                                                    │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTP REST + WebSocket
┌─────────────────────▼────────────────────────────────────────┐
│                    FastAPI Backend                             │
│  POST /api/audit/start          WS /api/audit/stream/{id}    │
│  GET  /api/audit/{id}/status    GET /api/audits/history       │
│  POST /api/audits/compare       GET /api/health               │
│  Port 8000                                                    │
│                   SQLAlchemy + SQLite DB                      │
└─────────────────────┬────────────────────────────────────────┘
                      │ Subprocess + IPC (Queue or Stdout)
┌─────────────────────▼────────────────────────────────────────┐
│                  Elliot Python Engine                         │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌───────────────┐  │
│  │  Scout   │→ │ Security │→ │ Vision │→ │ Graph Invest. │  │
│  │  Agent   │  │  Agent   │  │ Agent  │  │    Agent      │  │
│  └──────────┘  └──────────┘  └────────┘  └──────┬────────┘  │
│                                                   │           │
│  ┌────────────────────────────────────────────────▼────────┐  │
│  │                     Judge Agent                          │  │
│  │   Weighted Scoring · Risk Classification · Dual Verdict  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │
│  OSINT Engine · Darknet Module · Quality Consensus Engine    │
│  NVIDIA NIM (LLM + VLM) · Playwright · LanceDB              │
└───────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
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
git clone https://github.com/your-org/elliot.git
cd elliot
```

### 2. Set Up Python Environment

```bash
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install Python engine dependencies
pip install -r elliot/requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure Environment Variables

Create the file `elliot/.env`:

```env
# ── NVIDIA NIM ──────────────────────────────
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_NIM_ENDPOINT=https://integrate.api.nvidia.com/v1
NIM_VISION_MODEL=nvidia/llama-3.2-nv-vision-90b-instruct
NIM_VISION_FALLBACK=nvidia/llama-3.2-nv-vision-11b-instruct
NIM_LLM_MODEL=nvidia/llama-3.3-nemotron-super-49b-v1

# ── Database Persistence ────────────────────
USE_DB_PERSISTENCE=true             # Set false to disable DB writes
DATABASE_URL=sqlite+aiosqlite:///./elliot_dev.db

# ── API Keys (optional) ────────────────────
TAVILY_API_KEY=                     # Web search (leave empty to disable)

# ── IPC Mode ────────────────────────────────
USE_QUEUE_IPC=false                 # true = multiprocessing.Queue, false = stdout

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

**Option A — One-click (Windows):**
```cmd
start.bat
```

**Option B — Two terminals:**

```bash
# Terminal 1 — Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## Application Routes

| Route | Description |
|---|---|
| `/` | Landing page — URL input, tier selection, recent audits |
| `/audit/[id]` | Live audit terminal — 16-panel real-time forensic view |
| `/report/[id]` | Full forensic report — score, signals, patterns, security |
| `/history` | Audit history browser with filtering and pagination |
| `/compare` | Multi-audit comparison with trust score deltas |

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

### Docker

```yaml
# docker-compose.yml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file: elliot/.env

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
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
|---|---|---|
| `GET` | `/api/health` | Service health check |
| `POST` | `/api/audit/start` | Start a new audit |
| `GET` | `/api/audit/{id}/status` | Get audit status + result |
| `GET` | `/api/audit/{id}/screenshot/{sid}` | Serve a saved screenshot file |
| `GET` | `/api/audits/history` | Paginated audit history (DB) |
| `POST` | `/api/audits/compare` | Compare 2+ audits, compute trust deltas |

#### POST /api/audit/start

**Request:**
```json
{
  "url": "https://example.com",
  "tier": "standard_audit",
  "verdict_mode": "expert",
  "security_modules": ["security_headers", "phishing_db"]
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

#### POST /api/audits/compare

**Request:**
```json
{ "audit_ids": ["vrts_aaa", "vrts_bbb"] }
```

**Response:** Returns full audit data for each ID plus computed `trust_score_deltas` and `risk_level_changes` arrays.

#### GET /api/audits/history

**Query params:** `limit` (1–100), `offset`, `status_filter`, `risk_level_filter`

### WebSocket Events

Connect to `ws://localhost:8000/api/audit/stream/{audit_id}`.

| Event Type | Key Payload Fields | Description |
|---|---|---|
| `phase_start` | `phase`, `message`, `pct` | Agent phase begins |
| `phase_complete` | `phase`, `summary`, `pct` | Agent phase finishes |
| `phase_error` | `phase`, `error` | Agent phase failed |
| `finding` | `finding` (object) | Dark pattern or security issue found |
| `screenshot` | `url`, `image` (base64), `index`, `label` | Screenshot captured |
| `stats_update` | `stats` (object) | Live stats refresh |
| `log_entry` | `agent`, `message`, `level` | Technical log line |
| `site_type` | `site_type`, `confidence` | Site category classified |
| `security_result` | `module`, `result` | Security module output |
| `dark_pattern_finding` | fields | Visual dark pattern from VLM |
| `temporal_finding` | fields | Time-based content change detected |
| `osint_result` | fields | OSINT query result |
| `darknet_threat` | fields | Marketplace threat data |
| `ioc_indicator` | fields | IOC indicator found |
| `ioc_detection_complete` | fields | IOC scan complete |
| `cvss_metrics` | `metrics[]` | CVSS metric values |
| `mitre_technique_mapped` | `technique` | MITRE ATT&CK technique matched |
| `threat_attribution` | fields | APT group attribution |
| `exploitation_advisory` | fields | Exploitation advisory |
| `knowledge_graph` | `graph` | Entity relationship graph data |
| `graph_analysis` | fields | Graph anomaly analysis |
| `site_classification` | fields | Detailed site classification |
| `exploration_path` | `path` | Scout URL traversal path |
| `captcha_detected` | fields | CAPTCHA detection result |
| `form_detected` | fields | Form discovered during crawl |
| `dom_health` | fields | DOM structure health report |
| `corporate_entities` | `entities[]` | Business entity claims |
| `green_flags` | `flags[]` | Positive trust signals |
| `dual_verdict` | `technical`, `non_technical`, `trust_score` | Final dual verdict |
| `audit_result` | `result` (full object) | Complete audit data |
| `audit_complete` | `audit_id` | Audit finished |
| `audit_error` | `error` | Fatal audit error |
| `agent_personality` | `agent`, `context`, `params` | Agent behavioral event |

---

## Project Structure

```
elliotAI/
├── elliot/                        # Python auditing engine
│   ├── __main__.py                 # CLI entry point (argparse)
│   ├── __init__.py
│   ├── .env                        # API keys + config
│   ├── requirements.txt
│   ├── agents/                     # AI agent modules
│   │   ├── scout.py                # Phase 1: Crawling, DOM, screenshots
│   │   ├── security_agent.py       # Phase 2: Headers, forms, phishing
│   │   ├── vision.py               # Phase 3: VLM screenshot analysis
│   │   ├── graph_investigator.py   # Phase 4: Entity graph + link analysis
│   │   └── judge.py                # Phase 5: Scoring + dual verdict
│   ├── analysis/                   # Deterministic analysis modules
│   │   ├── dom_analyzer.py
│   │   ├── form_validator.py
│   │   ├── js_analyzer.py
│   │   ├── meta_analyzer.py
│   │   ├── pattern_matcher.py      # Dark pattern detection
│   │   ├── phishing_checker.py
│   │   ├── redirect_analyzer.py
│   │   ├── security_headers.py
│   │   ├── temporal_analyzer.py
│   │   ├── exploitation_advisor.py
│   │   ├── scenario_generator.py
│   │   └── security/               # Extended security sub-modules
│   ├── core/                       # Core infrastructure
│   │   ├── orchestrator.py         # LangGraph pipeline orchestrator
│   │   ├── nim_client.py           # NVIDIA NIM API client
│   │   ├── evidence_store.py       # LanceDB vector evidence
│   │   ├── evidence.py
│   │   ├── evidence_evidence.py
│   │   ├── osint_enrichment.py     # OSINT enrichment pipeline
│   │   ├── web_searcher.py         # Tavily web search
│   │   ├── tor_client.py           # Tor network client
│   │   ├── ipc.py                  # IPC mode selection (Queue vs Stdout)
│   │   ├── circuit_breaker.py      # Resilience / rate-limit breaker
│   │   ├── complexity_analyzer.py
│   │   ├── degradation.py          # Graceful degradation logic
│   │   ├── timeout_manager.py
│   │   └── types.py                # Core type definitions
│   ├── osint/                      # OSINT intelligence engine
│   │   ├── orchestrator.py         # OSINT pipeline orchestrator
│   │   ├── ioc_detector.py         # IOC indicator detection
│   │   ├── cti.py                  # Cyber threat intelligence
│   │   ├── reputation.py           # Domain reputation checks
│   │   ├── attack_patterns.py      # Attack pattern recognition
│   │   ├── vulnerability_mapper.py # CVE / vulnerability mapping
│   │   ├── cache.py                # OSINT result caching
│   │   └── types.py
│   ├── darknet/                    # Darknet / Tor analysis
│   │   ├── onion_detector.py       # Onion link detection
│   │   ├── threat_scraper.py       # Marketplace threat data
│   │   └── tor_client.py
│   ├── quality/                    # Quality control layer
│   │   ├── confidence_scorer.py    # Per-finding confidence scoring
│   │   ├── consensus_engine.py     # Multi-signal consensus
│   │   └── validation_state.py
│   ├── db/                         # Database persistence
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   ├── repositories.py         # Data access layer
│   │   └── config.py
│   ├── config/                     # Configuration
│   │   ├── settings.py
│   │   ├── trust_weights.py
│   │   ├── dark_patterns.py
│   │   └── site_types.py
│   ├── reporting/                  # Report generation
│   │   └── report_generator.py     # PDF / HTML / Markdown reports
│   ├── reporters/
│   ├── cwe/                        # CWE data
│   ├── ui/                         # Optional Streamlit UI
│   └── tests/
│
├── backend/                        # FastAPI API layer
│   ├── main.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── audit.py                # All audit REST + WS endpoints
│   │   └── health.py
│   └── services/
│       └── audit_runner.py         # Subprocess wrapper for engine
│
├── frontend/                       # Next.js 15 UI
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── globals.css         # Cybercore dark theme + animations
│       │   ├── page.tsx            # Landing page
│       │   ├── audit/[id]/page.tsx # Live audit terminal (16 panels)
│       │   ├── report/[id]/page.tsx# Full forensic report
│       │   ├── history/page.tsx    # Audit history browser
│       │   └── compare/page.tsx    # Multi-audit comparison
│       ├── components/
│       │   ├── terminal/           # 16 live terminal panel components
│       │   │   ├── AgentProcState.tsx
│       │   │   ├── CorporateEntitiesPanel.tsx
│       │   │   ├── CvssRadar.tsx
│       │   │   ├── DarknetOsintGrid.tsx
│       │   │   ├── FinalAuditReport.tsx
│       │   │   ├── KnowledgeGraph.tsx
│       │   │   ├── MitreGrid.tsx
│       │   │   ├── NodeDetailPanel.tsx
│       │   │   ├── ScoutImagery.tsx
│       │   │   ├── ScoutTelemetry.tsx
│       │   │   ├── SysLogStream.tsx
│       │   │   ├── TerminalPanel.tsx
│       │   │   ├── ThreatIntelligenceMatrix.tsx
│       │   │   ├── VerdictPanel.tsx
│       │   │   └── VisionIntelligence.tsx
│       │   ├── landing/            # CommandInput, RecentAudits, CapabilitiesGrid
│       │   ├── providers/          # ChromaticProvider (agent-driven theming)
│       │   ├── ambient/            # ParticleField background
│       │   ├── audit/
│       │   ├── report/
│       │   ├── data-display/
│       │   ├── layout/             # Navbar
│       │   └── ui/                 # shadcn/ui primitives
│       ├── hooks/
│       │   └── useAuditStream.ts   # WebSocket hook with reconnect logic
│       ├── config/
│       │   └── agents.ts           # AGENT_ORDER, AgentId type
│       └── lib/
│           ├── types.ts            # 60+ TypeScript interfaces
│           ├── store.ts            # Zustand store (~1300 lines, 40+ state fields)
│           └── education.ts
│
├── start.bat                       # One-click Windows launcher
├── stop.bat                        # Kill all servers
├── install_dependencies.bat        # Windows dependency installer
├── install_dependencies.sh         # Unix dependency installer
├── kill_port.py                    # Port cleanup utility
├── Dockerfile
├── pytest.ini
├── README.md
└── USER_GUIDE.md
```

---

## Tech Stack

### Backend / Engine

| Technology | Purpose |
|---|---|
| **Python 3.12+** | Core engine runtime |
| **LangChain + LangGraph** | Multi-agent state machine orchestration |
| **NVIDIA NIM** | LLM reasoning + VLM screenshot analysis |
| **Playwright** | Headless Chromium automation |
| **LanceDB** | Vector database for evidence storage |
| **sentence-transformers** | Text embeddings |
| **NetworkX** | Entity relationship graphs |
| **FastAPI** | REST + WebSocket API |
| **SQLAlchemy (async)** | ORM — audit DB persistence |
| **aiosqlite** | Async SQLite adapter |
| **BeautifulSoup4** | HTML/DOM parsing |
| **Uvicorn** | ASGI server |

### Frontend

| Technology | Purpose |
|---|---|
| **Next.js 15** | App Router, Turbopack, SSR |
| **React 19** | UI library |
| **TypeScript 5** | Type safety (60+ interfaces) |
| **Tailwind CSS 4** | Utility-first styling |
| **shadcn/ui** | Component library (New York style) |
| **Framer Motion** | Animations & transitions |
| **Zustand** | Global state (40+ fields, 1300 lines) |
| **Recharts** | Radar & bar charts |
| **Lucide React** | Icon library |

---

## Audit Tiers

| Tier | Key | Approx. Duration | Description |
|---|---|---|---|
| Quick Scan | `quick_scan` | ~60 s | DNS, headers, visible patterns |
| Standard Audit | `standard_audit` | ~3 min | Full 5-agent pipeline + screenshots |
| Deep Forensic | `deep_forensic` | ~5 min | Temporal analysis, extended crawl, graph |
| Darknet Investigation | `darknet_investigation` | ~8 min | All above + Tor/darknet threat intelligence |

## Verdict Modes

| Mode | Description |
|---|---|
| `expert` | Full forensic narrative with CVSS, MITRE ATT&CK, IOCs, technical details |
| `simple` | Plain-English consumer-friendly summary and actionable advice |

---

## Testing

### Python Engine Tests

```bash
python -m pytest elliot/tests/test_elliot.py -v
```

Expected: **20 passed**.

### Frontend Build Verification

```bash
cd frontend
npm run build
```

Expected: 5 routes generated, 0 errors.

---

## Configuration Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `NVIDIA_API_KEY` | **Yes** | — | NVIDIA NIM API key |
| `NVIDIA_NIM_ENDPOINT` | No | `https://integrate.api.nvidia.com/v1` | NIM base URL |
| `NIM_VISION_MODEL` | No | `nvidia/llama-3.2-nv-vision-90b-instruct` | Primary VLM |
| `NIM_VISION_FALLBACK` | No | `nvidia/llama-3.2-nv-vision-11b-instruct` | Fallback VLM |
| `NIM_LLM_MODEL` | No | `nvidia/llama-3.3-nemotron-super-49b-v1` | LLM for reasoning |
| `USE_DB_PERSISTENCE` | No | `true` | Enable SQLite audit history |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./elliot_dev.db` | DB connection string |
| `USE_QUEUE_IPC` | No | `false` | Use multiprocessing.Queue for IPC |
| `TAVILY_API_KEY` | No | — | Web search (optional) |
| `NIM_TIMEOUT` | No | `30` | API timeout (seconds) |
| `NIM_RETRY_COUNT` | No | `2` | API retry count |
| `NIM_REQUESTS_PER_MINUTE` | No | `10` | Rate limit |
| `MAX_PAGES_PER_AUDIT` | No | `10` | Max pages to crawl |
| `CONFIDENCE_THRESHOLD` | No | `0.6` | Min confidence for findings |
| `BROWSER_HEADLESS` | No | `true` | Run browser headlessly |

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: elliot` | Run backend from `backend/` dir — `main.py` adds parent path automatically |
| `playwright._impl._errors.Error` | Run `playwright install chromium` inside the venv |
| NVIDIA NIM 401/403 | Verify `NVIDIA_API_KEY` in `elliot/.env` |
| NVIDIA NIM 404 | Check [NVIDIA NIM Catalog](https://build.nvidia.com/explore/discover) for current model names |
| Port already in use | Run `kill_port.py` or `taskkill /F /PID <pid>` |
| WebSocket fails | Ensure backend is running before opening the audit page |
| Frontend blank page | Run `npm install` in `frontend/`, check browser console |
| `UnicodeEncodeError` on Windows | Already patched — engine uses `utf-8` encoding explicitly |
| LanceDB lock errors | Delete `elliot/data/vectordb/` and restart |
| DB errors on startup | SQLite DB auto-created at `elliot_dev.db`. Delete and restart to reset. |
| Audit history empty | Ensure `USE_DB_PERSISTENCE=true` in `elliot/.env` |

---

## How It Works — Deep Dive

1. **Scout Agent** — Playwright navigates to the target URL using a full headless Chromium browser. It waits for network idle, captures full-page screenshots, extracts the rendered DOM, detects forms and CAPTCHAs, and crawls linked pages up to `MAX_PAGES_PER_AUDIT`.

2. **Security Agent** — Runs 6 deterministic analysis modules: HTTP security headers (CSP, HSTS, X-Frame-Options, etc.), form security (HTTPS submission, autocomplete), phishing heuristics, JS behavior analysis, redirect chain tracing, and meta tag analysis.

3. **Vision Agent** — Sends screenshots to NVIDIA NIM VLMs. Detects deceptive visual patterns invisible in raw HTML: fake countdowns, camouflaged decline buttons, urgency banners, misleading layouts, and hidden subscription disclosures.

4. **Graph Investigator** — Builds a NetworkX entity graph: domain ↔ registrar ↔ ASN ↔ hosting ↔ SSL issuer. Cross-references OSINT: IOC indicators, domain reputation, APT group attributions, CVSS scores, MITRE ATT&CK technique matches, and darknet threat mentions.

5. **Quality Consensus Engine** — A confidence scorer and consensus engine run across all findings before the Judge, filtering low-confidence signals and resolving contradictions between agents.

6. **Judge Agent** — Aggregates all evidence with configurable signal weights. Applies site-type-specific scoring adjustments. Produces both a **technical forensic verdict** (with technical IOCs, CVSS vector, CWE entries, remediation steps) and a **non-technical executive summary** (plain English, consumer-facing advice).

---

## CLI Usage

The engine can be run directly from the command line without the frontend:

```bash
# Standard audit
python -m elliot https://suspicious-site.com

# Deep forensic with PDF report
python -m elliot https://store.example.com --tier deep_forensic --report pdf

# Quick scan with JSON output
python -m elliot https://example.com --tier quick_scan --json

# Expert vs simple verdict
python -m elliot https://example.com --verdict-mode simple

# Custom security modules
python -m elliot https://example.com --security-modules security_headers,phishing_db,js_analysis
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "feat: my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

Ensure all 20 Python tests pass and `npm run build` succeeds before submitting.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with NVIDIA NIM · LangGraph · Next.js 15 · FastAPI · SQLAlchemy
</p>
