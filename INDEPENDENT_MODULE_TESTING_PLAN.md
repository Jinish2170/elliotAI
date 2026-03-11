# Veritas — Independent Module Testing Plan

**Created:** 2026-03-11  
**Purpose:** Test each module/agent independently to see its full potential without API budget limits  
**Target Site:** `avrut.com` (known legitimate company) + `example.com` (baseline)

---

## Strategy

Instead of running the full orchestrator (which masks individual module behavior behind budget limits, tier configs, and error fallbacks), we test **each module in isolation** with:

1. **No budget limits** — remove NIM call caps, page limits, timeout restrictions
2. **Full logging** — capture complete input/output for every module
3. **Results documented** — each test writes a `.md` report in `testing/results/`
4. **Sequential execution** — one module at a time so we can analyze each properly

---

## Test Phases (Execution Order)

### Phase T1: OSINT & Data Sources (No API cost — free lookups)
> These run without NIM credits. They tell us what intelligence the system can actually gather.

| # | Module | File | What We Test | API Key Needed? |
|---|--------|------|-------------|-----------------|
| T1.1 | DNS Lookup | `veritas/osint/sources/dns_lookup.py` | All record types (A, AAAA, MX, TXT, NS, SOA, CNAME) for avrut.com | No |
| T1.2 | WHOIS Lookup | `veritas/osint/sources/whois_lookup.py` | Full WHOIS data (registrar, dates, nameservers, privacy) | No |
| T1.3 | SSL Certificate | `veritas/osint/sources/ssl_verify.py` | Certificate chain, issuer, SAN domains, expiry | No |
| T1.4 | IOC Detector | `veritas/osint/ioc_detector.py` | Extract IOCs from avrut.com page HTML | No |
| T1.5 | Attack Pattern Mapper | `veritas/osint/attack_patterns.py` | Map IOCs to MITRE ATT&CK techniques | No |
| T1.6 | CTI (Cyber Threat Intel) | `veritas/osint/cti.py` | Full threat assessment with IOC + ATT&CK | No |
| T1.7 | URLVoid | `veritas/osint/sources/urlvoid.py` | Domain reputation (AV engine detections) | **Yes** — `URLVOID_API_KEY` |
| T1.8 | AbuseIPDB | `veritas/osint/sources/abuseipdb.py` | IP abuse confidence score | **Yes** — `ABUSEIPDB_API_KEY` |
| T1.9 | OSINT Orchestrator | `veritas/osint/orchestrator.py` | All sources together via `query_all()` per category | Partial |
| T1.10 | Phishing Checker | `veritas/analysis/phishing_checker.py` | Google Safe Browsing + heuristic patterns | Optional key |
| T1.11 | Meta Analyzer | `veritas/analysis/meta_analyzer.py` | Quick domain trust (WHOIS age, SSL, DNS, headers) | No |

**Expected Output:** Complete OSINT profile of avrut.com — we see exactly which sources work, which fail, and what data each provides.

---

### Phase T2: Scout & Browser Automation (No NIM cost — browser only)
> Tests browser navigation, scrolling, link discovery, metadata extraction.

| # | Module | File | What We Test | Needs |
|---|--------|------|-------------|-------|
| T2.1 | Scout Basic | `veritas/agents/scout.py` | Navigate avrut.com, capture screenshots, extract metadata, DOM analysis | Playwright |
| T2.2 | Link Explorer | `veritas/agents/scout_nav/link_explorer.py` | Discover all navigable links from avrut.com landing page | Playwright |
| T2.3 | Scroll Orchestrator | `veritas/agents/scout_nav/scroll_orchestrator.py` | Full scroll with lazy-load detection (15 cycles max) | Playwright |
| T2.4 | Lazy Load Detector | `veritas/agents/scout_nav/lazy_load_detector.py` | MutationObserver injection and DOM change tracking | Playwright |
| T2.5 | Scout Multi-Page | `veritas/agents/scout.py` `explore_multi_page()` | Visit all discovered pages (up to 8) with scroll on each | Playwright |

**Expected Output:** Full navigation map of avrut.com — all pages visited, all screenshots captured, scroll behavior documented, link priorities listed.

---

### Phase T3: Analysis Modules (No external API — runs on captured data)
> These process data already captured by Scout. No NIM or external API calls.

| # | Module | File | What We Test | Input From |
|---|--------|------|-------------|-----------|
| T3.1 | DOM Analyzer | `veritas/analysis/dom_analyzer.py` | Hidden elements, pre-selected checkboxes, tracking scripts, privacy links | Scout page |
| T3.2 | Form Validator | `veritas/analysis/form_validator.py` | Cross-domain actions, password fields, autocomplete, payment processors | Scout page |
| T3.3 | JS Analyzer | `veritas/analysis/js_analyzer.py` | eval(), Base64, crypto miners, obfuscation, WebSocket mining | Scout page |
| T3.4 | Redirect Analyzer | `veritas/analysis/redirect_analyzer.py` | Redirect chains, cross-domain hops, HTTPS downgrade | URL |
| T3.5 | Security Headers | `veritas/analysis/security_headers.py` | CSP, HSTS, X-Frame-Options, X-Content-Type-Options | Scout headers |
| T3.6 | Temporal Analyzer (Heuristic) | `veritas/analysis/temporal_analyzer.py` | Pixel comparison between t0 and t+delay screenshots | Scout screenshots |
| T3.7 | Pattern Matcher | `veritas/analysis/pattern_matcher.py` | Dark pattern taxonomy matching on DOM/temporal findings | Findings |

**Expected Output:** Complete analysis profile — every security signal, dark pattern indicator, and form risk detected from avrut.com.

---

### Phase T4: Security Agent (No external API — all rule-based)
> Runs all 16+ security modules in tier-based execution.

| # | Module | File | What We Test |
|---|--------|------|-------------|
| T4.1 | Security Agent (Full) | `veritas/agents/security_agent.py` | All tiers: FAST + MEDIUM + DEEP (cookies, CSP, TLS, OWASP A01-A10, GDPR, PCI DSS, darknet indicators) |

**Expected Output:** Complete security assessment with CVSS scores, CWE mappings, compliance status.

---

### Phase T5: Vision Agent (Uses NIM credits — **no budget limit**)
> This is the expensive phase. We run Vision with NO `nim_budget` cap.

| # | Module | File | What We Test | NIM Calls |
|---|--------|------|-------------|-----------|
| T5.1 | Vision 5-Pass Pipeline | `veritas/agents/vision.py` | All 5 passes on ALL screenshots (no budget cutoff) | ~5 per screenshot |
| T5.2 | Vision Temporal | `veritas/agents/vision/temporal_analysis.py` | SSIM + optical flow between t0/t+delay | 2 per pair |
| T5.3 | Vision Static Analysis | `veritas/agents/vision.py` | Static dark pattern detection on each screenshot | Varies |

**Expected Output:** Full dark pattern analysis — every pass result, temporal findings, confidence per category. We see exactly what Vision Agent finds when unconstrained.

---

### Phase T6: Graph Investigator (Uses NIM + Tavily — **no budget limit**)
> Entity verification + knowledge graph building.

| # | Module | File | What We Test |
|---|--------|------|-------------|
| T6.1 | Graph Investigation | `veritas/agents/graph_investigator.py` | Full entity extraction, OSINT integration, Tavily search verification, knowledge graph |
| T6.2 | Graph + All OSINT | `veritas/agents/graph_investigator.py` | `_run_osint_investigation()` with ALL categories (DNS, WHOIS, SSL, THREAT_INTEL, REPUTATION, SOCIAL) |

**Expected Output:** Complete knowledge graph of avrut.com entities — verified vs unverifiable vs contradicted, with all OSINT data integrated.

---

### Phase T7: Judge Agent (Uses NIM — **no budget limit**)  
> Final verdict synthesis.

| # | Module | File | What We Test |
|---|--------|------|-------------|
| T7.1 | Judge Scoring | `veritas/agents/judge.py` | Site type detection, strategy selection, trust score calculation with full evidence |
| T7.2 | Judge Verdict | `veritas/agents/judge.py` | Dual verdict (technical + non-technical) with full narrative |
| T7.3 | Judge Strategies | `veritas/agents/judge/strategies/*.py` | Scoring weights and adjustments for detected site type |

**Expected Output:** Full verdict document — trust score breakdown, risk level, recommendations, CWE/CVSS entries.

---

### Phase T8: Full Pipeline (No limits — end to end)
> After validating each module works, run the full orchestrator with all limits removed.

| # | Module | File | What We Test |
|---|--------|------|-------------|
| T8.1 | Full Orchestrator | `veritas/core/orchestrator.py` | Complete audit of avrut.com — all agents, all pages, no budget limits |

**Expected Output:** Complete audit result compared against individual module outputs to verify nothing is lost in the pipeline.

---

## Test Infrastructure

### Directory Structure
```
testing/
├── results/                    # All test output docs go here
│   ├── T1_osint/              
│   │   ├── T1.1_dns.md
│   │   ├── T1.2_whois.md
│   │   ├── ...
│   ├── T2_scout/
│   ├── T3_analysis/
│   ├── T4_security/
│   ├── T5_vision/
│   ├── T6_graph/
│   ├── T7_judge/
│   └── T8_full_pipeline/
├── scripts/                    # Test runner scripts
│   ├── test_t1_osint.py       # Phase T1 test runner
│   ├── test_t2_scout.py       # Phase T2 test runner
│   ├── test_t3_analysis.py    # Phase T3 test runner
│   ├── test_t4_security.py    # Phase T4 test runner
│   ├── test_t5_vision.py      # Phase T5 test runner
│   ├── test_t6_graph.py       # Phase T6 test runner
│   ├── test_t7_judge.py       # Phase T7 test runner
│   └── test_t8_full.py        # Phase T8 test runner
├── data/                       # Captured data shared between phases
│   ├── screenshots/            # Scout screenshots (used by T3, T5)
│   ├── html/                   # Saved page HTML (used by T3, T4)
│   └── metadata/               # Scout metadata JSON (used by T3, T6)
└── TESTING_PROGRESS.md         # Running log of all test executions
```

### Report Format (each `.md` result file)
```markdown
# Test [ID] — [Module Name]
**Date:** YYYY-MM-DD HH:MM  
**Target:** avrut.com  
**Duration:** X.Xs  
**Status:** PASS / PARTIAL / FAIL / ERROR

## Input
<what was fed to the module>

## Output
<complete raw output — JSON, dict, or formatted>

## Analysis
- What worked
- What failed
- What was unexpected
- Data quality assessment

## Verdict
<one-line summary: does this module deliver on its promise?>
```

---

## Execution Rules

1. **One phase at a time** — complete T1 fully before starting T2
2. **Every module output saved** — raw JSON + formatted .md report
3. **No budget limits during testing** — remove all `nim_budget`, `max_pages`, timeout caps
4. **Errors are documented, not hidden** — if a module fails, log the full traceback
5. **No fake/fallback data** — if a module can't produce results, report empty, not synthetic
6. **Shared data flows forward** — T2 (Scout) captures data that T3/T4/T5 consume
7. **Compare module output vs pipeline output** — T8 validates nothing is lost

---

## API Key Status (Check Before Starting)

| Key | Env Variable | Status | Needed For |
|-----|-------------|--------|-----------|
| NVIDIA NIM | `NVIDIA_NIM_API_KEY` | ✅ Set | T5 Vision, T6 Graph, T7 Judge |
| Tavily | `TAVILY_API_KEY` | ✅ Set | T6 Graph entity verification |
| URLVoid | `URLVOID_API_KEY` | ❓ Check | T1.7 Domain reputation |
| AbuseIPDB | `ABUSEIPDB_API_KEY` | ❓ Check | T1.8 IP abuse scoring |
| Google Safe Browsing | `GOOGLE_SAFE_BROWSING_KEY` | ❓ Check | T1.10 Phishing detection |

---

## Success Criteria

After completing all 8 phases, we will know:
1. **Exactly which modules work** and to what extent
2. **What data each module produces** with full evidence
3. **Where the bottlenecks are** (API failures, timeouts, missing data)
4. **What NIM costs** for a full unconstrained audit
5. **Comparison: individual vs pipeline** — what gets lost in orchestration
6. **Actionable fix list** — prioritized by impact on final audit quality
