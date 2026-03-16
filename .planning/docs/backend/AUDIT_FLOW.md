# VERITAS Backend Audit Flow

**Last updated:** 2026-03-09
**Source of truth:** `backend/routes/audit.py`, `backend/services/audit_runner.py`, `veritas/core/orchestrator.py`

## Flow Summary

1. `POST /api/audit/start` creates an in-memory audit record.
2. `GET /api/audit/stream/{audit_id}` opens the WebSocket and starts the audit.
3. `AuditRunner` launches `python -m veritas <url> --json` in a subprocess.
4. Progress is read from Queue IPC or stdout markers.
5. The runner converts progress plus the final canonical orchestrator result into WebSocket events.
6. `audit_result` is stored in memory and persisted through `on_audit_completed()`.
7. The runner emits `audit_complete`.

## Canonical Runtime Path

```text
veritas.core.orchestrator
  -> canonical result dict
backend.services.audit_runner
  -> WebSocket events + persistence-ready audit_result
backend.routes.audit
  -> DB persistence + status endpoint
```

## Canonical Orchestrator Result

The backend expects one final result object with these top-level sections:

- `scout_results`
- `vision_result`
- `security_results`
- `security_summary`
- `graph_result`
- `judge_decision`

The backend no longer expects legacy singleton fields such as `scout_result` or `security_result`.

## Runner Transformation

`AuditRunner` performs four main transformations:

1. Progress messages become `phase_start`, `phase_complete`, `phase_error`, `agent_personality`, and `log_entry`.
2. Screenshot file paths become `screenshot` events with optional base64 payloads.
3. Canonical result sections become domain events such as `security_result`, `dark_pattern_finding`, `osint_result`, `knowledge_graph`, and verdict events.
4. The final summary becomes `audit_result`.

## Persistence Flow

### Start

`on_audit_started()` creates or updates the `Audit` record with:

- `id`
- `url`
- `status=running`
- `audit_tier`
- `verdict_mode`

### During execution

`_handle_screenshot_event()` persists screenshots only from `screenshot` events. Screenshot persistence is not reconstructed later from the final result.

### Completion

`on_audit_completed()` persists the `audit_result.result` payload:

- `trust_score`
- `risk_level`
- `narrative`
- `signal_scores`
- `site_type`
- `site_type_confidence`
- `security_results`
- `pages_scanned`
- `elapsed_seconds`
- `dark_pattern_summary.findings`

If `completed_at` is absent from the payload, the route sets it at persistence time.

## Status Endpoint Contract

`GET /api/audit/{audit_id}/status` returns:

```json
{
  "audit_id": "vrts_xxxxxxxx",
  "status": "queued|running|completed|error|disconnected",
  "url": "https://example.com",
  "result": null,
  "error": null
}
```

For completed audits, `result` contains the same persisted summary shape used in `audit_result`, plus dark-pattern findings reconstructed from the `AuditFinding` table.

## Event Ordering Notes

- `vision_pass_*` events are passthroughs from the vision agent and may appear before the final `dark_pattern_finding` events derived from the final result.
- `security_result` is emitted once per module inside `security_results`.
- `owasp_module_result` is emitted only for module names starting with `owasp_`.
- `audit_result` always precedes `audit_complete`.

## Known Degraded Modes

- If Queue IPC setup fails, the runner falls back to stdout parsing.
- If optional CV dependencies are missing, vision temporal analysis degrades and the runtime reports that explicitly.
- If the subprocess exits without parseable JSON, the runner emits `audit_error` instead of `audit_result`.
