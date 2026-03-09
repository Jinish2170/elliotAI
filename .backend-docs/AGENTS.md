# VERITAS Agent Reference

**Last updated:** 2026-03-09
**Scope:** canonical backend-facing agent contracts

## Execution Order

The backend-facing flow is:

1. Scout
2. Vision
3. Security
4. Graph Investigator
5. Judge

The orchestrator is the source of truth for the final merged result. The backend does not call agents directly.

## 1. Scout Agent

**Primary file:** `veritas/agents/scout.py`

### Canonical outputs consumed by the backend

- `scout_results[*].screenshots`
- `scout_results[*].screenshot_labels`
- `site_type`
- `site_type_confidence`

### Notes

- `veritas/agents/scout_nav/*` remains helper code behind the main scout path.
- The backend derives screenshot events from scout screenshot paths in the final result.

## 2. Vision Agent

**Primary file:** `veritas/agents/vision.py`

### Canonical outputs consumed by the backend

- `vision_result.findings`
- `vision_result.temporal_findings`
- `vision_result.screenshots_analyzed`
- `vision_result.prompts_sent`
- `vision_result.nim_calls_made`
- `vision_result.fallback_used`

### Notes

- The backend treats `findings` as canonical. It still tolerates `dark_patterns` during normalization for compatibility.
- `vision_pass_start`, `vision_pass_complete`, and `vision_pass_findings` are passthrough progress events from the agent’s 5-pass pipeline.
- Temporal analysis degrades when optional CV dependencies such as `opencv-python` are unavailable.

## 3. Security Agent

**Primary file:** `veritas/agents/security_agent.py`

### Canonical outputs consumed by the backend

- `security_results`
- `security_summary`
- `security_mode`

### Runtime modes

- `agent_tier`: default V2 mode when tier utilities are available
- `agent_legacy`: security agent is active but tier execution is unavailable
- `function`: orchestrator function path used directly
- `function_fallback`: hard fallback from agent path

### Notes

- Tier execution is the preferred V2 path.
- The backend emits one `security_result` event per module in `security_results`.
- Module names such as `phishing_db` and `redirect_chain` are canonical; older aliases are patched only for compatibility.

## 4. Graph Investigator

**Primary file:** `veritas/agents/graph_investigator.py`

### Canonical outputs consumed by the backend

- `graph_result.osint_sources`
- `graph_result.osint_indicators`
- `graph_result.claims_extracted`
- `graph_result.verifications`
- `graph_result.inconsistencies`
- `graph_result.graph_data` when available

### Notes

- The backend emits `osint_result` from `osint_sources`.
- Darknet-related OSINT sources also produce `darknet_threat`.
- If no explicit graph structure exists, the runner synthesizes a minimal knowledge graph from the result sections present.

## 5. Judge Agent

**Primary file:** `veritas/agents/judge.py`

### Canonical outputs consumed by the backend

- `judge_decision.narrative`
- `judge_decision.recommendations`
- `judge_decision.green_flags`
- `judge_decision.trust_score_result`
- `judge_decision.technical_verdict`
- `judge_decision.non_technical_verdict`

### Notes

- The backend emits `verdict_technical`, `verdict_nontechnical`, and `dual_verdict_complete`.
- `audit_result` summary fields are primarily derived from `judge_decision` plus high-level metadata from other agents.

## Shared Backend Summary

All agents contribute to the final backend summary payload:

```python
{
  "trust_score": int | None,
  "risk_level": str | None,
  "narrative": str,
  "signal_scores": dict,
  "dark_pattern_summary": {"findings": list[dict]},
  "security_results": dict,
  "security_summary": dict,
  "site_type": str,
  "site_type_confidence": float,
  "pages_scanned": int,
  "elapsed_seconds": float,
}
```

This summary is emitted as `audit_result` and persisted by `backend/routes/audit.py`.
