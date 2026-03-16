# VERITAS Backend - API Routes Reference

**Version:** 2.0.0
**Last Updated:** 2026-03-08

---

## Overview

VERITAS backend provides a FastAPI-based REST API with WebSocket support for real-time audit streaming.

---

## Base URL

```
http://localhost:8000/api
```

---

## CORS Configuration

All origins are allowed (`*`). Credentials allowed. All methods allowed. All headers allowed.

---

## Routes

### Health Check

#### GET /api/health

Returns API health status.

```yaml
Response:
  status: "ok"
  service: "veritas-api"
  version: "2.0.0"
```

**File:** `backend/routes/health.py`

---

### Audit Routes

#### POST /api/audit/start

Start a new audit and return the audit ID and WebSocket URL.

**Request Body:**

```json
{
  "url": "https://example.com",
  "tier": "standard_audit",
  "verdict_mode": "expert",
  "security_modules": null
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| url | string | Yes | Target URL to audit |
| tier | string | No | Audit tier (default: "standard_audit") |
| verdict_mode | string | No | Verdict mode (default: "expert") |
| security_modules | array | No | Specific security modules to run |

**Tiers:**
- `standard_audit` - Basic URL analysis
- `premium_audit` - Advanced security analysis
- `enterprise_audit` - Full audit suite
- `darknet_audit` - Darknet marketplace monitoring

**Verdict Modes:**
- `expert` - Detailed technical and plain-English verdicts
- `simple` - Simplified verdict only

**Response:**

```json
{
  "audit_id": "audit-1234567890",
  "status": "queued",
  "ws_url": "/api/audit/stream/audit-1234567890"
}
```

**Status Codes:**
- 200 - OK, audit started
- 400 - Bad request (invalid parameters)
- 500 - Server error

**File:** `backend/routes/audit.py`

---

#### WebSocket /api/audit/stream/{audit_id}

WebSocket endpoint that runs the audit and streams real-time events.

**Connection:** Connect immediately after receiving audit_id from `/api/audit/start`.

**Event Format:**

```json
{
  "type": "event_name",
  "timestamp": "HH:MM:SS",
  // ... event-specific fields
}
```

**Event Types:** See [EVENTS.md](./EVENTS.md) for complete reference (45+ events).

**Connection Flow:**
1. Client connects with audit_id
2. Server accepts connection
3. Server retrieves audit info
4. Server starts AuditRunner
5. Runner executes audit in subprocess
6. Progress events are streamed as WebSocket messages
7. Final audit_result is sent
8. Connection closes

**Error Handling:**
- If audit_id not found: Returns `{"type": "audit_error", "error": "Audit ID not found"}`

**File:** `backend/routes/audit.py`

---

#### GET /api/audit/{audit_id}/status

Check the status of a specific audit.

**Parameters:**
| Path Parameter | Type | Required | Description |
|----------------|------|----------|-------------|
| audit_id | string | Yes | Unique audit identifier |

**Response (Database Persistence Enabled):**

```json
{
  "audit_id": "audit-1234567890",
  "status": "completed",
  "url": "https://example.com",
  "result": {
    "trust_score": 75,
    "risk_level": "probably_safe",
    "signal_scores": {
      "domain_age": 0.8,
      "ssl_valid": 1.0,
      "reputation": 0.6
    },
    "narrative": "Audit summary text...",
    "site_type": "ecommerce",
    "site_type_confidence": 0.85,
    "security_results": {},
    "pages_scanned": 5,
    "elapsed_seconds": 45.2,
    "dark_pattern_summary": {
      "findings": [
        {
            "id": "finding-1",
            "pattern_type": "countdown_timer",
            "category": "pressure",
            "severity": "medium",
            "confidence": 0.8,
            "description": "Technical description",
            "plain_english": "User-friendly description",
            "screenshot_index": 0
        }
      ]
    }
  },
  "error": null,
  "created_at": "2024-01-15T10:30:00",
  "started_at": "2024-01-15T10:30:01",
  "completed_at": "2024-01-15T10:30:46"
}
```

**Response (In-Memory Fallback):**

```json
{
  "audit_id": "audit-1234567890",
  "status": "completed",
  "url": "https://example.com",
  "result": {/* same as above */},
  "error": null
}
```

**Status Codes:**
- 200 - OK, status retrieved
- 404 - Audit not found
- 500 - Server error

**File:** `backend/routes/audit.py`

---

#### GET /api/audits/history

Get paginated audit history with optional filters.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 20 | Number of audits to return (1-100) |
| offset | integer | No | 0 | Pagination offset |
| status_filter | string | No | null | Filter by audit status |
| risk_level_filter | string | No | null | Filter by risk level |

**Status Filter Options:** `queued`, `running`, `completed`, `error`, `disconnected`

**Risk Level Filter Options:** `trusted`, `probably_safe`, `suspicious`, `high_risk`, `likely_fraudulent`, `dangerous`

**Response:**

```json
{
  "audits": [
    {
      "audit_id": "audit-1234567890",
      "url": "https://example.com",
      "status": "completed",
      "audit_tier": "standard_audit",
      "verdict_mode": "expert",
      "trust_score": 75,
      "risk_level": "probably_safe",
      "signal_scores": {},
      "site_type": "ecommerce",
      "site_type_confidence": 0.85,
      "pages_scanned": 5,
      "screenshots_count": 10,
      "elapsed_seconds": 45.2,
      "created_at": "2024-01-15T10:30:00",
      "started_at": "2024-01-15T10:30:01",
      "completed_at": "2024-01-15T10:30:46"
    }
  ],
  "count": 1,
  "limit": 20,
  "offset": 0
}
```

**Status Codes:**
- 200 - OK, history retrieved
- 400 - Bad request (invalid parameters)
- 500 - Server error

**File:** `backend/routes/audit.py`

---

#### POST /api/audits/compare

Compare multiple audits to detect changes over time.

**Request Body:**

```json
{
  "audit_ids": [
    "audit-1234567890",
    "audit-1234567891"
  ]
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| audit_ids | array | Yes | List of audit IDs to compare |

**Requirements:**
- At least 2 audit IDs required
- All audit IDs must exist

**Response:**

```json
{
  "audits": [
    {
      "audit_id": "audit-1234567890",
      "url": "https://example.com",
      "status": "completed",
      "trust_score": 70,
      "risk_level": "probably_safe",
      "site_type": "ecommerce",
      "created_at": "2024-01-15T10:30:00",
      "completed_at": "2024-01-15T10:30:45",
      "findings_summary": {
        "total": 12,
        "critical": 1,
        "high": 2,
        "medium": 5,
        "low": 4
      },
      "screenshots_count": 10
    },
    {
      "audit_id": "audit-1234567891",
      "url": "https://example.com",
      "status": "completed",
      "trust_score": 75,
      "risk_level": "probably_safe",
      "site_type": "ecommerce",
      "created_at": "2024-01-20T10:30:00",
      "completed_at": "2024-01-20T10:30:46",
      "findings_summary": {
        "total": 8,
        "critical": 0,
        "high": 1,
        "medium": 3,
        "low": 4
      },
      "screenshots_count": 10
    }
  ],
  "trust_score_deltas": [
    {
      "from_audit_id": "audit-1234567890",
      "to_audit_id": "audit-1234567891",
      "delta": 5,
      "percentage_change": 7.14
    }
  ],
  "risk_level_changes": []
}
```

**Status Codes:**
- 200 - OK, comparison completed
- 400 - Bad request (less than 2 IDs, invalid format)
- 404 - One or more audits not found
- 500 - Server error

**File:** `backend/routes/audit.py`

---

## Database Event Handlers

The following internal functions handle database persistence events. These are not exposed as API routes but are called during audit lifecycle.

### on_audit_started
Called when an audit starts. Creates a new `Audit` record in the database with `RUNNING` status.

**Location:** `backend/routes/audit.py:361`

### on_audit_completed
Called when an audit completes successfully. Updates the audit record with final results, findings, and completion timestamp.

**Location:** `backend/routes/audit.py:398`

### on_audit_error
Called when an audit encounters an error. Updates the audit status to `ERROR` and stores the error message.

**Location:** `backend/routes/audit.py:453`

### _handle_screenshot_event
Called for each screenshot event. Saves the screenshot to the filesystem and creates a database record.

**Location:** `backend/routes/audit.py:487`

---

## Database Persistence

### Enable/Disable

Database persistence is controlled by the `USE_DB_PERSISTENCE` environment variable.

```bash
# Enable persistence
USE_DB_PERSISTENCE=true

# Disable persistence (default)
USE_DB_PERSISTENCE=false
```

### Database Schema

See [FILES_REFERENCE.md](./FILES_REFERENCE.md) → Database Models for complete schema definition.

---

## WebSocket Reconnection Handling

The backend supports automatic reconnection for clients using React Strict Mode's double effect firing:

1. Existing audit record is retrieved
2. Status is updated to `RUNNING`
3. Audit continues normally

This prevents duplicate audit records being created.

---

## Error Responses

All endpoints return JSON error responses:

```json
{
  "detail": "Error message describing the issue"
}
```

## Rate Limiting

Currently not implemented. Can be added with `slowapi` or `fastapi-limiter`.

---

**End of API Routes Reference**
