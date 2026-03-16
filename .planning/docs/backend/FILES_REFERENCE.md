# VERITAS Backend - Files Reference

**Version:** 2.0.0
**Last Updated:** 2026-03-08

---

## Overview

This document provides a detailed reference for all files in the backend with their purpose and reason for existence.

---

## File Organization

```
backend/
├── main.py                  # FastAPI application entry point
├── __init__.py
├── routes/
│   ├── __init__.py
│   ├── health.py             # Health check endpoint
│   └── audit.py              # Audit routes and WebSocket streaming
├── services/
│   ├── __init__.py
│   └── audit_runner.py       # Audit orchestration and WebSocket events
├── tests/
│   ├── __init__.py
│   ├── test_audit_persistence.py
│   └── test_audit_runner_queue.py
└── test_imports.py

veritas/
├── .env                      # Environment variables
├── core/
│   ├── ipc.py                # Inter-process communication
│   └── prompting.py          # VLM prompt templates
├── agents/
│   ├── __init__.py
│   ├── scout.py              # Web navigation agent
│   ├── scout_nav/            # Scout navigation submodules
│   │   ├── __init__.py
│   │   ├── lazy_load_detector.py
│   │   ├── link_explorer.py
│   │   └── scroll_orchestrator.py
│   ├── vision.py             # VLM visual analysis agent
│   ├── vision/
│   │   ├── __init__.py
│   │   └── temporal_analysis.py
│   ├── graph_investigator.py # Knowledge graph and OSINT agent
│   ├── security_agent.py     # Security vulnerability scanning agent
│   ├── judge.py              # Expert verdict agent
│   └── judge/
│       ├── strategies/       # Site-specific verdict strategies
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── company_portfolio.py
│       │   ├── darknet_suspicious.py
│       │   ├── ecommerce.py
│       │   ├── education.py
│       │   ├── financial.py
│       │   ├── gaming.py
│       │   ├── government.py
│       │   ├── healthcare.py
│       │   ├── news_blog.py
│       │   ├── saas_subscription.py
│       │   └── social_media.py
│       └── verdict/
│           ├── __init__.py
│           └── base.py
├── analysis/
│   ├── __init__.py
│   ├── dom_analyzer.py       # DOM structure analysis
│   ├── exploitation_advisor.py
│   ├── form_validator.py     # Form security validation
│   ├── js_analyzer.py        # JavaScript code analysis
│   ├── meta_analyzer.py      # HTML metadata analysis
│   ├── pattern_matcher.py    # Dark pattern detection
│   ├── phishing_checker.py   # Phishing URL detection
│   ├── redirect_analyzer.py  # Redirect chain analysis
│   ├── scenario_generator.py # Attack scenario construction
│   ├── security/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── cookies.py
│   │   ├── csp.py
│   │   ├── darknet.py
│   │   ├── gdpr.py
│   │   ├── owasp/
│   │   │   ├── __init__.py
│   │   │   ├── a01_broken_access_control.py
│   │   │   ├── a02_cryptographic_failures.py
│   │   │   ├── a03_injection.py
│   │   │   ├── a04_insecure_design.py
│   │   │   ├── a05_security_misconfiguration.py
│   │   │   ├── a06_vulnerable_components.py
│   │   │   ├── a07_authentication_failures.py
│   │   │   ├── a08_data_integrity.py
│   │   │   ├── a09_logging_failures.py
│   │   │   ├── a10_ssrf.py
│   │   │   └── __init__.py
│   │   ├── pci_dss.py
│   │   ├── tls_ssl.py
│   │   └── utils.py
│   ├── security_headers.py
│   └── temporal_analyzer.py
├── cwe/
│   ├── __init__.py
│   ├── cvss_calculator.py    # CVSS v4.0 scoring
│   └── registry.py           # CVE/CWE database
├── config/
│   ├── __init__.py
│   ├── dark_patterns.py      # Dark pattern definitions
│   ├── darknet_rules.py      # Darknet monitoring rules
│   ├── security_rules.py     # Security check rules
│   ├── settings.py           # Application settings
│   ├── site_types.py         # Site type definitions
│   └── trust_weights.py      # Trust scoring weights
├── darknet/
│   ├── __init__.py
│   ├── onion_detector.py     # .onion domain detection
│   ├── threat_scraper.py     # Darknet threat scraping
│   └── tor_client.py         # Tor network client
├── db/
│   ├── __init__.py
│   ├── config.py             # Database configuration
│   ├── models.py             # SQLAlchemy ORM models
│   └── repositories.py       # Data access layer
├── osint/
│   ├── __init__.py
│   ├── attack_patterns.py    # MITRE ATT&CK integration
│   ├── cache.py              # OSINT result caching
│   ├── cti.py                # Cyber threat intelligence
│   ├── ioc_detector.py       # Indicator of compromise detection
│   ├── orchestrator.py       # OSINT query orchestration
│   ├── reputation.py         # Reputation aggregation
│   ├── types.py              # OSINT data types
│   └── sources/
│       ├── __init__.py
│       ├── abuseipdb.py
│       ├── base.py
│       ├── darknet_alpha.py
│       ├── darknet_dream.py
│       ├── darknet_empire.py
│       ├── darknet_hansa.py
│       ├── darknet_tor2web.py
│       ├── darknet_wallstreet.py
│       ├── dns_lookup.py
│       ├── ssl_verify.py
│       ├── urlvoid.py
│       └── whois_lookup.py
├── screenshots/
│   ├── __init__.py
│   └── storage.py            # Screenshot filesystem storage
└── (other files)
```

---

## Detailed File Reference

### Backend Root (`backend/`)

#### main.py
**Purpose:** FastAPI application entry point

**Why Needed:** Provides the WSGI application that serves the REST API and WebSocket endpoints.

**Key Functions:**
- `lifespan()` - Application startup/shutdown lifecycle
- `app.add_middleware(CORSMiddleware)` - CORS configuration
- Route registration (`/api/health`, `/api/audit`)

---

### Routes (`backend/routes/`)

#### health.py
**Purpose:** Health check endpoint

**Why Needed:** Allows monitoring and health checks to verify the service is running.

**Endpoints:**
- `GET /api/health` - Returns status "ok"

---

#### audit.py
**Purpose:** Audit routes and WebSocket streaming

**Why Needed:** Defines all audit-related API endpoints: start audit, WebSocket stream, status, history, comparison.

**Key Components:**
- `AuditStartRequest` - Pydantic model for starting audits
- `start_audit()` - Create audit and return audit_id + WebSocket URL
- `stream_audit()` - WebSocket endpoint for real-time audit streaming
- `audit_status()` - Get audit status from database or in-memory store
- `get_audit_history()` - Paginated audit history with filters
- `compare_audits()` - Compare multiple audits for changes
- `on_audit_started()` - Database event: create audit record
- `on_audit_completed()` - Database event: update with results
- `on_audit_error()` - Database event: record error
- `_handle_screenshot_event()` - Database event: screenshot persistence

---

### Services (`backend/services/`)

#### audit_runner.py
**Purpose:** Audit orchestration and WebSocket event streaming

**Why Needed:** Wraps the VeritasOrchestrator to convert progress markers into structured WebSocket events for the frontend. Handles subprocess execution for Windows compatibility.

**Key Classes:**
- `AuditRunner` - Runs audit in subprocess, streams events via callback

**Key Methods:**
- `run()` - Execute audit and stream events
- `_determine_ipc_mode()` - Choose Queue or Stdout IPC
- `_read_queue_and_stream()` - Read events from Queue
- `_get_cve_severity_value()` - Severity to numeric conversion
- `_generate_exploitation_advisories()` - Generate remediation guidance
- `_generate_attack_scenarios()` - Construct attack scenarios
- `_calculate_agent_performance()` - Performance metrics
- `_has_graph_data()` - Check for graph data
- `_construct_knowledge_graph()` - Build knowledge graph
- `_calculate_graph_analysis()` - Graph metrics

**Events Emitted:** 45+ WebSocket events (see [EVENTS.md](./EVENTS.md))

---

### Database (`veritas/db/`)

#### config.py
**Purpose:** Database configuration

**Why Needed:** Centralizes database URL, session management, and async engine setup.

---

#### models.py
**Purpose:** SQLAlchemy ORM models

**Why Needed:** Defines database schema for persistence.

**Models:**
- `Audit` - Main audit record
- `AuditFinding` - Dark pattern findings
- `AuditScreenshot` - Screenshot metadata
- `AuditStatus` - Enum for audit status

---

#### repositories.py
**Purpose:** Data access layer

**Why Needed:** Provides clean interface for database operations, abstracting away SQLAlchemy details.

**Class:** `AuditRepository`
- `get_by_id()` - Retrieve audit by ID
- `create()` - Create new audit
- `update()` - Update existing audit
- `list_audits()` - List audits with pagination and filters

---

### Agents (`veritas/agents/`)

#### scout.py
**Purpose:** Web navigation and page analysis

**Why Needed:** Performs initial exploration, captures screenshots, extracts metadata, handles CAPTCHAs and redirects.

**Key Functions:**
- Navigate to URLs
- Handle redirect chains
- Detect lazy-load content
- Extract page metadata
- Take screenshots
- Detect forms

---

#### scout_nav/ (Scout Navigation Submodules)
##### lazy_load_detector.py
**Purpose:** Detect lazy-loading patterns

**Why Needed:** Identifies when content loads on scroll, ensuring complete page analysis.

---

##### scroll_orchestrator.py
**Purpose:** Manage page scrolling for lazy content

**Why Needed:** Orchestrates progressive scrolling to trigger lazy-loaded content.

---

##### link_explorer.py
**Purpose:** Discover and analyze page links

**Why Needed:** Maps site structure for navigation and exploration.

---

#### vision.py
**Purpose:** VLM visual analysis

**Why Needed:** Uses Vision Language Model to detect dark patterns, UI deception, and temporal changes in screenshots.

**Key Functions:**
- Run 5 analysis passes
- Detect dark patterns
- Analyze temporal changes
- Generate bilingual descriptions

---

#### vision/temporal_analysis.py
**Purpose:** Temporal pattern detection

**Why Needed:** Compares screenshots over time to detect changes in prices, availability, etc.

---

#### graph_investigator.py
**Purpose:** Knowledge graph construction and OSINT

**Why Needed:** Builds knowledge graph from all findings, performs OSINT queries, verifies entity claims.

**Key Functions:**
- Build graph from results
- Query OSINT sources
- Verify claims
- Detect inconsistencies
- Map to MITRE ATT&CK

---

#### security_agent.py
**Purpose:** Security vulnerability scanning

**Why Needed:** Performs comprehensive security checks including OWASP Top 10, TLS/SSL, headers.

**Key Functions:**
- Check TLS/SSL certificates
- Analyze security headers
- Scan for OWASP vulnerabilities
- Check cookies and CSP
- Generate advisories

---

#### judge.py
**Purpose:** Expert verdict synthesis

**Why Needed:** Combines all agent findings into technical and non-technical verdicts with trust scoring.

**Key Functions:**
- Synthesize findings
- Calculate trust score
- Generate technical verdict
- Generate non-technical verdict
- Provide recommendations

---

#### judge/strategies/ (Site-Specific Verdict Strategies)
**Purpose:** Specialized verdict logic for different site types

**Why Needed:** Different site types have different evaluation criteria and patterns.

| File | Site Type | Specialization |
|------|-----------|---------------|
| `ecommerce.py` | E-commerce | Checkout flow analysis, price manipulation |
| `social_media.py` | Social media | Privacy settings, data collection |
| `news_blog.py` | News/Blog | Source verification, fake news detection |
| `saas_subscription.py` | SaaS | Pricing transparency, dark patterns |
| `gaming.py` | Gaming | Loot box mechanics, RNG analysis |
| `financial.py` | Financial | Security, regulatory compliance |
| `healthcare.py` | Healthcare | HIPAA compliance, medical info |
| `government.py` | Government | Official domain verification |
| `education.py` | Education | Accreditation, content quality |
| `company_portfolio.py` | Corporate | Business entity verification |
| `darknet_suspicious.py` | Darknet | Marketplace identification, threat detection |

---

### Analysis (`veritas/analysis/`)

#### pattern_matcher.py
**Purpose:** Dark pattern detection

**Why Needed:** Identifies manipulative UI patterns (confirmshaming, countdowns, hidden costs).

---

#### js_analyzer.py
**Purpose:** JavaScript code analysis

**Why Needed:** Detects tracking beacons, suspicious code patterns in JavaScript.

---

#### phishing_checker.py
**Purpose:** Phishing URL detection

**Why Needed:** Identifies typosquatting, suspicious TLDs, known phishing patterns.

---

#### form_validator.py
**Purpose:** Form security validation

**Why Needed:** Checks for CSRF protection, input validation, security attributes.

---

#### security/ (Security Analysis Modules)
##### owasp/ (OWASP Top 10 Modules)
**Purpose:** OWASP Top 10 vulnerability scanners

**Why Needed:** Comprehensive security scanning against industry-standard vulnerability categories.

| File | OWASP Category |
|------|----------------|
| `a01_broken_access_control.py` | A01 - Broken Access Control |
| `a02_cryptographic_failures.py` | A02 - Cryptographic Failures |
| `a03_injection.py` | A03 - Injection |
| `a04_insecure_design.py` | A04 - Insecure Design |
| `a05_security_misconfiguration.py` | A05 - Security Misconfiguration |
| `a06_vulnerable_components.py` | A06 - Vulnerable Components |
| `a07_authentication_failures.py` | A07 - Authentication Failures |
| `a08_data_integrity.py` | A08 - Software and Data Integrity |
| `a09_logging_failures.py` | A09 - Logging Failures |
| `a10_ssrf.py` | A10 - Server-Side Request Forgery |

##### cookies.py
**Purpose:** Cookie security analysis

**Why Needed:** Checks for HttpOnly, Secure, SameSite attributes.

---

##### csp.py
**Purpose:** Content Security Policy analysis

**Why Needed:** Validates CSP headers and detects policies.

---

##### darknet.py
**Purpose:** Darknet marketplace analysis

**Why Needed:** Checks for darknet marketplace threats and exit scams.

---

##### gdpr.py
**Purpose:** GDPR compliance check

**Why Needed:** Identifies GDPR compliance indicators and privacy policies.

---

##### tls_ssl.py
**Purpose:** TLS/SSL validation

**Why Needed:** Checks certificate validity, TLS version, cipher suite strength.

---

#### exploitation_advisor.py
**Purpose:** Generate exploitation advisories

**Why Needed:** Provides detailed remediation guidance for vulnerabilities.

---

#### scenario_generator.py
**Purpose:** Construct attack scenarios

**Why Needed:** Chains vulnerabilities into realistic attack paths.

---

### CWE/CVSS (`veritas/cwe/`)

#### cvss_calculator.py
**Purpose:** CVSS v4.0 scoring

**Why Needed:** Calculates CVSS scores for vulnerabilities with metric breakdown.

---

#### registry.py
**Purpose:** CVE/CWE database

**Why Needed:** Provides access to CVE and CWE database for vulnerability mapping.

---

### OSINT (`veritas/osint/`)

#### orchestrator.py
**Purpose:** OSINT query orchestration

**Why Needed:** Coordinates queries across multiple OSINT sources.

---

#### ioc_detector.py
**Purpose:** Indicator of compromise detection

**Why Needed:** Extracts and validates IOCs (IPs, domains, emails, etc.).

---

#### cti.py
**Purpose:** Cyber threat intelligence

**Why Needed:** Provides threat actor attribution and APT group information.

---

#### attack_patterns.py
**Purpose:** MITRE ATT&CK integration

**Why Needed:** Maps findings to MITRE ATT&CK techniques for threat attribution.

---

#### sources/ (OSINT Data Sources)
**Purpose:** Individual OSINT data providers

**Why Needed:** Each source provides specialized threat intelligence.

| File | Source | Purpose |
|------|--------|---------|
| `abuseipdb.py` | AbuseIPDB | IP reputation database |
| `urlvoid.py` | URLVoid | URL reputation service |
| `dns_lookup.py` | DNS | DNS records and DNS-based detection |
| `whois_lookup.py` | WHOIS | Domain registration data |
| `ssl_verify.py` | SSL | Certificate verification |
| `darknet_empire.py` | Empire | Empire marketplace monitor |
| `darknet_alpha.py` | AlphaBay | AlphaBay marketplace monitor |
| `darknet_dream.py` | Dream | Dream marketplace monitor |
| `darknet_hansa.py` | Hansa | Hansa marketplace monitor |
| `darknet_wallstreet.py` | WallStreet | WallStreet marketplace monitor |
| `darknet_tor2web.py` | Tor2Web | Gateway de-anonymization detection |

---

### Darknet (`veritas/darknet/`)

#### onion_detector.py
**Purpose:** .onion domain detection

**Why Needed:** Identifies Tor hidden services and darknet links.

---

#### tor_client.py
**Purpose:** Tor network client

**Why Needed:** Provides SOCKS5 proxy support for Tor network access.

---

#### threat_scraper.py
**Purpose:** Darknet threat scraping

**Why Needed:** Scrapes darknet marketplaces for threat data.

---

### Screenshots (`veritas/screenshots/`)

#### storage.py
**Purpose:** Screenshot filesystem storage

**Why Needed:** Persists screenshots to filesystem and provides metadata access.

---

### Configuration (`veritas/config/`)

#### settings.py
**Purpose:** Application settings

**Why Needed:** Centralizes environment variables and configuration.

---

#### security_rules.py
**Purpose:** Security check rules

**Why Needed:** Defines security check thresholds and rules.

---

#### dark_patterns.py
**Purpose:** Dark pattern definitions

**Why Needed:** Provides dark pattern templates and definitions.

---

#### site_types.py
**Purpose:** Site type definitions

**Why Needed:** Defines site type classifications and detection rules.

---

#### trust_weights.py
**Purpose:** Trust scoring weights

**Why Needed:** Defines trust scoring algorithm weights.

---

#### darknet_rules.py
**Purpose:** Darknet monitoring rules

**Why Needed:** Defines darknet marketplace monitoring rules and threat thresholds.

---

### Core (`veritas/core/`)

#### ipc.py
**Purpose:** Inter-process communication

**Why Needed:** Provides Queue and Stdout IPC modes for subprocess communication.

---

#### prompting.py
**Purpose:** VLM prompt templates

**Why Needed:** Provides prompt templates for VLM API calls.

---

---

**End of Files Reference**
