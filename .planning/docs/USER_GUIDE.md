# Veritas — Local User Guide (This PC)

> Quick reference for running Veritas on **this machine** (`C:\jinish\elliotAI`).

---

## Prerequisites (Already Installed)

| Tool | Version | Location |
|------|---------|----------|
| Python | 3.14.2 | `.venv\Scripts\python.exe` |
| Node.js | 24.13.0 | System PATH |
| npm | 11.5.2 | System PATH |
| Playwright | Installed | Inside `.venv` |

---

## Quick Start (2 Terminals)

### Terminal 1 — Backend (FastAPI on port 8000)

```cmd
cd C:\jinish\elliotAI\backend
C:\jinish\elliotAI\.venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✦ Veritas API — Online
```

Verify: open http://localhost:8000/api/health → `{"status":"ok"}`

### Terminal 2 — Frontend (Next.js on port 3000)

```cmd
cd C:\jinish\elliotAI\frontend
npm run dev
```

You should see:
```
▲ Next.js 16.1.6 (Turbopack)
- Local: http://localhost:3000
✓ Ready in ~1s
```

### Open the App

Navigate to **http://localhost:3000** in your browser.

---

## Using the App

### 1. Landing Page (/)

- Enter any website URL in the input field (e.g., `https://example.com`)
- Select an audit tier:
  - **Quick Scan** — ~60 seconds, basic checks
  - **Standard Audit** — ~3 minutes, full analysis
  - **Deep Forensic** — ~5 minutes, everything
- Click **Analyze**

### 2. Live Audit Page (/audit/[id])

The three-column layout shows:
- **Left** — Agent Pipeline: 5 phases (Scout → Security → Vision → Graph → Judge) with live status
- **Center** — Narrative Feed: real-time cards showing what each agent discovers, plus educational content
- **Right** — Evidence Panel: screenshots, findings, and live stats
- **Bottom** — Forensic Log: terminal-style technical feed

When the audit completes, a completion overlay shows the trust score with a link to the full report.

### 3. Report Page (/report/[id])

Full forensic report with:
- Trust Score gauge (animated 0-100)
- Signal Breakdown (radar chart + bar chart)
- Dark Patterns Found (category tabs + detail cards)
- Entity Verification (domain info table)
- Security Audit (header checklist)
- Recommendations (prioritized)
- Audit Metadata

Toggle **Simple / Expert** mode in the top-right for different detail levels.

---

## Stopping the Servers

- **Backend**: Press `Ctrl+C` in Terminal 1
- **Frontend**: Press `Ctrl+C` in Terminal 2

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Port 8000 already in use | Kill the process: `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F` |
| Port 3000 already in use | Kill the process: `netstat -ano \| findstr :3000` then `taskkill /PID <pid> /F` |
| Backend can't find modules | Make sure you're running from `C:\jinish\elliotAI\backend` and using `.venv\Scripts\uvicorn.exe` |
| Frontend 500 error | Check backend is running first. Frontend calls `localhost:8000` |
| NVIDIA NIM errors | Check your API key in `veritas/.env` → `NVIDIA_API_KEY=nvapi-...` |
| WebSocket not connecting | Ensure backend is on port 8000. Frontend expects `ws://localhost:8000` by default |

---

## File Locations

```
C:\jinish\elliotAI\
├── .venv\                  ← Python virtual environment (DO NOT DELETE)
├── veritas\                ← Core Python engine (20/20 tests passing)
│   ├── .env                ← API keys and config
│   ├── agents\             ← Scout, Vision, Graph, Judge
│   ├── analysis\           ← DOM, forms, patterns, security
│   ├── core\               ← Orchestrator, NIM client, evidence store
│   └── tests\              ← Test suite
├── backend\                ← FastAPI API layer
│   ├── main.py             ← App entry point
│   ├── routes\audit.py     ← REST + WebSocket endpoints
│   └── services\           ← Audit runner (subprocess wrapper)
└── frontend\               ← Next.js UI
    ├── src\app\            ← Pages (/, /audit/[id], /report/[id])
    ├── src\components\     ← 30+ React components
    ├── src\hooks\           ← useAuditStream WebSocket hook
    └── src\lib\            ← Types, Zustand store, education data
```

---

## Running Tests (Python Engine)

```cmd
cd C:\jinish\elliotAI
.venv\Scripts\python.exe -m pytest veritas\tests\test_veritas.py -v
```

Expected: **20/20 tests passing**.

---

## Production Build (Frontend)

```cmd
cd C:\jinish\elliotAI\frontend
npm run build
npm start
```

This creates an optimized production build and serves it on port 3000.
