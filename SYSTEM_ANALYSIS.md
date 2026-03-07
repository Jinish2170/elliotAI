# VERITAS - Complete System Architecture Analysis
## Date: 2026-03-05

---

## EXECUTIVE SUMMARY

Veritas is a multi-modal forensic web auditing platform with 5 specialized AI agents, 25+ analysis modules, and a tier-based security analysis architecture. The system consists of:

- **Backend**: Python 3.11+ with FastAPI, LangGraph orchestration, NVIDIA NIM integration
- **Frontend**: Next.js 15 with TypeScript, WebSocket streaming for real-time updates
- **Database**: SQLite with LanceDB vector store for evidence persistence

---

## 1. AGENT LAYER (Core Analysis Engines)

### 1.1 Scout Agent (`veritas/agents/scout.py`)
**Role**: Browser reconnaissance and evidence capture
**Input**: URL, tier configuration, viewport settings
**Output**: `ScoutResult` containing:
- screenshots: List of file paths
- screenshot_labels: Context labels for each screenshot
- html_content: Full page HTML
- url: Target URL
- viewport: Viewport dimensions (mobile/desktop)
- dom_meta: Extracted DOM metadata
- external_links: List of discovered URLs
- scripts: List of loaded scripts
- forms: Extracted form structures
- temporal_data: Temporal analysis results
- site_type: Detected site category
- site_type_confidence: Classification confidence

**Key Methods**:
- `visit_url()` - Navigate to target with stealth
- `capture_screenshot()` - Take screenshots
- `extract_dom()` - Parse HTML for metadata
- `detect_lazy_load()` - Identify lazy-loading content
- `scroll_for_content()` - Scroll to trigger lazy loads

---

### 1.2 Vision Agent (`veritas/agents/vision.py`)
**Role**: Visual dark pattern detection using NVIDIA NIM VLM
**Input**: Screenshot file paths, VLM prompts from taxonomy
**Output**: `VisionResult` containing:
- findings: List of dark pattern detections
- visual_score: Aggregate visual threat score
- screenshot_index: Which screenshot produced the finding
- pass: Which analysis pass (1-3)

**Key Methods**:
- `analyze_screenshots()` - Send screenshots to NIM VLM
- `compute_visual_score()` - Weighted score from findings
- `generate_forensic_summary()` - Text summary of visual threats

**Dark Pattern Categories** (Urgency, Misdirection, Social Proof, Obstruction, Sneaking)

---

### 1.3 Graph Investigator (`veritas/agents/graph_investigator.py`)
**Role**: Entity verification through knowledge graphs
**Input**: Domain, meta_analysis from Scout
**Output**: `GraphResult` containing:
- domain_intel: Domain age, registrar, country
- ip_geolocation: IP address, country, city
- ssl_info: SSL certificate issuer, validity
- inconsistencies: Discrepancies between claimed vs actual
- verifications: List of entity verification results
- nodes: Knowledge graph node count
- edges: Knowledge graph relationship count

**Key Methods**:
- `verify_domain()` - Check WHOIS/DNS records
- `verify_ssl()` - Validate SSL certificate
- `verify_entity_claims()` - Cross-check metadata with reality
- `build_graph()` - Create NetworkX entity graph

---

### 1.4 Judge Agent (`veritas/agents/judge.py`)
**Role**: Evidence synthesis and trust scoring
**Input**: `AuditEvidence` (all agent outputs)
**Output**: `JudgeDecision` containing:
- action: "RENDER_VERDICT" or "REQUEST_MORE_INVESTIGATION"
- trust_score_result: Final TrustScoreResult
- forensic_narrative: Technical explanation of verdict
- simple_narrative: Plain-English explanation
- recommendations: List of actionable advice
- risk_level: Risk classification
- site_type: Detected website type

**Dual Verdict Mode** (V2 feature):
- `VerdictTechnical`: CWE IDs, CVSS scores, technical details
- `VerdictNonTechnical`: Plain English, user-friendly explanations

**Key Methods**:
- `deliberate()` - Main decision logic
- `analyze()` - Public API with dual verdict support
- `_should_investigate_more()` - Budget-controlled iteration logic

---

### 1.5 Security Agent (`veritas/agents/security_agent.py`)
**Role**: Tier-based security analysis with 25+ modules
**Input**: URL, page_content, headers, dom_meta
**Output**: `SecurityResult` containing:
- composite_score: Aggregated security score (0.0-1.0)
- findings: List of SecurityFinding objects
- modules_results: Per-module detailed results
- modules_run: List of executed modules
- modules_executed: Count of modules run
- darknet_correlation: Darknet threat intel

**Execution Tiers**:
- **FAST** (< 5s): HSTS, CSP, cookies, TLS/SSL
- **MEDIUM** (< 15s): GDPR, PCI DSS, OWASP analysis
- **DEEP** (< 30s): Full security audit

**Key Methods**:
- `analyze()` - Main entry point
- `get_all_security_modules()` - Auto-discovery
- `run_tier()` - Execute modules by tier
- `correlate_with_darknet()` - Darknet threat intel

---

## 2. ANALYSIS MODULES (Detailed Sub-systems)

### 2.1 Core Analysis Modules (`veritas/analysis/`)

| Module | Input | Output | Description |
|--------|-------|--------|-------------|
| `dom_analyzer.py` | HTML string | DOM metadata | HTML structure analysis, depth, node counts |
| `form_validator.py` | Form elements | Validation results | HTTPS check, autocomplete, required fields |
| `js_analyzer.py` | JavaScript source | Behavior analysis | obfuscation detection, suspicious APIs |
| `meta_analyzer.py` | Meta tags | SEO/check results | Title, description, OG tags validation |
| `pattern_matcher.py` | Content | Dark pattern matches | Textual dark pattern detection |
| `phishing_checker.py` | URL, content | Phishing indicators | Suspicious URLs, form patterns |
| `redirect_analyzer.py` | URL chain | Redirect summary | Traces HTTP redirects |
| `security_headers.py` | HTTP headers | Header findings | CSP, HSTS, X-Frame-Options |
| `temporal_analyzer.py` | Two page captures | Temporal findings | Time-based changes detection |

---

### 2.2 Security Modules (`veritas/analysis/security/`)

#### FAST Tier (< 5s timeout)
| Module | CWE | Checks |
|--------|-----|--------|
| `tls_ssl.py` | CWE-523 | HSTS, CSP, X-Frame-Options, X-Content-Type-Options |
| `cookies.py` | CWE-1004 | Secure flag, SameSite attribute, HttpOnly |
| `csp.py` | CWE-829, CWE-95 | unsafe-inline, unsafe-eval, wildcards |

#### MEDIUM Tier (< 15s timeout)
| Module | CWE | Checks |
|--------|-----|--------|
| `gdpr.py` | GDPR compliance | Cookie consent, privacy policy links |
| `pci_dss.py` | PCI DSS 4.0 | Form security, HTTPS, card data handling |

#### OWASP Top 10 Modules (`veritas/analysis/security/owasp/`)
| Module | OWASP | CWE | Checks |
|--------|-------|-----|--------|
| `a01_broken_access_control.py` | A01:2021 | CWE-284 | IDOR, privilege escalation |
| `a02_cryptographic_failures.py` | A02:2021 | CWE-327 | Weak encryption, HTTP on login forms |
| `a03_injection.py` | A03:2021 | CWE-89, CWE-79 | SQL/XSS injection indicators |
| `a04_insecure_design.py` | A04:2021 | CWE-223 | Insecure patterns in forms/links |
| `a05_security_misconfiguration.py` | A05:2021 | CWE-770 | Debug modes, default credentials |
| `a06_vulnerable_components.py` | A06:2021 | CWE-1035 | Outdated libraries from headers |
| `a07_authentication_failures.py` | A07:2021 | CWE-287 | Login form security issues |
| `a08_data_integrity.py` | A08:2021 | CWE-345 | Data validation issues |
| `a09_logging_failures.py` | A09:2021 | CWE-201 | Error expose, logging issues |
| `a10_ssrf.py` | A10:2021 | CWE-918 | SSRF indicators in forms/params |

#### Darknet Module (`veritas/analysis/security/darknet.py`)
- `.onion` address detection
- Darknet threat correlation
- Suspicious marketplace indicators

---

### 2.3 OSINT Components (`veritas/osint/`)

| Module | Input | Output | Description |
|--------|-------|--------|-------------|
| `ioc_detector.py` | Content, metadata | `IOCDetectionResult` | URL, domain, IP, email, hash detection |
| `attack_patterns.py` | Indicators | MITRE techniques | ATT&CK technique mapping |
| `cti.py` | Page data | Threat analysis | Comprehensive threat intelligence |
| `orchestrator.py` | Query | `OSINTOrchestration` | Multiple OSINT source queries |
| `reputation.py` | Domain/IP | Reputation score | Domain trustworthiness scoring |
| `vulnerability_mapper.py` | Findings | CVE mappings | Map findings to CVE IDs |

**IOC Types Supported**:
- URL, Domain, IPv4, IPv6, Email
- MD5, SHA1, SHA256 hashes
- Filenames, Onion addresses

---

## 3. CONFIGURATION LAYER (`veritas/config/`)

| File | Purpose |
|------|---------|
| `settings.py` | Environment configuration, API keys, timeouts |
| `trust_weights.py` | Signal weight definitions per site type |
| `dark_patterns.py` | Dark pattern taxonomy with VLM prompts |
| `site_types.py` | Site classification rules (12+ types) |
| `security_rules.py` | CWE/CVSS mapping, severity defaults |
| `darknet_rules.py` | Darknet threat indicators |

---

## 4. FRONTEND-BACKEND INTEGRATION

### 4.1 Backend API Routes (`backend/routes/`)

| Route | Method | Purpose | Request Body | Response |
|-------|--------|---------|--------------|----------|
| `/health` | GET | Health check | - | `{"status": "ok"}` |
| `/audit/start` | POST | Start audit | `{url, tier, verdict_mode, security_modules}` | `{audit_id, ws_url}` |
| `/audit/stream/{id}` | WS | Real-time audit stream | - | Event stream |
| `/audit/{id}/status` | GET | Get audit status | - | `{status, result, url, ...}` |
| `/audits/history` | GET | Get audit history | `{limit, offset, status_filter, risk_level_filter}` | `{audits, count}` |
| `/audits/compare` | POST | Compare multiple audits | `{audit_ids}` | `{audits, trust_score_deltas, risk_level_changes}` |

---

### 4.2 WebSocket Events to Frontend

| Event Type | Payload | Frontend Handler |
|------------|---------|-------------------|
| `phase_start` | `{phase, message, pct}` | AgentPipeline |
| `phase_complete` | `{phase, message, pct, summary}` | AgentPipeline |
| `phase_error` | `{phase, message, error}` | AgentPipeline + log |
| `finding` | `{finding}` | NarrativeFeed |
| `screenshot` | `{url, label, index, data}` | ScreenshotCarousel, EvidencePanel |
| `stats_update` | `{stats}` | EvidencePanel |
| `log_entry` | `{timestamp, agent, message, level}` | ForensicLog |
| `site_type` | `{site_type, confidence}` | NarrativeFeed |
| `security_result` | `{module, result}` | Report SecurityPanel |
| `audit_result` | `{result}` | Report page, CompletionOverlay |
| `audit_complete` | `{audit_id, elapsed}` | Status |

---

### 4.3 Frontend Pages (`frontend/src/app/`)

| Page | Path | Purpose | Key Features |
|------|------|---------|--------------|
| Landing | `/` | Home page | Hero, signals showcase, dark pattern carousel |
| Live Audit | `/audit/[id]` | Real-time audit view | Phase pipeline, narrative feed, screenshots, evidence panel, logs |
| Report | `/report/[id]` | Audit results | Trust score hero, signal breakdown, dark patterns, security panel, recommendations |

---

### 4.4 Frontend Components (`frontend/src/components/`)

**Landing**:
- `HeroSection.tsx` - Landing hero with URL input
- `SignalShowcase.ts` - Signal types display
- `DarkPatternCarousel.tsx` - Pattern examples
- `HowItWorks.tsx` - Process explanation
- `SiteTypeGrid.tsx` - Detectable site types

**Audit**:
- `AgentPipeline.tsx` - Phase status indicators
- `AuditHeader.tsx` - URL and status display
- `CompletionOverlay.tsx` - Success/failure overlay
- `EvidencePanel.tsx` - Screenshots and findings
- `ForensicLog.tsx` - Technical log entries
- `NarrativeFeed.tsx` - Live narrative updates
- `ScreenshotCarousel.tsx` - Image viewer with highlights
- `GreenFlagCelebration.tsx` - Confetti for positive audits

**Report**:
- `ReportHeader.tsx` - Report metadata and mode toggle
- `TrustScoreHero.tsx` - Score and risk level display
- `SignalBreakdown.tsx` - Radar chart of signals
- `DarkPatternGrid.tsx` - Pattern findings cards
- `EntityDetails.tsx` - Domain info verification
- `SecurityPanel.tsx` - Security findings display
- `Recommendations.tsx` - Actionable advice)
- `AuditMetadata.tsx` - Audit execution metadata

**Data Display**:
- `RiskBadge.tsx` - Risk level badge
- `SeverityBadge.tsx` - Severity indicator
- `SignalBar.tsx` - Signal value indicator
- `SignalRadarChart.tsx` - Multi-signal visualization
- `StatCounter.tsx` - Animated stat display
- `TrustGauge.tsx` - Trust score gauge

---

## 5. FRONTEND TYPE SYSTEM (`frontend/src/lib/types.ts`)

### 5.1 Core Types

```typescript
// Phase management
type Phase = "init" | "scout" | "security" | "vision" | "graph" | "judge"
type PhaseStatus = "waiting" | "active" | "complete" | "error"

interface PhaseState {
  status: PhaseStatus;
  message: string;
  pct: number;
  summary?: Record<string, unknown>;
  error?: string;
  activePass?: number;  // Vision-specific
  completedPasses?: number[];
}

// Findings
interface Finding {
  id: string;
  category: string;
  pattern_type: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  description: string;
  plain_english: string;
  screenshot_index?: number;
  bbox?: [number, number, number, number];  // Bounding box percentages
}

// Screenshots
interface Screenshot {
  url: string;
  label: string;
  index: number;
  data?: string;  // Base64
  width?: number;
  height?: number;
  findings?: Finding[];
  overlays?: HighlightOverlay[];
}

// Domain Info
interface DomainInfo {
  age_days?: number | null;
  registrar?: string | null;
  country?: string | null;
  ip?: string | null;
  ssl_issuer?: string | null;
  inconsistencies?: string[];
  entity_verified?: boolean;
}

// Full Audit Result
interface AuditResult {
  url: string;
  status: string;
  audit_tier?: string;
  trust_score: number;
  risk_level: string;
  signal_scores: Record<string, number>;
  overrides: string[];
  narrative: string;
  recommendations: string[];
  findings: Finding[];
  dark_pattern_summary: Record<string, unknown>;
  security_results: Record<string, unknown>;
  site_type: string;
  site_type_confidence: number;
  domain_info: DomainInfo;
  pages_scanned: number;
  screenshots_count: number;
  elapsed_seconds: number;
  errors: string[];
  verdict_mode: string;
  green_flags?: GreenFlag[];
}
```

---

## 6. IDENTIFIED DEAD CODE / MISSING FRONTEND INTEGRATIONS

### 6.1 Backend Features Without Frontend Integration

| Backend Feature | Location | Integration Status |
|----------------|----------|---------------------|
| **Audit History** | `GET /api/audits/history` | ❌ No UI to view audit history |
| **Audit Comparison** | `POST /api/audits/compare` | ❌ No UI to compare multiple audits |
| **Audit Tiers Selection** | Frontend only uses default | ⚠️ No tier selector in landing page |
| **Security Module Selection** | `POST /api/audit/start` supports `security_modules` parameter | ❌ No UI to select specific modules |
| **Verdict Mode Toggle** | `POST /api/audit/start` supports `verdict_mode` | ⚠️ Only in report view (not audit start) |
| **Temporal Analysis** | Scout agent supports temporal data | ❌ No UI for temporal comparison |
| **Darknet Detection** | Fully implemented in backend | ⚠️ Partially shown in security results |
| **MITRE ATT&CK Display** | Mapped in backend | ❌ No UI for MITRE technique visualization |
| **CVE/CVSS Display** | Mapped in backend via CWERegistry | ⚠️ Shown in expert mode but not detailed UI |
| **Entity Verification Details** | Graph Investigator provides full details | ⚠️ Simplified display in report |
| **IoC Indicators** | OSINT IOC detector fully functional | ❌ No dedicated IoC display panel |
| **Reputation Scores** | OSINT reputation module exists | ❌ No reputation score display |
| **Threat Attribution** | CTI module provides attribution | ❌ No attribution display in UI |

### 6.2 Frontend-Only Features Without Backend

| Frontend Feature | Location | Status |
|------------------|----------|--------|
| Dark Pattern Carousel | `DarkPatternCarousel.tsx` | ✅ Static content - no backend needed |

### 6.3 Partial Integrations

| Feature | Backend Support | Frontend Support | Notes |
|---------|----------------|-----------------|-------|
| Site Type Detection | ✅ Scout agent | ⚠️ Shown in narrative but not prominent | Could be showcased |
| Green Flags | ✅ Computed in Judge | ✅ `GreenFlag[]` in AuditResult | Displayed in completion overlay |
| Screenshots | ✅ Full support | ✅ Carousel with highlights | Good coverage |
| Security Findings | ✅ Full CWE/CVSS | ⚠️ Shown but could be expandable | Expert mode only |

---

## 7. TEST INFRASTRUCTURE

### 7.1 Backend Tests (`veritas/tests/`)
- `test_ioc_detector.py` - 32 tests for IOC detection
- `test_scout.py` - Scout agent tests
- `test_vision.py` - Vision agent tests
- `test_graph.py` - Graph investigator tests
- `test_judge.py` - Judge decision logic tests
- `test_security_modules.py` - Security module tests

### 7.2 Test Status
- Frontend build: ✅ PASSING
- Backend imports: ✅ FIXED (circular imports resolved)
- IOC Detector tests: ⚠️ 31/32 failing (missing `detect_url()` and `detect_content()` methods)

---

## 8. INTEGRATION POINTS DATA FLOW

```
User → Landing Page (/)
  → [POST /api/audit/start] → Backend
  → {audit_id, ws_url} returned
  → Navigate to /audit/[id]
  → [WS /api/audit/stream/{id}] connected

WebSocket Events Flow:
  1. phase_start → AgentPipeline update
  2. log_entry → ForensicLog update
  3. screenshot → ScreenshotCarousel + EvidencePanel
  4. finding → NarrativeFeed
  5. security_result → Report SecurityPanel
  6. audit_result → CompletionOverlay → Navigate to /report/[id]

Report Page:
  → [GET /api/audit/{id}/status] (if not from live audit)
  → Display all results from AuditResult
```

---

## 9. AUDIT TIERS

| Tier | Max Pages | Max NIM Calls | Duration | Description |
|------|-----------|--------------|----------|-------------|
| `quick` | 3 | 5 | ~60s | Basic checks (DNS, headers, visible patterns) |
| `standard_audit` | 5 | 15 | ~3min | Full pipeline (all 5 agents, screenshots, scoring) |
| `deep_forensic` | 10 | 30 | ~5min | Deep analysis (temporal, extended crawl, graph) |

---

## 10. CONFIGURATION REQUIREMENTS

### Required Environment Variables
```bash
# NVIDIA NIM (Required for AI analysis)
NVIDIA_API_KEY=nvapi-xxx
NVIDIA_NIM_ENDPOINT=https://integrate.api.nvidia.com/v1
NIM_VISION_MODEL=nvidia/llama-3.2-nv-vision-90b-instruct
NIM_VISION_FALLBACK=nvidia/llama-3.2-nv-vision-11b-instruct
NIM_LLM_MODEL=nvidia/llama-3.3-nemotron-super-49b-v1

# Optional
TAVILY_API_KEY=          # For web search
DB_PATH=                # SQLite database path
USE_DB_PERSISTENCE=true # Enable DB persistence
```

---

## 11. DEPENDENCIES

### Python (veritas/requirements.txt)
- FastAPI, Uvicorn, WebSockets
- LangChain, LangGraph
- Playwright, BeautifulSoup4
- sentence-transformers, LanceDB
- NetworkX, httpx, python-whois

### Node.js (frontend/package.json)
- Next.js 15, React 19, TypeScript 5
- tailwindcss, shadcn/ui
- Framer Motion, Recharts
- Zustand

---

## 12. NEXT STEPS FOR LAUNCH

### Phase 1: Critical Fixes
1. ✅ Fix circular imports (DONE)
2. ⚠️ Implement IOCDetector.detect_url() and detect_content() methods
3. ⚠️ Run all tests and ensure they pass

### Phase 2: Backend Testing
1. Test all API endpoints end-to-end
2. Verify WebSocket event streaming
3. Test audit tiers (quick, standard, deep)
4. Test dual verdict mode

### Phase 3: Frontend Integration
1. Create audit history page
2. Create audit comparison UI
3. Add audit tier selector to landing page
4. Add security module selection UI
5. Enhance MITRE ATT&CK visualization
6. Add IoC indicators panel
7. Add reputation score display
8. Add threat attribution display

### Phase 4: End-to-End Testing
1. Use Playwright MCP to test complete user flows
2. Test on multiple site types
3. Test dark pattern detection accuracy
4. Test security module coverage

### Phase 5: Production Readiness
1. Create Docker containers
2. Set up SSL/certificate management
3. Configure monitoring and logging
4. Create deployment documentation
