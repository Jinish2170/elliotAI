# VERITAS V3 — Redesign Blueprint

> Deep audit of the current codebase: 130+ files examined. Architectural, product, and agentic framework analysis.

---

## Part 1: WHAT ACTUALLY EXISTS (Real Codebase Map)

### Layer 1: Agents (7,792 lines)
| Agent | Lines | What It Does |
|-------|-------|-------------|
| **StealthScout** | 1,567 | Playwright browser with anti-detection, screenshots, DOM, IOC/Onion detection, TOR, CAPTCHA handling |
| **SecurityAgent** | 1,221 | Tier-based (FAST/MEDIUM/DEEP) security module execution, OWASP 10, CVSS scoring, darknet correlation |
| **VisionAgent** | 1,504 | VLM screenshot analysis, multi-pass dark pattern detection, temporal analysis |
| **GraphInvestigator** | 1,985 | Entity relationship graphs, WHOIS/DNS/SSL via OSINT orchestrator, link analysis |
| **JudgeAgent** | 1,515 | Weighted scoring with 12 site-type strategies, natural language verdicts |

### Layer 2: Analysis Modules (~30 files)
- **Passive checks**: DOM analyzer, form validator, meta analyzer, pattern matcher, phishing checker, redirect analyzer, security headers, temporal analyzer, JS obfuscation detector
- **Security tier modules**: OWASP A01-A10, CSP, Cookies, TLS/SSL, GDPR, PCI DSS, Social Engineering, Darknet analysis
- **Advanced**: Exploitation advisor (passive), scenario generator

### Layer 3: Core Infrastructure (~15 files)
- **NIMClient**: 4-level fallback (NIM VLM → NIM fallback → Tesseract OCR → nothing), circuit breaker, disk cache, rate limiting, budget tracking
- **LangGraph Orchestrator**: Linear chain (Scout → Security → Vision → Graph → Judge), with loop-back for deep investigation
- **EvidenceStore**: LanceDB vector database for evidence persistence
- **TimeoutManager**: Adaptive complexity analysis with dynamic timeouts
- **FallbackManager**: Circuit breaker per-module with degradation patterns
- **ProgressEmitter**: WebSocket streaming with token-bucket rate limiting, completion time estimation

### Layer 4: OSINT Framework (~20 files)
- **OSINTOrchestrator**: Source discovery, circuit breaker, rate limiter, intelligent fallback, parallel queries
- **Sources**: DNS (dnspython), WHOIS, SSL verification, URLVoid (API key), AbuseIPDB (API key), Tavily (3 sources), 6 darknet marketplace feeds
- **Supporting**: IOC detector, CTI engine, vulnerability mapper, reputation engine, social engineering patterns, attack patterns, cache

### Layer 5: Quality & Scoring (~5 files)
- **CVSS Calculator**: CVSS 3.1 score computation
- **CWE Registry**: Finding-to-CWE mapping
- **Confidence Scorer**: Per-module confidence calculation
- **Consensus Engine**: Multi-source result agreement
- **Validation State**: Audit validation tracking

### Layer 6: API + UI
- **FastAPI Backend**: REST + WebSocket, audit_runner subprocess wrapper
- **Next.js Frontend**: Landing, live audit (3-column animated), report (Simple/Expert modes)
- **Gradio UI**: `veritas/ui/app.py` — alternate interface

---

## Part 2: COMPLETE GAP ANALYSIS (14 Gaps)

### GAP 1: OSINT Orchestrator Is Not Wired Into The Pipeline
**Severity: CRITICAL**

The OSINTOrchestrator is well-built — circuit breakers, rate limiting, source discovery, intelligent fallback, parallel execution. It's a solid piece of engineering. But it's **not connected to the main audit pipeline**.

- GraphInvestigator calls it selectively for WHOIS/DNS/SSL
- SecurityAgent imports CTI but doesn't use the orchestrator
- The main LangGraph pipeline has NO direct OSINT node
- The darknet marketplace feeds (6 sources) are hardcoded static data from `marketplace_threat_feeds.json` — not live intelligence

**Reality**: The OSINT framework is a parked car with a full tank — it works but nothing drives to it.

### GAP 2: Missing Top-Tier Threat Intelligence Sources
**Severity: CRITICAL**

Current OSINT sources: DNS, WHOIS, SSL, URLVoid, AbuseIPDB, Tavily, darknet static feeds.

**Missing — the ones that matter most for security audits**:
- ❌ VirusTotal — The gold standard for URL reputation
- ❌ URLhaus — Real-time malicious URL database (free, no API key)
- ❌ Google Safe Browsing — Phishing/malware detection (free, 10K/day)
- ❌ Shodan — Open port and service enumeration
- ❌ Certificate Transparency logs (crt.sh) — Rogue cert detection
- ❌ Wayback Machine — Historical content comparison

Darknet marketplace feeds are **static JSON snapshots** of known markets (AlphaBay, Hansa, etc.). They check if a URL mentions a darknet market — useful but extremely narrow. They don't do live intelligence gathering.

### GAP 3: The Pipeline Is Rigidly Linear With False Adaptivity
**Severity: HIGH**

The LangGraph topology looks adaptive on paper:
```
scout → security → vision → graph → judge → [loop back → scout]
```

But the actual routing is extremely limited:
- `route_after_scout`: Only branches to "security" or "abort"
- `route_after_judge`: Only branches to "scout (deepen)", "force_verdict", or "end"
- There's no parallel execution — everything is sequential
- Security phase runs ALL modules or a subset, but they run in order, not in parallel tiers

**Agentic framework gap**: A real multi-agent system would have agents working simultaneously, sharing evidence, and triggering re-investigation when new information arrives. This is a state machine, not an agentic system.

### GAP 4: Test Coverage Is Extremely Low
**Severity: HIGH**

Existing tests:
- `test_veritas.py`: 20 unit tests (claimed, likely mocked)
- `test_security_agent.py`: Security agent tests
- `test_ioc_detector.py`: IOC detector tests
- `test_darknet_integration.py`: Darknet tests
- LangGraph tests: 3 test files
- Integration tests: 2 files

**Gap**: ~130+ Python files, maybe ~12 test files. Most modules have NO tests. The security tier modules (OWASP A01-A10, CSP, TLS, GDPR, PCI DSS) are completely untested. The OSINT sources have minimal testing.

**No end-to-end test** that runs the full pipeline and validates output quality.

### GAP 5: No Standardized Evidence Schema
**Severity: HIGH**

Each agent produces its own result format:
- ScoutResult, VisionResult, GraphResult, SecurityResult, JudgeDecision
- Plus OSINTResult from the OSINT layer
- Plus SecurityFinding from modules
- Plus AuditEvidence for the Judge

There's no unified evidence interface. The Judge has to deserialize and aggregate dicts from different formats. This makes correlation across agents fragile and ad-hoc.

### GAP 6: VLM Hallucination Risk Is Under-Addressed
**Severity: MEDIUM-HIGH**

Current mitigation: A text instruction appended to prompts ("Do NOT hallucinate"). This is the weakest possible defense.

**What's missing**:
- No JSON schema validation of VLM output (response_format with strict schema)
- No self-consistency checking (run same prompt N times, compare)
- No evidence grounding — VLM claims should be verifiable against DOM/HTML
- The Consensus Engine exists but isn't wired into VLM validation

### GAP 7: No Error Budget or SLO Tracking
**Severity: MEDIUM-HIGH**

The system has circuit breakers and fallbacks (good), but:
- No SLO definition: What's acceptable error rate? Max latency? Minimum score accuracy?
- No error budget tracking across the pipeline
- Degradation goes: "full NIM → fallback NIM → Tesseract → nothing." That last step ("nothing") is a cliff. The user gets a report that may have massive gaps with no clear warning.

### GAP 8: Product-Market Fit Is Undefined
**Severity: HIGH (Product-level)**

Who is this product for?

As-is, VERITAS tries to serve everyone:
- Security teams (OWASP checks, CVSS scoring)
- UX researchers (dark pattern detection)
- Consumers (trust score for "is this site safe?")
- Compliance teams (GDPR, PCI DSS checks)
- Darknet investigators (marketplace detection, TOR analysis)

**The problem**: Each persona needs a different product. A security team doesn't care about dark patterns. A consumer doesn't care about OWASP A08. Trying to serve all means serving none well.

### GAP 9: No API Versioning or Public Interface Contract
**Severity: MEDIUM**

The FastAPI backend has REST endpoints but:
- No API versioning (`/api/v1/...`)
- No OpenAPI/Swagger customization for the audit-specific endpoints
- The WebSocket event schema is undocumented beyond the README
- No rate limiting on the API level (only on the NIM client level)
- No authentication/authorization on the API

### GAP 10: Data Persistence Is Incomplete
**Severity: MEDIUM**

- SQLite database exists (`veritas_audits.db`) with repository pattern
- LanceDB vector store for evidence
- But: No audit history, no historical comparison, no trend analysis
- Audit results are ephemeral — stored during pipeline run, then only the final report persists

### GAP 11: Cost Model Is Unknown
**Severity: MEDIUM**

- NIM calls are tracked (call count), but not priced
- No cost-per-audit estimation
- No tier-based cost control (quick scan vs deep forensic cost difference)
- If this goes production, costs could spiral without governance

### GAP 12: The "Graph Investigation" Is Not Real Graph Analysis
**Severity: MEDIUM**

Despite its name and 1,985 lines, GraphInvestigator:
- Builds a NetworkX graph of domain→IP→registrar→hosting→nameserver
- Checks for inconsistencies and domain age
- Does NOT do real link analysis (PageRank, community detection, betweenness centrality)
- Does NOT correlate across multiple audits to build a "known bad actor" network
- Does NOT use the graph for anything beyond a per-audit summary

**What it should do**: Compare a site's infrastructure against a database of previously-flagged infrastructure. If example-phish.com and legit-site.com share a registrar/hosting/IP block AND example-phish.com was flagged — that's actionable intelligence.

### GAP 13: Agentic Framework Is Under-Utilized
**Severity: HIGH (Architecture-level)**

Current state: 5 agents orchestrated by a LangGraph state machine.

What's MISSING from the agentic paradigm:

1. **Tool Use**: Agents don't have tools — they have hardcoded paths. Real agents should be able to choose between: "scan this URL" vs "check reputation" vs "look up WHOIS" based on what they find.

2. **Memory Sharing**: Each agent works on serialized dicts passed through state. There's no shared working memory where agents can store and retrieve context during an investigation.

3. **Observation → Hypothesis → Test Cycle**: Agents don't reason — they execute. A real investigator would: "This page has a payment form → Is it HTTPS? → No? → Flag it → Check if any data is actually transmitted → Check the form action URL reputation." Current agents run independently.

4. **Multi-Agent Debate**: When Vision says "dark pattern detected" but Scout says "normal page," there's no mechanism for agents to reconcile conflicting evidence.

5. **Agent Self-Assessment**: Agents don't rate their own confidence or suggest follow-up investigations.

### GAP 14: Frontend Doesn't Reflect Full Pipeline Depth
**Severity: MEDIUM**

- Frontend shows: score, signals, patterns, security checks
- Missing: OSINT findings, WHOIS data, DNS results, SSL details, darknet intelligence, CVE matches, historical comparison
- The "Expert Mode" in reports doesn't expose the 22+ analysis modules or OSINT data

---

## Part 3: ITERATIVE SOLUTION DESIGN

### Iteration 1 — First Pass Solutions

| Gap | First Solution |
|-----|---------------|
| GAP 1 (OSINT not wired) | Add OSINT node to LangGraph pipeline |
| GAP 2 (Missing threat intel) | Build VirusTotal, URLhaus, Safe Browsing integrations |
| GAP 3 (Rigid pipeline) | Replace LangGraph with adaptive orchestrator |
| GAP 4 (Testing) | Write tests for all modules |
| GAP 5 (Evidence schema) | Create unified Evidence dataclass |
| GAP 6 (Hallucination) | Add JSON schema validation |
| GAP 7 (No SLO) | Define SLOs and track errors |
| GAP 8 (Product-market) | Focus on one persona first |
| GAP 9 (API contract) | Add versioning and OpenAPI |
| GAP 10 (Persistence) | Add audit history and trends |
| GAP 11 (Cost) | Track cost per audit |
| GAP 12 (Graph) | Add cross-audit correlation |
| GAP 13 (Agentic) | Convert to true multi-agent with tools |
| GAP 14 (Frontend) | Extend report visualization |

### Iteration 2 — Critique of Iteration 1

**What's wrong with Iteration 1**:

1. **Adding an OSINT node to LangGraph** doesn't solve the problem. LangGraph's state machine is still linear. The OSINT orchestrator already supports parallel execution — we need to leverage that, not bottleneck it through a node.

2. **Building VirusTotal integrations one-by-one** repeats the pattern we already have. Better approach: Create a pluggable threat intel registry pattern where new providers are added by dropping a file, not modifying core code.

3. **Replacing LangGraph entirely** is too disruptive. We already invested in LangGraph. Better: Layer adaptive behavior ON TOP of LangGraph by using conditional edges more aggressively and running parallel subgraphs.

4. **Writing tests for all 130 files** is a massive task. Better: Start with integration tests for the pipeline, then unit tests for modules with highest risk (scoring, threat intel).

5. **Unified Evidence dataclass** is good but needs to be designed around what the Judge needs, not as a "one size fits all."

6. **"Focus on one persona"** is too binary. We can have tiered output: Simple (consumer), Standard (developer), Deep (security team). Same pipeline, different report views.

### Iteration 3 — Refined Solutions

#### Solution A: Wire OSINT Properly

**Architecture Decision**: Don't add an OSINT "node" — make OSINT a **parallel data source** that feeds the Recon Scout.

```
                    ┌─────────────────────────┐
                    │    Recon Scout           │
                    │  (Playwright + DOM)      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     OSINT ORCHESTRATOR   │
                    │  (parallel, all sources)  │
                    │  DNS, WHOIS, SSL, VT,    │
                    │  URLhaus, SafeBrowsing    │
                    └─────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Intelligence Fusion     │
                    │  (correlate on-page +    │
                    │   external intelligence)  │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────▼────┐   ┌────────▼─────┐   ┌───────▼──────┐
    │ Security      │   │ VLM Vision   │   │ Threat Intel │
    │ Analysis      │   │ Analysis     │   │ Correlation  │
    └─────────┬────┘   └────────┬─────┘   └───────┬──────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Verdict Engine        │
                    └─────────────────────────┘
```

**Key insight**: Recon + OSINT run first and in parallel. Their combined intelligence THEN feeds three parallel analysis branches (Security, Vision, Threat). The Verdict Engine aggregates everything.

#### Solution B: Pluggable Threat Intel Registry

```python
# veritas/intel/registry.py
# Auto-discovers all sources in veritas/intel/sources/

INTEL_SOURCES = {
    "virustotal": {"api_key": "VIRUSTOTAL_API_KEY", "free_tier": "500/day"},
    "urlhaus": {"api_key": None, "free_tier": "unlimited"},
    "safebrowsing": {"api_key": "GOOGLE_SAFE_BROWSING_KEY", "free_tier": "10K/day"},
    "abuseipdb": {"api_key": "ABUSEIPDB_API_KEY", "free_tier": "1K/day"},
    "shodan": {"api_key": "SHODAN_API_KEY", "free_tier": "100/month"},
    "crtsh": {"api_key": None, "free_tier": "unlimited"},
    "wayback": {"api_key": None, "free_tier": "unlimited"},
}
```

Each source implements a uniform `ThreatIntelSource` protocol:
```python
@dataclass
class ThreatIntelFinding:
    source: str              # "virustotal"
    category: str            # "malware", "phishing", "suspicious"
    severity: str            # "low", "medium", "high", "critical"
    score: float             # 0.0 - 1.0
    evidence: dict           # Raw data from source
    confidence: float        # 0.0 - 1.0
    actionable: bool         # True if requires user action
    remediation: str = ""    # What to do about it
```

#### Solution C: Keep LangGraph, Layer Adaptive Behavior

Instead of throwing away LangGraph:

1. **Use subgraphs**: Create OSINT subgraph, Security subgraph, Vision subgraph — run them in parallel via `asyncio.gather()` within a LangGraph super-node.

2. **Conditional edges for depth**: If Intelligence Fusion finds something suspicious → route to "deep analysis" subgraph. If clean → route directly to Verdict.

3. **Preserve loop-back**: Keep the existing judge → scout loop for multi-page investigation.

#### Solution D: Unified Evidence Schema (Judge-Centric)

```python
@dataclass
class Evidence:
    id: str                  # Unique: "scout-001", "vt-001"
    source: str              # Which agent/module produced this
    category: str            # "security", "osint", "vision", "dark_pattern"
    type: str                # "finding", "indicator", "metric"
    severity: str            # "info", "warning", "critical"
    title: str               # Human-readable title
    detail: str              # Description
    raw_data: dict           # Original data
    confidence: float        # 0.0 - 1.0
    cwe_id: str = ""         # CWE-79, CWE-20, etc.
    cvss_score: float = 0.0  # If applicable
    mitre_technique: str = "" # "T1190" etc.
    remediation: str = ""    # Actionable fix
    timestamp: float = 0.0
```

Every agent and module outputs Evidence instances. The Judge aggregates Evidence lists.

#### Solution E: VLM Hallucination Defense-in-Depth

Layer 1: **Structured output** — Use `response_format={"type": "json_schema", "json_schema": {...}}` to force valid JSON.

Layer 2: **Evidence grounding** — After VLM says "suspicious button found," verify the claim against the DOM (does the button actually exist?).

Layer 3: **Self-consistency** — For critical findings, run the same image through both primary and fallback VLM models. Consensus = higher confidence.

Layer 4: **Score penalty** — If VLM output can't be grounded or validated, reduce its weight in the final score.

#### Solution F: Tiered Product Strategy

Three tiers, same pipeline, different output depth:

| Tier | Target | Depth | OSINT | Active Test | Report |
|------|--------|-------|-------|-------------|--------|
| **Quick** | Consumers | On-page + basic headers | None | None | Simple (Green/Yellow/Red) |
| **Standard** | Developers | Full pipeline | DNS, WHOIS, Safe Browsing | Passive only | Standard (Score + Findings) |
| **Deep** | Security teams | Everything | All sources + cross-audit | Non-destructive active probes | Expert (MITRE, CVE, Remediation) |

This solves the product-market gap by making the product serve all personas through **depth control**, not feature fragmentation.

---

## Part 4: PRACTICAL IMPLEMENTATION PRIORITIES

### Phase 1: Fix The Foundation (Week 1-2)
1. Wire OSINT Orchestrator into the pipeline (GAP 1)
2. Add VirusTotal + URLhaus integrations (GAP 2)
3. Create unified Evidence schema (GAP 5)
4. Implement JSON schema validation for VLM (GAP 6, Layer 1)

### Phase 2: Intelligence Depth (Week 3-4)
5. Add WHOIS, DNS, SSL analysis to Recon phase (GAP 2)
6. Implement Intelligence Fusion module (combines on-page + OSINT)
7. Add Google Safe Browsing + crt.sh (GAP 2)
8. VLM evidence grounding (GAP 6, Layer 2)

### Phase 3: Verdict Engine Upgrade (Week 5-6)
9. MITRE ATT&CK mapping for all findings
10. Prioritized remediation guidance engine
11. Confidence interval calculation (based on data quality)
12. Multi-format export (JSON, Markdown, PDF-ready)

### Phase 4: Pipeline Evolution (Week 7-8)
13. Parallel execution for Security + Vision + Threat Intel
14. Conditional branching (deep-scan loop)
15. Agent tool-use abstraction
16. Shared working memory between agents

### Phase 5: Production Readiness (Week 9-10)
17. Comprehensive test suite (GAP 4)
18. API versioning (GAP 9)
19. Audit history persistence (GAP 10)
20. Cost tracking per audit (GAP 11)

### Phase 6: Advanced Capabilities (Future)
21. Cross-audit graph correlation (GAP 12)
22. Continuous monitoring with delta reports
23. Bulk URL scanning
24. Webhook-based alerts for score changes

---

## Part 5: STRATEGIC DECISIONS (Resolved)

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Primary persona | **Security team → Developer → Consumer** | Build for the hardest use case first (security team), then simplify downward |
| 2 | OSINT build vs. integrate | **Wire existing sources first**, then add free high-value ones (URLhaus, crt.sh, Wayback, Safe Browsing) | Use what's built and parked, add free tier sources, no API cost bloat |
| 3 | LangGraph investment | **Keep investing + research full capabilities** | Subgraphs, parallel nodes, commands, interruptibility, checkpointer — all unused potential worth exploring before abandoning |
| 4 | Active testing depth | **Configurable, Quick/Standard = free passive, Deep = premium with non-destructive active probes** | Same model as darknet tier: premium feature for advanced depth |
| 5 | Revenue model | **Parked** — First priority is making the tech world-class for cybersecurity | Revenue discussion deferred until the product works properly |
| 6 | Analysis modules | **Keep all 22+ modules, improve weak ones, upgrade to produce real findings** | No pruning — fix, don't discard. Every module must produce actionable intelligence |

### Darknet Tier Status
Darknet intelligence (6 marketplace static feeds) is marked as **parked/premium**. Not a Phase 1 priority. Will be revisited and completed after core pipeline works.

---

*Document Version: 3.0 — 14 gaps identified, 6 strategic decisions resolved, 3 solution iterations. Ready for Phase 1 planning.*
