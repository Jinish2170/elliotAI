# ELLIOT — Autonomous Multi-Modal Forensic Web Auditor
## Production-Grade Technical Report

**Project Name:** Elliot  
**Classification:** Academic / Research Prototype — Production Architecture  
**Report Date:** April 2026  
**Author:** Jinish Kathiriya  
**Stack:** Python 3.14 · FastAPI · LangGraph · NVIDIA NIM · Next.js 15 · React 19 · SQLAlchemy · LanceDB · Playwright

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Motivation](#2-problem-statement--motivation)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Backend — FastAPI API Layer](#4-backend--fastapi-api-layer)
5. [The Elliot Python Engine](#5-the-elliot-python-engine)
6. [Multi-Agent Pipeline — Phase by Phase](#6-multi-agent-pipeline--phase-by-phase)
7. [OSINT Intelligence Engine](#7-osint-intelligence-engine)
8. [Darknet & Tor Integration](#8-darknet--tor-integration)
9. [Quality Consensus Engine](#9-quality-consensus-engine)
10. [Database Persistence Layer](#10-database-persistence-layer)
11. [Frontend — The Forensic Terminal Interface](#11-frontend--the-forensic-terminal-interface)
12. [Real-Time Event System](#12-real-time-event-system)
13. [Security & Ethical Design](#13-security--ethical-design)
14. [Performance & Scalability Considerations](#14-performance--scalability-considerations)
15. [Testing Strategy](#15-testing-strategy)
16. [CLI Interface](#16-cli-interface)
17. [Key Technical Innovations](#17-key-technical-innovations)
18. [Limitations & Future Work](#18-limitations--future-work)
19. [Conclusion](#19-conclusion)
20. [Appendix A — Full WebSocket Event Catalogue](#20-appendix-a--full-websocket-event-catalogue)
21. [Appendix B — Configuration Reference](#21-appendix-b--configuration-reference)

---

## 1. Executive Summary

Elliot is an autonomous, multi-modal forensic web auditing platform designed to systematically evaluate any publicly accessible website across six dimensions: **trust**, **safety**, **dark patterns**, **security posture**, **entity integrity**, and **threat intelligence**. Unlike traditional web scanners that rely solely on deterministic rule matching, Elliot combines classical static analysis with:

- **Large Language Model (LLM) reasoning** via NVIDIA NIM for contextual interpretation
- **Vision Language Model (VLM) analysis** of live browser screenshots for deceptive layout detection
- **Multi-agent state machine orchestration** using LangGraph
- **OSINT intelligence enrichment** including IOC detection and MITRE ATT&CK mapping
- **Darknet threat research** via Tor network integration
- **Real-time forensic streaming** through WebSocket with a terminal-style interface

The result is a platform that produces explainable, multi-perspective trust verdicts rendered simultaneously as both a technical forensic report and a plain-English consumer advisory — streamed live to an immersive operator terminal in the browser.

---

## 2. Problem Statement & Motivation

### 2.1 The Trust Gap

As of 2025, over 1.5 million new phishing sites are created every month (Anti-Phishing Working Group). Existing consumer-facing tools (VirusTotal, Google Safe Browsing) operate on reputation blacklists — they can only flag **known** malicious sites, missing the long tail of freshly registered, sophisticated scam operations that employ legitimate hosting, valid SSL certificates, and persuasive UI design.

### 2.2 Dark Pattern Blindness

Academic research (Gray et al., 2018; Mathur et al., 2019) has identified over 200 distinct dark pattern subtypes across e-commerce platforms. Existing automated tools cannot reliably detect visually subtle patterns (e.g., pre-ticked subscriptions styled to appear as ordinary confirmation checkboxes) because they rely on structural DOM parsing rather than visual reasoning.

### 2.3 The Expert Access Problem

Existing forensic security tools (Burp Suite, OWASP ZAP, Maltego) require significant technical expertise to operate and interpret. There is a need for a tool that can produce both **machine-readable forensic data** for security professionals and **accessible plain-English summaries** for non-technical consumers simultaneously — without degrading the quality of either output.

### 2.4 Elliot's Approach

Elliot addresses all three gaps:
1. **Behavioral analysis** (not just blacklist matching) via LLM + playwright interaction
2. **Visual dark pattern detection** via VLM screenshot analysis
3. **Dual-mode output** — forensic + consumer verdicts generated in parallel by the Judge Agent

---

## 3. System Architecture Overview

### 3.1 Three-Layer Decoupled Architecture

```
┌─────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER: Next.js 15 (Port 3000)             │
│  5 routes · 16 terminal panels · WebSocket client       │
│  Zustand state (40+ fields) · ChromaticProvider theming │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP REST + WebSocket
┌────────────────────▼────────────────────────────────────┐
│  API LAYER: FastAPI (Port 8000)                         │
│  REST endpoints · WebSocket streaming                   │
│  SQLAlchemy async DB · Screenshot filesystem storage    │
└────────────────────┬────────────────────────────────────┘
                     │ Subprocess (IPC: Queue or Stdout)
┌────────────────────▼────────────────────────────────────┐
│  ENGINE LAYER: Elliot Python Engine                    │
│  LangGraph orchestrator · 5 AI agents                   │
│  OSINT · Darknet · Quality Consensus · LanceDB vector   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

1. User submits URL + tier via the landing page
2. Frontend POSTs to `/api/audit/start` → receives `audit_id` + `ws_url`
3. Frontend opens WebSocket to `ws://localhost:8000/api/audit/stream/{audit_id}`
4. Backend accepts WS connection → spawns `AuditRunner` subprocess
5. `AuditRunner` executes `ElliotOrchestrator` via the Python engine
6. Engine emits ~40 distinct event types as JSON to stdout (or Queue)
7. Backend reads events, writes to DB, forwards each to the WebSocket client
8. Frontend's `useAuditStream` hook receives events → dispatches to Zustand store
9. Zustand store processes events in sequence order → updates 40+ state fields
10. React components re-render reactively from Zustand subscriptions → panels update live
11. On completion, DB is updated; user can view history and compare

---

## 4. Backend — FastAPI API Layer

### 4.1 API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/audit/start` | Create audit record, return WS URL |
| `WS` | `/api/audit/stream/{id}` | Start + stream audit in real-time |
| `GET` | `/api/audit/{id}/status` | Poll audit status + results |
| `GET` | `/api/audit/{id}/screenshot/{sid}` | Serve persisted screenshot file |
| `GET` | `/api/audits/history` | Paginated audit history with filters |
| `POST` | `/api/audits/compare` | Multi-audit comparison with delta computation |

### 4.2 Input Validation

The `AuditStartRequest` Pydantic model enforces:
- **URL**: Validated against RFC-compliant HTTP/HTTPS regex — rejects malformed, IP-only, or private network URLs
- **Tier**: Must be one of `{quick_scan, standard_audit, deep_forensic, darknet_investigation}`
- **Verdict Mode**: Must be one of `{simple, expert}`
- **Security Modules**: Optional whitelist of module names

### 4.3 Audit Lifecycle State Machine

```
QUEUED → RUNNING → COMPLETED
                 → ERROR
                 → DISCONNECTED (client left early)
```

State transitions are reflected both in the in-memory `_audits` dict and in the SQLite database (when persistence is enabled).

### 4.4 IPC Architecture

A key engineering challenge was reliably passing structured data from the Python engine subprocess back to the FastAPI WebSocket handler. Elliot implements two IPC modes:

- **Stdout Mode (default):** Engine writes JSON to stdout; backend reads line-by-line. Simple, portable, zero additional dependencies.
- **Queue Mode (`USE_QUEUE_IPC=true`):** Uses `multiprocessing.Queue` for higher-throughput, lower-latency IPC. Avoids stdout buffer flushing issues on Windows.
- **Validate Mode (`--validate-ipc`):** Runs both modes concurrently and diffs results — used during development to ensure parity.

The `determine_ipc_mode()` function in `elliot/core/ipc.py` selects the mode based on CLI flags, environment variables, or a percentage rollout configuration.

### 4.5 Screenshot Persistence

When `USE_DB_PERSISTENCE=true`, every screenshot is:
1. Base64-decoded from the WebSocket event
2. Saved to the filesystem via `ScreenshotStorage` (under `backend/data/screenshots/{audit_id}/`)
3. Recorded in the `AuditScreenshot` table with `file_path`, `label`, `index_num`, and `file_size_bytes`
4. Served back via the `/api/audit/{id}/screenshot/{sid}` REST endpoint

---

## 5. The Elliot Python Engine

### 5.1 Entry Point

The engine is invoked as a Python module: `python -m elliot <url> --tier <tier>`. The `__main__.py` CLI provides:

- `argparse`-based interface for all options
- IPC mode selection (`--use-queue-ipc`, `--use-stdout`, `--validate-ipc`)
- Security module whitelisting (`--security-modules`)
- Verdict mode selection (`--verdict-mode simple|expert`)
- Output formats: stdout JSON, file JSON, PDF report, HTML report
- Windows-specific UTF-8 stdout patching (prevents `UnicodeEncodeError` when piping emojis)

### 5.2 LangGraph Orchestration

The `ElliotOrchestrator` in `elliot/core/orchestrator.py` (45KB) implements a **LangGraph state machine**. Each agent is a LangGraph node. The graph defines:

- **Sequential edges:** Scout → Security → Vision → Graph → Judge
- **Conditional edges:** If a phase fails below the confidence threshold, the graph can route to a degraded path that skips expensive NIM calls
- **State object:** A typed Python dataclass carrying all accumulated findings, screenshots, security results, and metadata across all phases
- **Iteration limit:** Controlled via `MAX_ITERATIONS` (default 5) to prevent infinite loops

### 5.3 Circuit Breaker & Degradation

`elliot/core/circuit_breaker.py` implements a circuit breaker pattern around all NVIDIA NIM API calls:
- **Closed state:** Normal operation
- **Open state:** Trips after N consecutive failures — bypasses NIM calls entirely for the circuit's duration
- **Half-open state:** Tests one call after a cooldown period

`elliot/core/degradation.py` provides graceful fallback strategies when NIM is unavailable — deterministic analysis modules still run, and the Judge generates a verdict from available evidence only.

### 5.4 NIM Client

`elliot/core/nim_client.py` (25KB) wraps the NVIDIA NIM API:
- Configurable primary and fallback VLM models
- Per-request rate limiting (`NIM_REQUESTS_PER_MINUTE`)
- Automatic retry with exponential backoff (`NIM_RETRY_COUNT`)
- Timeout handling (`NIM_TIMEOUT`)
- Circuit breaker integration

### 5.5 Evidence Store (LanceDB)

`elliot/core/evidence_store.py` manages a LanceDB vector database:
- Each finding is stored as an embedding (via `sentence-transformers`)
- Enables semantic similarity search across findings
- Persists evidence beyond session memory — the Judge can query for similar historical findings
- Locked/reset-safe: if the DB is locked by a crashed process, delete `elliot/data/vectordb/` to reset

---

## 6. Multi-Agent Pipeline — Phase by Phase

### Phase 1: Scout Agent (`elliot/agents/scout.py` — 71KB)

The Scout is the data collection layer. It runs a full Playwright-controlled Chromium browser session:

**Capabilities:**
- Full-page screenshot capture (both initial viewport and full-scroll)
- Rendered DOM extraction (post-JavaScript execution)
- Form element detection: type, action URL, HTTPS enforcement
- CAPTCHA presence detection
- Internal link following up to `MAX_PAGES_PER_AUDIT` pages
- Exploration path recording (the exact URL traversal tree)
- Network idle detection before capture (ensures fully loaded DOM)
- DOM health scoring (measures structural complexity and anomalies)
- Cookie dialog and consent overlay detection

**Output events:** `screenshot`, `page_scanned`, `navigation_start`, `navigation_complete`, `captcha_detected`, `form_detected`, `dom_health`, `exploration_path`

---

### Phase 2: Security Agent (`elliot/agents/security_agent.py` — 52KB)

Runs 6+ deterministic analysis modules in parallel:

**`security_headers.py`** — Checks HTTP response headers:
| Header | Checked For |
|---|---|
| `Content-Security-Policy` | Presence + `unsafe-inline` / `unsafe-eval` flags |
| `Strict-Transport-Security` | `max-age`, `includeSubDomains` |
| `X-Frame-Options` | `DENY` / `SAMEORIGIN` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | Overly permissive values |
| `Permissions-Policy` | Camera/microphone access |

**`form_validator.py`** — Password/checkout form checks:
- Ensures form `action` targets HTTPS
- Flags `autocomplete="off"` on login forms (accessibility AND phishing indicator)
- Detects hidden pre-ticked fields

**`js_analyzer.py`** — JavaScript behavior:
- Detects `eval()`, `document.write()`, obfuscated script patterns
- Identifies clipboard hijacking patterns
- Detects `window.onbeforeunload` abusers (fake "leave site" dialogs)

**`phishing_checker.py`** — Heuristic phishing indicators:
- Homoglyph attack patterns in domain (e.g., `payρal.com`)
- Mismatched visible text vs href link URL
- Domain age + registration date inconsistencies
- Login form on HTTP (non-HTTPS)

**`redirect_analyzer.py`** — Redirect chain tracing:
- Follows up to 10 hops
- Flags final landing on a different domain than initially requested
- Detects open redirect patterns

**`temporal_analyzer.py`** — Repeated screenshot comparison:
- Takes two screenshots separated by `TEMPORAL_DELAY` seconds
- Pixel-diff comparison detects fake countdown timers and dynamically changing prices

**Output events:** `security_result`, `finding`, `dark_pattern_finding`, `temporal_finding`, `site_type`

---

### Phase 3: Vision Agent (`elliot/agents/vision.py` — 64KB)

The Vision Agent sends screenshots to NVIDIA NIM's VLMs (up to 90B parameter Llama-based models) for visual reasoning. Unlike the Security Agent which sees structured HTML, the Vision Agent sees what a user would see.

**Detects:**
- **Fake urgency:** Countdown timers, "Only 2 left!" banners, artificial scarcity
- **Misdirection:** Hidden "No thanks" links, camouflaged decline buttons, accept buttons styled as close buttons
- **Sneaking:** Pre-selected add-ons, auto-added items in cart, invisible subscription checkboxes
- **Social proof manipulation:** Fake reviews with inconsistent timestamps, paid-badge misrepresentation
- **Obstruction:** Confirm-shaming dialogs, deliberately complex cancellation flows
- **Deceptive pricing:** Price anchoring without disclosure, hidden fees revealed only at checkout

**VLM Prompting Strategy:**
The Vision Agent constructs structured prompts that include:
1. Screenshot + context about the site type and tier
2. A request for a structured JSON response with `pattern_type`, `confidence`, `bbox` (bounding box coordinates), and `evidence_text`
3. Fallback to the 11B model if the 90B model times out or fails

**Output events:** `dark_pattern_finding`, `vision_pass_complete`, `finding`

---

### Phase 4: Graph Investigator (`elliot/agents/graph_investigator.py` — 87KB)

Builds a knowledge graph of the website's external entity relationships using NetworkX.

**Entity Types:**
- **Domain** (target URL, all linked domains)
- **Registrar** (WHOIS lookup)
- **ASN / Hosting Provider** (IP → ASN mapping)
- **SSL Certificate Issuer** (Let's Encrypt vs. commercial CA)
- **CDN / Proxy** (Cloudflare, Fastly detection)

**Anomaly Analysis:**
- E-commerce site on shared hosting with anonymous registrar → suspicious
- SSL certificate issued < 30 days ago + unknown registrar → high-risk indicator
- Target domain links to known malicious domains → finding emitted
- Corporate entity claims (business name, address) cross-referenced against WHOIS and DNS data

**OSINT Enrichment at Graph Phase:**
The Graph Investigator triggers the OSINT engine to:
- Detect IOC indicators in the domain and IP space
- Map detected attack techniques to MITRE ATT&CK entries
- Compute CVSS metrics for any detected technical vulnerabilities
- Check domain against reputation databases

**Output events:** `knowledge_graph`, `graph_analysis`, `cvss_metrics`, `mitre_technique_mapped`, `osint_result`, `corporate_entities`, `site_classification`, `threat_attribution`

---

### Phase 5: Judge Agent (`elliot/agents/judge.py` — 70KB)

The Judge is the synthesis layer. It aggregates all evidence from all previous phases and produces the final verdict.

**Trust Scoring Algorithm:**
The trust score (0–100) is computed as a weighted sum of signal categories. Weights are site-type-adjusted (e.g., e-commerce sites are penalized more harshly for missing HTTPS than a personal blog):

```
trust_score = 100
  - Σ (finding.severity_weight × finding.confidence)    [deductions]
  + Σ (green_flag.bonus × green_flag.strength)          [additions]
  × site_type_adjustment_factor
  ∩ [0, 100]
```

Severity weights:
- `critical` → 20 points per finding
- `high` → 10 points
- `medium` → 5 points
- `low` → 2 points

**Risk Classification:**
| Score Range | Risk Level | Recommended Action |
|---|---|---|
| 80–100 | LOW_RISK | Site appears trustworthy |
| 60–79 | MODERATE_RISK | Proceed with caution |
| 40–59 | HIGH_RISK | Significant concerns detected |
| 0–39 | CRITICAL_RISK | Avoid interacting with this site |

**Dual Verdict System:**
The Judge produces two simultaneously generated outputs:

1. **`verdict_technical`** (Expert mode):
   - CVSS base score + vector string
   - CWE entries
   - IOC indicators
   - Threat indicators (HTTP patterns, suspicious JS, redirect chains)
   - MITRE ATT&CK techniques list
   - Exploitability + impact assessments
   - Deep forensic narrative (2–4 paragraphs)
   - Technical remediation steps

2. **`verdict_nontechnical`** (Simple mode):
   - Risk level in plain English
   - Consumer summary (1 paragraph)
   - Key findings in bullet points
   - Actionable "What to do" steps
   - Warnings (red flags)
   - Positive signals (green flags)

Both verdicts are always generated — the frontend renders them side-by-side in the **VERDICT.MATRIX** panel.

**Output events:** `dual_verdict`, `audit_result`, `green_flags`, `exploitation_advisory`, `attack_scenario`, `audit_complete`

---

## 7. OSINT Intelligence Engine

The OSINT module (`elliot/osint/`) is a standalone intelligence pipeline triggered during the Graph Investigation phase.

### 7.1 Module Breakdown

| Module | File | Purpose |
|---|---|---|
| OSINT Orchestrator | `orchestrator.py` (28KB) | Coordinates all OSINT sub-modules |
| IOC Detector | `ioc_detector.py` (30KB) | Identifies Indicators of Compromise in domain, IP, JS |
| Cyber Threat Intelligence | `cti.py` (9KB) | Queries threat intelligence for known threat actors |
| Reputation Checker | `reputation.py` (12KB) | Domain/IP reputation scoring |
| Attack Patterns | `attack_patterns.py` (14KB) | Pattern matching against known attack signatures |
| Vulnerability Mapper | `vulnerability_mapper.py` | CVE lookup + CVSS calculation |
| OSINT Cache | `cache.py` (6KB) | TTL-based caching of expensive OSINT queries |

### 7.2 IOC Types Detected

The `ioc_detector.py` (the largest module at 30KB) detects:
- Known malicious IP addresses
- Domain-generation algorithm (DGA) patterns
- Suspicious DNS (long TTL below threshold, NXDOMAIN abuse)
- Certificate transparency log anomalies
- Embedded content from flagged malicious domains
- JavaScript-level IOC patterns (encoded payloads, C2 callback patterns)
- Open redirect chains to known phishing infrastructure

### 7.3 MITRE ATT&CK Mapping

Techniques are matched using the `normalizeTechnique()` function in the Zustand store, which parses both structured objects (`{technique_id, technique_name, tactic, confidence, matched_markers}`) and string formats (`"T1566 - Phishing"`). Matched techniques are rendered in the **MITRE.ATTACK.GRID** panel.

### 7.4 CVSS Metrics

Computed CVSS v3.1 vector components are streamed as `cvss_metrics` events and visualized in the **CVSS.RADAR** panel as a radar chart with axes for:
- Attack Vector (AV)
- Attack Complexity (AC)
- Privileges Required (PR)
- User Interaction (UI)
- Scope (S)
- Confidentiality Impact (C)
- Integrity Impact (I)
- Availability Impact (A)

---

## 8. Darknet & Tor Integration

The darknet module (`elliot/darknet/`) provides threat intelligence from Tor-accessible sources.

### 8.1 Onion Detector (`onion_detector.py` — 9KB)

Scans the target site's HTML and linked resources for `.onion` domain references. Flags:
- Direct `.onion` links (legitimate use vs. suspicious redirection)
- JavaScript that dynamically constructs Tor URLs
- Darknet marketplace naming conventions in domain or URL structure

### 8.2 Threat Scraper (`threat_scraper.py` — 4KB)

Queries known threat intelligence aggregators (accessible via clearnet APIs) for mentions of the target domain. Returns `MarketplaceThreatData` objects indicating if the domain appears on:
- Leaked credential dumps
- Carding forums
- Fraud marketplace listings

### 8.3 Tor Client

`elliot/core/tor_client.py` (9KB) handles the Tor SOCKS5 proxy connection for deep darknet queries in `darknet_investigation` tier audits. Falls back gracefully if Tor is not available locally (darknet data is treated as optional intelligence, not a blocker).

---

## 9. Quality Consensus Engine

A critical differentiator of Elliot is that it does not blindly aggregate all findings. The quality layer (`elliot/quality/`) applies a confidence-based consensus filter before the Judge receives evidence.

### 9.1 Confidence Scorer (`confidence_scorer.py` — 7KB)

Each finding is scored on:
- **Source weight:** VLM findings slightly downweighted vs deterministic checks
- **Evidence corroboration:** Findings corroborated by multiple agents get a confidence boost
- **Pattern frequency:** A dark pattern found on 3 out of 5 pages is scored higher than one found on 1 page

Only findings above `CONFIDENCE_THRESHOLD` (default 0.6) are promoted to the final report.

### 9.2 Consensus Engine (`consensus_engine.py` — 20KB)

Resolves contradictions between agents:
- The Vision Agent says "No urgency patterns" but the Security Agent's DOM analysis found a countdown timer → consensus keeps the finding at reduced confidence
- All agents agree on HTTPS enforcement → green flag is issued at high confidence
- LLM narrative generated by Judge conflicts with deterministic finding count → numerical evidence wins

### 9.3 Validation State (`validation_state.py`)

Tracks which claims have been validated by at least N agents, maintaining a validation ledger throughout the audit lifecycle.

---

## 10. Database Persistence Layer

### 10.1 Models (`elliot/db/models.py` — 8KB)

Three ORM models using SQLAlchemy async:

**`Audit`** — Primary audit record:
- `id` (VARCHAR, primary key — format `vrts_xxxxxxxx`)
- `url`, `status`, `audit_tier`, `verdict_mode`
- `trust_score` (FLOAT), `risk_level` (VARCHAR)
- `narrative` (TEXT), `signal_scores` (JSON)
- `site_type`, `site_type_confidence`
- `security_results` (JSON), `pages_scanned`, `elapsed_seconds`
- `created_at`, `started_at`, `completed_at` (timestamps)
- Relationships: `findings[]`, `screenshots[]`

**`AuditFinding`** — Persisted dark pattern / security finding:
- `id` (auto), `audit_id` (FK)
- `pattern_type`, `category`, `severity`, `confidence`
- `description`, `plain_english`, `screenshot_index`

**`AuditScreenshot`** — Persisted screenshot metadata:
- `id` (auto), `audit_id` (FK)
- `file_path` (relative filesystem path), `label`, `index_num`, `file_size_bytes`

### 10.2 Repository Pattern

`elliot/db/repositories.py` implements an `AuditRepository` class with async CRUD:
- `create(audit)` — insert new audit
- `get_by_id(audit_id)` — fetch with eager-loaded findings + screenshots
- `update(audit)` — persist changes
- `list(limit, offset, filters)` — paginated query

### 10.3 Feature Flag

`USE_DB_PERSISTENCE` is a feature flag that defaults to `true`. When `false`, the system operates statelessly — all data only lives in memory during the audit and is discarded afterward. This mode is useful for privacy-sensitive deployments or when running many test audits.

---

## 11. Frontend — The Forensic Terminal Interface

### 11.1 Design Philosophy

The Elliot UI is built around a "cybercore operator terminal" aesthetic. The design is **functionally intentional** — not just cosmetic:
- The monospaced, terminal-style typography signals to the user that raw, unfiltered forensic data is being shown
- Panel color coding (amber for UI chrome, green for active processes, red for threats, cyan for intelligence data) creates an instant visual hierarchy
- The scrolling SysLog stream conveys that work is actually happening in real time

### 11.2 The 5 Application Routes

| Route | File | Description |
|---|---|---|
| `/` | `app/page.tsx` | Landing: URL input + tier selector + recent audits |
| `/audit/[id]` | `app/audit/[id]/page.tsx` | Live 16-panel audit terminal |
| `/report/[id]` | `app/report/[id]/page.tsx` | Full forensic static report |
| `/history` | `app/history/page.tsx` | Paginated audit history browser |
| `/compare` | `app/compare/page.tsx` | Multi-audit diff comparison |

### 11.3 The 16 Terminal Panel Components

All panels are housed in `TerminalPanel` wrappers which provide:
- **Amber header bar** with panel label (e.g., `[ CVSS.RADAR ]`)
- **Expand/Collapse toggle** — any panel can be fullscreened to `fixed inset-4`
- **`PanelErrorBoundary`** — React class-based error boundary prevents one broken panel from crashing the entire terminal
- **`GhostPanel`** — Loading placeholder with pulsing amber indicator while data streams in

| Panel | Component | Data Source |
|---|---|---|
| `CVSS.RADAR` | `CvssRadar.tsx` | `cvss_metrics` events |
| `MITRE.ATTACK.GRID` | `MitreGrid.tsx` | `mitre_technique_mapped` events |
| `THREAT.MATRIX` | `ThreatIntelligenceMatrix.tsx` | `osint_result` + `darknet_threat` events |
| `CORP.INTEGRITY.VERIFICATION` | `CorporateEntitiesPanel.tsx` | `corporate_entities` event |
| `AGENT.PROC.STATE` | `AgentProcState.tsx` | `phase_start` / `phase_complete` events |
| `LIVE.TELEMETRY.STREAM` | (inline) | `stats_update` events |
| `VERDICT.MATRIX` | `VerdictPanel.tsx` | `dual_verdict` + `audit_result` |
| `GREEN.FLAGS` | (inline) | `green_flags` event |
| `SCOUT.TELEMETRY` | `ScoutTelemetry.tsx` | `exploration_path`, `form_detected`, `captcha_detected` |
| `SYS.LOG.STREAM` | `SysLogStream.tsx` | `log_entry` + `phase_start` events |
| `SCOUT.IMAGERY` | `ScoutImagery.tsx` | `screenshot` events (base64 streamed) |
| `VISION.INTELLIGENCE` | `VisionIntelligence.tsx` | `dark_pattern_finding`, `temporal_finding` |
| `KNOWLEDGE.GRAPH` | `KnowledgeGraph.tsx` | `knowledge_graph` event |
| `DARKNET.OSINT.GRID` | `DarknetOsintGrid.tsx` | `osint_result`, `darknet_threat` |
| `NODE.DETAIL` | `NodeDetailPanel.tsx` | User-selected graph node detail |
| `FINAL.AUDIT.REPORT` | `FinalAuditReport.tsx` | Full overlay post-completion |

### 11.4 ChromaticProvider

`ChromaticProvider` is a React context provider that wraps the entire `/audit/[id]` page. It accepts the `activeAgent` prop (the current LangGraph phase) and adjusts CSS custom properties globally to change the ambient UI color scheme as the audit progresses:

- **Scout phase** → Blue-tinted ambient
- **Security phase** → Amber/orange ambient
- **Vision phase** → Purple ambient
- **Graph phase** → Cyan ambient
- **Judge phase** → Green ambient (trust established) or Red (threat detected)

This creates a visually distinct "feel" for each phase without any manual user interaction.

### 11.5 VerdictPanel — Dual Typewriter

The `VerdictPanel` renders three elements:
1. **Trust Score** — Large numeric display with color coding (red < 40, amber 40–70, green > 70)
2. **FORENSIC ANALYSIS panel** — Technical narrative rendered with `TypewriterText` (15ms/char)
3. **EXECUTIVE SUMMARY panel** — Non-technical narrative rendered with `TypewriterText` (20ms/char, slightly slower for readability)

The typewriter effect is implemented without a library — a `setInterval` advances a character index through the string, triggering a React state update on each tick.

### 11.6 Zustand Store Architecture

`frontend/src/lib/store.ts` (~1,300 lines, ~42KB) is the largest frontend file. It manages 40+ state fields including:

- Connection lifecycle: `auditId`, `url`, `tier`, `status`
- Phase tracking: `currentPhase`, `phases` (6 phase states), `pct`
- Evidence collections: `findings[]`, `screenshots[]`, `darkPatternFindings[]`, `temporalFindings[]`
- OSINT data: `osintResults[]`, `marketplaceThreats[]`, `iocIndicators[]`, `iocDetection`
- Security data: `cveEntries[]`, `cvssMetrics[]`, `mitreTechniques[]`, `attackPatterns[]`
- Intelligence data: `knowledgeGraph`, `graphAnalysis`, `siteClassification`
- Navigation data: `explorationPath`, `captchaResults[]`, `formDetections[]`
- Verdict: `dualVerdict`, `result`, `trustScoreResult`
- Reliability: `processedEventIds[]` (deduplication), `eventSequencer` (ordering)

### 11.7 Audit History & Compare Pages

**`/history`** (15KB page):
- Fetches from `/api/audits/history` with filters and pagination
- Displays audit cards with trust score, risk level, site type, date, duration
- Click-through links to individual reports

**`/compare`** (31KB page):
- Allows selection of 2+ audits from history
- Calls `/api/audits/compare` to receive computed trust score deltas
- Visual delta indicators (↑ +12.4, ↓ -8.1) with color coding
- Risk level change visualization (e.g., MODERATE_RISK → CRITICAL_RISK)

---

## 12. Real-Time Event System

### 12.1 WebSocket Connection Management

`useAuditStream.ts` manages the WebSocket lifecycle:
- **Dynamic WS base URL:** Derives WebSocket URL from `window.location` at runtime, preventing `localhost` being hardcoded when accessed remotely
- **Intentional close flag:** `__isIntentionalClose` prevents spurious error states when React Strict Mode mounts/unmounts the component twice
- **Reconnect on abnormal close:** If WS closes with code ≠ 1000 while status is `running`, polls `/api/audit/{id}/status` once to determine the final state
- **Cleanup:** The `useEffect` cleanup properly calls `ws.close()` to prevent memory leaks

### 12.2 Event Sequencing

The `EventSequencer` class (`frontend/src/hooks/useEventSequencer.ts`) implements a reorder buffer:
- Events with `sequence` numbers are buffered
- Events are dispatched in strict numerical order, even if they arrive out of order
- Events without sequence numbers are processed immediately (backward compatibility)

### 12.3 At-Least-Once Delivery

Each event may optionally carry an `event_id`. The store maintains a `processedEventIds` ring buffer (capped at 5,000 entries) and skips events with already-seen IDs — preventing duplicate state updates if the backend re-sends events.

### 12.4 Event Volume

A full `deep_forensic` audit may emit 100–400+ discrete WebSocket events. The store handles this without performance degradation due to:
- Zustand's subscription-based re-render model (only subscribed components re-render)
- The ring-buffer design for `processedEventIds`
- React 19's automatic batching of multiple state updates within a single microtask

---

## 13. Security & Ethical Design

### 13.1 Passive Read-Only Auditing

Elliot is explicitly designed as a **passive observer**:
- It does not inject payloads (no SQLi, XSS, or SSRF probes)
- It does not attempt login or form submission (except reading form structure)
- It does not modify cookies or session state on the target
- Playwright is configured to be a standard browser client — not to bypass WAFs or CAPTCHAs

### 13.2 Input Sanitization

- The URL validator rejects private network addresses, IP-only URLs, and non-HTTP(S) schemes
- All dynamic content passed to React components is rendered as text, not `dangerouslySetInnerHTML`

### 13.3 Rate Limiting

- `NIM_REQUESTS_PER_MINUTE` controls the LLM/VLM call rate to avoid triggering the target site's bot detection via excessive requests and to stay within NVIDIA NIM quotas

### 13.4 Data Privacy

- The `USE_DB_PERSISTENCE=false` mode allows fully ephemeral operation with no data retention
- Screenshots are stored only on the local filesystem, not transmitted to any external service
- NVIDIA NIM is the only external API call; screenshot data is sent only to NIM's endpoint for VLM analysis

---

## 14. Performance & Scalability Considerations

### 14.1 Current Performance Profile

| Metric | Quick Scan | Standard Audit | Deep Forensic |
|---|---|---|---|
| Wall-clock time | ~60s | ~180s | ~300s |
| Pages crawled | 1–3 | 3–10 | 5–15 |
| NIM API calls | 0–2 | 5–12 | 10–25 |
| WebSocket events | 20–50 | 80–200 | 150–400 |
| DB records created | 1 audit + N findings | same | same + screenshots |

### 14.2 Concurrency Model

- **Backend:** FastAPI + Uvicorn in async mode. Each WebSocket connection runs in an asyncio `Task`. Multiple concurrent audits are supported in theory but NIM rate limits are shared.
- **Engine:** Each audit runs in a **separate subprocess** — full process isolation prevents one audit's crash from affecting others.
- **Frontend:** React 19's concurrent rendering and Zustand's atomic subscription model keep the UI responsive even during rapid event bursts.

### 14.3 Scalability Path

For production multi-tenant scaling, the current architecture would evolve:
- **Backend:** FastAPI behind Nginx, Gunicorn workers, Redis for `_audits` state (currently in-process dict)
- **Engine:** Celery task queue, one worker process per audit
- **Database:** PostgreSQL via `asyncpg` (DATABASE_URL is already configurable)
- **Screenshots:** S3-compatible blob storage instead of local filesystem
- **Frontend:** Deployed on Vercel or behind CDN

---

## 15. Testing Strategy

### 15.1 Python Engine Tests

`elliot/tests/test_elliot.py` — 20 unit tests covering:
- Agent initialization and configuration
- Analysis module output schemas
- Trust scoring calculations
- Event serialization formats
- OSINT module connectivity (mocked responses)
- LanceDB read/write operations

Run with: `python -m pytest elliot/tests/test_elliot.py -v`  
Expected result: **20/20 passed**.

### 15.2 Frontend Build Validation

`npm run build` (Next.js production build) validates:
- TypeScript type checking across all 5 routes and 40+ components
- No unreachable imports
- All dynamic routes (`[id]`, `[ids]`) properly defined

### 15.3 Backend Integration Tests

`backend/tests/` contains integration tests for:
- `POST /api/audit/start` request validation (invalid URLs, unsupported tiers)
- `GET /api/audits/history` pagination and filter logic
- WebSocket connection lifecycle (connect, receive events, disconnect)
- Database repository CRUD operations

---

## 16. CLI Interface

The engine exposes a full-featured CLI for headless/automated usage:

```bash
# Basic audit
python -m elliot https://example.com

# Full options
python -m elliot https://example.com \
  --tier deep_forensic \
  --verdict-mode expert \
  --security-modules security_headers,phishing_db,js_analysis \
  --report pdf \
  --output result.json \
  --verbose \
  --use-queue-ipc
```

**IPC Modes:**
```bash
# Force Queue IPC (lower latency, higher throughput)
python -m elliot https://example.com --use-queue-ipc

# Force stdout IPC (most compatible)
python -m elliot https://example.com --use-stdout

# Validate both modes produce same results
python -m elliot https://example.com --validate-ipc
```

---

## 17. Key Technical Innovations

### 17.1 Dual-Mode LLM Verdict Generation

Rather than asking the LLM to produce one generic output and then filtering it for audience, Elliot instructs the Judge Agent to simultaneously produce two structurally distinct verdict objects — one optimized for forensic technical consumers, one for lay audiences. This eliminates the quality degradation that occurs when a single technical output is post-processed for simplification.

### 17.2 VLM-Powered Dark Pattern Detection

This is the core differentiator. Dark patterns that exist as visual deception (not as DOM structures) have historically been undetectable by automated tools. By combining Playwright screenshot capture with NVIDIA NIM's 90B-parameter vision model, Elliot can reason about visual ambiguity in the same way a human user would.

### 17.3 Chromatic Agent Theming

The `ChromaticProvider` dynamically adjusts the global CSS custom properties in response to which AI agent is currently active. This creates an ambient "pulse" through the UI that conveys the audit's internal state without requiring the user to read status text — a form of affective computing applied to security tooling.

### 17.4 Event Sequencer with At-Least-Once Delivery

The combination of `EventSequencer` (ordering) and `processedEventIds` ring buffer (deduplication) implements a reliable exactly-once-processed event delivery guarantee at the frontend — addressing a common challenge in real-time WebSocket-based applications where network retransmission or React Strict Mode double-mounting can cause duplicate event processing.

### 17.5 IPC Mode Validation

The `--validate-ipc` flag is a production-safety feature unique to this system. It runs the engine twice — once with Queue IPC and once with Stdout IPC — and compares the event streams. Discrepancies are logged, allowing developers to catch IPC implementation drift without deploying to production.

### 17.6 Panel Error Boundaries with `MODULE_PANIC_ERR`

Each of the 16 terminal panels is individually wrapped in a React class-based `PanelErrorBoundary`. If one panel's rendering throws a JavaScript exception (e.g., due to malformed streaming data), only that panel displays a `[MODULE_PANIC_ERR]` message — the rest of the terminal continues operating. This is essential for a system that renders untrusted, streaming external data.

---

## 18. Limitations & Future Work

### 18.1 Current Limitations

| Limitation | Impact | Planned Fix |
|---|---|---|
| NVIDIA NIM dependency | Engine degrades gracefully but VLM findings are MIA without API key | Local VLM option (Ollama) |
| Single-machine deployment | No horizontal scaling | Celery + Redis task queue |
| SQLite as default DB | Concurrent write contention under load | PostgreSQL option |
| No authentication layer | Any user can start audits | API key authentication + rate limiting |
| Playwright resource usage | ~500MB RAM per audit process | Browser pool management |
| `darknet_investigation` requires Tor | Not available in all environments | Fallback to clearnet-only darknet APIs |

### 18.2 Future Roadmap

1. **User authentication** — Multi-tenant accounts with audit ownership
2. **Scheduled re-audits** — Periodic re-scan with change alerting
3. **Headless API mode** — Pure JSON API without WebSocket for integration into CI/CD pipelines
4. **Browser extension** — Run a quick scan on the current tab with one click
5. **Report export** — PDF generation of the full forensic report
6. **Remediation tracking** — Mark findings as resolved, track remediation over time
7. **Knowledge base integration** — Link findings to OWASP, CVE, and CWE documentation automatically
8. **Local LLM support** — Ollama/LM Studio as a local alternative to NVIDIA NIM for air-gapped environments

---

## 19. Conclusion

Elliot represents a significant advancement over traditional web security scanners by introducing **multi-modal AI reasoning** into the forensic analysis pipeline. Its five-agent architecture ensures that each dimension of website trustworthiness is evaluated by an agent optimized for that specific task — from Playwright-driven behavioral observation to NVIDIA NIM VLM visual pattern recognition to NetworkX-based entity graph anomaly detection.

The platform's **dual verdict system** addresses a longstanding UX failure in security tooling: the inability to serve both expert and non-expert audiences from the same analysis. By generating both a forensic technical report and a plain-English consumer advisory simultaneously, Elliot makes advanced threat analysis accessible without sacrificing depth.

The **real-time forensic terminal interface** transforms a traditionally background-running CLI tool into an interactive, transparent, and visually compelling forensic workstation — making the act of website analysis itself educational and observable.

With a fully typed TypeScript frontend (60+ interfaces), a 1,300-line Zustand store with 40+ state fields handling 40+ event types with sequencing and deduplication, a 87KB Graph Investigator agent, and database persistence with audit history and comparison capabilities, Elliot is architected for production-grade deployment while remaining accessible to academic research and demonstration.

---

## 20. Appendix A — Full WebSocket Event Catalogue

| Event | Key Fields | Emitting Agent |
|---|---|---|
| `phase_start` | `phase`, `message`, `pct` | Orchestrator |
| `phase_complete` | `phase`, `summary`, `pct` | Orchestrator |
| `phase_error` | `phase`, `error` | Orchestrator |
| `finding` | `finding{id, category, severity, confidence, description, evidence, bbox, screenshot_index}` | All agents |
| `screenshot` | `url`, `image` (base64), `index`, `label`, `width`, `height` | Scout |
| `stats_update` | `stats{pages_scanned, screenshots, findings, ai_calls, security_checks, elapsed_seconds}` | Runner |
| `log_entry` | `agent`, `message`, `level`, `timestamp`, `context`, `params` | All agents |
| `site_type` | `site_type`, `confidence` | Scout / Security |
| `security_result` | `module`, `result` | Security |
| `dark_pattern_finding` | `pattern_type`, `category`, `confidence`, `description`, `bbox` | Vision |
| `temporal_finding` | `change_type`, `confidence`, `description`, `before_url`, `after_url` | Security |
| `vision_pass_complete` | `summary`, `nim_calls`, `patterns_detected` | Vision |
| `osint_result` | `source`, `result`, `domain`, `iocs` | OSINT |
| `darknet_threat` | `marketplace`, `threat_type`, `confidence`, `raw` | Darknet |
| `ioc_indicator` | `type`, `value`, `severity`, `context` | OSINT |
| `ioc_detection_complete` | `total`, `critical`, `high`, `medium`, `low` | OSINT |
| `cve_detected` | `cve_id`, `severity`, `description`, `cvss_score` | OSINT |
| `cvss_metrics` | `metrics[]`, `base_score`, `vector` | OSINT |
| `mitre_technique_mapped` | `technique{technique_id, technique_name, tactic, confidence}` | OSINT |
| `threat_attribution` | `apt_group`, `confidence`, `techniques[]` | OSINT |
| `apt_group_attribution` | `group`, `aliases[]`, `confidence` | OSINT |
| `exploitation_advisory` | `cve_id`, `advisory`, `severity` | Judge |
| `attack_scenario` | `scenario`, `likelihood`, `impact` | Judge |
| `knowledge_graph` | `graph{nodes[], edges[]}` | Graph |
| `graph_analysis` | `inconsistencies[]`, `domain_intel` | Graph |
| `site_classification` | `category`, `confidence`, `signals[]` | Scout / Security |
| `corporate_entities` | `entities[]` | Graph |
| `exploration_path` | `path{nodes[], edges[]}` | Scout |
| `navigation_start` | `url`, `timestamp` | Scout |
| `navigation_complete` | `url`, `duration`, `status_code` | Scout |
| `page_scanned` | `url`, `index`, `pages_scanned` | Scout |
| `captcha_detected` | `url`, `type`, `confidence` | Scout |
| `form_detected` | `url`, `action`, `method`, `inputs[]`, `is_https` | Scout |
| `dom_health` | `score`, `complexity`, `anomalies[]` | Scout |
| `green_flags` | `flags[]` | Judge |
| `dual_verdict` | `trust_score`, `technical{}`, `non_technical{}` | Judge |
| `audit_result` | full result object | Judge |
| `audit_complete` | `audit_id` | Orchestrator |
| `audit_error` | `error` | Orchestrator / Backend |
| `agent_personality` | `agent`, `context`, `params` | All agents |

---

## 21. Appendix B — Configuration Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `NVIDIA_API_KEY` | string | — | **Required.** NVIDIA NIM API key |
| `NVIDIA_NIM_ENDPOINT` | URL | `https://integrate.api.nvidia.com/v1` | NIM base URL |
| `NIM_VISION_MODEL` | string | `nvidia/llama-3.2-nv-vision-90b-instruct` | Primary VLM |
| `NIM_VISION_FALLBACK` | string | `nvidia/llama-3.2-nv-vision-11b-instruct` | Fallback VLM |
| `NIM_LLM_MODEL` | string | `nvidia/llama-3.3-nemotron-super-49b-v1` | Text LLM |
| `USE_DB_PERSISTENCE` | bool | `true` | Enable SQLite DB writes |
| `DATABASE_URL` | URL | `sqlite+aiosqlite:///./elliot_dev.db` | DB connection |
| `USE_QUEUE_IPC` | bool | `false` | Use Queue IPC instead of Stdout |
| `TAVILY_API_KEY` | string | — | Tavily web search (optional) |
| `NIM_TIMEOUT` | int | `30` | API timeout (seconds) |
| `NIM_RETRY_COUNT` | int | `2` | API retry attempts |
| `NIM_REQUESTS_PER_MINUTE` | int | `10` | Rate limit |
| `MAX_ITERATIONS` | int | `5` | LangGraph max iterations |
| `MAX_PAGES_PER_AUDIT` | int | `10` | Max pages to crawl |
| `TEMPORAL_DELAY` | int | `10` | Delay between temporal snapshots |
| `CONFIDENCE_THRESHOLD` | float | `0.6` | Min confidence for promoted findings |
| `BROWSER_HEADLESS` | bool | `true` | Headless Playwright mode |

---

*Report generated: April 2026 | Elliot v9.4.0 | For academic presentation purposes*
