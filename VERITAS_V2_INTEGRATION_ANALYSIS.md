# VERITAS V2 Integration Analysis

**Last updated:** 2026-03-09
**Scope:** backend, event contract, Veritas agents
**Status:** V2 backend contract normalized; remaining risk is optional dependency degradation and slow end-to-end security coverage

## Executive Summary

The repo already contained most V2 functionality. The primary failure was not missing features, but integration drift:

1. The orchestrator and agents were mostly producing V2-shaped data.
2. The backend runner still consumed mixed V1/V2 result shapes.
3. Runtime imports still depended on legacy top-level paths and local `sys.path` hacks.
4. The docs described a cleaner contract than the runtime actually guaranteed.

That drift is now reduced to one canonical runtime path:

- `veritas.core.orchestrator` produces the canonical audit result.
- `backend.services.audit_runner` derives WebSocket events and API summary data from that canonical result.
- `backend.routes.audit` persists the runner-emitted `audit_result` payload directly.

No feature paths were intentionally removed. Older modules remain as compatibility code where still referenced.

## Canonical Source Of Truth

| Layer | Canonical source | Notes |
|---|---|---|
| Python imports | `veritas.*` and `backend.*` | Runtime code no longer depends on top-level `analysis`, `core`, `agents`, or `config` imports. |
| Audit state/result | `veritas/core/orchestrator.py` | Security output is split into `security_results` plus aggregate `security_summary`. |
| WebSocket events | `backend/services/audit_runner.py` | Runner converts canonical result into frontend-facing events. |
| Persistence payload | `backend/routes/audit.py` | `on_audit_completed()` persists the `audit_result.result` summary payload directly. |

## Canonical Contracts

### Orchestrator result

```python
{
  "status": str,
  "url": str,
  "audit_tier": str,
  "verdict_mode": str,
  "elapsed_seconds": float,
  "site_type": str,
  "site_type_confidence": float,
  "scout_results": list[dict],
  "vision_result": dict | None,
  "security_results": dict,
  "security_summary": dict,
  "security_mode": str,
  "graph_result": dict | None,
  "judge_decision": dict | None,
  "errors": list[str],
}
```

### Backend summary payload (`audit_result.result`)

```python
{
  "url": str,
  "status": str,
  "audit_tier": str,
  "verdict_mode": str,
  "trust_score": int | None,
  "risk_level": str | None,
  "narrative": str,
  "signal_scores": dict,
  "dark_pattern_summary": {"findings": list[dict]},
  "recommendations": list[str],
  "green_flags": list[str],
  "security_results": dict,
  "security_summary": dict,
  "site_type": str,
  "site_type_confidence": float,
  "domain_info": dict,
  "pages_scanned": int,
  "screenshots_count": int,
  "elapsed_seconds": float,
  "errors": list[str],
}
```

## Integration Status

| Capability | Status | Canonical path | Notes |
|---|---|---|---|
| Scout navigation and screenshots | Wired | `veritas.agents.scout` | `scout_nav/*` remains support code under the main scout path. |
| Vision 5-pass events | Wired | `veritas.agents.vision` -> progress passthrough | `vision_pass_*` events come from agent progress output and are forwarded by the runner. |
| Vision summary/result serialization | Wired | `veritas.core.orchestrator` | Canonical serialized shape is `findings` + `temporal_findings`, not legacy singleton fields. |
| Security tier execution | Wired | `veritas.agents.security_agent` | Tier execution is now the default V2 path when tier utilities are available. |
| Security fallback | Wired | `veritas.core.orchestrator.security_node_with_agent` | Falls back to legacy/function paths and records explicit `security_mode`. |
| Graph / OSINT / CTI | Wired | `veritas.agents.graph_investigator` | Runner now emits `osint_result`, `darknet_threat`, `ioc_indicator`, `knowledge_graph`, `graph_analysis`. |
| Dual verdict output | Wired | `veritas.agents.judge` | Runner emits technical, non-technical, and combined verdict events. |
| Persistence | Wired | `backend.routes.audit` | Completed audits persist canonical summary fields and dark-pattern findings. |
| Legacy result keys (`scout_result`, `security_result`) | Removed from runtime assumptions | n/a | Backend no longer depends on singleton legacy keys. |

## Resolved Gaps

### Import hygiene

Runtime imports were normalized in the critical backend/agent path:

- `veritas/core/orchestrator.py`
- `veritas/agents/vision.py`
- `veritas/agents/scout.py`
- `veritas/agents/graph_investigator.py`
- `veritas/agents/security_agent.py`
- `veritas/analysis/security/darknet.py`
- `veritas/config/__init__.py`
- `backend/routes/audit.py`
- `backend/services/audit_runner.py`

Remaining legacy import matches are currently in comments or compatibility-heavy tests, not in the primary runtime path.

### Security mode drift

The V2 default is now:

- `agent_tier` when tier utilities are available and `SECURITY_USE_TIER_EXECUTION=true`
- `agent_legacy` when the security agent is used but tier execution is unavailable
- `function` or `function_fallback` only for non-agent or hard-fallback paths

### Backend result-shape drift

The runner now derives output from the canonical result only. It no longer expects:

- `scout_result`
- `security_result`
- legacy vision dark-pattern container names as the only source

### Persistence mismatch

`backend/routes/audit.py` now safely persists:

- trust score
- risk level
- narrative
- signal scores
- site type
- security results
- pages scanned
- elapsed time
- dark-pattern findings

and sets a completion timestamp when the result payload does not provide one.

## Canonical Vs Compatibility Paths

| Area | Canonical | Compatibility retained |
|---|---|---|
| Scout | `veritas.agents.scout` | `veritas.agents.scout_nav.*` helpers |
| Vision | `veritas.agents.vision` | legacy field aliases still tolerated in runner for normalization |
| Security | `SecurityAgent` tier execution | legacy function path retained for fallback |
| Graph | `veritas.agents.graph_investigator` | none required beyond optional source failures |
| Judge | `veritas.agents.judge` | older key aliases patched where security module names changed |

## Known Remaining Risks

1. `opencv-python` is still optional. Without it, temporal CV degrades and the runtime explicitly warns that optical flow is unavailable.
2. `veritas/tests/test_security_integration.py` is still a slow, network-heavy suite. It should be treated as an environment/integration check, not a fast contract test.
3. Some older tests still use legacy import paths via local path shims. They do not currently block the runtime path, but they are not the desired long-term state.

## Verification Snapshot

Verified on 2026-03-09:

- `python -m veritas --help`
- `python -c "import veritas.core.orchestrator, veritas.agents.vision, veritas.agents.security_agent, backend.services.audit_runner; print('imports-ok')"`
- `pytest -q veritas/tests/test_migration_path.py`
- `pytest -q backend/tests/test_audit_runner_queue.py backend/tests/test_audit_route_contract.py backend/tests/test_audit_persistence.py`
- `pytest -q veritas/tests/test_security_agent.py -k "tier_execution or async_context_manager"`

## Recommended Next Work

1. Replace remaining legacy-import compatibility tests with `veritas.*` imports.
2. Add a bounded, mocked `test_security_integration.py` slice for tier execution and fallback without live network reliance.
3. Extend route/API tests to cover the WebSocket stream endpoint itself, not just helper functions.
