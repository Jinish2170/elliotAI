# Phase 13: Production Hardening & Workflow Repair

## Phase Goal

Transform VERITAS from a collection of individually-built features into a cohesive, production-grade product where every audit tier works end-to-end with proper data flow between all 5 agents, correct tier-aware behavior, and no orphaned features.

## Executive Summary

After 12 phases of feature development, the system has world-class capabilities (5-pass Vision, 15+ OSINT sources, 25+ security modules, darknet intelligence, dual-tier verdicts) but they were built incrementally and never unified into a working product. The orchestrator has accumulated patch-on-patch fixes. Data flows between agents are fragile. Tier behavior is inconsistent. Several features are implemented but never wired into the main pipeline. This phase treats the codebase as a senior engineer would treat a pre-launch product: audit every data path, fix every broken connection, ensure every tier delivers its promised value, and clean the codebase for maintainability.

---

## System Audit Findings

### Category 1: Orchestrator Pipeline Issues

**1.1 — Orchestrator is 1700+ lines of accumulated patches**
The `orchestrator.py` file has grown to ~1700 lines through 12 phases of incremental fixes. It contains:
- 7 node functions (scout_node, vision_node, graph_node, judge_node, security_node_with_agent, security_node, force_verdict_node)
- 3 routing functions
- Graph builder
- VeritasOrchestrator class with 400+ line `audit()` method
- Helper functions added as patches

This monolith is fragile — every fix risks breaking something else.

**1.2 — VeritasOrchestrator.audit() bypasses LangGraph entirely**
The `audit()` method manually sequences nodes in a for-loop instead of using `self._compiled.ainvoke()`. This means:
- The graph topology defined in `build_audit_graph()` is decoration — it's not used
- Conditional edges (`route_after_scout`, `route_after_judge`) are defined but the manual loop implements its own routing
- This creates a maintenance trap: changes to the graph topology have no effect

**1.3 — Scout node only processes ONE URL per invocation**
`scout_node` pops `pending_urls[0]` and processes it. But the manual `audit()` loop calls `scout_node` once per iteration. If Judge requests investigating 3 new URLs, only 1 gets processed per iteration cycle, wasting iteration budget.

**1.4 — Progress emission is scattered across 3 different systems**
- `self._emit()` in VeritasOrchestrator → writes to `progress_queue` (IPC)
- `ProgressEmitter` → WebSocket streaming
- `##PROGRESS:` stdout markers → parsed by AuditRunner
These 3 systems run in parallel and emit different events with different schemas. The frontend gets a chaotic mix.

### Category 2: Tier-Specific Issues

**2.1 — Quick Scan does too much work**
Quick scan (1 page, 2 screenshots) still runs:
- Full graph investigation (WHOIS, DNS, SSL, entity verification, Tavily searches)
- Full OSINT orchestrator
- ConsensusEngine cross-validation in judge
Quick scan should be fast (< 30 seconds). Currently it can take minutes.

**2.2 — Darknet tier has no TOR routing in the pipeline**
`darknet_investigation` tier has `enable_tor: True` in settings but:
- Scout doesn't check `enable_tor` to route through TOR
- `TORClient` (veritas/core/tor_client.py) exists but is never called by Scout
- `OnionDetector` scans for .onion URLs in page content but Scout doesn't act on findings
- The darknet security modules aren't wired in the graph

**2.3 — Standard vs Deep difference is only pass count**
standard_audit (3 passes) and deep_forensic (5 passes) differ only in vision pass count. But deep_forensic should also:
- Run more graph verifications (max_verifications: 15 vs 10)
- Enable deeper OSINT analysis
- Run OWASP + PCI DSS + GDPR security modules (via _get_security_modules_for_tier — THIS works)

**2.4 — Graph node ignores tier config entirely**
`graph_node` reads `audit_tier` but only logs it. It doesn't:
- Limit verifications for quick_scan
- Skip Tavily searches for quick_scan
- Enable deep OSINT for deep_forensic/darknet

### Category 3: Data Flow Breaks

**3.1 — Scout → Security data transfer is fabricated**
In `security_node_with_agent`, the `page_content` passed to SecurityAgent is *fabricated* from metadata:
```python
page_content = f"<html><head><title>{page_metadata.get('title', '')}</title></head>..."
```
This is not real HTML. Security modules that analyze actual HTML (CSP, injection, form analysis) get fake content. Scout has access to real page HTML via Playwright but doesn't capture it.

**3.2 — Scout doesn't capture HTTP response headers**
The `headers` dict passed to SecurityAgent is hardcoded:
```python
headers = {"content-type": "text/html", "server": "unknown"}
```
Real response headers (X-Frame-Options, Strict-Transport-Security, Content-Security-Policy, etc.) are critical for security analysis but Scout doesn't capture them.

**3.3 — Vision findings don't include bounding boxes**
The frontend has `ScreenshotCarousel` with highlight overlays that expect `bbox: [x, y, width, height]` on findings. But VisionAgent's `DarkPatternFinding` dataclass has no bbox field. The carousel overlay feature is dead code.

**3.4 — Graph data isn't used in the Judge narrative**
JudgeAgent receives `graph_result` with entity verifications, domain intel, and OSINT data. But the forensic narrative generation may not effectively use all this data — the LLM prompt may lack structured injection of graph findings.

### Category 4: Broken/Orphaned Components

**4.1 — Duplicate scout modules**
Both `veritas/agents/scout/` and `veritas/agents/scout_nav/` exist with overlapping files:
- `scout/scroll_orchestrator.py` vs `scout_nav/scroll_orchestrator.py`
- `scout/lazy_load_detector.py` vs `scout_nav/lazy_load_detector.py`
- `scout_nav/link_explorer.py` (no equivalent in scout/)

**4.2 — Darknet modules disconnected**
- `veritas/darknet/onion_detector.py` — OnionDetector class (standalone)
- `veritas/darknet/threat_scraper.py` — ThreatScraper class (standalone)
- `veritas/darknet/tor_client.py` — TORClient class (standalone)
- `veritas/core/tor_client.py` — ANOTHER TORClient (from Phase 12!)
- `veritas/reporters/darknet_reporter.py` — DarknetReporter (never called)
- `veritas/osint/sources/darknet_*.py` — 6 marketplace sources (built but not clearly integrated)

These exist but aren't wired into the main audit pipeline.

**4.3 — Phase 12 plans 03-05 never executed**
The ROADMAP shows Phase 12 at 20% (1/5 plans). Plans 12-03 through 12-05 were never implemented:
- 12-03: Scout TOR Integration (making Scout route through TOR for .onion URLs)
- 12-04: Darknet threat analysis pipeline
- 12-05: Integration testing

**4.4 — Report generator exists but isn't in the pipeline**
`veritas/reporting/report_generator.py` exists and the CLI has `--report pdf/html` flags, but:
- The `audit()` method returns raw state, not a formatted report
- Report generation isn't triggered from the API
- The frontend has a report page but it works off the raw audit result

### Category 5: Test & Quality Issues

**5.1 — Test assertion hardcodes 3 tiers (fails with 4)**
`test_audit_tiers` asserts `len(settings.AUDIT_TIERS) == 3` — fails now that darknet tier exists.

**5.2 — Onion detector tests failing (7 failures)**
Pattern matching tests for v3 onion addresses are broken — likely regex issue.

**5.3 — No integration tests for tier workflows**
Zero tests verify that "quick_scan runs fast with limited modules" or "deep_forensic runs all OWASP modules". Each tier workflow is untested.

**5.4 — No test for end-to-end data flow**
No test verifies that Scout output → Security input → Vision input → Graph input → Judge input flows correctly with all fields preserved.

### Category 6: Frontend/Backend Interface Issues

**6.1 — Store handles 80+ state fields**
The Zustand store has become a massive state dump with 80+ fields. Many fields (like `darknetAnalysisResult`, `tor2WebThreats`, `aptGroupAttributions`) are defined but never populated.

**6.2 — AuditRunner hardcodes progress event schema**
The AuditRunner maps CLI progress events to WebSocket events with a hardcoded label map. New agents or phases require manual updates.

**6.3 — No error recovery in WebSocket stream**
If any node throws during the audit, the WebSocket stream dies. There's no graceful degradation that says "Vision failed, continuing with partial results".

---

## Decisions

### Locked (from user)
- **All 4 tiers must work correctly**: quick_scan, standard_audit, deep_forensic, darknet_investigation
- **All features must be wired into the main pipeline**: No orphaned code
- **Industry-grade product engineering**: This should work like a real product
- **Clean unnecessary files**: Remove duplicates and dead code
- **Reorganize if needed**: File structure should make sense

### Claude's Discretion
- How to refactor the orchestrator (split vs restructure)
- Which darknet features to wire vs which to defer (Phase 12 plans 03-05 scope)
- How to handle Scout HTML/header capture (Playwright response interception vs page.content())
- Frontend store cleanup approach

---

## Deferred Ideas
- Authentication/multi-user (out of scope per PROJECT.md)
- Alternative AI providers
- Production hosting infrastructure
- Real-time alerting/analytics
