# VERITAS - Complete System Functionality Analysis
## Date: 2026-03-05

---

## EXECUTIVE SUMMARY

This document provides a comprehensive analysis of the VERITAS (Autonomous Multi-Modal Forensic Web Auditor) project, including all functionalities, agent inputs/outputs, categories, implementation phases, frontend integration status, and a plan for testing and completion.

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [Agent Layer - Complete Functionality](#2-agent-layer)
3. [Analysis Modules - Complete Taxonomy](#3-analysis-modules)
4. [Security Modules - Detailed Breakdown](#4-security-modules)
5. [OSINT Components - Threat Intelligence](#5-osint-components)
6. [Darknet Auditor - Phase 12 Features](#6-darknet-auditor)
7. [Frontend Integration Status](#7-frontend-integration-status)
8. [Dead Code Identification](#8-dead-code-identification)
9. [Integration Plan](#9-integration-plan)
10. [Testing Plan - Playwright MCP](#10-testing-plan)
11. [Phase Status Overview](#11-phase-status-overview)

---

## 1. PROJECT OVERVIEW

### 1.1 Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    Next.js 15 Frontend                        │
│  Landing (/) → Live Audit (/audit/[id]) → Report (/report/[id]) │
│  Port 3000                                                      │
└───────────────────────┬───────────────────────────────────────┘
                        │ HTTP + WebSocket
┌───────────────────────▼───────────────────────────────────────┐
│                      FastAPI Backend                          │
│  POST /api/audit/start   WS /api/audit/stream/{id}            │
│  GET  /api/audit/{id}/status   GET /api/audits/history        │
│  POST /api/audits/compare                                   │
│  Port 8000                                                      │
└───────────────────────┬───────────────────────────────────────┘
                        │ Subprocess
┌───────────────────────▼───────────────────────────────────────┐
│                 Veritas Python Engine                         │
│                                                                │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌───────────┐        │
│  │  Scout   │→│Security  │→│ Vision │→│   Graph    │          │
│  │  Agent   │  │  Agent   │  │ Agent  │→│Investigator│         │
│  └─────────┘  └──────────┘  └────────┘  └─────┬─────┘        │
│                                              │                │
│  ┌────────────────────────────────────────────▼─────┐        │
│  │                  Judge Agent                        │        │
│  │  Trust Score · Verdict · Recommendations           │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                │
│  NVIDIA NIM (LLM + VLM) · Playwright · LanceDB · OSINT       │
└───────────────────────────────────────────────────────────────┘
```

### 1.2 Tech Stack

**Backend (Python):**
- FastAPI, Uvicorn, WebSockets
- LangChain, LangGraph
- Playwright (headless browser)
- NVIDIA NIM (LLM + VLM)
- LanceDB (vector store)
- NetworkX (knowledge graphs)
- SQLAlchemy (database)

**Frontend (Next.js 15):**
- React 19, TypeScript 5
- Tailwind CSS 4, shadcn/ui
- Framer Motion (animations)
- Zustand (state management)
- Recharts (data visualization)

---

## 2. AGENT LAYER

### 2.1 Scout Agent (`veritas/agents/scout.py`)

**Purpose:** Browser reconnaissance and evidence capture using stealth browsing.

**Input:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | Target website URL |
| `tier` | str | Audit tier (quick, standard, deep) |
| `viewport` | tuple | Browser viewport dimensions |
| `max_pages` | int | Maximum pages to crawl |

**Output (ScoutResult):**
| Field | Type | Description |
|-------|------|-------------|
| `screenshots` | List[str] | File paths to captured screenshots |
| `screenshot_labels` | List[str] | Context labels for each screenshot |
| `html_content` | str | Full page HTML |
| `url` | str | Target URL |
| `viewport` | dict | Viewport dimensions used |
| `dom_meta` | dict | Extracted DOM metadata |
| `external_links` | List[str] | Discovered URLs |
| `scripts` | List[str] | Loaded JavaScript files |
| `forms` | List[dict] | Form structures |
| `temporal_data` | dict | Temporal analysis results |
| `site_type` | str | Detected site category |
| `site_type_confidence` | float | Classification confidence |

**Key Methods:**
- `visit_url()` - Navigate with stealth (anti-detection)
- `capture_screenshot()` - Full-page screenshots
- `extract_dom()` - Parse HTML metadata
- `detect_lazy_load()` - Identify lazy-loaded content
- `scroll_for_content()` - Trigger content reveals

**Frontend Integration:** ✅ COMPLETE
- Phase status shown in `AgentPipeline.tsx`
- Screenshots displayed in `ScreenshotCarousel.tsx`
- URL shown in `AuditHeader.tsx`

---

### 2.2 Vision Agent (`veritas/agents/vision.py`)

**Purpose:** Visual dark pattern detection using NVIDIA NIM Vision Language Model.

**Input:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `screenshots` | List[str] | File paths to screenshots |
| `prompts` | dict | VLM prompts from taxonomy |
| `pass_config` | dict | Multi-pass analysis configuration |

**Output (VisionResult):**
| Field | Type | Description |
|-------|------|-------------|
| `findings` | List[Finding] | Dark pattern detections |
| `visual_score` | float | Aggregate visual threat score (0-1) |
| `screenshot_index` | int | Which screenshot produced finding |
| `pass` | int | Analysis pass number (1-3) |

**Dark Pattern Categories Detected:**
1. **Urgency** - Fake countdowns, time pressure, scarcity
2. **Misdirection** - Hidden unsubscribe, fake buttons
3. **Social Proof** - Fake reviews, misleading testimonials
4. **Obstruction** - Hard-to-cancel, guilt tripping
5. **Sneaking** - Hidden costs, pre-selected options

**Key Methods:**
- `analyze_screenshots()` - Multi-pass VLM analysis
- `detect_temporal_changes()` - Timer manipulation detection
- `compute_visual_score()` - Weighted threat scoring
- `generate_forensic_summary()` - Text summary

**Frontend Integration:** ✅ COMPLETE (Phase 6 implemented)
- Findings shown in `NarrativeFeed.tsx`
- Visual patterns highlighted in `ScreenshotCarousel.tsx` with overlays
- Pass sequences shown in `AgentPipeline.tsx`

---

### 2.3 Graph Investigator (`veritas/agents/graph_investigator.py`)

**Purpose:** Entity verification through knowledge graphs and OSINT.

**Input:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `domain` | str | Domain to verify |
| `meta_analysis` | dict | Scout metadata for cross-reference |
| `osint_sources` | List[str] | External intel sources |

**Output (GraphResult):**
| Field | Type | Description |
|-------|------|-------------|
| `domain_intel` | dict | WHOIS, domain age, registrar, country |
| `ip_geolocation` | dict | IP address, country, city |
| `ssl_info` | dict | Certificate issuer, validity |
| `inconsistencies` | List[str] | Discrepancies found |
| `verifications` | List[dict] | Entity verification results |
| `nodes` | int | Knowledge graph node count |
| `edges` | int | Knowledge graph edge count |

**Key Methods:**
- `verify_domain()` - WHOIS/DNS checks
- `verify_ssl()` - Certificate validation
- `verify_entity_claims()` - Cross-reference with reality
- `build_graph()` - Create NetworkX knowledge graph

**Frontend Integration:** ⚠️ PARTIAL
- Domain info shown in `EntityDetails.tsx` (simplified)
- Full graph visualization NOT implemented

---

### 2.4 Judge Agent (`veritas/agents/judge.py`)

**Purpose:** Evidence synthesis and trust scoring with dual verdict modes.

**Input:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `evidence` | AuditEvidence | All previous agent outputs |
| `verdict_mode` | str | "simple" or "expert" |
| `site_type` | str | Detected site type |

**Output (JudgeDecision):**
| Field | Type | Description |
|-------|------|-------------|
| `action` | str | RENDER_VERDICT or REQUEST_MORE_INVESTIGATION |
| `trust_score` | int | Final trust score (0-100) |
| `risk_level` | str | Risk classification |
| `forensic_narrative` | str | Technical explanation |
| `simple_narrative` | str | Plain-English explanation |
| `recommendations` | List[str] | Actionable advice |
| `green_flags` | List[GreenFlag] | Positive indicators |

**Site Type Strategies (11 strategies implemented):**
1. `company_portfolio` - Corporate sites
2. `ecommerce` - Online stores
3. `financial` - Banking/investment
4. `healthcare` - Medical sites
5. `government` - Official domains
6. `education` - Universities
7. `gaming` - Gaming sites
8. `social_media` - Social platforms
9. `saas_subscription` - Subscription services
10. `news_blog` - Content sites
11. `darknet_suspicious` - Dark patterns in darknet

**Frontend Integration:** ✅ COMPLETE
- Trust score shown in `TrustGauge.tsx` and `TrustScoreHero.tsx`
- Risk level in `RiskBadge.tsx`
- Recommendations in `Recommendations.tsx`
- Green flags in `GreenFlagCelebration.tsx` (Phase 11)

---

### 2.5 Security Agent (`veritas/agents/security_agent.py`)

**Purpose:** Tier-based security analysis with 25+ modules.

**Input:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | Target URL |
| `page_content` | str | Page HTML |
| `headers` | dict | HTTP response headers |
| `dom_meta` | dict | DOM metadata |
| `tier` | str | Analysis tier (FAST, MEDIUM, DEEP) |

**Output (SecurityResult):**
| Field | Type | Description |
|-------|------|-------------|
| `composite_score` | float | Aggregated security score (0-1) |
| `findings` | List[SecurityFinding] | Security issues found |
| `modules_results` | dict | Per-module detailed results |
| `modules_run` | List[str] | Executed modules |
| `modules_executed` | int | Count of modules run |
| `darknet_correlation` | dict | Darknet threat intel |

**Execution Tiers:**
| Tier | Timeout | Modules | Duration |
|------|---------|---------|----------|
| FAST < 5s | HSTS, CSP, Cookies, TLS/SSL | 4 modules ~5s |
| MEDIUM < 15s | GDPR, PCI DSS, OWASP | 15 modules ~15s |
| DEEP < 30s | Full security audit | 25+ modules ~30s |

**Frontend Integration:** ⚠️ PARTIAL
- Basic security shown in `SecurityPanel.tsx`
- Full CWE/CVSS details NOT fully exposed in UI

---

## 3. ANALYSIS MODULES

### 3.1 Core Analysis Modules (`veritas/analysis/`)

| Module | File | Input | Output | Frontend |
|--------|------|-------|--------|----------|
| DOM Analyzer | `dom_analyzer.py` | HTML string | DOM metadata, structure, depth | ⚠️ Summary only |
| Form Validator | `form_validator.py` | Form elements | HTTPS check, autocomplete, validation | ❌ Not shown |
| JS Analyzer | `js_analyzer.py` | JavaScript source | Behavior analysis, obfuscation, suspicious APIs | ❌ Not shown |
| Meta Analyzer | `meta_analyzer.py` | Meta tags | SEO checks, OG tags validation | ❌ Not shown |
| Pattern Matcher | `pattern_matcher.py` | Content | Textual dark pattern matches | ✅ In findings |
| Phishing Checker | `phishing_checker.py` | URL, Content | Phishing indicators, suspicious patterns | ⚠️ Part of security |
| Redirect Analyzer | `redirect_analyzer.py` | URL chain | Redirect summary, destination | ❌ Not shown |
| Security Headers | `security_headers.py` | HTTP headers | CSP, HSTS, X-Frame findings | ✅ In security panel |
| Temporal Analyzer | `temporal_analyzer.py` | Two captures | Time-based changes, timer manipulation | ✅ In vision pass |

### 3.2 Specialized Analysis Modules

| Module | Input | Output | Description |
|--------|-------|--------|-------------|
| Exploitation Advisor | Scanner output | Exploit suggestions | Post-scan advisory |
| Scenario Generator | Site data | Attack scenarios | Threat modeling |
| Form Validator | Forms | Security issues | Input validation, CSRF |

---

## 4. SECURITY MODULES

### 4.1 Security Modules Matrix

#### FAST Tier (< 5s)
| Module | CWE | Checks | Output |
|--------|-----|--------|--------|
| `tls_ssl.py` | CWE-523 | HSTS, CSP, X-Frame, X-Content | SecurityFinding[] |
| `cookies.py` | CWE-1004 | Secure, SameSite, HttpOnly | SecurityFinding[] |
| `csp.py` | CWE-829, CWE-95 | unsafe-inline, unsafe-eval | SecurityFinding[] |

#### MEDIUM Tier (< 15s)
| Module | CWE | Checks | Output |
|--------|-----|--------|--------|
| `gdpr.py` | GDPR | Cookie consent, privacy policy | SecurityFinding[] |
| `pci_dss.py` | PCI 4.0 | Form security, HTTPS, card data | SecurityFinding[] |
| `darknet.py` | Darknet | .onion detection, threat correlation | Dict |

#### OWASP Top 10 Modules
| ID | File | OWASP | CWE | Checks | Frontend |
|----|------|-------|-----|--------|----------|
| A01 | `a01_broken_access_control.py` | A01:2021 | CWE-284 | IDOR, privilege escalation | ⚠️ Partial |
| A02 | `a02_cryptographic_failures.py` | A02:2021 | CWE-327 | Weak encryption, HTTP login | ⚠️ Partial |
| A03 | `a03_injection.py` | A03:2021 | CWE-89, CWE-79 | SQL/XSS indicators | ⚠️ Partial |
| A04 | `a04_insecure_design.py` | A04:2021 | CWE-223 | Insecure patterns | ⚠️ Partial |
| A05 | `a05_security_misconfiguration.py` | A05:2021 | CWE-770 | Debug modes, defaults | ⚠️ Partial |
| A06 | `a06_vulnerable_components.py` | A06:2021 | CWE-1035 | Outdated libraries | ⚠️ Partial |
| A07 | `a07_authentication_failures.py` | A07:2021 | CWE-287 | Login security issues | ⚠️ Partial |
| A08 | `a08_data_integrity.py` | A08:2021 | CWE-345 | Data validation | ⚠️ Partial |
| A09 | `a09_logging_failures.py` | A09:2021 | CWE-201 | Error expose, logging | ⚠️ Partial |
| A10 | `a10_ssrf.py` | A10:2021 | CWE-918 | SSRF indicators | ⚠️ Partial |

---

## 5. OSINT COMPONENTS

### 5.1 OSINT Modules Matrix

| Module | File | Input | Output | Description | Frontend |
|--------|------|-------|--------|-------------|----------|
| IOC Detector | `ioc_detector.py` | Content | IOCDetectionResult | URL, Domain, IP, Email detection | ❌ Not shown |
| Attack Patterns | `attack_patterns.py` | Indicators | MITRE techniques | ATT&CK mapping | ❌ Not shown |
| CTI | `cti.py` | Page data | Threat analysis | Comprehensive threat intel | ❌ Not shown |
| Orchestrator | `orchestrator.py` | Query | OSINTOrchestration | Multi-source queries | ❌ Not shown |
| Reputation | `reputation.py` | Domain/IP | Reputation score | Domain trustworthiness | ❌ Not shown |
| Vulnerability Mapper | `vulnerability_mapper.py` | Findings | CVE mappings | Map to CVE IDs | ⚠️ Partial |

### 5.2 IOC Types Supported
- URL, Domain, IPv4, IPv6
- Email addresses
- MD5, SHA1, SHA256 hashes
- Filenames
- Onion addresses

### 5.3 OSINT Sources Implemented
| Source | File | Status |
|--------|------|--------|
| DNS Lookup | `dns_lookup.py` | ✅ Implemented |
| SSL Verify | `ssl_verify.py` | ✅ Implemented |
| WHOIS Lookup | `whois_lookup.py` | ✅ Implemented |
| URLVoid | `urlvoid.py` | ✅ Implemented |
| AbuseIPDB | `abuseipdb.py` | ✅ Implemented |
| Darknet Alpha | `darknet_alpha.py` | ✅ Implemented |
| Darknet Dream | `darknet_dream.py` | ✅ Implemented |
| Darknet Empire | `darknet_empire.py` | ✅ Implemented |
| Darknet Hansa | `darknet_hansa.py` | ✅ Implemented |
| Darknet Wallstreet | `darknet_wallstreet.py` | ✅ Implemented |
| Darknet Tor2Web | `darknet_tor2web.py` | ✅ Implemented |

---

## 6. DARKNET AUDITOR

### 6.1 Phase 12 Features

**Purpose:** Audit darknet/.onion sites for threat intelligence.

**New Components:**

| Module | File | Input | Output | Frontend |
|--------|------|-------|--------|----------|
| Onion Detector | `onion_detector.py` | Content | OnionAddressResult | ❌ Not shown |
| Threat Scraper | `threat_scraper.py` | URL | ThreatIntel | ❌ Not shown |
| Tor Client | `tor_client.py` | .onion URL | Page content | ❌ Not shown |
| Darknet Reporter | `reporter.py` | ThreatIntel | DarknetAuditReport | ❌ Not shown |
| Darknet Config | `config/darknet_rules.py` | - | Threat rules | ❌ Not used |

**Key Features:**
1. **Onion Address Detection**: Identify .onion links
2. **Threat Intelligence**: Correlate with known markets
3. **Marketplace Analysis**: Alpha, Dream, Empire, Hansa, Wallstreet
4. **Tor Integration**: Access Tor network for hidden sites
5. **Premium Category**: Darknet-specific analysis

**Frontend Integration Status:** ❌ NONE
- No UI component for darknet audits
- No visualization of threat intelligence
- No marketplace correlation display
- **This is DEAD CODE - no frontend integration exists**

---

## 7. FRONTEND INTEGRATION STATUS

### 7.1 Backend API Routes

| Route | Method | Purpose | Frontend Integration |
|-------|--------|---------|----------------------|
| `/health` | GET | Health check | ❌ Not used in UI |
| `/audit/start` | POST | Start audit | ✅ HeroSection.tsx |
| `/audit/stream/{id}` | WS | Real-time stream | ✅ useAuditStream.tsx hook |
| `/audit/{id}/status` | GET | Get audit status | ✅ Report page |
| `/audits/history` | GET | Get audit history | ❌ NO UI exists |
| `/audits/compare` | POST | Compare audits | ❌ NO UI exists |

### 7.2 WebSocket Events

| Event Type | Payload | Frontend Handler | Status |
|------------|---------|-------------------|--------|
| `phase_start` | `{phase, message, pct}` | AgentPipeline.tsx | ✅ |
| `phase_complete` | `{phase, message, pct, summary}` | AgentPipeline.tsx | ✅ |
| `phase_error` | `{phase, message, error}` | AgentPipeline + Log | ✅ |
| `finding` | `{finding}` | NarrativeFeed.tsx | ✅ |
| `screenshot` | `{url, label, index, data}` | ScreenshotCarousel, EvidencePanel | ✅ |
| `stats_update` | `{stats}` | EvidencePanel.tsx | ✅ |
| `log_entry` | `{timestamp, agent, message, level}` | ForensicLog.tsx | ✅ |
| `site_type` | `{site_type, confidence}` | NarrativeFeed.tsx | ⚠️ Shown but not prominent |
| `security_result` | `{module, result}` | SecurityPanel.tsx | ✅ |
| `audit_result` | `{result}` | CompletionOverlay, Report | ✅ |
| `audit_complete` | `{audit_id, elapsed}` | Status | ✅ |

### 7.3 Frontend Pages

| Page | Path | Purpose | Status |
|------|------|---------|--------|
| Landing | `/` | Home page with URL input | ✅ COMPLETE |
| Live Audit | `/audit/[id]` | Real-time audit view | ✅ COMPLETE |
| Report | `/report/[id]` | Audit results | ✅ COMPLETE |
| V2 | `/v2` | Alternative landing | ⚠️ EXISTS, unused |

### 7.4 Frontend Components - Status Matrix

**Landing Components:**
| Component | Status | Notes |
|-----------|--------|-------|
| HeroSection | ✅ | URL input, tier selector missing |
| SignalShowcase | ✅ | Static content |
| DarkPatternCarousel | ✅ | Static examples |
| HowItWorks | ✅ | Static content |
| SiteTypeGrid | ✅ | Static content |

**Audit Components:**
| Component | Status | Notes |
|-----------|--------|-------|
| AgentPipeline | ✅ | Phase status indicators |
| AuditHeader | ✅ | URL/status display |
| CompletionOverlay | ✅ | Success/failure overlay |
| EvidencePanel | ✅ | Screenshots + findings |
| ForensicLog | ✅ | Technical log entries |
| NarrativeFeed | ✅ | Live narrative updates |
| ScreenshotCarousel | ✅ | With highlight overlays |
| GreenFlagCelebration | ✅ | Confetti for positive audits |
| RunningLog | ✅ | Agent activity |

**Report Components:**
| Component | Status | Notes |
|-----------|--------|-------|
| ReportHeader | ✅ | Mode toggle (simple/expert) |
| TrustScoreHero | ✅ | Score + risk level |
| SignalBreakdown | ✅ | Radar chart |
| DarkPatternGrid | ✅ | Pattern findings |
| EntityDetails | ✅ | Simplified domain info |
| SecurityPanel | ✅ | Security findings |
| Recommendations | ✅ | Actionable advice |
| AuditMetadata | ✅ | Execution metadata |

**Data Display Components:**
| Component | Status | Notes |
|-----------|--------|-------|
| RiskBadge | ✅ | Risk level indicator |
| SeverityBadge | ✅ | Severity indicator |
| SignalBar | ✅ | Signal value |
| SignalRadarChart | ✅ | Multi-signal visualization |
| StatCounter | ✅ | Animated stats |
| TrustGauge | ✅ | Score gauge |

---

## 8. DEAD CODE IDENTIFICATION

### 8.1 Backend Features Without Frontend Integration

| Backend Feature | Location | Integration Status | Priority |
|-----------------|----------|---------------------|----------|
| **Audit History** | `GET /api/audits/history` | ❌ NO UI | HIGH |
| **Audit Comparison** | `POST /api/audits/compare` | ❌ NO UI | HIGH |
| **Audit Tier Selector** | `POST /api/audit/start` | ⚠️ NOT ON LANDING PAGE | MEDIUM |
| **Security Module Selection** | `security_modules` param | ❌ NO UI | MEDIUM |
| **Verdict Mode Toggle (at start)** | `verdict_mode` param | ⚠️ ONLY in report view | MEDIUM |
| **Temporal Analysis Comparison** | Scout temporal data | ❌ NO COMPARISON UI | MEDIUM |
| **Darknet Detection** | Fully implemented | ⚠️ SHOWN IN SECURITY ONLY | MEDIUM |
| **MITRE ATT&CK Visualization** | Mapped in backend | ❌ NO UI | LOW |
| **CVE/CVSS Details** | CWERegistry module | ⚠️ IN EXPERT MODE ONLY | LOW |
| **Entity Verification Details** | Full Graph results | ⚠️ SIMPLIFIED | MEDIUM |
| **IOC Indicators** | OSINT module fully functional | ❌ NO DEDICATED PANEL | LOW |
| **Reputation Scores** | Reputation module | ❌ NO DISPLAY | LOW |
| **Threat Attribution** | CTI module | ❌ NO UI | LOW |
| **Knowledge Graph Visualization** | NetworkX graph | ❌ NO VISUALIZATION | LOW |
| **Attack Pattern Display** | MITRE mapping | ❌ NO UI | LOW |
| **Darknet Marketplace Data** | Phase 12 features | ❌ NO UI | HIGH (if using phase 12) |

### 8.2 Frontend Components Not Connected

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| `/v2` page | `app/v2/page.tsx` | ⚠️ EXISTS | Unused alternative landing |

### 8.3 Analysis Modules Not Shown

These backend modules exist but have NO frontend display:
- DOM Analyzer detailed results
- Form Validator results
- JS Analyzer findings
- Meta Analyzer findings
- Redirect Analyzer chain visualization
- Exploitation Advisor output
- Scenario Generator output

### 8.4 Dead Code Summary

**Critical Dead Code** (Backend working, no frontend):
1. Phase 12 Darknet Auditor - COMPLETELY MISSING FROM UI
2. Audit History API - Working but no page to view history
3. Audit Comparison API - Working but no comparison UI

**High Priority Missing UI**:
1. Tier selector on landing page
2. Security module selection interface
3. OSINT indicator display panel

---

## 9. INTEGRATION PLAN

### 9.1 Phase 1: Critical Frontend UI Additions

**Priority: HIGH**

1. **Audit History Page** (`/history`)
   - Create `src/app/history/page.tsx`
   - Fetch from `GET /api/audits/history`
   - Display table of past audits
   - Filter by status, risk level
   - Click to view full report

2. **Audit Comparison UI**
   - Create `src/app/compare/[ids]/page.tsx`
   - Allow selecting multiple audits
   - Display delta visualization
   - Show trust score changes over time

3. **Tier Selector on Landing Page**
   - Add dropdown to HeroSection.tsx
   - Options: quick, standard, deep
   - Show estimated duration/cost for each

4. **Security Module Selection**
   - Add module picker to landing/audit start
   - Checkboxes for individual modules
   - Presets: FAST, MEDIUM, DEEP

5. **Darknet Auditor UI** (if using Phase 12)
   - Dedicated darknet audit mode
   - Threat intelligence visualization
   - Marketplace correlation display

### 9.2 Phase 2: Enhanced Visualization

**Priority: MEDIUM**

1. **IOC Indicators Panel**
   - New component for OSINT findings
   - Icons per IOC type (URL, IP, Email, Hash)
   - Threat level coloring

2. **Knowledge Graph Visualization**
   - Use viz.js or Cytoscape.js
   - Show entity relationships
   - Interactive exploration

3. **MITRE ATT&CK Matrix**
   - ATT&CK Navigator integration
   - Highlight detected techniques
   - Threat severity mapping

4. **Entity Verification Details**
   - Expand EntityDetails.tsx
   - Show full verification results
   - Confidence indicators for each claim

### 9.3 Phase 3: Advanced Features

**Priority: LOW**

1. **Reputation Score Display**
   - Visual score gauge for domains
   - Historical reputation trends

2. **Threat Attribution Panel**
   - Show CTI attribution data
   - Actor grouping and relationships

3. **Temporal Comparison View**
   - Side-by-side screenshot comparison
   - Highlighted changes between snapshots

---

## 10. TESTING PLAN - PLAYWRIGHT MCP

### 10.1 Test Scenarios

**Use Playwright MCP to test:**

#### Test 1: Complete Audit Flow
```
1. Navigate to http://localhost:3000
2. Enter test URL (safe site example: wikipedia.org)
3. Click "Start Audit"
4. Verify redirect to /audit/[id]
5. Watch WebSocket events stream
6. Verify all 5 phases complete
7. Verify completion overlay appears
8. Click "View Report"
9. Verify report page displays all data
```

#### Test 2: Dark Pattern Detection
```
1. Use a test site with known dark patterns
2. Run audit
3. Verify Vision Agent detects patterns
4. Verify findings appear in NarrativeFeed
5. Verify screenshot highlights work
```

#### Test 3: Security Analysis
```
1. Use site with known security issues
2. Verify SecurityAgent runs
3. Check SecurityPanel displays findings
4. Verify CWE/CVSS data in expert mode
```

#### Test 4: Audit History
```
1. Run multiple audits
2. Navigate to /history
3. Verify audit list displays
4. Test filters
5. Click audit to view report
```

#### Test 5: Audit Comparison
```
1. Run audit of same URL twice (different times)
2. Navigate to compare with both IDs
3. Verify delta display
4. Check score changes
```

### 10.2 Test Sites for Different Categories

| Site Type | Test URL | Expected Behavior |
|-----------|----------|-------------------|
| Trusted | wikipedia.org | High trust score, green flags |
| E-commerce | amazon.com | Some patterns, moderate score |
| News | cnn.com | Moderate-high score |
| Suspicious | Known scam site | Low score, many findings |
| Darknet | .onion address (if available) | Threat intelligence data |

### 10.3 Expected Test Results

**Minimum Success Criteria:**
- All 5 agents complete without errors
- WebSocket events stream correctly
- Screenshots display with highlights
- Report page shows all findings
- Trust score calculated correctly
- No 500 errors in network tab

---

## 11. PHASE STATUS OVERVIEW

### 11.1 Implementation Phase Status

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 1 | IPC Communication Stabilization | ✅ COMPLETE | 5 sub-phases done |
| 2 | Agent Architecture Refactor | ✅ COMPLETE | 5 sub-phases done |
| 3 | LangGraph State Machine | ✅ COMPLETE | Investigation completed |
| 4 | Stub Cleanup | ✅ COMPLETE | Code quality improved |
| 5 | Persistent Audit Storage | ✅ COMPLETE | DB with SQLite |
| 6 | Vision Agent Enhancement | ✅ COMPLETE | Multi-pass analysis |
| 7 | Scout Navigation Quality | ✅ COMPLETE | Link exploration |
| 8 | OSINT/CTI Integration | ✅ COMPLETE | Full OSINT pipeline |
| 9 | Judge Orchestraor | ✅ COMPLETE | Dual verdict mode |
| 10 | Cybersecurity Deep Dive | ✅ COMPLETE | 25+ security modules |
| 11 | Agent Theater Showcase | ✅ COMPLETE | Personality system, green flags |
| 12 | Darknet Auditor | ✅ BACKEND COMPLETE | ❌ NO FRONTEND UI |

### 11.2 Backend vs Frontend Status

| Component | Backend | Frontend | Gap |
|-----------|---------|----------|-----|
| Core Agents | ✅ | ✅ | None |
| Vision Multi-pass | ✅ | ✅ | None |
| Security Modules | ✅ | ⚠️ | Partial (basic only) |
| OSINT Pipeline | ✅ | ❌ | Complete (no UI) |
| Judge System | ✅ | ✅ | None |
| Darknet Auditor | ✅ | ❌ | Complete (no UI) |
| Audit History | ✅ | ❌ | Complete (no UI) |
| Audit Comparison | ✅ | ❌ | Complete (no UI) |

---

## 12. SUMMARY AND RECOMMENDATIONS

### 12.1 Key Findings

1. **Backend is feature-complete** - All 12 phases implemented in Python
2. **Frontend covers core flow** - Landing → Audit → Report working
3. **Significant UI gaps exist** - Many backend features have no UI
4. **Dead Code** - Phase 12 Darknet Auditor completely missing from UI

### 12.2 Critical Missing Features (In Priority Order)

1. **Audit History Page** - Users cannot see past audits
2. **Audit Comparison** - Cannot detect changes over time
3. **Tier Selector** - Users cannot choose audit depth
4. **Darknet UI** - Darknet features completely unused
5. **OSINT Display** - Threat intelligence hidden
6. **Graph Visualization** - No entity relationship view

### 12.3 Recommended Action Plan

**Immediate (This Session):**
1. Test current flow with Playwright MCP
2. Identify any bugs in existing integration
3. Document any issues found

**Short Term (Next Development):**
1. Implement Audit History page
2. Add Audit Comparison UI
3. Add tier selector to landing page

**Medium Term:**
1. Create Darknet Auditor UI page
2. Add OSINT indicators panel
3. Implement graph visualization

**Long Term:**
1. Enterprise features (user auth, org dashboards)
2. API-only headless mode
3. Mobile app development

---

*Analysis Date: 2026-03-05*
*Total Backend Modules: 100+*
*Frontend Components: 25*
*Integration Gap: ~40% of backend features missing from UI*
