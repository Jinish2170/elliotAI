# ELLIOT — Implementation Tracker

> **Single source of truth for build progress. Update checkboxes as tasks complete.**
> **Rule: Never advance to next phase until the Phase Gate is ✅**

---

## Status Dashboard

| Phase | Status | Progress | Target |
|-------|--------|----------|--------|
| **Phase 0:** Scaffold & Config | 🟡 IN PROGRESS | 0/9 | Days 1–2 |
| **Phase 1:** Core Clients & Scout | ⬜ NOT STARTED | 0/8 | Days 3–7 |
| **Phase 2:** Vision + Graph + Judge | ⬜ NOT STARTED | 0/12 | Days 8–16 |
| **Phase 3:** Orchestration & Evidence | ⬜ NOT STARTED | 0/10 | Days 17–24 |
| **Phase 4:** UI & Reporting | ⬜ NOT STARTED | 0/8 | Days 25–30 |
| **Phase 5:** Testing & Evaluation | ⬜ NOT STARTED | 0/7 | Days 31–35 |

---

## Critical Corrections (from codebase analysis)

> These are real findings from analyzing the base model projects. The original `agent.md` made
> incorrect assumptions about what code exists. This tracker reflects **reality**.

| Original Assumption | Reality | Impact |
|---------------------|---------|--------|
| "Port `glass_box/browser.py`" | No standalone browser.py exists. Stealth code is inline in `backend/main.py` ~30 lines | Must **build** scout.py from scratch, merging 2 inline patterns |
| "Port `glass_box/scoring.py`" | No scoring.py exists. Scoring is done by Gemini VLM prompt | Must **build** trust_scorer.py from scratch using formula in agent.md |
| "Port `glass_box/analyzer.py`" | No analyzer.py exists | Must **build** dom_analyzer.py from scratch |
| "Swap FAISS → LanceDB" | RAGv5 uses **Weaviate**, not FAISS | Migration is **Weaviate → LanceDB**, different API surface |
| "Port `rag_engine.py` hybrid search" | No rag_engine.py exists. RAGv5 uses simple Weaviate similarity | Must **build** hybrid retrieval (BM25+Dense+Rerank) from scratch |
| "Port confidence scoring" | No confidence scoring exists in codebase | Formula in agent.md is a **design**, not extracted code |
| "4-week timeline" | ~10 referenced files don't exist; building from scratch | Realistic timeline: **5–6 weeks** |

### What DOES Exist & Is Reusable

| Pattern | Source File | Lines | Reuse Quality |
|---------|-------------|-------|---------------|
| Stealth browser (mobile viewport, navigator patches) | `glass-box-portal/backend/main.py` → `capture_mobile_screenshot()` | ~30 lines | ✅ Good — merge into scout.py |
| Enhanced stealth (UA rotation, JS patches, proxy) | `Rag_v5.0.0/rag-core/ingestion/scrapers.py` → `StealthScraper` | ~200 lines | ✅ Excellent — carry forward |
| Rate limiter + disk cache + retry decorator | `Rag_v5.0.0/rag-core/ingestion/scrapers.py` | ~80 lines | ✅ Excellent — use for nim_client.py |
| Content extraction via JS DOM cloning | `Rag_v5.0.0/rag-core/ingestion/scrapers.py` → `_extract_with_js()` | ~40 lines | ✅ Good — use for dom_analyzer.py |
| LangChain prompt template pattern | `Rag_v5.0.0/rag-core/retrieval/qa.py` | ~50 lines | ✅ Good — use for judge prompts |
| Centralized config with dotenv | `Rag_v5.0.0/rag-core/config/settings.py` | ~25 lines | ✅ Good — extend for elliot config |
| Streaming response pattern | `glass-box-portal/backend/main.py` | ~20 lines | 🟡 Later — for Streamlit SSE |

---

## Phase 0: Scaffold & Config (Days 1–2)

### Tasks

- [ ] **P0.1** Create `elliot/` root directory with `__init__.py`
- [ ] **P0.2** Create all sub-packages: `agents/`, `core/`, `analysis/`, `reporting/`, `ui/`, `tests/`, `data/`
- [ ] **P0.3** Create `elliot/requirements.txt` — all deps with minimum versions, verified for 8GB RAM
- [ ] **P0.4** Create `elliot/.env.template` — all required and optional env vars documented
- [ ] **P0.5** Create `elliot/config/settings.py` — centralized config extending RAGv5 pattern
- [ ] **P0.6** Create `elliot/config/dark_patterns.py` — full taxonomy with 5 categories + VLM prompts
- [ ] **P0.7** Create `elliot/config/trust_weights.py` — scoring weights, override rules, tier thresholds
- [ ] **P0.8** Create `data/` subdirectories: `evidence/`, `reports/`, `cache/`, `vectordb/`
- [ ] **P0.9** Verify all imports resolve and directory auto-creation works

### Phase Gate 0 → 1
```
✅ All config files importable without errors
✅ `from config.settings import *` works
✅ `from config.dark_patterns import DARK_PATTERN_TAXONOMY` works
✅ `from config.trust_weights import TrustWeights` works
✅ Data directories auto-create on import
```

---

## Phase 1: Core Clients & Scout Agent (Days 3–7)

### Tasks

- [ ] **P1.1** Create `core/nim_client.py` — NIM API wrapper (OpenAI-compatible)
- [ ] **P1.2** Implement 4-level fallback chain: NIM primary → NIM fallback → Tesseract → Heuristic
- [ ] **P1.3** Implement rate limiting (asyncio.Semaphore) + disk-based response cache (24h TTL)
- [ ] **P1.4** Implement retry logic (tenacity: exponential backoff, 3 attempts)
- [ ] **P1.5** Create `agents/scout.py` — Stealth Playwright browser
- [ ] **P1.6** Implement temporal screenshot capture (Screenshot_A at t0, Screenshot_B at t+delay)
- [ ] **P1.7** Implement CAPTCHA detection (content scan + iframe URL scan)
- [ ] **P1.8** Implement page metadata extraction (title, links, forms, scripts, SSL, cookies)

### Phase Gate 1 → 2
```
✅ NIMClient can send a text prompt and get a response (or gracefully fallback)
✅ NIMClient can send an image + prompt and get a response (or gracefully fallback)
✅ NIMClient caches responses and respects rate limits
✅ StealthScout can navigate to any URL without being blocked as a bot
✅ StealthScout captures temporal screenshots (2 files saved to data/evidence/)
✅ StealthScout detects CAPTCHAs and returns CAPTCHA_BLOCKED status
✅ StealthScout extracts page metadata as structured dict
✅ All operations complete within timeout limits
```

### Verification Commands
```bash
# Test NIM client (requires API key in .env)
cd elliot && python -c "import asyncio; from core.nim_client import NIMClient; c = NIMClient(); print(asyncio.run(c.generate_text('Hello')))"

# Test Scout (requires playwright install)
cd elliot && python -c "import asyncio; from agents.scout import StealthScout
async def test():
    async with StealthScout() as s:
        r = await s.investigate('https://example.com', temporal_delay=3)
        print(r.status, len(r.screenshots))
asyncio.run(test())"
```

---

## Phase 2: Vision + Graph + Judge Agents (Days 8–16)

### Tasks

- [ ] **P2.1** Create `agents/vision.py` — VLM-based dark pattern analyzer
- [ ] **P2.2** Implement prompt builder from `dark_patterns.py` taxonomy (generates VLM prompts per category)
- [ ] **P2.3** Implement structured JSON output parsing from VLM responses
- [ ] **P2.4** Implement temporal comparison logic (compare Screenshot_A answers vs Screenshot_B answers)
- [ ] **P2.5** Create `core/knowledge_graph.py` — NetworkX graph builder with typed nodes/edges
- [ ] **P2.6** Create `agents/graph_investigator.py` — entity extraction + external verification
- [ ] **P2.7** Implement Tavily search integration for entity cross-referencing
- [ ] **P2.8** Implement WHOIS + DNS lookup for domain verification
- [ ] **P2.9** Create `agents/judge.py` — verdict synthesis with NIM LLM
- [ ] **P2.10** Create `core/trust_scorer.py` — weighted multi-signal scoring engine
- [ ] **P2.11** Implement override rules (hard stops for domain age, SSL, temporal failures)
- [ ] **P2.12** Create `analysis/dom_analyzer.py` — structural DOM analysis (forms, scripts, link patterns)

### Phase Gate 2 → 3
```
✅ VisionAgent accepts screenshot path + returns structured dark pattern findings (JSON)
✅ VisionAgent handles temporal comparison (detects fake timers between 2 screenshots)
✅ GraphInvestigator builds a NetworkX graph from extracted entities
✅ GraphInvestigator verifies entities via Tavily search + WHOIS
✅ JudgeAgent synthesizes vision + graph evidence into a verdict string
✅ TrustScorer computes a 0-100 score from 5 sub-signals with correct weights
✅ Override rules correctly cap/force scores (e.g., SSL=None → max 50)
✅ Each agent works standalone with mock inputs
```

---

## Phase 3: Orchestration & Evidence Store (Days 17–24)

### Tasks

- [ ] **P3.1** Create `core/orchestrator.py` — LangGraph state machine
- [ ] **P3.2** Define `AuditState` TypedDict with all required fields
- [ ] **P3.3** Implement 7-state transition map (START→SCOUT→VISION→GRAPH→JUDGE→REPORT→END)
- [ ] **P3.4** Implement budget controls (max_iterations, max_pages, timeout enforcement)
- [ ] **P3.5** Implement backtracking logic (Judge → Scout when confidence < threshold)
- [ ] **P3.6** Create `core/evidence_store.py` — LanceDB adapter for evidence storage
- [ ] **P3.7** Implement embedding storage + similarity search interface
- [ ] **P3.8** Create `analysis/temporal_analyzer.py` — screenshot diff logic
- [ ] **P3.9** Create `analysis/meta_analyzer.py` — WHOIS + SSL + DNS enrichment
- [ ] **P3.10** Wire all 4 agents into the LangGraph cyclic graph + end-to-end test

### Phase Gate 3 → 4
```
✅ Orchestrator runs full URL → Report pipeline on synthetic test site
✅ Backtracking works: Judge can request Scout to visit additional pages
✅ Budget controls terminate the loop after max_iterations
✅ Evidence persists in LanceDB across agent steps
✅ Temporal analyzer detects timer resets between screenshots
✅ Full pipeline completes within 2 minutes for a single-page audit
```

---

## Phase 4: UI & Reporting (Days 25–30)

### Tasks

- [ ] **P4.1** Create `reporting/templates/audit_report.html` — Jinja2 HTML template
- [ ] **P4.2** Create `reporting/report_generator.py` — WeasyPrint HTML→PDF engine
- [ ] **P4.3** Create `reporting/visualizations.py` — NetworkX graph → matplotlib PNG renders
- [ ] **P4.4** Create `ui/app.py` — Streamlit main app with URL input
- [ ] **P4.5** Create `ui/components/live_log.py` — Real-time agent activity feed
- [ ] **P4.6** Create `ui/components/score_gauge.py` — Trust score visualization
- [ ] **P4.7** Create `ui/components/evidence_viewer.py` — Screenshot + annotation viewer
- [ ] **P4.8** End-to-end: URL input → live agent logs → PDF download

### Phase Gate 4 → 5
```
✅ Streamlit app loads without errors
✅ URL input triggers full audit pipeline
✅ Live log shows agent activity in real-time
✅ Trust score gauge renders correctly (0-100 scale with color coding)
✅ PDF report generates with all sections (summary, evidence, findings, graph, score)
✅ PDF includes screenshot images and knowledge graph visualization
```

---

## Phase 5: Testing & Evaluation (Days 31–35)

### Tasks

- [ ] **P5.1** Create 5 synthetic test HTML sites (fake_urgency, hidden_unsubscribe, pre_selected, fake_reviews, clean_site)
- [ ] **P5.2** Write unit tests: `test_scout.py`, `test_vision.py`, `test_graph.py`, `test_trust_scorer.py`
- [ ] **P5.3** Write integration test: `test_integration.py` (full pipeline on synthetic sites)
- [ ] **P5.4** Run Tier 1 evaluation: synthetic sites (known ground truth)
- [ ] **P5.5** Run Tier 2 evaluation: known scam URLs (PhishTank/URLhaus)
- [ ] **P5.6** Run Tier 3 evaluation: legitimate sites (false positive check)
- [ ] **P5.7** Compute & document metrics (Detection Rate, False Alarm Rate, Trust Score MAE, Latency)

### Phase Gate 5 → DONE
```
✅ All unit tests pass
✅ Integration test completes on all 5 synthetic sites
✅ Detection Rate > 80% on synthetic sites
✅ False Alarm Rate < 20% on legitimate sites
✅ Average audit latency < 120 seconds
✅ Metrics documented in final report
```

---

## Dependency Map

```
config/settings.py ──────┐
config/dark_patterns.py ──┤
config/trust_weights.py ──┤
                          ├──→ core/nim_client.py ──→ agents/vision.py ──┐
                          │                                              │
                          ├──→ agents/scout.py ─────────────────────────┤
                          │                                              ├──→ core/orchestrator.py ──→ ui/app.py
                          ├──→ core/knowledge_graph.py ──→ agents/graph_investigator.py ──┤
                          │                                              │
                          ├──→ core/trust_scorer.py ──→ agents/judge.py ┘
                          │
                          ├──→ core/evidence_store.py (LanceDB)
                          │
                          ├──→ analysis/dom_analyzer.py
                          ├──→ analysis/temporal_analyzer.py
                          └──→ analysis/meta_analyzer.py
```

---

## File Checklist (All Planned Files)

### Config Layer
- [ ] `elliot/__init__.py`
- [ ] `elliot/config/__init__.py`
- [ ] `elliot/config/settings.py`
- [ ] `elliot/config/dark_patterns.py`
- [ ] `elliot/config/trust_weights.py`

### Agent Layer
- [ ] `elliot/agents/__init__.py`
- [ ] `elliot/agents/scout.py`
- [ ] `elliot/agents/vision.py`
- [ ] `elliot/agents/graph_investigator.py`
- [ ] `elliot/agents/judge.py`

### Core Layer
- [ ] `elliot/core/__init__.py`
- [ ] `elliot/core/nim_client.py`
- [ ] `elliot/core/trust_scorer.py`
- [ ] `elliot/core/evidence_store.py`
- [ ] `elliot/core/knowledge_graph.py`
- [ ] `elliot/core/orchestrator.py`

### Analysis Layer
- [ ] `elliot/analysis/__init__.py`
- [ ] `elliot/analysis/dom_analyzer.py`
- [ ] `elliot/analysis/temporal_analyzer.py`
- [ ] `elliot/analysis/meta_analyzer.py`
- [ ] `elliot/analysis/pattern_matcher.py`

### Reporting Layer
- [ ] `elliot/reporting/__init__.py`
- [ ] `elliot/reporting/report_generator.py`
- [ ] `elliot/reporting/visualizations.py`
- [ ] `elliot/reporting/templates/audit_report.html`

### UI Layer
- [ ] `elliot/ui/app.py`
- [ ] `elliot/ui/components/live_log.py`
- [ ] `elliot/ui/components/score_gauge.py`
- [ ] `elliot/ui/components/evidence_viewer.py`

### Tests
- [ ] `elliot/tests/__init__.py`
- [ ] `elliot/tests/test_scout.py`
- [ ] `elliot/tests/test_vision.py`
- [ ] `elliot/tests/test_graph.py`
- [ ] `elliot/tests/test_trust_scorer.py`
- [ ] `elliot/tests/test_integration.py`
- [ ] `elliot/tests/test_sites/` (5 HTML files)

### Infrastructure
- [ ] `elliot/requirements.txt`
- [ ] `elliot/.env.template`
- [ ] `elliot/data/evidence/.gitkeep`
- [ ] `elliot/data/reports/.gitkeep`
- [ ] `elliot/data/cache/.gitkeep`
- [ ] `elliot/data/vectordb/.gitkeep`

---

*Last updated: Phase 0 start*
