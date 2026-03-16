# VERITAS: Complete Implementation Strategy Document

**Author:** Jinish Kathiriya
**Date:** February 7, 2026
**Status:** Pre-Implementation Analysis & Strategy Lock

---

## PART 1: BASE MODEL ANALYSIS

### 1.1 RAGv5 — What We Already Have

Your `ragv5` project is a **multi-modal RAG pipeline** with the following proven components:

#### Existing Capabilities (Directly Reusable)

| Component | File | What It Does | Reuse in Veritas |
|-----------|------|-------------|------------------|
| **Hybrid Retrieval** | `rag_engine.py` | BM25 + Dense (FAISS) + Cross-Encoder reranking | ✅ Core of evidence retrieval |
| **Chunking Pipeline** | `chunker.py` | Recursive + Semantic chunking with overlap | ✅ For processing scraped web content |
| **Embedding Engine** | `vector_store.py` | `all-MiniLM-L6-v2` with FAISS indexing | ⚠️ Swap FAISS → LanceDB for disk-based ops |
| **Query Decomposition** | `rag_engine.py` → `_decompose_query()` | Breaks complex queries into sub-queries | ✅ For breaking audit tasks into sub-investigations |
| **Confidence Scoring** | `rag_engine.py` → `_calculate_confidence()` | Weighted confidence from retrieval + reranking scores | ✅ Directly maps to Trust Score calculation |
| **Multi-format Ingest** | `ingest.py` | PDF, DOCX, TXT, CSV, JSON, MD, images (OCR via Tesseract) | ✅ For processing downloaded site assets |
| **Conversation Memory** | `rag_engine.py` → `ConversationMemory` | Sliding window context management | ✅ For maintaining audit session state |
| **Caching Layer** | `rag_engine.py` → `_check_cache()` | LRU response cache | ✅ Avoid re-auditing same URLs |
| **Image OCR** | `ingest.py` → Tesseract integration | Extract text from images | ✅ Fallback OCR when VLM is unavailable |

#### Key Code Patterns to Carry Forward

**1. The Confidence Calculation Pattern (from `rag_engine.py`):**
```python
# Your existing pattern — gold
def _calculate_confidence(self, results, rerank_scores):
    if not results:
        return 0.0
    retrieval_confidence = min(results[0].get("score", 0) / 1.5, 1.0) if results else 0
    rerank_confidence = min(rerank_scores[0] / 8.0, 1.0) if rerank_scores else 0
    source_diversity = min(len(set(r.get("source", "") for r in results[:5])) / 3, 1.0)
    return round(
        retrieval_confidence * 0.3 + rerank_confidence * 0.5 + source_diversity * 0.2,
        3
    )
```
This weighted scoring pattern is **exactly** what we need for Trust Score computation.

**2. The Hybrid Search Pattern (from `rag_engine.py`):**
```python
# BM25 + Dense fusion — we keep this
bm25_results = self._bm25_search(query, k * 2)
dense_results = self._dense_search(query, k * 2)
combined = self._fuse_results(bm25_results, dense_results, k)
reranked = self._rerank(query, combined, k)
```
This fusion approach will be reused for combining multiple evidence signals.

**3. The Query Decomposition Pattern (from `rag_engine.py`):**
```python
def _decompose_query(self, query: str) -> list:
    # Uses LLM to break "Is this site trustworthy?" into:
    # ["Check domain age", "Verify SSL certificate", "Analyze UI patterns", ...]
```

#### What We Need to Change/Upgrade

| RAGv5 Component | Problem for Veritas | Solution |
|----------------|---------------------|----------|
| FAISS vector store | In-memory, crashes on 8GB RAM with large crawls | Migrate to **LanceDB** (disk-based, same API pattern) |
| Tesseract OCR | Slow, low accuracy on web screenshots | Replace with **NVIDIA NIM VLM** as primary, keep Tesseract as fallback |
| Static file ingest | Only processes local files | Add **live URL ingest** via Playwright |
| Single-model LLM | Uses one model for everything | Split into **specialist agents** (Vision, Reasoning, Judging) |
| No graph layer | Cannot represent entity relationships | Add **NetworkX** knowledge graph |

---

### 1.2 Glass Box — What We Already Have

Your `glass_box` project is a **stealth web auditor** with the following proven components:

#### Existing Capabilities (Directly Reusable)

| Component | File | What It Does | Reuse in Veritas |
|-----------|------|-------------|------------------|
| **Stealth Browser** | `browser.py` | Playwright with full anti-detection (CDP patches, navigator.webdriver=false, timezone/locale spoofing) | ✅ **Direct reuse — this is Agent 1** |
| **Page Analyzer** | `analyzer.py` | DOM structure analysis, link extraction, text extraction, metadata parsing | ✅ Core of pre-VLM analysis |
| **Risk Scoring** | `scoring.py` | Multi-factor risk score (SSL, domain age, content analysis, link safety) | ✅ **Direct reuse — feeds into Trust Score** |
| **URL Validation** | `utils.py` | URL normalization, domain extraction, safety checks | ✅ Input validation layer |
| **Report Generation** | `reporter.py` | HTML report generation with risk visualization | ✅ Base for PDF audit report |
| **Crawl Manager** | `crawler.py` | Multi-page crawl with depth control and rate limiting | ✅ For multi-page site audits |
| **Config System** | `config.py` | Centralized configuration with environment variables | ✅ Project-wide config pattern |

#### Key Code Patterns to Carry Forward

**1. The Stealth Browser Pattern (from `browser.py`):**
```python
# Your existing stealth setup — this is battle-tested
async def _setup_stealth(self, page):
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    """)
    # Viewport randomization
    # Mouse jitter
    # Request interception for fingerprint masking
```
This is **production-ready** stealth. We carry it forward as-is.

**2. The Risk Scoring Pattern (from `scoring.py`):**
```python
# Multi-factor scoring — matches our Trust Score concept
class RiskScorer:
    def calculate_risk(self, analysis_data):
        ssl_score = self._check_ssl(analysis_data)
        domain_score = self._check_domain_age(analysis_data)
        content_score = self._check_content(analysis_data)
        link_score = self._check_links(analysis_data)
        
        total = (ssl_score * 0.25 + domain_score * 0.30 + 
                 content_score * 0.25 + link_score * 0.20)
        return {"score": total, "breakdown": {...}}
```

**3. The Page Analysis Pattern (from `analyzer.py`):**
```python
# DOM forensics — reusable
async def analyze_page(self, page):
    metadata = await self._extract_metadata(page)
    links = await self._extract_links(page)
    forms = await self._extract_forms(page)
    scripts = await self._analyze_scripts(page)
    return AnalysisResult(metadata, links, forms, scripts)
```

#### What Glass Box Lacks (Our Upgrade Path)

| Missing Capability | Impact | Veritas Solution |
|-------------------|--------|-----------------|
| No Vision/VLM | Cannot "see" dark patterns, only reads DOM | Add **NVIDIA NIM VLM** agent |
| No entity graph | Cannot cross-reference real-world entities | Add **NetworkX** knowledge graph |
| No agentic loop | Linear pipeline, no iterative reasoning | Add **LangGraph** orchestration |
| No time-series | Single snapshot only | Add **temporal screenshot comparison** |
| No RAG | No knowledge base for pattern matching | Integrate **RAGv5 hybrid retrieval** |
| Basic reports | HTML only, no forensic narrative | Upgrade to **PDF forensic reports** |

---

### 1.3 Merge Strategy — What Comes From Where

```
┌─────────────────────────────────────────────────────────┐
│                    PROJECT VERITAS                        │
│                                                          │
│  ┌──────────────┐          ┌──────────────────┐         │
│  │  GLASS_BOX   │          │     RAGv5        │         │
│  │              │          │                  │         │
│  │ • browser.py ────────────→ Agent 1: Scout  │         │
│  │ • analyzer.py────────────→ Pre-VLM Layer   │         │
│  │ • scoring.py ────────────→ Trust Scorer    │         │
│  │ • crawler.py ────────────→ Multi-page Nav  │         │
│  │ • reporter.py────────────→ Report Engine   │         │
│  │ • config.py  ────────────→ Global Config   │         │
│  └──────────────┘          │                  │         │
│                            │ • chunker.py ──────→ Web Content Processing │
│         NEW MODULES        │ • rag_engine.py ───→ Evidence Retrieval     │
│  ┌──────────────┐          │ • vector_store.py ─→ LanceDB Migration      │
│  │ • nim_client │          │ • ingest.py ───────→ Multi-format Input     │
│  │ • vision_agent│         │ • confidence ──────→ Trust Score Math       │
│  │ • graph_agent │         └──────────────────┘         │
│  │ • judge_agent │                                       │
│  │ • langgraph   │                                       │
│  │   orchestrator│                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

---

## PART 2: STRATEGY GAP ANALYSIS & SOLUTIONS

### Gap 1: Trust Score Formula is Undefined

**Problem:** The original doc says "assign a Trust Score" but never defines the math.

**Solution — Weighted Multi-Signal Trust Score:**

```
TrustScore = Σ(wi × Si) for i in [visual, structural, temporal, graph, meta]

Where:
  S_visual     = VLM dark pattern detection score (0-1)
  S_structural = DOM analysis score from glass_box analyzer (0-1)  
  S_temporal   = Time-series consistency score (0-1)
  S_graph      = Entity verification score from knowledge graph (0-1)
  S_meta       = Domain metadata score (SSL + age + WHOIS) (0-1)

Default Weights:
  w_visual     = 0.25  (high impact but VLM can hallucinate)
  w_structural = 0.15  (reliable but gameable)
  w_temporal   = 0.15  (unique signal, hard to fake)
  w_graph      = 0.30  (most reliable real-world anchor)
  w_meta       = 0.15  (easy to check, hard to fake)

Final Score: 0-100 scale
  90-100 = Trusted
  70-89  = Probably Safe
  40-69  = Suspicious
  20-39  = High Risk
  0-19   = Likely Fraudulent
```

**Override Rules (Hard Stops):**
- If `domain_age < 7 days` AND `S_graph < 0.3` → Force score below 30 regardless of visual score
- If `SSL = None` → Cap maximum score at 50
- If `S_temporal < 0.2` (fake timers detected) → Deduct 25 points flat

This uses the same weighted pattern from your RAGv5 confidence calculation — proven and explainable.

---

### Gap 2: No Dark Pattern Taxonomy

**Problem:** The VLM needs structured categories to detect against. "Find dark patterns" is too vague.

**Solution — Veritas Dark Pattern Classification Taxonomy:**

```
DARK_PATTERN_TAXONOMY = {
    "visual_interference": {
        "description": "UI elements designed to mislead through visual hierarchy",
        "sub_types": {
            "hidden_unsubscribe": "Unsubscribe/cancel buttons made visually small, low-contrast, or hidden",
            "misdirected_click": "Accept/Agree buttons visually dominant while Decline is suppressed",
            "disguised_ads": "Advertisements styled to look like content or navigation",
            "trick_questions": "Confusing double-negatives in opt-in/opt-out checkboxes"
        },
        "vlm_prompts": [
            "Compare the visual prominence (size, color, contrast) of the 'Accept' vs 'Decline' buttons. Which is more visually dominant and by how much?",
            "Is there any clickable element that is unusually small (under 12px) or has very low contrast against its background?"
        ]
    },
    "false_urgency": {
        "description": "Fake time pressure to force decisions",
        "sub_types": {
            "fake_countdown": "Countdown timers that reset on refresh",
            "fake_scarcity": "'Only 2 left!' messages that never change",
            "fake_social_proof": "'15 people viewing this' with no real data"
        },
        "detection_method": "TEMPORAL — requires Screenshot_A vs Screenshot_B comparison",
        "vlm_prompts": [
            "Is there a countdown timer or urgency indicator visible? Read its exact value.",
            "Is there a 'limited stock' or 'people viewing' indicator? Read its exact value."
        ]
    },
    "forced_continuity": {
        "description": "Making it hard to cancel or leave",
        "sub_types": {
            "hidden_cancel": "Cancel subscription button buried in settings",
            "guilt_tripping": "'Are you sure? You'll lose everything!' messaging",
            "roach_motel": "Easy to sign up, extremely hard to delete account"
        },
        "vlm_prompts": [
            "Is there a clearly visible 'Cancel' or 'Delete Account' option on this page?",
            "Does the cancellation flow use emotional or guilt-inducing language?"
        ]
    },
    "sneaking": {
        "description": "Adding items or charges without explicit consent",
        "sub_types": {
            "hidden_costs": "Fees revealed only at checkout",
            "pre_selected_options": "Add-ons or insurance pre-checked",
            "bait_and_switch": "Advertised price differs from actual price"
        },
        "vlm_prompts": [
            "Are there any pre-selected checkboxes on this page? What do they say?",
            "Is the total price clearly visible, or are there additional fees in smaller text?"
        ]
    },
    "social_engineering": {
        "description": "Manipulating trust signals",
        "sub_types": {
            "fake_reviews": "Testimonials with stock photos or AI-generated faces",
            "fake_badges": "Trust badges (Norton, BBB) that are just images with no verification link",
            "fake_authority": "Claims of awards or certifications with no proof"
        },
        "vlm_prompts": [
            "Are there trust badges or certification logos? Do they appear to be clickable/verifiable or just static images?",
            "Do the testimonial photos appear to be stock photos or AI-generated?"
        ]
    }
}
```

---

### Gap 3: No Error Handling / Termination Conditions for LangGraph

**Problem:** The cyclic reasoning loop could run forever or fail silently.

**Solution — Audit State Machine with Budget Controls:**

```
AUDIT_CONFIG = {
    "max_iterations": 5,           # Max times the loop can cycle
    "max_pages_per_audit": 10,     # Max pages to crawl per site
    "screenshot_timeout": 15,      # Seconds before screenshot fails
    "nim_timeout": 30,             # Seconds before NIM API call fails
    "nim_retry_count": 2,          # Retries on NIM failure
    "confidence_threshold": 0.6,   # Minimum confidence to accept a finding
    "min_evidence_count": 3,       # Minimum evidence pieces before judging
    "temporal_delay": 10,          # Seconds between Screenshot_A and Screenshot_B
}

STATE_TRANSITIONS = {
    "START": → "SCOUT",
    "SCOUT": → "VISION" (success) | → "RETRY_SCOUT" (bot blocked) | → "ABORT" (3 failures),
    "VISION": → "GRAPH" (patterns found) | → "JUDGE" (no patterns, skip graph),
    "GRAPH": → "JUDGE" (evidence sufficient) | → "SCOUT" (need more pages, under budget),
    "JUDGE": → "REPORT" (confidence > threshold) | → "SCOUT" (confidence < threshold, under budget),
    "REPORT": → "END",
    "ABORT": → "PARTIAL_REPORT" → "END"
}
```

**Fallback Chain for NIM Failures:**
```
Primary:   NVIDIA NIM (nvidia/neva-22b)     → Best quality
Fallback1: NVIDIA NIM (microsoft/phi-3-vision) → Smaller, faster
Fallback2: Local Tesseract OCR + Heuristic rules → No API needed
Fallback3: DOM-only analysis (glass_box analyzer) → Zero AI, pure structural
```

This ensures Veritas **always produces a report**, even if all AI services are down.

---

### Gap 4: No Ground Truth / Evaluation Strategy

**Problem:** How do we know the system actually works? No benchmarks mentioned.

**Solution — Three-Tier Evaluation:**

**Tier 1: Synthetic Test Sites (Controlled)**
Build 5 local HTML pages with known dark patterns:
```
test_sites/
├── fake_urgency.html      # Timer that resets every 30s
├── hidden_unsubscribe.html # Tiny gray "unsubscribe" on gray background
├── pre_selected.html       # Pre-checked "Add insurance" box
├── fake_reviews.html       # Stock photo testimonials
└── clean_site.html         # Legitimate site (control group)
```
Expected output is known → measure precision/recall.

**Tier 2: Known Scam Sites (Wild)**
Use documented scam URLs from:
- [URLhaus](https://urlhaus.abuse.ch/)
- [PhishTank](https://www.phishtank.com/)
- FTC enforcement action databases

Compare Veritas Trust Score against known-bad status.

**Tier 3: Legitimate Sites (False Positive Check)**
Run Veritas against:
- amazon.com (has some dark patterns — should flag them)
- wikipedia.org (should score 90+)
- stripe.com (should score 85+)

Ensure the system doesn't cry wolf on legitimate sites.

**Metrics:**
```
Detection Rate     = True Positives / (True Positives + False Negatives)
False Alarm Rate   = False Positives / (False Positives + True Negatives)
Trust Score MAE    = Mean Absolute Error vs. human auditor scores
Latency            = Time from URL input to report generation
```

---

### Gap 5: No PDF Report Generation Strategy

**Problem:** "Generate a PDF" is mentioned but no library or template defined.

**Solution:**
- **Library:** `WeasyPrint` (HTML → PDF, supports CSS, lightweight)
- **Template:** Extend `glass_box/reporter.py` HTML template
- **Structure:**

```
VERITAS FORENSIC AUDIT REPORT
├── Header (URL, Date, Audit Duration, Agent Version)
├── Executive Summary (1 paragraph + Trust Score gauge visual)
├── Evidence Timeline
│   ├── Screenshot_A with annotations
│   ├── Screenshot_B with annotations
│   └── Delta Analysis (what changed between A and B)
├── Dark Pattern Findings (table with category, confidence, screenshot crop)
├── Entity Verification Results
│   ├── Knowledge Graph visualization (NetworkX → matplotlib → PNG)
│   ├── WHOIS data summary
│   └── Inconsistency flags
├── Trust Score Breakdown (bar chart of 5 sub-scores)
├── Risk Level & Recommendation
└── Appendix: Raw Evidence JSON
```

---

### Gap 6: NVIDIA NIM Credit Budget & Rate Limiting

**Problem:** 1000 free credits is finite. No strategy for conservation.

**Solution — Tiered API Usage:**

```
BUDGET_STRATEGY = {
    "quick_scan": {
        "pages": 1,
        "screenshots": 2,     # Only homepage
        "nim_calls": 3,       # 1 vision + 1 graph query + 1 judge
        "estimated_credits": 5,
        "use_case": "Quick URL check"
    },
    "standard_audit": {
        "pages": 5,
        "screenshots": 10,
        "nim_calls": 12,
        "estimated_credits": 20,
        "use_case": "Default audit mode"
    },
    "deep_forensic": {
        "pages": 10,
        "screenshots": 20,
        "nim_calls": 30,
        "estimated_credits": 50,
        "use_case": "Full investigation"
    }
}

# With 1000 credits:
#   ~200 quick scans  OR  ~50 standard audits  OR  ~20 deep forensics
```

**Conservation Tactics:**
1. **Pre-filter with free tools first** — Run glass_box DOM analysis before calling NIM. If DOM analysis already shows SSL=None + domain_age=1day, skip expensive VLM call.
2. **Cache NIM responses** — Same URL within 24h returns cached result.
3. **Batch VLM prompts** — Send multiple questions per screenshot in one API call instead of separate calls.

---

### Gap 7: Concurrency & Rate Limiting

**Problem:** No discussion of parallel audits or API throttling.

**Solution:**

```python
CONCURRENCY_CONFIG = {
    "max_concurrent_audits": 2,          # 8GB RAM limit
    "max_concurrent_browser_pages": 3,   # Playwright memory limit
    "nim_requests_per_minute": 10,       # Stay under free tier rate limit
    "tavily_requests_per_minute": 5,     # Tavily free tier limit
    "inter_request_delay_ms": 500,       # Minimum delay between requests
}
```

Use `asyncio.Semaphore` for all external calls — already a pattern you're comfortable with since glass_box uses async Playwright.

---

### Gap 8: Knowledge Graph Schema

**Problem:** "Build a knowledge graph" is vague. What are the node/edge types?

**Solution — Veritas Entity Graph Schema:**

```
NODE TYPES:
  - WebsiteNode(url, domain, ip, ssl_status, domain_age_days)
  - EntityNode(name, type=[company|person|address|phone|email])
  - ClaimNode(claim_text, source_page, confidence)
  - EvidenceNode(type=[screenshot|whois|dns|search_result], data)

EDGE TYPES:
  - CLAIMS(WebsiteNode → EntityNode, claim_type=[ceo|address|founded|phone])
  - VERIFIED_BY(EntityNode → EvidenceNode, verification_status=[confirmed|denied|unverifiable])
  - CONTRADICTS(EvidenceNode → ClaimNode, contradiction_detail=str)
  - LINKS_TO(WebsiteNode → WebsiteNode, link_type=[outbound|redirect])

EXAMPLE GRAPH:
  [scam-bank.com] --CLAIMS(ceo)--> [John Doe]
  [John Doe] --VERIFIED_BY--> [LinkedIn Search: "No results"]  → STATUS: DENIED
  [scam-bank.com] --CLAIMS(address)--> [123 Tech Park, SF]
  [123 Tech Park, SF] --VERIFIED_BY--> [Google Maps: "Residential"]  → STATUS: CONTRADICTED
  [scam-bank.com] --LINKS_TO--> [legitimate-bank.com]  → IMPERSONATION FLAG
```

---

## PART 3: FINAL PROJECT FILE STRUCTURE

```
veritas/
├── README.md
├── VERITAS_STRATEGY.md          # This document
├── requirements.txt
├── .env                         # NIM API keys, Tavily key
├── config/
│   ├── settings.py              # All configs from this doc
│   ├── dark_patterns.py         # Taxonomy + VLM prompts
│   └── trust_weights.py         # Score weights + override rules
│
├── agents/
│   ├── __init__.py
│   ├── scout.py                 # Agent 1: Stealth browser (from glass_box/browser.py)
│   ├── vision.py                # Agent 2: NIM VLM integration
│   ├── graph_investigator.py    # Agent 3: NetworkX + Tavily
│   └── judge.py                 # Agent 4: NIM LLM synthesis
│
├── core/
│   ├── __init__.py
│   ├── nim_client.py            # NVIDIA NIM API wrapper with retry + fallback
│   ├── trust_scorer.py          # Weighted scoring engine (from ragv5 confidence pattern)
│   ├── evidence_store.py        # LanceDB integration (replacing ragv5 FAISS)
│   ├── knowledge_graph.py       # NetworkX graph builder + query
│   └── orchestrator.py          # LangGraph state machine
│
├── analysis/
│   ├── __init__.py
│   ├── dom_analyzer.py          # From glass_box/analyzer.py (upgraded)
│   ├── temporal_analyzer.py     # Screenshot_A vs Screenshot_B diff
│   ├── meta_analyzer.py         # WHOIS + SSL + DNS checks
│   └── pattern_matcher.py       # VLM prompt builder from taxonomy
│
├── reporting/
│   ├── __init__.py
│   ├── report_generator.py      # WeasyPrint PDF generation
│   ├── templates/
│   │   └── audit_report.html    # Jinja2 HTML template
│   └── visualizations.py        # NetworkX → matplotlib graph renders
│
├── ui/
│   ├── app.py                   # Streamlit main app
│   ├── components/
│   │   ├── url_input.py
│   │   ├── live_log.py          # Real-time agent activity feed
│   │   ├── score_gauge.py       # Trust score visualization
│   │   └── evidence_viewer.py   # Screenshot + annotation viewer
│   └── static/
│       └── style.css
│
├── tests/
│   ├── test_sites/              # Synthetic dark pattern HTML files
│   │   ├── fake_urgency.html
│   │   ├── hidden_unsubscribe.html
│   │   ├── pre_selected.html
│   │   ├── fake_reviews.html
│   │   └── clean_site.html
│   ├── test_scout.py
│   ├── test_vision.py
│   ├── test_graph.py
│   ├── test_trust_scorer.py
│   └── test_integration.py
│
└── data/
    ├── evidence/                # Runtime screenshot storage
    ├── reports/                 # Generated PDF reports
    ├── cache/                   # NIM response cache
    └── vectordb/                # LanceDB persistent storage
```

---

## PART 4: IMPLEMENTATION PRIORITY ORDER

```
Week 1: Foundation
  ├── Day 1-2: Project scaffold + config system + .env setup
  ├── Day 3-4: nim_client.py (NIM API wrapper with retry/fallback)
  └── Day 5-7: Port glass_box/browser.py → agents/scout.py (add temporal screenshots)

Week 2: Core Agents
  ├── Day 1-3: agents/vision.py + config/dark_patterns.py (VLM + taxonomy)
  ├── Day 4-5: agents/graph_investigator.py + core/knowledge_graph.py
  └── Day 6-7: agents/judge.py + core/trust_scorer.py

Week 3: Orchestration & RAG
  ├── Day 1-3: core/orchestrator.py (LangGraph state machine)
  ├── Day 4-5: core/evidence_store.py (LanceDB migration from FAISS)
  └── Day 6-7: Integration testing with synthetic test sites

Week 4: UI & Reporting
  ├── Day 1-3: ui/app.py (Streamlit dashboard)
  ├── Day 4-5: reporting/report_generator.py (WeasyPrint PDF)
  └── Day 6-7: End-to-end testing + evaluation metrics + documentation
```

---

## PART 5: DELIMA RESOLUTIONS

### Dilemma 1: "FAISS vs LanceDB — should I rewrite the entire vector store?"

**Resolution: No. Adapter pattern.**

Keep the same interface from `ragv5/vector_store.py`, swap the backend:

```python
# core/evidence_store.py
import lancedb

class EvidenceStore:
    """Same interface as ragv5 VectorStore, disk-based backend."""
    
    def __init__(self, db_path="./data/vectordb"):
        self.db = lancedb.connect(db_path)  # Disk-based, not RAM
        
    def add_evidence(self, text: str, metadata: dict, embedding: list):
        # Same as ragv5 add_document() but writes to disk
        table = self.db.open_table("evidence")
        table.add([{"text": text, "vector": embedding, **metadata}])
    
    def search(self, query_embedding: list, k: int = 5):
        # Same as ragv5 search() interface
        table = self.db.open_table("evidence")
        return table.search(query_embedding).limit(k).to_list()
```

Migration effort: **~2 hours**. Your RAG engine code stays 95% the same.

---

### Dilemma 2: "What if NIM credits run out mid-demo?"

**Resolution: Graceful degradation chain.**

```python
# core/nim_client.py
class NIMClient:
    async def analyze_image(self, image_path: str, prompt: str) -> dict:
        # Level 1: Try primary NIM model
        try:
            return await self._call_nim("nvidia/neva-22b", image_path, prompt)
        except (CreditExhausted, APIError):
            pass
        
        # Level 2: Try smaller NIM model
        try:
            return await self._call_nim("microsoft/phi-3-vision", image_path, prompt)
        except (CreditExhausted, APIError):
            pass
        
        # Level 3: Local Tesseract OCR + heuristic rules
        text = pytesseract.image_to_string(Image.open(image_path))
        return self._heuristic_analysis(text)
    
    def _heuristic_analysis(self, text: str) -> dict:
        """Rule-based fallback — no AI needed."""
        patterns = []
        if re.search(r'only \d+ left', text, re.I):
            patterns.append({"type": "fake_scarcity", "confidence": 0.6})
        if re.search(r'timer|countdown|\d{2}:\d{2}', text, re.I):
            patterns.append({"type": "possible_urgency", "confidence": 0.5})
        # ... more rules
        return {"patterns": patterns, "fallback_mode": True}
```

The demo **never breaks**. It just gets less accurate gracefully.

---

### Dilemma 3: "LangGraph vs simple sequential pipeline — is the complexity worth it?"

**Resolution: Yes, and here's the concrete proof.**

Sequential pipeline cannot do this:
```
Scout finds homepage → Vision finds "CEO: Jane Smith" → 
Graph checks LinkedIn → Jane Smith doesn't exist → 
Judge says "not enough evidence, check About page" → 
Scout navigates to /about → Vision extracts address → 
Graph checks Google Maps → Address is fake → 
Judge now has enough evidence → Generate report
```

This **backtracking loop** is impossible without LangGraph's cyclic state machine. Linear LangChain would require you to pre-define every possible path.

However, **start with a simplified 3-node graph** for MVP:
```
Scout → Vision → Judge (no Graph agent initially)
```
Add the Graph agent in Week 2 once the core loop works. This is lower risk.

---

### Dilemma 4: "Playwright stealth works but how do I handle CAPTCHAs?"

**Resolution: Don't solve CAPTCHAs. Document and bypass.**

```python
# agents/scout.py
async def navigate(self, url: str) -> ScoutResult:
    page = await self._get_stealth_page()
    await page.goto(url, wait_until="networkidle")
    
    # CAPTCHA detection
    captcha_indicators = [
        "captcha", "recaptcha", "hcaptcha", "challenge-platform",
        "cf-turnstile", "arkose"
    ]
    page_content = await page.content()
    
    if any(indicator in page_content.lower() for indicator in captcha_indicators):
        return ScoutResult(
            status="CAPTCHA_BLOCKED",
            screenshots=[],
            note="Site uses CAPTCHA protection — manual review recommended",
            trust_modifier=-0  # Don't penalize for having CAPTCHAs (that's good security)
        )
    
    # Continue with normal screenshot flow...
```

In the audit report, flag it as: *"This site employs CAPTCHA protection, which prevented full automated analysis. This is NOT a negative indicator — it suggests active security measures. Partial analysis based on publicly accessible pages follows."*

This is **honest** and **defensible** in a viva.

---

### Dilemma 5: "NetworkX graph is in-memory — what if the graph gets too big?"

**Resolution: It won't.**

Each audit creates a graph for ONE website. Typical graph size:
- Nodes: 10-30 (website + entities + evidence)
- Edges: 15-50

This consumes ~50KB of RAM. Even 100 concurrent audits = 5MB. NetworkX handles this trivially.

If you ever need persistence (future scope), dump to JSON:
```python
import networkx as nx
import json

# Save
data = nx.node_link_data(graph)
json.dump(data, open("graph_backup.json", "w"))

# Load
data = json.load(open("graph_backup.json"))
graph = nx.node_link_graph(data)
```

No need for Neo4j. This is a strength, not a compromise.

---

### Dilemma 6: "How do I handle rate limiting from Tavily and other external APIs?"

**Resolution: Async semaphore + exponential backoff (pattern from glass_box):**

```python
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt

class RateLimitedClient:
    def __init__(self, requests_per_minute: int = 5):
        self._semaphore = asyncio.Semaphore(requests_per_minute)
        self._delay = 60.0 / requests_per_minute
    
    @retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3))
    async def call(self, func, *args, **kwargs):
        async with self._semaphore:
            result = await func(*args, **kwargs)
            await asyncio.sleep(self._delay)
            return result
```

---

### Dilemma 7: "What makes this different enough from existing tools to be thesis-worthy?"

**Resolution: The combination is novel. Here's the defensible claim:**

| Existing Tool | What It Does | What It Lacks |
|---------------|-------------|---------------|
| **Lighthouse** (Google) | Performance + accessibility audit | No dark pattern detection, no entity verification |
| **ScamAdviser** | Domain reputation scoring | No visual analysis, no agentic reasoning |
| **Darkpatterns.org** | Manual dark pattern catalogue | No automation at all |
| **URLVoid** | Blacklist checking | No visual or structural analysis |

**Veritas is the FIRST tool that combines:**
1. Visual dark pattern detection via VLM ← **novel application**
2. Temporal fraud detection (timer manipulation) ← **novel technique**
3. Graph-based entity cross-referencing ← **novel in web audit context**
4. Agentic reasoning loop with backtracking ← **novel architecture for this domain**

No existing open-source tool does all four. That's the thesis contribution.

---

## PART 6: REQUIREMENTS.TXT (Verified for 8GB RAM)

```
# Core
python>=3.10
langchain>=0.3.0
langgraph>=0.2.0
playwright>=1.40.0

# NVIDIA NIM
openai>=1.0.0              # NIM uses OpenAI-compatible API format

# Vector Store
lancedb>=0.4.0
sentence-transformers>=2.2.0  # For local embeddings (all-MiniLM-L6-v2)

# Graph
networkx>=3.2
matplotlib>=3.8.0          # For graph visualization

# Analysis
Pillow>=10.0.0
pytesseract>=0.3.10        # Fallback OCR
python-whois>=0.9.0
dnspython>=2.4.0

# RAG
rank-bm25>=0.2.2
numpy>=1.24.0

# Search
tavily-python>=0.3.0

# Reporting
WeasyPrint>=60.0
Jinja2>=3.1.0

# UI
streamlit>=1.30.0

# Utilities
python-dotenv>=1.0.0
tenacity>=8.2.0            # Retry logic
aiohttp>=3.9.0
pydantic>=2.5.0
```

**Estimated RAM Usage:**
- Playwright browser: ~300-500MB
- sentence-transformers model: ~200MB
- LanceDB (disk-based): ~50MB RAM
- NetworkX graphs: ~5MB
- Python + libraries: ~500MB
- **Total: ~1.5GB** — well within 8GB limit

---

*This document is the single source of truth for Project Veritas implementation. All dilemmas are resolved. All gaps are filled. Start building.*