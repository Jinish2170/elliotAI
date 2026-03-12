# Elliot AI — Frontend API Integration Guide

> **Version**: 2.0 | **Last updated**: 2026-03-12
> **Backend**: FastAPI 0.115.0 + WebSocket streaming
> **Target audience**: Frontend developers integrating Veritas audit system

---

## Table of Contents

1. [REST Endpoints](#1-rest-endpoints)
2. [WebSocket Streaming](#2-websocket-streaming)
3. [Event Reference (All Types)](#3-event-reference)
4. [Audit Tiers](#4-audit-tiers)
5. [Event Lifecycle Flow](#5-event-lifecycle-flow)
6. [Error Handling](#6-error-handling)
7. [Frontend Integration Patterns](#7-frontend-integration-patterns)

---

## 1. REST Endpoints

### 1.1 Health Check

```
GET /api/health
```

**Response** `200 OK`
```json
{
  "status": "ok",
  "service": "veritas-api",
  "version": "2.0.0"
}
```

---

### 1.2 Start Audit

```
POST /api/audit/start
```

**Request Body**
```json
{
  "url": "https://example.com",
  "tier": "standard_audit",
  "verdict_mode": "expert",
  "security_modules": ["owasp_injection", "phishing_db"]
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `url` | string | Yes | Any valid URL |
| `tier` | string | Yes | `"quick_scan"` \| `"standard_audit"` \| `"deep_forensic"` \| `"darknet_investigation"` |
| `verdict_mode` | string | Yes | `"expert"` \| `"simple"` |
| `security_modules` | string[] | No | List of security module IDs |

**Response** `200 OK`
```json
{
  "audit_id": "vrts_a1b2c3d4",
  "status": "queued",
  "ws_url": "/api/audit/stream/vrts_a1b2c3d4"
}
```

| Status Code | Meaning |
|-------------|---------|
| 200 | Audit created |
| 400 | Invalid request body |
| 422 | Validation error (bad tier / verdict_mode) |

---

### 1.3 Get Audit Status

```
GET /api/audit/{audit_id}/status
```

**Response** `200 OK`
```json
{
  "audit_id": "vrts_a1b2c3d4",
  "status": "completed",
  "url": "https://example.com",
  "result": {
    "trust_score": 87,
    "risk_level": "low",
    "signal_scores": {
      "domain_age": 95,
      "ssl_validity": 100,
      "reputation": 82
    },
    "narrative": "This website appears to be legitimate...",
    "site_type": "ecommerce",
    "site_type_confidence": 0.95,
    "security_results": {},
    "pages_scanned": 8,
    "screenshots_count": 20,
    "elapsed_seconds": 450,
    "dark_pattern_summary": {
      "findings": [
        {
          "id": "dark_pattern_0",
          "pattern_type": "roach_motel",
          "category": "deceptive_patterns",
          "severity": "high",
          "confidence": 0.92,
          "description": "Difficult unsubscribe process found",
          "plain_english": "The website makes it hard to cancel your subscription",
          "screenshot_index": 5
        }
      ]
    }
  },
  "error": null,
  "created_at": "2026-03-12T10:30:00",
  "started_at": "2026-03-12T10:30:05",
  "completed_at": "2026-03-12T10:37:30"
}
```

**Status field values**: `"queued"` | `"running"` | `"completed"` | `"error"` | `"disconnected"`

**Risk level values**: `"critical"` | `"high"` | `"medium"` | `"low"`

| Status Code | Meaning |
|-------------|---------|
| 200 | Audit found |
| 404 | Audit ID not found |

---

### 1.4 Get Audit History

```
GET /api/audits/history?limit=20&offset=0&status_filter=completed&risk_level_filter=high
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 20 | 1–100 |
| `offset` | int | 0 | Pagination offset |
| `status_filter` | string | — | Filter by status |
| `risk_level_filter` | string | — | Filter by risk level |

**Response** `200 OK`
```json
{
  "audits": [
    {
      "audit_id": "vrts_a1b2c3d4",
      "url": "https://example.com",
      "status": "completed",
      "audit_tier": "standard_audit",
      "verdict_mode": "expert",
      "trust_score": 87,
      "risk_level": "low",
      "signal_scores": {},
      "site_type": "ecommerce",
      "site_type_confidence": 0.95,
      "pages_scanned": 8,
      "screenshots_count": 20,
      "elapsed_seconds": 450,
      "created_at": "2026-03-12T10:30:00",
      "started_at": "2026-03-12T10:30:05",
      "completed_at": "2026-03-12T10:37:30"
    }
  ],
  "count": 15,
  "limit": 20,
  "offset": 0
}
```

---

### 1.5 Compare Audits

```
POST /api/audits/compare
```

**Request Body**
```json
{
  "audit_ids": ["vrts_a1b2c3d4", "vrts_e5f6g7h8"]
}
```

**Response** `200 OK`
```json
{
  "audits": [
    {
      "audit_id": "vrts_a1b2c3d4",
      "url": "https://example.com",
      "status": "completed",
      "trust_score": 82,
      "risk_level": "medium",
      "site_type": "ecommerce",
      "created_at": "2026-03-10T10:30:00",
      "completed_at": "2026-03-10T10:37:30",
      "findings_summary": {
        "total": 5,
        "critical": 0,
        "high": 1,
        "medium": 3,
        "low": 1
      },
      "screenshots_count": 20
    }
  ],
  "trust_score_deltas": [
    {
      "from_audit_id": "vrts_a1b2c3d4",
      "to_audit_id": "vrts_e5f6g7h8",
      "delta": 5,
      "percentage_change": 6.1
    }
  ],
  "risk_level_changes": [
    {
      "from_audit_id": "vrts_a1b2c3d4",
      "to_audit_id": "vrts_e5f6g7h8",
      "from": "medium",
      "to": "low"
    }
  ]
}
```

---

## 2. WebSocket Streaming

### Connection

```
WS /api/audit/stream/{audit_id}
```

**Flow**:
1. `POST /api/audit/start` → get `ws_url`
2. Open WebSocket to `ws_url`
3. Receive JSON events until `audit_complete` or `audit_error`
4. WebSocket closes automatically on completion

**Every event has a `type` field** — use it to route events to the correct UI handler.

---

## 3. Event Reference

### 3.1 Phase Lifecycle Events

#### `phase_start`
Emitted when a phase begins. Use `pct` for progress bar.

```json
{
  "type": "phase_start",
  "phase": "scout",
  "message": "Beginning browser reconnaissance",
  "pct": 5,
  "label": "Browser Reconnaissance"
}
```

| `phase` value | `pct` range | Description |
|---------------|-------------|-------------|
| `"init"` | 0–5 | Startup & browser setup |
| `"scout"` | 5–20 | Browser navigation & screenshots |
| `"vision"` | 20–40 | Dark pattern detection |
| `"security"` | 40–60 | Security module checks |
| `"graph"` | 60–80 | OSINT & entity verification |
| `"judge"` | 80–100 | Verdict generation |

#### `phase_complete`
Emitted when a phase finishes. Includes summary data.

```json
{
  "type": "phase_complete",
  "phase": "scout",
  "message": "Scanned 8 pages, captured 20 screenshots",
  "pct": 15,
  "label": "Browser Reconnaissance",
  "summary": {
    "pages_scanned": 8,
    "screenshots_captured": 20,
    "forms_found": 3,
    "captchas_encountered": 1,
    "avg_navigation_time_ms": 1500
  }
}
```

#### `phase_error`
Non-fatal phase error. Audit may continue.

```json
{
  "type": "phase_error",
  "phase": "scout",
  "message": "Failed to connect to website",
  "pct": 15,
  "error": "Connection timeout after 30 seconds"
}
```

---

### 3.2 Agent Personality Events

#### `agent_personality`
Agent activity status — use for UI agent avatar animations.

```json
{
  "type": "agent_personality",
  "agent": "scout",
  "context": "working",
  "timestamp": "10:30:45",
  "params": {
    "phase": "scout",
    "step": "navigating",
    "detail": "Scanning page structure"
  }
}
```

| `context` | Meaning |
|-----------|---------|
| `"working"` | Agent actively processing |
| `"complete"` | Agent finished |

#### `log_entry`
Detailed log from agent. Use for activity feed / debug console.

```json
{
  "type": "log_entry",
  "timestamp": "10:30:45",
  "agent": "Browser Reconnaissance",
  "message": "Navigating to /products page",
  "level": "info"
}
```

| `level` | Meaning |
|---------|---------|
| `"info"` | Normal operation |
| `"warning"` | Degraded but continuing |
| `"error"` | Failed operation |

---

### 3.3 Scout Phase Events

#### `navigation_start`
```json
{
  "type": "navigation_start",
  "url": "https://example.com",
  "timestamp": "2026-03-12T10:30:50Z"
}
```

#### `page_scanned`
```json
{
  "type": "page_scanned",
  "url": "https://example.com",
  "page_title": "Welcome to Example",
  "navigation_time_ms": 2500,
  "timestamp": "2026-03-12T10:30:55Z"
}
```

#### `form_detected`
```json
{
  "type": "form_detected",
  "count": 2,
  "forms": [
    {
      "id": "form_0",
      "action": "/login",
      "method": "POST",
      "inputs": 3,
      "has_password": true
    }
  ],
  "timestamp": "2026-03-12T10:30:55Z"
}
```

#### `captcha_detected`
```json
{
  "type": "captcha_detected",
  "detected": true,
  "captcha_type": "challenge",
  "confidence": 1.0,
  "timestamp": "2026-03-12T10:30:56Z"
}
```

#### `navigation_complete`
```json
{
  "type": "navigation_complete",
  "url": "https://example.com",
  "status": "SUCCESS",
  "duration_ms": 2500,
  "screenshots_count": 3,
  "timestamp": "2026-03-12T10:30:57Z"
}
```

#### `exploration_path`
Summary of all visited pages. Use for breadcrumb / sitemap.

```json
{
  "type": "exploration_path",
  "base_url": "https://example.com",
  "visited_urls": [
    "https://example.com",
    "https://example.com/products",
    "https://example.com/about"
  ],
  "breadcrumbs": [
    "https://example.com",
    "https://example.com/products",
    "https://example.com/about"
  ],
  "total_pages": 3,
  "total_time_ms": 12000
}
```

#### `screenshot`
Screenshot data (base64 JPEG). Use for visual evidence gallery.

```json
{
  "type": "screenshot",
  "url": "/path/to/screenshot.png",
  "label": "Homepage",
  "index": 0,
  "data": "<base64_encoded_jpeg>"
}
```

---

### 3.4 Vision Phase Events

#### `finding`
Individual dark pattern finding.

```json
{
  "type": "finding",
  "finding": {
    "id": "dark_pattern_0",
    "category": "deceptive_patterns",
    "pattern_type": "roach_motel",
    "severity": "high",
    "confidence": 0.92,
    "description": "Difficult unsubscribe process detected",
    "plain_english": "The website makes it hard to cancel your subscription"
  }
}
```

#### `dark_pattern_finding`
Dark pattern with screenshot reference.

```json
{
  "type": "dark_pattern_finding",
  "finding": {
    "category": "deceptive_patterns",
    "pattern_type": "roach_motel",
    "severity": "high",
    "confidence": 0.92,
    "description": "Difficult unsubscribe process detected",
    "plain_english": "The website makes it hard to cancel your subscription",
    "screenshot_path": "/data/screenshots/screenshot_3.png"
  }
}
```

#### `temporal_finding`
Time-sensitive dark pattern.

```json
{
  "type": "temporal_finding",
  "finding": {
    "id": "temporal_0",
    "pattern_type": "hidden_elements",
    "category": "deceptive_patterns",
    "severity": "medium",
    "confidence": 0.85,
    "description": "Elements appear/disappear based on timing",
    "discovery_timestamp": "2026-03-12T10:31:30Z",
    "pattern_lifecycle": "hidden -> visible -> hidden"
  }
}
```

**Severity values**: `"critical"` | `"high"` | `"medium"` | `"low"`

**Dark pattern categories**:
| Category | Description |
|----------|-------------|
| `deceptive_patterns` | Tricks / misleading UI |
| `false_urgency` | Fake timers / scarcity |
| `social_engineering` | Fake social proof |
| `sneaking` | Hidden costs / preselected items |
| `forced_continuity` | Hard cancellation / roach motel |
| `obstruction` | Intentional barriers |

---

### 3.5 Security Phase Events

#### `security_result`
Raw module result.

```json
{
  "type": "security_result",
  "module": "owasp_injection",
  "result": {
    "findings": [
      {
        "type": "SQL_INJECTION",
        "severity": "critical",
        "param": "user_id",
        "endpoint": "/api/user"
      }
    ],
    "score": 0.9,
    "analysis_time_ms": 5000
  }
}
```

#### `security_module_result`
Normalized module result with recommendations.

```json
{
  "type": "security_module_result",
  "result": {
    "module_name": "owasp_injection",
    "category": "owasp",
    "findings_count": 1,
    "severity": "CRITICAL",
    "composite_score": 0.9,
    "execution_time_ms": 5000,
    "findings": [],
    "recommendations": [
      "Use parameterized queries",
      "Implement input validation"
    ]
  }
}
```

#### `darknet_analysis_result`
Darknet threat intelligence (only on `darknet_investigation` tier).

```json
{
  "type": "darknet_analysis_result",
  "result": {
    "marketplace_threats": [
      {
        "marketplace": "AlphaBay",
        "status": "exit_scam",
        "shutdown_date": "2017-07-04",
        "confidence": 0.95,
        "description": "Domain hosted on infrastructure of seized marketplace"
      }
    ],
    "tor2web_exposure": false,
    "dark_web_mentions": 2,
    "threat_score": 0.4
  }
}
```

#### `marketplace_threat`
```json
{
  "type": "marketplace_threat",
  "threat": {
    "marketplace": "AlphaBay",
    "status": "exit_scam",
    "shutdown_date": "2017-07-04",
    "confidence": 0.95
  }
}
```

#### `exit_scam_detected`
```json
{
  "type": "exit_scam_detected",
  "marketplace": "AlphaBay",
  "shutdown_date": "2017-07-04"
}
```

#### `tor2web_anonymous_breach`
```json
{
  "type": "tor2web_anonymous_breach",
  "threat": {
    "gateway_domains": ["tor2web"],
    "de_anon_risk": "high",
    "recommendation": "Use direct TOR Browser for .onion access.",
    "anonymity_breach": "TOR gateway exposure detected"
  }
}
```

---

### 3.6 Graph Phase Events

#### `osint_result`
OSINT source data.

```json
{
  "type": "osint_result",
  "result": {
    "source": "urlvoid",
    "detections": 2,
    "engines_scanned": 68,
    "reputation_score": 0.15,
    "confidence_score": 0.8
  }
}
```

#### `darknet_threat`
```json
{
  "type": "darknet_threat",
  "threat": {
    "source": "darknet_mentions_db",
    "data": {
      "mentions": 3,
      "marketplace_listings": 5,
      "last_mention_date": "2026-03-10"
    },
    "confidence": 0.75
  }
}
```

#### `ioc_indicator`
Indicator of Compromise.

```json
{
  "type": "ioc_indicator",
  "indicator": {
    "type": "ip_address",
    "value": "192.0.2.1",
    "threat_level": "medium",
    "sources": ["abuseipdb", "urlvoid"],
    "last_seen": "2026-03-12T10:30:00Z"
  }
}
```

#### `knowledge_graph`
Full entity relationship graph — render with D3.js / Cytoscape.

```json
{
  "type": "knowledge_graph",
  "graph": {
    "nodes": [
      {
        "id": "domain:example.com",
        "type": "domain",
        "label": "example.com",
        "properties": {
          "url": "example.com",
          "trust_score": 87,
          "site_type": "ecommerce"
        }
      }
    ],
    "edges": [
      {
        "source": "domain:example.com",
        "target": "scout:example.com",
        "relationship": "analyzed_by",
        "weight": 1.0
      }
    ],
    "node_count": 6,
    "edge_count": 5,
    "graph_density": 0.33,
    "avg_clustering": 0.0
  }
}
```

#### `graph_analysis`
```json
{
  "type": "graph_analysis",
  "analysis": {
    "total_nodes": 6,
    "total_edges": 5,
    "graph_sparsity": 0.67,
    "connected_components": 1
  }
}
```

---

### 3.7 Judge Phase Events

#### `site_type`
```json
{
  "type": "site_type",
  "site_type": "ecommerce",
  "confidence": 0.95
}
```

**Site type values**: `"ecommerce"` | `"news"` | `"social"` | `"government"` | `"financial"` | `"educational"` | `"corporate"` | `"blog"` | `"unknown"`

#### `green_flags`
Positive security indicators — show as trust badges.

```json
{
  "type": "green_flags",
  "flags": [
    "Valid SSL certificate from trusted CA",
    "Domain registered for 8+ years",
    "No known security vulnerabilities"
  ],
  "green_flags": [
    "Valid SSL certificate from trusted CA",
    "Domain registered for 8+ years",
    "No known security vulnerabilities"
  ]
}
```

#### `verdict_technical`
Expert-level verdict.

```json
{
  "type": "verdict_technical",
  "verdict": {
    "risk_level": "low",
    "trust_score": 87,
    "summary": "Strong security posture with valid SSL...",
    "recommendations": [
      "Continue monitoring for certificate expiration",
      "Regular security audits recommended"
    ]
  }
}
```

#### `verdict_nontechnical`
Plain-language verdict for general users.

```json
{
  "type": "verdict_nontechnical",
  "verdict": {
    "risk_level": "low",
    "summary": "This appears to be a legitimate website.",
    "actionable_advice": [
      "Safe to make purchases on this website",
      "Your data should be protected with encryption"
    ],
    "green_flags": [
      "Valid SSL certificate from trusted CA",
      "Domain registered for 8+ years"
    ]
  }
}
```

#### `dual_verdict_complete`
Combined technical + non-technical verdict.

```json
{
  "type": "dual_verdict_complete",
  "dual_verdict": {
    "verdict_technical": { "..." },
    "verdict_nontechnical": { "..." },
    "metadata": {
      "timestamp": "2026-03-12T10:37:30Z",
      "audit_id": "vrts_a1b2c3d4"
    }
  }
}
```

---

### 3.8 Statistics Events

#### `stats_update`
```json
{
  "type": "stats_update",
  "stats": {
    "pages_scanned": 8,
    "screenshots": 20,
    "findings": 5,
    "findings_detected": 5,
    "ai_calls": 45,
    "security_checks": 5,
    "elapsed_seconds": 450,
    "duration_seconds": 450
  }
}
```

#### `agent_performance`
```json
{
  "type": "agent_performance",
  "performance": {
    "agent": "scout",
    "tasks_completed": 8,
    "tasks_total": 8,
    "accuracy": 1.0,
    "processing_time_ms": 15000,
    "finding_rate": 2.5
  }
}
```

---

### 3.9 Completion Events

#### `audit_result`
Final enriched result with all data.

```json
{
  "type": "audit_result",
  "result": {
    "url": "https://example.com",
    "status": "success",
    "audit_tier": "standard_audit",
    "verdict_mode": "expert",
    "trust_score": 87,
    "risk_level": "low",
    "narrative": "This website demonstrates strong security posture...",
    "signal_scores": {
      "domain_age": 95,
      "ssl_validity": 100,
      "reputation": 82,
      "content_analysis": 78,
      "security_headers": 85
    },
    "dark_pattern_summary": {
      "findings": []
    },
    "recommendations": [],
    "security_results": {},
    "site_type": "ecommerce",
    "site_type_confidence": 0.95,
    "domain_info": {
      "age_days": 1250,
      "registrar": "GoDaddy",
      "ip": "192.0.2.1",
      "ssl_issuer": "Let's Encrypt Authority X3",
      "country": "United States",
      "inconsistencies": [],
      "entity_verified": true
    },
    "pages_scanned": 8,
    "screenshots_count": 20,
    "elapsed_seconds": 450,
    "trust_score_result": {
      "final_score": 87,
      "risk_level": "low",
      "signal_scores": {}
    },
    "dual_verdict": {
      "verdict_technical": {},
      "verdict_nontechnical": {}
    },
    "elapsed_ms": 450000
  }
}
```

#### `audit_complete`
Final signal — close WebSocket after this.

```json
{
  "type": "audit_complete",
  "audit_id": "vrts_a1b2c3d4",
  "elapsed": 450.5
}
```

#### `audit_error`
Fatal error — audit terminated.

```json
{
  "type": "audit_error",
  "audit_id": "vrts_a1b2c3d4",
  "error": "Audit finished but result JSON could not be parsed"
}
```

---

## 4. Audit Tiers

| Tier | Pages | Screenshots | AI Calls | Vision | Judge | Target Duration | Credits |
|------|-------|-------------|----------|--------|-------|-----------------|---------|
| `quick_scan` | 2 | 6 | 16 | 10 | 6 | 5 min | ~20 |
| `standard_audit` | 8 | 20 | 50 | 35 | 15 | 8 min | ~60 |
| `deep_forensic` | 15 | 40 | 100 | 75 | 25 | 12 min | ~120 |
| `darknet_investigation` | 20 | 50 | 140 | 105 | 35 | 15 min | ~180 |

**Tier-specific features:**

| Feature | quick_scan | standard_audit | deep_forensic | darknet_investigation |
|---------|-----------|----------------|---------------|----------------------|
| OSINT | ✅ | ✅ | ✅ | ✅ |
| Tavily search | ✅ | ✅ | ✅ | ✅ |
| Deep OSINT | ❌ | ❌ | ✅ | ✅ |
| Darknet intel | ❌ | ❌ | ❌ | ✅ |
| TOR routing | ❌ | ❌ | ❌ | ✅ |
| Vision passes | 2 | 4 | 6 | 8 |

---

## 5. Event Lifecycle Flow

```
POST /api/audit/start → { audit_id, ws_url }
        │
        ▼
WS connect to ws_url
        │
        ▼
┌─── INIT PHASE (0-5%) ──────────────────────┐
│  phase_start (init)                         │
│  agent_personality (init, working)          │
│  log_entry (setup messages)                 │
│  phase_complete (init)                      │
└─────────────────────────────────────────────┘
        │
        ▼
┌─── SCOUT PHASE (5-20%) ────────────────────┐
│  phase_start (scout)                        │
│  For each page:                             │
│    navigation_start                         │
│    page_scanned                             │
│    form_detected (if forms)                 │
│    captcha_detected (if CAPTCHA)            │
│    navigation_complete                      │
│    screenshot (per capture)                 │
│  exploration_path (all URLs visited)        │
│  phase_complete (scout)                     │
└─────────────────────────────────────────────┘
        │
        ▼
┌─── VISION PHASE (20-40%) ──────────────────┐
│  phase_start (vision)                       │
│  For each screenshot:                       │
│    screenshot (with analysis)               │
│  For each dark pattern:                     │
│    finding                                  │
│    dark_pattern_finding                     │
│    temporal_finding (if time-sensitive)      │
│  phase_complete (vision)                    │
└─────────────────────────────────────────────┘
        │
        ▼
┌─── SECURITY PHASE (40-60%) ────────────────┐
│  phase_start (security)                     │
│  For each module:                           │
│    security_result                          │
│    security_module_result                   │
│    darknet_analysis_result (if darknet)     │
│    marketplace_threat (per threat)          │
│    exit_scam_detected (if applicable)       │
│    tor2web_anonymous_breach (if TOR)        │
│  phase_complete (security)                  │
└─────────────────────────────────────────────┘
        │
        ▼
┌─── GRAPH PHASE (60-80%) ───────────────────┐
│  phase_start (graph)                        │
│  osint_result (per source)                  │
│  darknet_threat (per threat)                │
│  ioc_indicator (per IoC)                    │
│  knowledge_graph                            │
│  graph_analysis                             │
│  phase_complete (graph)                     │
└─────────────────────────────────────────────┘
        │
        ▼
┌─── JUDGE PHASE (80-100%) ──────────────────┐
│  phase_start (judge)                        │
│  site_type                                  │
│  green_flags                                │
│  verdict_technical                          │
│  verdict_nontechnical                       │
│  dual_verdict_complete                      │
│  stats_update                               │
│  agent_performance (per agent)              │
│  phase_complete (judge)                     │
└─────────────────────────────────────────────┘
        │
        ▼
┌─── COMPLETION ─────────────────────────────┐
│  audit_result (full data)                   │
│  audit_complete                             │
│  ── WebSocket closes ──                     │
└─────────────────────────────────────────────┘
```

---

## 6. Error Handling

### Error Event Types

| Event | Fatal? | Description |
|-------|--------|-------------|
| `phase_error` | No | Phase failed but audit continues |
| `audit_error` | Yes | Audit terminated |
| `log_entry` (level: error) | No | Logged, informational |

### Common Error Scenarios

| Scenario | Phase | Recovery |
|----------|-------|----------|
| Connection timeout | scout | 3 retries with exponential backoff |
| Invalid URL | scout | Audit terminates immediately |
| CAPTCHA blocking | scout | Page skipped, audit continues |
| Security module failure | security | Module skipped, others continue |
| OSINT rate limit | graph | Exponential backoff retry |
| VLM model failure | vision | Falls back to secondary VLM → Tesseract OCR |
| NIM API down | vision/judge | Circuit breaker skips API, falls back to heuristics |
| DB persistence error | any | Audit completes, result in-memory only |

### Frontend Error Handling Strategy

```typescript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "phase_error":
      // Show warning toast, don't terminate
      showWarning(`${data.phase}: ${data.message}`);
      break;

    case "audit_error":
      // Show error, mark audit as failed
      showError(data.error);
      setAuditStatus("error");
      break;

    case "audit_complete":
      // Audit finished successfully
      setAuditStatus("completed");
      break;
  }
};
```

---

## 7. Frontend Integration Patterns

### 7.1 WebSocket Connection with Reconnection

```typescript
function connectAudit(auditId: string) {
  const ws = new WebSocket(`ws://localhost:8000/api/audit/stream/${auditId}`);
  let retries = 0;
  const maxRetries = 3;

  ws.onopen = () => { retries = 0; };

  ws.onclose = (event) => {
    if (!event.wasClean && retries < maxRetries) {
      retries++;
      const delay = Math.pow(2, retries) * 1000; // exponential backoff
      setTimeout(() => connectAudit(auditId), delay);
    }
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleEvent(data);
  };

  return ws;
}
```

### 7.2 Event Router

```typescript
function handleEvent(event: AuditEvent) {
  switch (event.type) {
    // Progress
    case "phase_start":
    case "phase_complete":
      updateProgressBar(event.pct);
      updatePhaseLabel(event.label);
      break;

    // Scout
    case "page_scanned":
      addPageToSitemap(event.url, event.page_title);
      break;
    case "screenshot":
      addScreenshotToGallery(event.index, event.data, event.label);
      break;
    case "exploration_path":
      renderBreadcrumbs(event.breadcrumbs);
      break;

    // Vision
    case "finding":
    case "dark_pattern_finding":
      addFindingToList(event.finding);
      break;

    // Security
    case "security_module_result":
      addSecurityResult(event.result);
      break;

    // Graph
    case "knowledge_graph":
      renderKnowledgeGraph(event.graph);
      break;
    case "osint_result":
      addOsintData(event.result);
      break;

    // Judge
    case "site_type":
      setSiteType(event.site_type, event.confidence);
      break;
    case "green_flags":
      showGreenFlags(event.flags);
      break;
    case "verdict_technical":
      showTechnicalVerdict(event.verdict);
      break;
    case "verdict_nontechnical":
      showSimpleVerdict(event.verdict);
      break;
    case "stats_update":
      updateStatsPanel(event.stats);
      break;

    // Completion
    case "audit_result":
      setFinalResult(event.result);
      break;
    case "audit_complete":
      closeConnection();
      break;
    case "audit_error":
      handleAuditError(event.error);
      break;
  }
}
```

### 7.3 TypeScript Event Types

```typescript
// Base event
interface AuditEvent {
  type: string;
}

// Phase events
interface PhaseStartEvent extends AuditEvent {
  type: "phase_start";
  phase: "init" | "scout" | "vision" | "security" | "graph" | "judge";
  message: string;
  pct: number;
  label: string;
}

interface PhaseCompleteEvent extends AuditEvent {
  type: "phase_complete";
  phase: string;
  message: string;
  pct: number;
  label: string;
  summary: Record<string, any>;
}

// Finding events
interface FindingEvent extends AuditEvent {
  type: "finding" | "dark_pattern_finding";
  finding: {
    id?: string;
    category: string;
    pattern_type: string;
    severity: "critical" | "high" | "medium" | "low";
    confidence: number;
    description: string;
    plain_english?: string;
    screenshot_path?: string;
  };
}

// Verdict events
interface VerdictTechnicalEvent extends AuditEvent {
  type: "verdict_technical";
  verdict: {
    risk_level: "critical" | "high" | "medium" | "low";
    trust_score: number;
    summary: string;
    recommendations: string[];
  };
}

interface VerdictNontechnicalEvent extends AuditEvent {
  type: "verdict_nontechnical";
  verdict: {
    risk_level: string;
    summary: string;
    actionable_advice: string[];
    green_flags: string[];
  };
}

// Graph events
interface KnowledgeGraphEvent extends AuditEvent {
  type: "knowledge_graph";
  graph: {
    nodes: Array<{
      id: string;
      type: string;
      label: string;
      properties: Record<string, any>;
    }>;
    edges: Array<{
      source: string;
      target: string;
      relationship: string;
      weight: number;
    }>;
    node_count: number;
    edge_count: number;
  };
}

// Completion events
interface AuditResultEvent extends AuditEvent {
  type: "audit_result";
  result: {
    url: string;
    status: string;
    trust_score: number;
    risk_level: string;
    narrative: string;
    signal_scores: Record<string, number>;
    dark_pattern_summary: { findings: any[] };
    recommendations: string[];
    security_results: Record<string, any>;
    site_type: string;
    pages_scanned: number;
    screenshots_count: number;
    elapsed_seconds: number;
    dual_verdict: {
      verdict_technical: any;
      verdict_nontechnical: any;
    };
  };
}

interface AuditCompleteEvent extends AuditEvent {
  type: "audit_complete";
  audit_id: string;
  elapsed: number;
}

interface AuditErrorEvent extends AuditEvent {
  type: "audit_error";
  audit_id: string;
  error: string;
}
```

---

## Quick Reference: All Event Types

| Event Type | Phase | Description |
|-----------|-------|-------------|
| `phase_start` | All | Phase begins — update progress |
| `phase_complete` | All | Phase ends — update progress + summary |
| `phase_error` | All | Phase error — non-fatal warning |
| `agent_personality` | All | Agent activity status |
| `log_entry` | All | Detailed log message |
| `navigation_start` | Scout | Page navigation started |
| `page_scanned` | Scout | Page loaded successfully |
| `form_detected` | Scout | HTML forms found |
| `captcha_detected` | Scout | CAPTCHA challenge found |
| `navigation_complete` | Scout | Page navigation finished |
| `exploration_path` | Scout | All visited URLs summary |
| `screenshot` | Scout/Vision | Screenshot data (base64) |
| `finding` | Vision | Dark pattern detected |
| `dark_pattern_finding` | Vision | Dark pattern with screenshot ref |
| `temporal_finding` | Vision | Time-sensitive dark pattern |
| `security_result` | Security | Raw module result |
| `security_module_result` | Security | Normalized module result |
| `owasp_module_result` | Security | OWASP-specific result |
| `darknet_analysis_result` | Security | Darknet intelligence |
| `marketplace_threat` | Security | Marketplace threat alert |
| `exit_scam_detected` | Security | Exit scam warning |
| `tor2web_anonymous_breach` | Security | TOR anonymity breach |
| `osint_result` | Graph | OSINT source data |
| `darknet_threat` | Graph | Darknet threat |
| `ioc_indicator` | Graph | Indicator of Compromise |
| `knowledge_graph` | Graph | Entity relationship graph |
| `graph_analysis` | Graph | Graph structure analysis |
| `site_type` | Judge | Detected website type |
| `green_flags` | Judge | Positive security indicators |
| `verdict_technical` | Judge | Expert verdict |
| `verdict_nontechnical` | Judge | Simple verdict |
| `dual_verdict_complete` | Judge | Combined verdict |
| `stats_update` | Judge | Audit statistics |
| `agent_performance` | Judge | Agent metrics |
| `audit_result` | Complete | Final enriched result |
| `audit_complete` | Complete | Audit finished signal |
| `audit_error` | Error | Fatal audit error |
