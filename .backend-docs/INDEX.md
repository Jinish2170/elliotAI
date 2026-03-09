# VERITAS Backend - Complete Documentation

**Version:** 2.0.0
**Last Updated:** 2026-03-08
**Status:** Production-Ready Complete Reference

---

## Overview

VERITAS (Virtual Entity Risk, Integrity, and Trust Assessment System) is an autonomous multi-modal forensic web auditing platform. This documentation provides a complete, production-grade reference for all backend functionality, events, data types, and file purposes.

---

## Documentation Structure

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Overall backend architecture, components, and data flow |
| [EVENTS.md](./EVENTS.md) | Complete WebSocket event reference (45+ events) |
| [DATA_TYPES.md](./DATA_TYPES.md) | All data types and their interfaces |
| [AGENTS.md](./AGENTS.md) | 5 AI Agents: Scout, Security, Vision, Graph, Judge |
| [ROUTES.md](./ROUTES.md) | REST API endpoints and WebSocket routes |
| [SERVICES.md](./SERVICES.md) | Core services and their purposes |
| [FILES_REFERENCE.md](./FILES_REFERENCE.md) | Detailed file-by-file reference with purposes |
| [AUDIT_FLOW.md](./AUDIT_FLOW.md) | Complete audit execution flow |

---

## Quick Reference

### WebSocket Events (45+ Total)

See [EVENTS.md](./EVENTS.md) for complete reference.

**Phase Events:**
- `phase_start`, `phase_complete`, `phase_error`
- `agent_personality` (working/complete contexts)
- `log_entry`

**Audit Events:**
- `audit_complete`, `audit_error`, `audit_result`
- `screenshot`, `stats_update`
- `site_type`, `security_result`, `green_flags`
- `finding` (dark patterns, temporal findings)

**Vision Agent Events:**
- `vision_pass_start`, `vision_pass_complete`, `vision_pass_findings`
- `dark_pattern_finding`, `temporal_finding`

**Graph Agent Events:**
- `knowledge_graph`, `graph_analysis`
- `entity_claim`, `verification_result`
- `domain_intel`, `graph_inconsistency`

**Security Agent Events:**
- `owasp_module_result`, `security_module_result`

**OSINT/CTI Events:**
- `osint_result`, `darknet_threat`, `ioc_indicator`, `ioc_detection_complete`
- `marketplace_threat`, `exit_scam_detected`, `tor2web_anonymous_breach`

**CVSS/CVE Events:**
- `cvss_metric`, `cvss_metrics` (complete collection)
- `cve_detected`

**MITRE ATT&CK Events:**
- `mitre_technique_mapped`, `threat_attribution`, `attack_pattern_detected`
- `apt_group_attribution`

**Exploitation Events:**
- `exploitation_advisory`, `attack_scenario`

**Judge Agent Events:**
- `verdict_technical`, `verdict_nontechnical`, `dual_verdict_complete`

**Navigation/Scout Events:**
- `navigation_start`, `navigation_complete`, `page_scanned`, `scroll_event`
- `exploration_path`, `captcha_result`, `form_detected`

**Performance Events:**
- `agent_performance`
- `site_classification`, `business_entity_verified`

---

## Core Components

### 1. FastAPI Application (`backend/main.py`)
- CORS middleware configuration
- Route registration
- Lifespan management (database initialization)
- Entry point: `uvicorn main:app`

### 2. Routes (`backend/routes/`)
- `health.py` - Health check endpoint
- `audit.py` - Audit start, WebSocket streaming, status, history, comparison

### 3. Services (`backend/services/`)
- `audit_runner.py` - Audit orchestration and WebSocket event streaming

### 4. Veritas Package (`veritas/`)

#### Agents (`veritas/agents/`)
- `scout.py` - Web navigation and page analysis
- `scout_nav/` - Scout navigation modules
- `vision.py` - VLM-based visual analysis (5 passes)
- `vision/temporal_analysis.py` - Temporal pattern detection
- `graph_investigator.py` - Knowledge graph construction
- `security_agent.py` - Security vulnerability scanning
- `judge.py` - Expert decision making (dual verdict)
- `judge/strategies/` - 11+ specialized site type strategies

#### Analysis (`veritas/analysis/`)
- `pattern_matcher.py` - Dark pattern detection
- `js_analyzer.py` - JavaScript code analysis
- `phishing_checker.py` - Phishing URL detection
- `form_validator.py` - Form security analysis
- `security/` - Security analysis modules
  - `owasp/` - OWASP Top 10 modules (A01-A10)
  - `darknet.py` - Darknet marketplace analysis
  - `cookies.py`, `csp.py`, `tls_ssl.py` - Security checks
- `scenario_generator.py` - Attack scenario construction

#### OSINT/CTI (`veritas/osint/`)
- `orchestrator.py` - OSINT query orchestration
- `ioc_detector.py` - Indicator of compromise detection
- `cti.py` - Cyber threat intelligence
- `sources/` - 15+ OSINT data sources
  - `abuseipdb.py`, `urlvoid.py`
  - `darknet_*.py` - 6 marketplace monitors
  - `dns_lookup.py`, `whois_lookup.py`
- `attack_patterns.py` - MITRE ATT&CK integration

#### CWE/CVSS (`veritas/cwe/`)
- `cvss_calculator.py` - CVSS v4.0 scoring
- `registry.py` - CVE/CWE database

#### Configuration (`veritas/config/`)
- `settings.py` - Application settings
- `security_rules.py` - Security check rules
- `dark_patterns.py` - Dark pattern definitions
- `site_types.py` - Site type classifications
- `trust_weights.py` - Trust scoring weights

#### Database (`veritas/db/`)
- `models.py` - SQLAlchemy ORM models
- `repositories.py` - Data access layer
- `init_database.py` - Database initialization

#### Darknet (`veritas/darknet/`)
- `onion_detector.py` - .onion domain detection
- `tor_client.py` - Tor network client
- `threat_scraper.py` - Darknet threat scraping

#### Screenshots (`veritas/screenshots/`)
- `storage.py` - Screenshot file system storage

#### Core (`veritas/core/`)
- `ipc.py` - Inter-process communication
- `prompting.py` - VLM prompt templates

---

## Tiers and Features

### Audit Tiers
- `standard_audit` - Basic URL analysis
- `premium_audit` - Advanced security analysis
- `enterprise_audit` - Full audit suite
- `darknet_audit` - Darknet marketplace monitoring

### Premium Darknet Categories ($0-$999)
- `onion_detection` (Standard - Free)
- `marketplace_monitoring` (Premium - $99)
- `credential_leak_check` (Premium - $149)
- `phishing_kit_detection` (Darknet Premium - $499)
- `exit_scam_tracking` (Darknet Premium - $599)
- `attribution_engine` (Darknet Premium - $999)

---

## Data Flow

```
Frontend Request
    ↓
FastAPI Routes (POST /api/audit/start)
    ↓
WebSocket Connection (WS /api/audit/stream/{id})
    ↓
AuditRunner (orchestrator wrapper)
    ↓
VeritasOrchestrator (main logic)
    ↓
├── Scout Agent (navigation, page analysis)
├── Vision Agent (VLM visual analysis, 5 passes)
├── Security Agent (OWASP, TLS, etc.)
├── Graph Agent (knowledge graph, OSINT)
└── Judge Agent (dual verdict: technical + non-technical)
    ↓
ProgressEvent → AuditRunner
    ↓
WebSocket Events → Frontend (Zustand Store)
```

---

## WebSocket Event Format

All events follow this structure:

```json
{
  "type": "event_name",
  "timestamp": "HH:MM:SS",
  // ... event-specific fields
}
```

---

## Database Schema

### Tables
- `audits` - Audit records (id, url, status, trust_score, etc.)
- `audit_findings` - Dark pattern findings
- `audit_screenshots` - Screenshot metadata

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_DB_PERSISTENCE` | Enable database persistence | `false` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite+sqlite3:///./veritas.db` |
| `VLM_API_KEY` | Vision Language Model API key | Required |
| `OSINT_API_KEY_ABUSEIPDB` | AbuseIPDB API key | Optional |
| `OSINT_API_KEY_URLVOID` | URLVoid API key | Optional |

---

## Integration Points

### Frontend
- **Host:** Next.js frontend on port 3000 (default)
- **Protocol:** WebSocket (ws:// or wss://)
- **State Management:** Zustand store
- **Event Handling:** `processSingleEvent()` in `store.ts`

### External Services
- **VLM:** Vision Language Model API (screenshot analysis)
- **AbuseIPDB:** IP reputation database
- **URLVoid:** URL reputation service
- **DNS/WHOIS:** Domain information queries
- **Tor Network:** Darknet access via SOCKS5 proxy

---

## Development

### Running Backend
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
cd backend
python -m pytest tests/
```

### Adding New Events
1. Define event handler in `frontend/src/lib/store.ts`
2. Add TypeScript type in `frontend/src/lib/types.ts`
3. Emit event in `backend/services/audit_runner.py`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-03-08 | Complete production reference, all 45+ events documented |
| 1.0.0 | Initial release | Basic audit functionality |

---

## Support

For issues or questions, refer to the specific documentation file or contact the development team.

---

**End of Index**
