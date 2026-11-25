# elliotAI — Engineering Case Study

How a multi-agent website-trust auditor was made measurable, observable and robust:
which bugs were found, **how they were found** (traces, evals, tests, code sweeps),
how they were fixed, and the numbers before and after.

> Period: 2026-11-05 → 2026-11-25 · Branch: `feat/osint-pipeline` (= `main`)
> Models: NVIDIA NIM `nemotron-3.5-super-vl-120b-a12b` (vision + text), `mistral-large-4` fallback

---

## 0. Improvements at a glance

Every number below was measured in this project (same site / same eval set before and after); details and verification are in the F-table in section 3 and in section 4.

| Area | Before | After | How measured |
|---|---|---|---|
| Score explainability | 0 of 6 signals explained; 18-point drop unexplained | 6 of 6 signals with points + plain-English reason; arithmetic adds up to the score | `score_breakdown`, replayed through `compute_trust_score` (F1–F4) |
| Silent crash cost | 11 of 18 lost points came from a crashed agent's placeholder | 0 (same site 82 → 91) | Replay of stored signals (F1, F2) |
| Audit time, standard tier | 768 s (Vision 662 s = 86 %) | 293 s (Vision 239 s); 96 s on a quieter API hour | Same site, same hour, 35 AI calls both (F11) |
| Pages actually distinct | 1 page analysed 4× (`/#top`, `/#features`, …) | 4 distinct pages | Exploration path in UI (F13) |
| Quick-scan budget | 4 pages, 17 screenshots, 116 s | 2 pages, 9 screenshots, 93 s | Back-to-back runs (F7) |
| Form / CAPTCHA detection | github.com/login: "CAPTCHA blocked", 0 forms | success, 5 forms | Direct Scout run (F14) |
| Vision false alarms (7 labelled pages) | P 0.71, 2 false alarms, clean pages flagged 1/2 | **P 1.00, 0 false alarms, 0/2**; F1 0.83 → 0.89; recall 1.00 → 0.80 | 2 runs each, fresh cache (F17) |
| Vision model choice | — | kept nemotron-3.5-super-vl (1.6–2.0 s/call); smaller nano-omni had 3× the false alarms | 6 candidate models probed uncached (F16) |
| Refresh / reconnect mid-audit | audit killed and restarted from zero | same run continues, full state replayed | Live reload + 4 route tests (F5) |
| History after restart | empty, all-ABORTED dashboard | every panel replayed from the stored event log | Route test incl. path-traversal guard (F9) |
| Orphaned "running" audits | 3 | 0 | DB after restart (F5) |
| Live feedback | timer frozen, counters 0 until the end | pages ~50 s, security checks ~35 s, per-page Vision progress | Browser (F6, F15) |
| Prompt-injection attack success | 1/3 | 0/3 | Matched pairs (section 5) |
| Scoring policy checks | 2/5 | 5/5 (CI gate) | Deterministic suite |
| SSRF via redirects / embedded requests | public→public→private redirect reached private service | refused at the egress proxy, +0.9 s overhead | Controlled redirect test + live audit (F18) |
| Automated tests | 446 | 458 | `pytest backend/tests elliot/tests` |

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

### Found by using the public demo (2026-11-21)

| # | Bug | Sev | How found | Fix |
|---|---|---|---|---|
| D1 | **Scout rendered pages without CSS**, so the vision model judged a broken page and reported six invented dark patterns | Critical | A screenshot of the live "Scout imagery" panel; reproduced by comparing one page load with and without Scout's headers | Scout forced navigation-only headers (`Accept: text/html`, `Sec-Fetch-Dest: document`, ...) on **every** request, so CDNs answered CSS and image requests wrongly. Only `Accept-Language` and `DNT` are set now; Chromium owns the rest. |
| D2 | Screenshots reached the UI only after the whole audit, so the imagery panel stayed empty for minutes | High | Live UI vs. audit log ("Captured 17 screenshots" while the panel said offline) | Scout now announces its files and the runner streams them right after Scout (first frame at ~26 s instead of at the end); the final pass only sends what was not yet sent. |
| D3 | Every step appeared two to three times in the log | Medium | Screenshot of the log stream | Three events (`phase_start`, `agent_personality`, `log_entry`) each wrote a log line. One writer remains; repeated rounds are tagged "(round N)". |
| D4 | CVSS panel showed `SEVERITY` and `VECTOR_STRING` as radar axes and a false "no HTTPS" risk | High | Screenshot of the radar; vector `AC:H/C:L` is only produced when HTTPS is missing, on an https site | The runner forwarded non-metric fields as metrics; `has_ssl=None` (TLS unknown) was treated as "no HTTPS". Only a confirmed `False` counts now; each metric carries a plain-English question, answer and the evidence behind it, plus a link to FIRST.org's calculator so the score is reproducible. |
| D5 | Placeholder CVSS and MITRE events ("CALCULATING", three fake techniques) were sent at the start of every audit | Medium | Code read while tracing D4 | Removed: the UI never shows data we did not measure. |
| D6 | Darknet tier forced Chromium through a Tor proxy that may not exist, which would fail every navigation | High | Code read before enabling the tier | The proxy is used only if a Tor daemon answers on the configured port; otherwise the audit runs direct and logs a warning. |
| D7 | The UI said "Could not connect to backend" for any rejection (e.g. a disabled tier) | Medium | User screenshot | The server's own reason is shown. |

### Found by watching a full audit in the browser (2026-11-25)

Trigger: a user audited `takebloom.vercel.app`, got **82/100**, and nothing in the UI said where the 18 points went. Earlier fixes had been checked only through backend events and type-checks, never by watching a real audit end to end. Doing that exposed six bugs, each verified before and after on the same site.

| # | Symptom | Root cause | Fix | Before → after (measured) |
|---|---|---|---|---|
| F1 | Score 82 with no explanation; narrative said "TLS was not verified" on an HTTPS site | `graph_investigator`: OSINT WHOIS returns `{"registrar": None}`; `dict.get("registrar", fallback)` returns `None` (the key exists), then `_compute_meta_score` called `None.lower()` → `AttributeError`. The graph node caught it and returned **placeholder** values (`graph 0.5, meta 0.5, has_ssl False`) | Only overwrite with real values; `None`-safe registrar | graph signal **0.50 → 0.86**, meta **0.50 → 0.95**, TLS detected (Google Trust Services). Same site: **82 → 91** |
| F2 | A crashed agent looked like a slightly risky site | Placeholder dict went through the same path as real data; judge scored meta at 0.85 confidence | Fallback marked `failed: True`; judge treats it as *missing* (confidence ≤ 0.2) and names the failure in the reason | Of the 18 lost points, **11.0 (61 %) came from the crash placeholder** (graph 6.5 + meta 4.5), replayed exactly through `compute_trust_score` |
| F3 | "No countdown timers" cost points as if it were a finding | No-data signals used raw **0.5**, but the formula's prior for "no evidence" is **0.85**; 0.5 reads as evidence of a problem | No-data signals use the prior and are flagged `unverified` | Temporal: **3.8 points lost "to findings" → 0** (2.25 now shown honestly as "could not verify") |
| F4 | UI showed no reasons | `_summary()` dropped the judge's breakdown; live page never rendered signal scores | Exact per-signal points split into *lost to findings* `w·c·(1−raw)` and *could not verify* `w·(1−c)·(1−prior)`, plus override deltas; persisted (new nullable column, idempotent `ADD COLUMN`) and shown in a `SCORE.BREAKDOWN` panel with plain-English reasons | 0 → 6 of 6 signals explained; Σ earned + rounding = score (rounding **0.03**) |
| F5 | Refreshing the page mid-audit restarted it from zero; rows stuck `RUNNING` | The WebSocket route made "each connection own its run" and cancelled the run on disconnect (an earlier fix for React StrictMode double runs) | Run is a background task with its own DB session; events go to a per-audit log + subscriber queues; reconnects replay then follow live; disconnect only unsubscribes. Startup marks orphaned rows as interrupted | Observed before: ~5 min of work discarded, new process spawned. After: refresh at 60 s → same PID, full state restored, **1 run per audit**. Stuck rows **3 → 0** |
| F6 | Live counters frozen: timer `T+0.0S`, pages 0, Scout telemetry empty, Vision silent for minutes | Page count, elapsed time and Vision progress were only sent with the final result (same class as D2, late screenshots) | `stats_update` after Scout; ticking client timer; per-page Vision progress log + AI-call counter; `stats_update` no longer resets fields it doesn't carry | Pages shown at **~50 s instead of ~7 min**; timer ticks; Vision reports each page |
| F7 | QUICK SCAN promised "2 pages" but scanned 4 | Scout prefetched `SCOUT_PREFETCH_LINKS=3` extra pages regardless of the tier's page budget | Prefetch capped at `tier_pages − 1` | Quick scan: pages **4 → 2**, screenshots **17 → 9**, run time **116 s → 93 s** (same site, back to back) |
| F8 | Report said "no patterns in 17 screenshots" when the model had looked at 1 page | `screenshots_analyzed = len(screenshots)` counted what Scout captured, not what the VLM saw; the NIM budget stops the page loop early | Count pages actually analysed; reason says "1 of 2 pages (AI budget for this tier ran out)" | Claim accuracy: **17 → 1** for quick scan (the true number) |
| F9 | Every History link after a server restart opened an empty, all-`ABORTED` dashboard | Audits lived only in process memory; most panels are fed by streamed events, which were never stored | On completion the event log is written to `backend/data/events/<id>.jsonl` (base64 stripped); replay re-reads images, only from the screenshot folders, only for well-formed IDs | Panels filled on reopen after restart: **0 → all** (new audits); path-traversal guarded and tested |
| F10 | Panels looked broken while waiting | Placeholders said "AWAITING …" with no hint of when; Vision showed nothing until it finished; verdict showed generic fallback text and labelled a "trusted" site `NOMINAL`; badge said `CALIBRATING` forever | Each placeholder names the step that fills it; Vision shows the 5 categories it checks + per-page progress; verdict wired to the judge's narrative, recommendations and real risk level; badge shows the running phase | Qualitative (screenshots before/after in the session) |
| F11 | Full audits took 12+ minutes; UI sat on Vision | Vision ran every prompt for a page one after another (11–15 per page, ~19 s per NIM call on the day measured): **86 % of the audit** (662 of 768 s) | Prompts on a page are independent → run concurrently (`VISION_CONCURRENCY=4`); the NIM client already rate-limits and reserves budget atomically, so the tier's call budget cannot be overspent; findings keep their original order | Same site, same tier, same day: Vision **662 s → 239 s (2.8×)**, whole audit **768 s → 293 s (−62 %)**, AI calls **35 → 35** |
| F12 | Executive summary ended "Other concerns: mi" | `', '.join(types)[:2]` sliced the *joined string* to 2 characters instead of taking 2 items | Slice the list, humanise names, skip when empty | Fixed (one occurrence in the codebase) |
| F13 | "4 pages scanned" were one page: `/`, `/#top`, `/#features`, `/#actions` | Scout collected internal links with their `#fragment`, so same-page anchors deduplicated as different pages; Vision then spent its AI budget on the same page 4 times | Strip fragments in the in-browser link collector and skip links back to the current page; defensive `urldefrag` in prefetch | takebloom: 4 "pages" (1 real) → **4 distinct pages** (`/resize-photo-to-50kb/`, `/jpg-to-pdf/`, `/heic-to-png/`); AI calls now go to different content |
| F14 | CAPTCHA "detected" on normal pages; forms always 0 | The detector matched the substring `captcha` anywhere in the HTML (dormant scripts, CSS classes, i18n strings) and aborted the page as `CAPTCHA_BLOCKED` before forms were read | Judge by what a visitor sees: challenge-page title/text, or a visible CAPTCHA widget on a near-empty page = blocked; a visible widget on a normal page is recorded and the audit continues | github.com/login: `CAPTCHA_BLOCKED`, **0 forms → SUCCESS, 5 forms** |
| F15 | CVSS radar looked identical on every audit; MITRE grid always empty | CVSS scores *one vulnerability*, not a website: with no findings it is always 0.0 with a near-constant vector. The MITRE mapper (correctly) needs ≥ 2 distinct markers per technique, so it only fires on malicious sites | Replaced with `SECURITY.CHECKS` (8 checks in plain English, evidence + fix, live ~35 s in; CVSS kept as one verifiable line when > 0; MITRE matches shown as an alert block when present) and `DOMAIN.FACTS` (age, registrar, certificate issuer, IP, hosting country, identity) | Security results visible at **~35 s instead of at the end**; two always-empty panels → two always-populated ones |
| F16 | "Is there a faster vision model?" | Surveyed every image-capable model on the NIM account with raw, uncached calls through the production path (thinking off, same JSON schema) | Kept `nemotron-3.5-super-vl-120b`; the earlier 19–30 s per call was free-tier queueing at busy hours, not model size | super-vl **1.6–2.0 s**; nano-omni-30b 1.7–2.0 s (no faster, **6 vs 2 false alarms**, F1 0.63 vs 0.83); step-5 8.5 s; kimi-k3.1 > 100 s; Gemma-3 4B/12B and Cosmos-8B listed but **404** |
| F17 | Same clean page flagged in one run, clean in the next | Single VLM calls over-report on clean pages (e.g. a green "Add to Cart" called a misdirected click) | Each *positive* finding gets one targeted re-check; dropped if not reproduced (kept if the verifier itself fails). Clean pages cost nothing extra | Labelled set, 2 runs each, fresh cache: precision **0.71 → 1.00**, false alarms **2 → 0**, clean pages flagged **1/2 → 0/2**, F1 **0.83 → 0.89**, recall 1.00 → 0.80, AI calls +15 %, wall time unchanged (163 s) |
| F18 | SSRF: a public page could make the audit browser load the host's private services (e.g. a redirect to `http://127.0.0.1:8000`) | The guard checked only the submitted URL. First fix (Playwright `page.route`) was **tested and found leaky**: Playwright routes only the first URL of a redirect chain, so public → public → private still served the secret | Local **egress proxy** (Smokescreen pattern): Chromium sends all traffic through it (`--proxy-bypass-list=<-loopback>` so localhost can't skip it); it resolves each host itself, refuses non-public IPs, and dials the exact IP it checked (closes DNS rebinding). Checked IPs cached 60 s | Controlled test: redirect, 2-hop redirect and embedded image to a "private" server → **0 hits** (route version: leaked on 2-hop). Real public HTTPS works; `127.0.0.1:8010` and `169.254.169.254` refused. Overhead **+0.9 s** per Scout run (23.0 → 23.9 s) |

**Score attribution for the same site, before vs after** (site-type weights for `saas_subscription`):

| Signal (max pts) | Lost before | Lost after | Why it changed |
|---|---|---|---|
| Background check / graph (20) | 6.50 | 2.89 | F1/F2: real investigation instead of crash placeholder (1 claim, not confirmed) |
| Domain records / meta (10) | 4.47 | 0.65 | F1: real certificate + no age penalty for a platform subdomain |
| Fake timers / temporal (15) | 3.82 | 2.25 | F3: "nothing to test" is unverified, not a finding |
| Security setup (20) | 1.32 | 1.81 | real: 5 missing security headers (header check 74 %) |
| Page structure (15) | 0.98 | 0.98 | check tops out at 95 % by design |
| Manipulative design / visual (20) | 0.45 | 0.45 | 0 patterns in 17 screenshots |
| **Score** | **82** | **91** | |

**Audit time on the same site, standard tier, across the day** (one run each; NIM free-tier latency varies, so only the 768 → 293 s pair is a controlled comparison):

| Run | Vision | Whole audit | Note |
|---|---|---|---|
| Before F11 (sequential) | 662 s | 768 s | ~19 s per NIM call |
| After F11 (concurrent ×4) | 239 s | 293 s | same hour, same 35 calls |
| After F11–F15 | 44 s | **96 s** | faster NIM hour; 4 real pages instead of 1 page ×4 |

**How each claim was verified**
- Crash reproduced by calling `GraphInvestigator.investigate()` directly on the site: `AttributeError: 'NoneType' object has no attribute 'lower'`; after the fix the same call returns graph 0.857 / meta 0.95.
- The before-attribution comes from replaying the stored signal values through `compute_trust_score`; it reproduces **82** exactly.
- After-numbers come from a full audit run in Chrome (`vrts_607f1abe`, standard tier, 442 s, 35 NIM calls, 0 dark patterns), and the persisted `score_breakdown` row.
- Reconnect verified live (page reload mid-Vision, `ps` showed one process with an unchanged start time) and by four route tests (`backend/tests/test_audit_stream_disconnect.py`).
- Regression tests added: `test_meta_score_survives_missing_registrar`, `test_score_breakdown_accounts_for_every_point`, `test_override_points_are_reported`, `test_failed_graph_placeholder_is_not_scored_as_evidence`.

**Lesson:** 446 passing tests and a green type-check did not catch any of these. All six were visible within ten minutes of watching one real audit. The two worst (F1, F5) were *silent*: a swallowed exception turned into plausible-looking numbers, and a "cancel on disconnect" fix for one bug created another.

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
| Vision, re-measured 2026-11-25 (2 runs each, fresh cache) | 0.714 / 1.0 / 0.833 (2 false alarms) | **1.00 / 0.80 / 0.889** with positive-finding verification (F17) | The no-verify number is lower than the Nov 21 one (0.833); cause not isolated (model-side drift or pipeline changes). Same result on both runs of each config. |
| Injection ASR (3 attacks, matched pairs) | **1/3** | **0/3** (95% CI 0–0.56) | Spotlighting alone: still 1/3. Quarantine: 0/3. Controls clean 3/3. |
| Injection detector | — | 5/5 fixtures, 6/6 held-out phrasings, 0/7 benign phrases, 0/9 real pages | Held-out set was used to fix one miss → now dev data; needs a fresh test set |
| End-to-end, 4 real legit sites (standard tier) | — | **0/4 false alarms** (baseline 0/4), p50 200 s (Nov 21) | mindlyticai 84, synthara 78, example 94, wikipedia 91. Vision was ≈ 70–86 % of audit time before concurrent vision (F11). Legit-only: measures false alarms, not phishing recall. |

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
| Vision latency: fixed by concurrency (F11) but still bounded by NIM free-tier latency, which varied 10–30 s per call across one day; single before/after pair, not a benchmark | Medium | Partly mitigated |
| Vision false alarms: fixed on the labelled set by verifying positives (F17), at the cost of one missed hidden-unsubscribe (recall 0.8). Set is 7 pages: not tuned further to avoid fitting the test set | Medium | Mitigated; needs a larger labelled set |
| Security-headers module attaches `cvss_score: 8.8` to a *missing* CSP header (inflated; not shown in the UI since F15, still in API output) | Low | Open |
| Abandoned audits now run to completion (by design, so reloads don't lose work); they still hold the concurrency slot until done | Low | Accepted |
| mindlyticai score moved 90 → 84 after full-page + all-module analysis; per-finding attribution not yet itemised | Low | Open |
| Retry × timeout worst case (~4.5 min per call) not reproduced; observable now | Medium | UNVERIFIED |
| SSRF: browser traffic now goes through an egress proxy (F18). Not covered: WebRTC/UDP from page scripts; the darknet tier skips the proxy when Tor is active (Tor exits refuse private addresses) | Low | Mitigated |
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
- *"Why 82?"* had no answer until the score carried its own arithmetic. Splitting lost points into "found a problem" vs "could not verify" exposed a crash that had been costing **11 of 18 points** (F1–F4).
- Fallback values are the most dangerous output an agent has: they look like data. A failed agent must be *absent* evidence, never neutral evidence (F2).
- Coupling a long job's lifetime to a WebSocket made every refresh throw away the job; the fix was an event log with replay, which is a standard pattern (F5).
- Model choice was measured, not assumed: six image models probed through the production path with the cache bypassed. The bigger model stayed: it was as fast as the 30B one and had a third of the false alarms. The real latency problem was free-tier queueing, solved with concurrency (F11, F16).
- Verify the positives, not everything: a second look only at claimed findings removed all false alarms for +15 % calls and no extra wall time, because clean pages (the common case) need no second call. It cost one true detection; I stopped there rather than tune a 7-page test set (F17).
- Test the security fix against the attack, not against the function: the first SSRF fix passed its own logic but a controlled 2-hop redirect still reached the private server, which moved the guard from request interception to an egress proxy (F18).
- Probes need guards against their own shortcuts: a silent fallback model and a response cache both made broken or repeated calls look healthy until the probe checked which model answered and bypassed the cache.
