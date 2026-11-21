# elliotAI — Engineering Case Study

How a multi-agent website-trust auditor was made measurable, observable and robust:
which bugs were found, **how they were found** (traces, evals, tests, code sweeps),
how they were fixed, and the numbers before and after.

> Period: 2026-11-05 → 2026-11-21 · Branch: `feat/osint-pipeline`
> Models: NVIDIA NIM `nemotron-3.5-super-vl-120b-a12b` (vision + text), `mistral-large-4` fallback

---

## 1. System in one picture

```
URL ─► Scout (Playwright: t0, t+10s, fullpage, subpages)
        ├─► Security  (8 deterministic modules: headers, CSP, cookies, GDPR, PCI, social-eng, prompt-injection, darknet)
        ├─► Vision    (VLM, taxonomy-constrained JSON, 5 dark-pattern categories)
        ├─► Graph     (WHOIS/DNS/SSL/OSINT + LLM entity extraction & claim verification)
        └─► Judge     (code computes the 0-100 score from 6 weighted signals + override rules;
                       LLM only writes the narrative; may request more pages → loop)
```

Key design property: **LLMs perceive, code decides.** The trust score is a deterministic
function (`elliot/config/trust_weights.py`), so it can be unit-tested and evaluated
independently of the models, and a hijacked model can corrupt at most one signal.

---

## 2. What was added

| Capability | Where | What it gives |
|---|---|---|
| **Tracing** (OpenTelemetry + OpenInference) | `elliot/core/tracing.py` | One trace per audit: `audit › agent.* › nim.* › nim.call › LLM`. Exports to Phoenix (OTLP) and local JSONL; per-audit roll-up (`trace_summary`: tokens, LLM time, cache hits, retries, fallbacks, cost) returned in the API and shown in the UI. |
| **Structured outputs** | `elliot/core/structured.py` | Pydantic schemas derived from the taxonomy, NIM `response_format=json_schema` (constrained decoding), balanced-brace extraction, one repair retry with the validation error fed back. |
| **Eval harness** | `eval/` | 4 suites: deterministic scoring policy, vision P/R/F1 per category, prompt-injection attack-success-rate (matched pairs), end-to-end on real sites with a baseline. Results versioned in `eval/results/`. |
| **Injection defences** | `elliot/core/injection.py`, `analysis/security/prompt_injection.py` | Spotlighting, field quarantine (context minimisation), deterministic detector, and an override rule that turns an injection attempt into a *lower* trust score. |
| **Deploy hardening** | `backend/services/guards.py`, `Dockerfile`, `docs/DEPLOY.md` | SSRF guard, per-IP rate limit, concurrency cap, tier allowlist; Docker image + Vercel; live demo self-hosted behind a Cloudflare tunnel. |
| **CI** | `.github/workflows/ci.yml` | Tests + **eval gate** (scoring policy must be 5/5) + frontend type-check. |

---

## 3. Bugs: how each was found and fixed

Severity: **Critical** (security / silent corruption) · **High** (user-visible feature broken) · **Medium** · **Low**.

### Found by tracing

| # | Bug | Sev | How the trace showed it | Root cause → fix |
|---|---|---|---|---|
| T1 | **Vision analysed only the homepage** — reports said "8 pages scanned" but the VLM saw 1 | High | Per-iteration breakdown: `agent.vision` issued the **same 15 requests** in iterations 2–5, all cache hits, although Scout captured 21 new screenshots | Standard tier (<5 passes) uses the legacy path, which called `_select_primary_screenshot` once (`agents/vision.py`). Now one screenshot per scanned page, bounded by the tier's vision budget. |
| T2 | **One page per agent iteration** → whole pipeline re-ran per page | Medium | 5 `agent.judge` spans for a 4-page request; `agent.graph` repeated 5× (44 s) | `scout_node` processed `pending[0]` only (`core/nodes/scout.py`). Now batches all requested pages in one browser session. |
| T3 | Judge queued **external domains** (twitter.com) as pages to audit | Medium | Judge span log: `requesting investigation of [... 'https://twitter.com/syntharatech']` | Candidate links not filtered to the target site; also built from a `set` (non-deterministic order). Now same-site (www/apex aware), sorted. |
| T4 | **4 of 7 security modules never ran** (GDPR, PCI-DSS, social-engineering, darknet) | High | Audit log next to the trace: `MEDIUM tier execution failed: Can't instantiate abstract class SocialEngineeringAnalyzer` | One module implemented an older interface; its instantiation error aborted the whole tier. Module rewritten to the `SecurityModule` contract; executor now isolates per-module failures. Regression test fails without the fix. |
| T5 | Retry × timeout amplification (hypothesis for a 580 s vision phase) | — | Made observable: every attempt is now its own `nim.call` span with `attempt`, `queue_wait_s`. Today's traced runs: **0 retries, slowest call 4 s** → not reproduced; status **UNVERIFIED** | `@retry` on `TimeoutError` × `NIM_TIMEOUT=90` allows ~4.5 min per call. Left in place, now visible in Phoenix if it recurs. |

**Before → after (same site, standard tier, traced):**

| | Before fixes | After |
|---|---|---|
| Agent iterations | 5 | **2** |
| Graph time | 44.1 s | **17.6 s** |
| Real VLM calls (not cache) | 23 (homepage only) | **40** (subpages actually analysed) |
| Audit time | 161 s | 193 s |
| Tokens | 52 k | 107 k |

The higher cost after the fix is the honest price of analysing the pages the report claims to analyse — tracing made that trade-off visible instead of hiding it in a cache hit rate.

### Found by evals

| # | Bug | Sev | Eval signal | Root cause → fix |
|---|---|---|---|---|
| E1 | **Fail-open**: no evidence at all → 85 "probably safe" | High | Scoring suite `no_evidence_abstains` ❌ | Missing signals fall back to an optimistic prior (0.85). Added **abstention**: evidence coverage Σ(weight×confidence) < 0.25 → `insufficient_evidence` (hard-stop overrides still win). |
| E2 | No-SSL cap documented as 50, coded as 85; test failing since March | Medium | Scoring suite `no_ssl_cap` ❌ + `test_override_no_ssl` | Real cause: `GraphResult.has_ssl` returned **False when the lookup failed**, so HTTPS sites got capped; someone raised the cap to hide it. Fixed `has_ssl` to be tri-state (True/False/None — which also revives the Judge's dead scout fallback) and restored 50. |
| E3 | "Force below 15" produced exactly 15 | Low | Scoring suite `blacklist_forces_low` ❌ | `min(score, value)` → `min(score, value-1)`. |
| E4 | **Eval harness bug**: fake-countdown page never detected | — | Vision suite FN on `dp_fake_countdown` | `false_urgency` is a *temporal-only* category; the harness captured one fullpage shot. Harness now captures exactly what Scout captures (t0, t+10 s, fullpage). Recall 0.8 → 1.0. **Lesson: the eval pipeline is code and has bugs too.** |
| E5 | **Prompt injection via meta description** → elliotAI extracted *"Microsoft Corporation, founded 1975, Redmond"* as the identity of a fake shop | Critical | Injection suite: text-channel attack succeeded | Untrusted page text concatenated raw into the extraction prompt. See §5. |
| E6 | Injection detector **false positives on real AI-company sites** (GitHub, Synthara: "AI systems, agentic …") | Medium | Held-out real pages | Pattern `ai systems[:,]` too broad → vocative-only (`AI auditors:`), addressing words (`Dear AI …`). |

**Scoring policy suite:** 2/5 → **5/5** (now a CI gate).

### Found by code sweeps / tests while fixing the above

| # | Bug | Sev | How found | Fix |
|---|---|---|---|---|
| C1 | **Fraudulent sites told "This website looks okay"** | High | Adding the abstention enum value; `judge.py` imported two different `RiskLevel` enums under one name | The dual-verdict import shadowed `trust_weights.RiskLevel`, so `risk == RiskLevel.X` compared members of different enums (always False). Aliased; regression test reproduces the wrong advice. |
| C2 | **Cache key ignored the model** → model A/B comparisons silently returned the old model's answers (and made repeat runs look deterministic) | Critical (for evaluation) | Code read while designing the eval | Model + schema name in every cache key. |
| C3 | `is_blacklisted` hard-coded False → blocklist override could never fire | High | Code read; scoring suite | Wired to external blocklist hits (`phishing.sources`), not heuristics. |
| C4 | Model free text overwrote `category_id`; findings labelled `unknown` | Medium | Structured-output design | Taxonomy-validated `pattern_type`; category derived from taxonomy, never from model text. |
| C5 | JSON regex failed beyond 2 nesting levels; `<think>` blocks broke parsing | Medium | Unit tests | Balanced-brace scanner that respects strings; think-block stripping. |

### Found earlier (setup, 2026-11-05)

| # | Bug | Sev | How found | Fix |
|---|---|---|---|---|
| S1 | Backend crashed on start: `elliot.screenshots` missing | High | Import error | Module lost to an over-broad `.gitignore` rule during a rename; restored + rule narrowed. |
| S2 | Only the homepage was crawled | High | Audit result: 1 page | apex→www 307 redirect + strict host comparison dropped every internal link. |
| S3 | Every UI audit ran **twice** | High | Backend log: 2 subprocesses per audit | React StrictMode double-mount; first run kept going after its socket closed. Run is cancelled on disconnect; owner token keeps only the live run. |
| S4 | Audit stuck "running" forever | High | DB row after S3 fix | IntegrityError race on concurrent insert; now handled. |
| S5 | Reloading a finished audit re-ran it | Medium | Manual probe | Replays the stored result. |
| S6 | Reasoning models returned empty answers | High | Empty `content` at small `max_tokens` | `chat_template_kwargs.enable_thinking=false` (opt-in setting). |

---

## 4. Evaluation results

All fixtures are synthetic and served locally (`eval/fixtures/`); no live phishing pages were fetched.
Small n → wide intervals; numbers are a baseline, not a benchmark claim.

| Suite | Baseline | Final | Notes |
|---|---|---|---|
| Scoring policy (deterministic) | 2/5 | **5/5** | CI gate |
| Vision, micro P / R / F1 (7 pages, 5 categories) | 0.80 / 0.80 / 0.80 *(harness bug)* → 0.833 / 1.0 / 0.909 | **0.833 / 1.0 / 0.909** | Defences caused no regression. 1 false alarm on `clean_basic` (visual_interference) remains. |
| Injection ASR (3 attacks, matched pairs) | **1/3** | **0/3** (95% CI 0–0.56) | Spotlighting alone: still 1/3. Quarantine: 0/3. Controls clean 3/3. |
| Injection detector | — | 5/5 fixtures, 6/6 held-out phrasings, 0/7 benign phrases, 0/9 real pages | Held-out set was used to fix one miss → now dev data; needs a fresh test set |
| End-to-end, 4 real legit sites (standard tier) | — | **0/4 false alarms** (baseline 0/4), p50 200 s | mindlyticai 84, synthara 78, example 94, wikipedia 91. Vision ≈ 70 % of audit time. Legit-only: measures false alarms, not phishing recall. |

How the injection result evolved (one variable at a time):

```
baseline ............................ ASR 1/3  (meta → "Microsoft Corporation, 1975, Redmond")
+ spotlighting (fenced untrusted text + system rule) ... ASR 1/3  (3 injected entities → 1)
+ quarantine (drop fields the detector flags) .......... ASR 0/3
```

---

## 5. Prompt-injection defence in depth

elliotAI reads attacker-controlled content by design, so defences are layered (strongest first):

1. **Architecture** — the score is computed by code; no tool can send, buy or delete.
2. **Constrained outputs** — enums leave no field for "SAFE, score 100".
3. **Context minimisation** — untrusted fields flagged by the detector never reach the LLM.
4. **Spotlighting** — remaining untrusted text is fenced (`<untrusted_website_content>`), with breakout tags stripped.
5. **Attack → evidence** — `prompt_injection` security module + override rule caps the score at 39 (high risk): *a legitimate site has no reason to address AI auditors.*
6. **Red-team eval** — ASR tracked per change.

---

## 6. Observability: what to look at in Phoenix

Project `elliotai`. Useful views:
- Sort spans by latency → slowest `nim.call` (attempt, queue wait, timeout).
- Filter `elliot.cache_hit = true` under `agent.vision` → wasted or duplicated work (found T1).
- Count `agent.judge` spans per trace → agent loop iterations (found T2).
- `nim.structured_*` spans with `elliot.parse_ok = false` → schema failures and repair rate.

---

## 7. Remaining risks (honest list)

| Risk | Sev | Status |
|---|---|---|
| No phishing **recall** measurement: needs live phishing captures (not collected without explicit approval) | High | Open |
| Eval sets are small (7 / 3 / 4); confidence intervals are wide | Medium | Open |
| Graph OSINT still re-runs once per iteration (now 2×, was 5×) | Low | Open |
| Vision is ~70 % of audit latency (15 prompts × page); batching prompts per screenshot is the next optimisation | Medium | Open |
| mindlyticai score moved 90 → 84 after full-page + all-module analysis; per-finding attribution not yet itemised | Low | Open |
| Retry × timeout worst case (~4.5 min per call) not reproduced; observable now | Medium | UNVERIFIED |
| SSRF guard checks the submitted URL only, not redirects / DNS rebinding mid-crawl | Medium | Open |
| Rate limiter is in-memory (single instance) | Low | By design for free tier |
| Vision false alarm on `clean_basic` | Low | Open |

---

## 8. Interview talking points

- *"LLMs perceive, code decides"*: deterministic scoring makes the system evaluable component by component and limits what a hijacked model can do.
- Tracing found four pipeline bugs that 465 passing tests did not (T1–T4): tests check code; traces show behaviour.
- The eval had its own bug (E4) — the harness must replicate production capture exactly.
- A schema guarantees shape, not truth: with `type ∈ {company, person}`, the model labelled "Paris" a company → every enum got an escape value.
- Spotlighting alone did not stop injection; context minimisation did — measured, one variable at a time.
- A deployed auditor is an SSRF target and a cost target: guards are part of the AI system, not an afterthought.
