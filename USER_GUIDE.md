# Elliot — Local User Guide

> Quick reference for running Elliot on this machine (`C:\files\coding dev era\elliot\elliotAI`).

---

## Environment (Already Installed)

| Tool | Version | Location |
|---|---|---|
| Python | 3.14.2 | `.venv\Scripts\python.exe` |
| Node.js | 24+ | System PATH |
| npm | 11+ | System PATH |
| Playwright Chromium | Installed | Inside `.venv` |

---

## Quick Start (2 Terminals)

### Option A — One-Click (Recommended)

```cmd
cd C:\files\coding dev era\elliot\elliotAI
start.bat
```

This opens two terminal windows — one for the backend, one for the frontend.

---

### Option B — Manual (2 Terminals)

**Terminal 1 — Backend (FastAPI on port 8000):**

```cmd
cd C:\files\coding dev era\elliot\elliotAI\backend
C:\files\coding dev era\elliot\elliotAI\.venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
```

Expected output:
```
✦ Elliot API — Online
INFO: Uvicorn running on http://0.0.0.0:8000
```

Health check: http://localhost:8000/api/health → `{"status":"ok"}`

**Terminal 2 — Frontend (Next.js on port 3000):**

```cmd
cd C:\files\coding dev era\elliot\elliotAI\frontend
npm run dev
```

Expected output:
```
▲ Next.js 15 (Turbopack)
- Local: http://localhost:3000
✓ Ready in ~1s
```

### Open the App

Navigate to **http://localhost:3000**

---

## The 5 App Pages

### 1. Landing Page — `/`

- Enter any website URL (e.g., `https://example.com`)
- Select an audit tier:
  - **Quick Scan** (`quick_scan`) — ~60 sec, headers + visible patterns
  - **Standard Audit** (`standard_audit`) — ~3 min, full 5-agent pipeline
  - **Deep Forensic** (`deep_forensic`) — ~5 min, temporal + extended crawl
  - **Darknet Investigation** (`darknet_investigation`) — ~8 min, darknet + Tor intelligence
- Select **Verdict Mode**:
  - **Expert** — full forensic detail (IOCs, CVSS, MITRE ATT&CK)
  - **Simple** — plain-English consumer summary
- Click **Analyze**
- **Recent Audits** panel on the right shows your last 10 audits (stored in localStorage)

---

### 2. Live Audit Terminal — `/audit/[id]`

> ⚠️ Requires **minimum 1280px viewport width** (desktop only by design).

The live audit view is a full-screen terminal divided into **3 columns**:

**Left Column — Investigative Matrices:**
- `CVSS.RADAR` — Radar chart of CVSSv3 metric scores (Attack Vector, Complexity, Privileges, etc.)
- `MITRE.ATTACK.GRID` — Mapped ATT&CK techniques (e.g., T1566 - Phishing)
- `THREAT.MATRIX` — OSINT results, marketplace threats, darknet mentions
- `CORP.INTEGRITY.VERIFICATION` — Business entity claims (shows when CVSS data absent)
- `AGENT.PROC.STATE` — Live status of all 5 agent processes (STANDBY → ACTIVE → DONE)

**Center Column — Active Intel:**
- `LIVE.TELEMETRY.STREAM` — During audit: counters for Findings, Pages Mapped, Neural Casts, Sec Checks
- `VERDICT.MATRIX` — After audit: Trust Score (0–100) + Forensic Analysis + Executive Summary side-by-side (both typewriter-animated)
- `GREEN.FLAGS` — Positive trust signals streamed live (e.g., ✓ HTTPS enforced)
- `SCOUT.TELEMETRY` — URLs visited, forms detected, CAPTCHAs found, DOM health
- `SYS.LOG.STREAM` — Raw agent terminal logs with timestamps and severity levels

**Right Column — Evidence:**
- `SCOUT.IMAGERY` — Live screenshots as they are captured by Playwright
- `VISION.INTELLIGENCE` — Dark pattern findings from VLM analysis + temporal change detections
- `KNOWLEDGE.GRAPH` — Interactive entity relationship graph (domain → registrar → hosting → SSL)

**Header Bar:**
- `ELLIOT TERM /// 9.4.0`, target URL, elapsed time counter, live connection indicator

**After Audit Completes:**
- **VIEW COMPREHENSIVE REPORT** button appears (pulsing cyan) — opens the inline `FinalAuditReport` overlay

---

### 3. Final Audit Report — Inside `/audit/[id]` (overlay)

Click **VIEW COMPREHENSIVE REPORT** when the audit finishes to open the full inline report:

- Trust Score ring + risk classification
- Full findings list with severity, category, descriptions
- Forensic narrative (technical) + Executive Summary (non-technical)
- Recommendations list

---

### 4. Audit History — `/history`

Browse all past audits stored in the database:
- Filter by status (`running`, `completed`, `error`) or risk level
- Pagination support (20 per page by default)
- Click any audit to jump to its report

> Requires `USE_DB_PERSISTENCE=true` in `elliot/.env`

---

### 5. Multi-Audit Comparison — `/compare`

Compare two or more audits side-by-side:
- Paste audit IDs to compare
- View trust score deltas (increase/decrease between runs)
- See risk level changes (was: `LOW_RISK` → now: `CRITICAL`)
- Track finding count changes by severity

---

## Stopping the Servers

- **Quick stop:** Run `stop.bat` in the root folder
- **Manual:** Press `Ctrl+C` in Terminal 1 and Terminal 2

---

## Common Issues

| Problem | Solution |
|---|---|
| Port 8000 in use | `netstat -ano \| findstr :8000` → `taskkill /PID <pid> /F` or run `kill_port.py` |
| Port 3000 in use | `netstat -ano \| findstr :3000` → `taskkill /PID <pid> /F` |
| Backend module not found | Run from `backend\` dir; use `.venv\Scripts\uvicorn.exe` |
| Frontend 500 error | Start backend first; frontend calls `localhost:8000` |
| NVIDIA NIM 401 | Check `NVIDIA_API_KEY` in `elliot\.env` |
| WebSocket not connecting | Backend must be on port 8000 before opening audit page |
| Audit history empty | Set `USE_DB_PERSISTENCE=true` in `elliot\.env` |
| DB lock errors | Delete `elliot_dev.db` to reset, or restart both servers |
| LanceDB errors | Delete `elliot\data\vectordb\` and restart backend |
| Mobile/small screen blank | Live audit requires min 1280px (`xl:` breakpoint) |

---

## File Locations

```
C:\files\coding dev era\elliot\elliotAI\
├── .venv\                  ← Python virtual environment (DO NOT DELETE)
├── elliot\                ← Core Python engine
│   ├── .env                ← API keys and config (EDIT THIS)
│   ├── agents\             ← Scout, Security, Vision, Graph, Judge
│   ├── analysis\           ← DOM, forms, patterns, security, JS, temporal
│   ├── osint\              ← IOC detection, CTI, reputation, attack patterns
│   ├── darknet\            ← Onion detector, threat scraper
│   ├── quality\            ← Confidence scorer, consensus engine
│   ├── core\               ← Orchestrator, NIM client, evidence store, IPC
│   ├── db\                 ← SQLAlchemy models + repositories
│   ├── reporting\          ← PDF / HTML / Markdown report generation
│   └── tests\              ← Python test suite (20 tests)
├── backend\                ← FastAPI API layer
│   ├── main.py             ← App entry point
│   ├── routes\audit.py     ← All REST + WebSocket endpoints
│   └── services\           ← Audit runner (subprocess wrapper)
├── frontend\               ← Next.js 15 UI
│   └── src\
│       ├── app\            ← 5 pages: /, /audit/[id], /report/[id], /history, /compare
│       ├── components\     ← 16 terminal panels + landing + report components
│       ├── hooks\          ← useAuditStream WebSocket hook
│       ├── config\         ← Agent order config
│       └── lib\            ← Types (60+ interfaces), Zustand store, education data
├── start.bat               ← One-click launcher (Windows)
├── stop.bat                ← Kill all servers
├── install_dependencies.bat← Windows dependency installer
└── elliot_dev.db          ← SQLite audit database (auto-created)
```

---

## Running Tests

```cmd
cd C:\files\coding dev era\elliot\elliotAI
.venv\Scripts\python.exe -m pytest elliot\tests\test_elliot.py -v
```

Expected: **20/20 tests passing**.

---

## CLI — Run Engine Without Frontend

```cmd
.venv\Scripts\python.exe -m elliot https://example.com --tier standard_audit
.venv\Scripts\python.exe -m elliot https://example.com --tier deep_forensic --report pdf
.venv\Scripts\python.exe -m elliot https://example.com --json --output result.json
```

---

## Production Build (Frontend)

```cmd
cd C:\files\coding dev era\elliot\elliotAI\frontend
npm run build
npm start
```

Builds optimized production bundle and serves on port 3000.
