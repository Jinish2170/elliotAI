# VERITAS Backend Event Contract

**Last updated:** 2026-03-09
**Source of truth:** `backend/services/audit_runner.py`

## Overview

The backend emits two kinds of WebSocket events:

1. Runner-generated events derived from the canonical orchestrator result.
2. Passthrough progress events emitted directly by agents during execution.

The canonical final payload is `audit_result`, followed by `audit_complete`.

## Guaranteed Runner Events

### `phase_start`

```json
{
  "type": "phase_start",
  "phase": "scout|vision|security|graph|judge",
  "message": "Starting work",
  "pct": 0,
  "label": "Browser Reconnaissance"
}
```

### `phase_complete`

```json
{
  "type": "phase_complete",
  "phase": "vision",
  "message": "Phase complete",
  "pct": 55,
  "label": "Visual Intelligence",
  "summary": {}
}
```

### `phase_error`

```json
{
  "type": "phase_error",
  "phase": "security",
  "message": "Security analysis failed",
  "pct": 60,
  "error": "Security analysis failed"
}
```

### `agent_personality`

```json
{
  "type": "agent_personality",
  "agent": "scout|vision|security|graph|judge",
  "context": "working|complete",
  "timestamp": "HH:MM:SS",
  "params": {}
}
```

### `log_entry`

```json
{
  "type": "log_entry",
  "timestamp": "HH:MM:SS",
  "agent": "Scout|Vision|Security|Graph|Judge",
  "message": "Human-readable log line",
  "level": "info|error"
}
```

### `screenshot`

```json
{
  "type": "screenshot",
  "url": "path/to/file.png",
  "label": "Homepage",
  "index": 0,
  "data": "base64-encoded bytes or null"
}
```

### `site_type`

```json
{
  "type": "site_type",
  "site_type": "ecommerce",
  "confidence": 0.93
}
```

### `security_result`

One event per module in `security_results`.

```json
{
  "type": "security_result",
  "module": "phishing_db",
  "result": {}
}
```

### `owasp_module_result`

Emitted when the module name starts with `owasp_`.

```json
{
  "type": "owasp_module_result",
  "result": {
    "module": "owasp_a05"
  }
}
```

### `dark_pattern_finding`

```json
{
  "type": "dark_pattern_finding",
  "finding": {
    "category": "visual_interference",
    "pattern_type": "fake_urgency",
    "severity": "high",
    "confidence": 0.91,
    "description": "Countdown timer resets on refresh.",
    "plain_english": "Countdown timer resets on refresh.",
    "screenshot_path": "path/to/file.png"
  }
}
```

### `temporal_finding`

```json
{
  "type": "temporal_finding",
  "finding": {
    "finding_type": "fake_countdown",
    "is_suspicious": true,
    "confidence": 0.88
  }
}
```

### `osint_result`

One event per OSINT source in `graph_result.osint_sources`.

```json
{
  "type": "osint_result",
  "result": {
    "source": "abuseipdb"
  }
}
```

### `darknet_threat`

Emitted for OSINT sources whose name starts with `darknet_` or contains `tor2web`.

```json
{
  "type": "darknet_threat",
  "threat": {
    "source": "darknet_alpha",
    "data": {},
    "confidence": 0.81
  }
}
```

### `ioc_indicator`

```json
{
  "type": "ioc_indicator",
  "indicator": {}
}
```

### `knowledge_graph`

```json
{
  "type": "knowledge_graph",
  "graph": {
    "nodes": [],
    "edges": []
  }
}
```

### `graph_analysis`

```json
{
  "type": "graph_analysis",
  "analysis": {
    "total_nodes": 0,
    "total_edges": 0,
    "graph_sparsity": 1.0,
    "avg_clustering": 0.0,
    "connected_components": 0
  }
}
```

### `verdict_technical`

```json
{
  "type": "verdict_technical",
  "verdict": {
    "risk_level": "high",
    "trust_score": 42,
    "summary": "Security and entity signals are inconsistent.",
    "recommendations": []
  }
}
```

### `verdict_nontechnical`

```json
{
  "type": "verdict_nontechnical",
  "verdict": {
    "risk_level": "high",
    "summary": "This site looks risky.",
    "actionable_advice": [],
    "green_flags": []
  }
}
```

### `dual_verdict_complete`

```json
{
  "type": "dual_verdict_complete",
  "dual_verdict": {
    "verdict_technical": {},
    "verdict_nontechnical": {},
    "metadata": {
      "timestamp": "ISO-8601",
      "audit_id": "vrts_xxxxxxxx"
    }
  }
}
```

### `audit_result`

This is the persistence-ready summary contract.

```json
{
  "type": "audit_result",
  "result": {
    "url": "https://example.com",
    "status": "completed",
    "audit_tier": "standard_audit",
    "verdict_mode": "expert",
    "trust_score": 42,
    "risk_level": "high",
    "narrative": "Multiple trust and security inconsistencies detected.",
    "signal_scores": {},
    "dark_pattern_summary": {"findings": []},
    "recommendations": [],
    "green_flags": [],
    "security_results": {},
    "security_summary": {},
    "site_type": "ecommerce",
    "site_type_confidence": 0.93,
    "domain_info": {},
    "pages_scanned": 1,
    "screenshots_count": 1,
    "elapsed_seconds": 12.4,
    "errors": []
  }
}
```

### `audit_complete`

```json
{
  "type": "audit_complete",
  "audit_id": "vrts_xxxxxxxx",
  "elapsed": 12.4
}
```

### `audit_error`

```json
{
  "type": "audit_error",
  "audit_id": "vrts_xxxxxxxx",
  "error": "Audit finished but result JSON could not be parsed"
}
```

## Passthrough Agent Events

These are forwarded by the runner unchanged when agents emit them as progress payloads:

- `vision_pass_start`
- `vision_pass_complete`
- `vision_pass_findings`

Those events are available only when the vision agent runs the 5-pass pipeline and emits them. The runner does not synthesize per-pass data from the final result.

## Typical Event Order

1. `phase_start`
2. zero or more `agent_personality` and `log_entry`
3. zero or more passthrough agent events such as `vision_pass_start`
4. zero or more artifact and finding events (`screenshot`, `security_result`, `dark_pattern_finding`, `osint_result`, `knowledge_graph`, verdict events)
5. `audit_result`
6. `audit_complete`
