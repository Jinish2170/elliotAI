# Codebase Concerns
**Analysis Date:** 2026-05-14

## Tech Debt

- **Leftover debug file-write in production code path**
  - Issue: `open("judge_debug.txt", "w").write(...)` executes on every dual-verdict render. Unconditional, synchronous, no exception guard, no cleanup. The artifact file `judge_debug.txt` already exists at the repo root, confirming it runs in practice. Adjacent `logger.warning("----- JUDGE EMITTER PRESENT? ... -----")` lines at 228 and 230 are also debug noise dressed as warnings.
  - Files: `elliot/agents/judge.py:228-230`
  - Impact: Pollutes working dir, races under concurrent audits (single fixed filename), can throw on read-only filesystems, leaks internal state to disk.
  - Fix approach: Delete line 229 and the two `logger.warning` debug banners (228, 230); demote any genuinely useful signal to `logger.debug`. Confirm `judge_debug.txt` stays gitignored and remove the stray file.

- **`print()` used as progress/IPC transport instead of structured logging**
  - Issue: `print(f"##PROGRESS:{json.dumps(event)}", flush=True)` and bare diagnostic prints are scattered through agents. Mixes the IPC contract with ad-hoc debug prints (`print(f"Dark patterns found: ...")`, `print(f"Score: ...")`).
  - Files: `elliot/agents/vision.py:267,402-404`, `elliot/core/orchestrator.py:181-182,270`, `elliot/agents/judge.py:155-158`, `elliot/agents/scout.py`, `elliot/core/nim_client.py`, plus ~20 files (140 occurrences).
  - Impact: Debug prints contaminate stdout, which `backend/services/audit_runner.py` parses for `##PROGRESS:` markers — stray prints can be mis-parsed or break the JSON stream. Hard to silence in production.
  - Fix approach: Route all non-IPC output through `logger`. Keep exactly one sanctioned `##PROGRESS:` emit path; gate it behind the IPC-mode check already present in `elliot/__main__.py`.

- **Broad `except Exception` swallowing (222 occurrences across 57 files)**
  - Issue: Pervasive `except Exception` (and `except Exception:` with `pass`) — e.g. `elliot/core/nodes/security.py:115`, `elliot/core/nodes/graph.py:78`. No bare `except:` found (good).
  - Files: hotspots `elliot/agents/scout.py` (26), `elliot/agents/graph_investigator.py` (22), `elliot/agents/vision.py` (11), `elliot/core/orchestrator.py` (11), `elliot/core/evidence_store.py` (10).
  - Impact: Real failures (auth errors, schema drift, NIM contract changes) get silently degraded to empty results, making the audit pipeline fail open rather than surface the problem.
  - Fix approach: Narrow to specific exception types where the failure mode is known; for genuine catch-alls, always `logger.exception(...)` and record into `AuditState["errors"]` so the verdict reflects degraded evidence.

- **Stale `veritas` branding; `veritas/` directory does not exist**
  - Issue: The product was renamed to "elliot"; `veritas/` referenced in task scope and `.planning` docs is absent. `elliot/tests/test_veritas.py` (1004 lines) still carries the old brand.
  - Files: `elliot/tests/test_veritas.py`, numerous `.planning/docs/*VERITAS*` files.
  - Impact: Stale naming creates confusion about where code lives; onboarding friction; broken doc paths.
  - Fix approach: Rename `test_veritas.py` → `test_audit_pipeline.py`; sweep `.planning` docs for dead `veritas/` paths.

- **Several oversized modules (>1000 lines)**
  - Issue: `elliot/agents/graph_investigator.py` (2055), `elliot/agents/judge.py` (1584), `elliot/agents/scout.py` (1567), `elliot/agents/vision.py` (1507), `elliot/ui/app.py` (1495), `elliot/agents/security_agent.py` (1221). Total Python LOC ~53k.
  - Files: as above.
  - Impact: Hard to test in isolation, high merge-conflict surface, single-responsibility violations (judge.py mixes deliberation, dual-verdict building, CVSS emission, IPC).
  - Fix approach: Extract cohesive units — e.g. judge's dual-verdict/CVSS emission into the existing `elliot/agents/judge_core/verdict` package, which is the natural home.

## Known Bugs

- **`judge_debug.txt` written every dual-verdict run**
  - Symptoms: An unexpected `judge_debug.txt` appears/overwrites in the process CWD on each audit that renders a dual verdict.
  - Files: `elliot/agents/judge.py:229`
  - Trigger: `use_dual_verdict and decision.action == "RENDER_VERDICT" and DUAL_VERDICT_AVAILABLE` — i.e. the normal expert-mode success path.
  - Workaround: None needed for correctness; delete the line. File is gitignored so it does not get committed, but it still litters every run environment and collides across concurrent audits.

- **No-graph / signal-conflict early termination depends on un-asserted threshold keys**
  - Symptoms: `deliberate()` indexes `thresholds[...]` directly (`no_graph_max_iteration`, `signal_conflict_delta`, `early_exit_confidence`, `deep_scan_external_links_min_pages`, etc.). A missing key in a custom `JUDGE_THRESHOLDS` override or per-tier override raises `KeyError` mid-audit.
  - Files: `elliot/agents/judge.py:278,298,305-306,320-321,344,386,388,417-420`, `elliot/config/settings.py:295-326`
  - Trigger: Setting a partial per-tier override via `settings.get_judge_thresholds(tier)`.
  - Workaround: Always supply complete threshold dicts; better fix is `.get()` with defaults or schema validation at load.

## Security Considerations

- **Backend API has no authentication and binds 0.0.0.0**
  - Risk: `backend/main.py` registers `/api` audit + health routes with zero auth dependency; `uvicorn.run(host="0.0.0.0", port=8000, reload=True)`. CORS `allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True`.
  - Files: `backend/main.py:57-78`, `backend/routes/audit.py`
  - Current mitigation: `allow_origins` is env-driven and defaults to localhost only — the only control in place.
  - Recommendations: Add an API-key/bearer dependency on audit routes; bind `127.0.0.1` for the desktop-app use case; disable `reload=True` outside dev; never combine `allow_credentials=True` with wildcard methods/headers in any internet-exposed deployment.

- **Audit runner spawns a Python subprocess and parses its stdout**
  - Risk: `backend/services/audit_runner.py:168` and `elliot/ui/app.py:609` use `subprocess.Popen` to run the audit CLI; the target URL flows into the child process args/env. The IPC contract is "parse `##PROGRESS:` lines from stdout."
  - Files: `backend/services/audit_runner.py:8,168-191`, `elliot/ui/app.py:20,578-615`, `elliot/core/ipc.py`
  - Current mitigation: `shell=False` (list-form args), so no shell-injection; venv python resolved via `_find_venv_python()`.
  - Recommendations: Validate/normalize the URL before it reaches the subprocess boundary; ensure the URL is passed as an arg (not interpolated into a string); cap subprocess lifetime with a hard timeout; treat any non-`##PROGRESS:` stdout as untrusted.

- **TOR / .onion routing via SOCKS5h proxy**
  - Risk: `elliot/core/tor_client.py` (and `elliot/darknet/`, `elliot/osint/sources/darknet_*`) route requests through `socks5h://127.0.0.1:9050` to fetch attacker-controlled .onion content, then feed fetched HTML/JS to analyzers and the VLM.
  - Files: `elliot/core/tor_client.py:1-50`, `elliot/darknet/tor_client.py`, `elliot/darknet/threat_scraper.py`, `elliot/osint/sources/darknet_*.py`
  - Current mitigation: Module docstring asserts read-only OSINT, no transactions, no logging of user .onion URLs; `socks5h` keeps DNS on the proxy. No `verify=False` / SSL bypass anywhere in the tree (confirmed).
  - Recommendations: Ensure graceful degradation when the Tor daemon (9050) is closed; sandbox/limit rendering of darknet content; never execute fetched JS; verify the `darknet_*` source files are not stale placeholders shipped as live feeds.

- **API keys read from environment; `.env.example` present**
  - Risk: `NIM_API_KEY`, `TAVILY_API_KEY`, `URLVOID_API_KEY`, `ABUSEIPDB_API_KEY` loaded via `os.getenv`. A real `.env` may exist (not inspected per policy).
  - Files: `elliot/config/settings.py:44-76`, `.env.example`
  - Current mitigation: Keys default to empty strings; `.gitignore` modified in working tree (verify `.env` is excluded).
  - Recommendations: Confirm `.env` is gitignored; fail fast with a clear message when a required key is empty rather than degrading silently inside a broad `except`.

- **`eval()` / `document.write()` references are analyzer signatures, not live calls — cleared**
  - Risk: Grep for `eval(`/`exec(` hits only OWASP/JS-analyzer detection patterns (`elliot/analysis/security/owasp/a03_injection.py`, `a08_data_integrity.py`, `js_analyzer.py`). No dynamic code execution in the codebase itself.
  - Files: n/a (clean)
  - Current mitigation: n/a
  - Recommendations: None — confirmed safe.

## Performance Bottlenecks

- **Historical 5-8 JUDGE iterations to converge — fix landed (commit 855be24), needs verification under load**
  - Problem: The audit loop previously ran 5-8 judge iterations because iteration 1 was evidence-starved.
  - Files: `elliot/agents/vision.py:73-85` (pass priority), `elliot/core/nodes/scout.py:21-26,176` (prefetch), `elliot/core/nodes/graph.py:49-78` (link aggregation), `elliot/agents/judge.py:298-344` (early-exit gate), `elliot/config/settings.py:125,295` (`SCOUT_PREFETCH_LINKS`, `JUDGE_THRESHOLDS`)
  - Cause (now addressed): Vision pass 2 was `CONDITIONAL` — now `CRITICAL` and runs every page (`vision.py:75-76`); Scout fetched only the entry URL — now prefetches up to `SCOUT_PREFETCH_LINKS` priority pages (`scout.py:176`); Graph aggregated only the primary page's external links — now across all scouted pages; judge gained a high-confidence early-exit gate (`judge.py:320-321`).
  - Improvement path: Fix verified present in tree. Next: measure real iteration counts on a corpus to confirm convergence improved; tune `early_exit_confidence` / `early_exit_min_iteration` per tier if still slow.

- **Prefetch added to Scout's first pass increases per-iteration latency**
  - Problem: `scout_node` prefetches priority internal pages within the first pass; if serial, first-iteration latency grows with `SCOUT_PREFETCH_LINKS`.
  - Files: `elliot/core/nodes/scout.py:107-209`, `elliot/agents/scout.py`
  - Cause: Prefetch trades per-iteration time for fewer iterations.
  - Improvement path: Confirm prefetch fetches run concurrently (asyncio.gather with a small semaphore); keep `SCOUT_PREFETCH_LINKS` default low (currently 3).

- **VLM (NIM) calls are the dominant cost, governed by a rate limiter and budget**
  - Problem: Vision now runs more passes per page (pass 2 always-on); each is a NIM VLM call. `NIM_REQUESTS_PER_MINUTE=40`, `NIM_TIMEOUT=90`.
  - Files: `elliot/core/nim_client.py:488-529`, `elliot/agents/vision.py`, `elliot/config/settings.py:55-57`
  - Cause: Forensic depth requires VLM passes; rate limiter serializes them (`_min_delay` sleep between calls).
  - Improvement path: VLM result caching exists (`elliot/tests/test_vlm_caching.py`) — ensure it is hit for repeated screenshots; consider batching passes per image where the model supports multi-turn.

## Fragile Areas

- **LangGraph `AuditState` is a plain `TypedDict` with no channel reducers**
  - Files: `elliot/core/orchestrator.py:51-97`, `elliot/core/nodes/scout.py`, `vision.py`, `graph.py`, `judge.py`, `security.py`, `routing.py`
  - Why fragile: No `Annotated[..., reducer]` on any field. Nodes accumulate by reading-then-rewriting whole lists (e.g. `scout.py:176` `new_scout_results = scout_results + [...]`, returned as `{"scout_results": new_scout_results}`). If two nodes ever return the same key in one super-step, last-writer-wins silently drops data. State is passed as serialized plain dicts (`_serialize_scout_result`), so type drift between the dataclass and the dict shape is undetected until a `KeyError` deep in the judge.
  - Safe modification: Treat each node as the sole writer of its keys; never split ownership of a list across nodes. If accumulation across parallel branches is ever needed, add explicit reducers. Keep `_serialize_*` helpers in lockstep with their dataclasses.
  - Test coverage: `elliot/tests/langgraph_investigation/` (test_01/02/03) and `elliot/tests/integration/test_data_flow.py` exercise the graph; `test_scout_prefetch.py`, `test_judge_early_exit.py`, `test_vision_pass_priority.py` cover the 855be24 changes. No test asserts the no-double-writer invariant.

- **stdout is a shared channel for IPC, logging, and stray prints**
  - Files: `elliot/__main__.py:25-57,229`, `elliot/core/ipc.py`, `backend/services/audit_runner.py:191-222`, `elliot/agents/vision.py:267`, `elliot/core/orchestrator.py:270`
  - Why fragile: The parent parses `##PROGRESS:` JSON lines from the child's stdout. Any library or debug `print()` in the child can interleave and break a JSON line. `elliot/__main__.py` reroutes prints to stderr in "subprocess mode," but new `print()` calls in agents bypass that intent.
  - Safe modification: Never `print()` in agent/core code — use `logger`. Changes to the `##PROGRESS:` schema must update both emitter and `audit_runner._read_queue_and_stream` / stdout parser together.
  - Test coverage: `elliot/tests/test_ipc_queue.py`, `test_ipc_integration.py`, `backend/tests/test_audit_runner_queue.py` cover the Queue IPC path; the stdout-marker fallback path is less covered.

- **Windows-specific subprocess + multiprocessing spawn context**
  - Files: `elliot/core/ipc.py:8,127,175-208`, `backend/services/audit_runner.py:4,42-67`
  - Why fragile: IPC uses `multiprocessing` spawn context with Queue serialized via env vars — explicitly Windows-driven. The `langgraph_investigation/` test suite exists precisely because `ainvoke()` under subprocess isolation on Windows misbehaved.
  - Safe modification: Test any IPC/orchestrator change on Windows specifically; do not assume fork semantics.
  - Test coverage: `elliot/tests/langgraph_investigation/test_01_minimal_graph.py` etc. are diagnostic, not regression guards.

## Scaling Limits

- **Single-audit-per-subprocess model**
  - Current capacity: One audit = one spawned Python subprocess holding Playwright, LanceDB, sentence-transformers, OpenCV in memory (requirements doc budgets ~1.5GB RAM, "verified for 8GB RAM").
  - Limit: Concurrent audits multiply RAM linearly; the fixed `judge_debug.txt` filename also collides across concurrent runs. No worker pool / queue.
  - Scaling path: Introduce a bounded job queue + worker pool in `backend/`; reuse warm browser contexts; make any debug/temp filenames audit-id-scoped.

- **NIM API rate limit is a hard ceiling on throughput**
  - Current capacity: `NIM_REQUESTS_PER_MINUTE=40`, shared across all passes of an audit; rate limiter sleeps `_min_delay` between calls.
  - Limit: Vision (now multi-pass-per-page) plus judge calls compete for the same 40 rpm; multiple concurrent audits starve each other.
  - Scaling path: Per-account rate-limit awareness, request prioritization (judge > vision pass 4), or a higher-tier NIM quota; aggressive VLM cache reuse.

- **SQLite backend persistence**
  - Current capacity: `backend` uses SQLite with WAL mode (`backend/tests/test_audit_persistence.py`, `backend/routes/health.py`).
  - Limit: WAL helps single-writer concurrency but SQLite still caps write throughput; fine for a desktop app, not for multi-user server use.
  - Scaling path: If the backend ever goes multi-user, migrate to Postgres behind the existing SQLAlchemy async layer (already ORM-based, so low-friction).

## Dependencies at Risk

- **`langgraph>=0.2.0` / `langchain>=0.3.0` — unpinned, fast-moving APIs**
  - Risk: Both libraries change state/graph APIs frequently across minor versions; `>=` floors mean a fresh install can pull a breaking release.
  - Impact: `StateGraph`, the `TypedDict` state contract, and routing edges in `elliot/core/orchestrator.py` could break on upgrade.
  - Migration plan: Pin exact versions in `elliot/requirements.txt`; add a smoke test (the `langgraph_investigation` suite can serve) gated in CI before bumping.

- **`python-whois>=0.9.0` — lightly maintained / brittle parser**
  - Risk: WHOIS output formats vary by registrar; `python-whois` is known-flaky. Graph investigator depends on it.
  - Impact: `elliot/agents/graph_investigator.py` entity verification degrades silently (caught by one of its 22 broad excepts).
  - Migration plan: Strict timeout already exists (`GRAPH_WHOIS_TIMEOUT_S=20`); treat parse failures as explicit "unknown" evidence rather than empty; consider an RDAP-based client as a successor.

- **`WeasyPrint>=60.0` — heavy native dependency chain**
  - Risk: WeasyPrint pulls cairo/pango/gdk-pixbuf native libs; hard to install on Windows, which is the stated target platform.
  - Impact: Report generation (`elliot/reporting/report_generator.py`) can fail at install/runtime on clean Windows machines.
  - Migration plan: Verify it is actually exercised; if PDF export is optional, make the import lazy and degrade gracefully; otherwise document the native prerequisites.

- **Backend vs. agent requirement drift**
  - Risk: `backend/requirements.txt` pins `pydantic==2.9.0` exact; `elliot/requirements.txt` says `pydantic>=2.5.0`. Two separate dependency sets that can resolve to different versions in one repo.
  - Impact: Pydantic model behavior could differ between the FastAPI layer and the agent layer.
  - Migration plan: Consolidate to one lockfile (or a shared constraints file); align pin styles (pin everything).

## Missing Critical Features

- **No authentication/authorization on the backend API**
  - Problem: Audit-triggering endpoints are open (see Security Considerations).
  - Blocks: Any deployment beyond a trusted single-user localhost desktop setup; multi-user or networked use is unsafe.

- **No concurrency control / job queue for audits**
  - Problem: Each audit is an unbounded subprocess spawn with no admission control.
  - Blocks: Running more than a couple of audits at once without exhausting RAM; predictable resource usage.

- **No graceful-degradation contract when Tor / external APIs are unavailable**
  - Problem: Tor daemon, NIM, Tavily, WHOIS failures are absorbed into broad `except Exception` blocks and turned into empty evidence.
  - Blocks: Trustworthy verdicts — a degraded audit currently looks like a clean one. The verdict should explicitly flag "evidence incomplete because X was unavailable."

## Test Coverage Gaps

- **LangGraph state-passing invariants untested**
  - What's not tested: That no two nodes write the same `AuditState` key in one super-step; that `_serialize_*` dict shapes stay in sync with their dataclasses; behavior when an upstream node returns partial/empty state.
  - Files: `elliot/core/orchestrator.py:51-97`, `elliot/core/nodes/*.py`
  - Risk: Silent evidence loss or `KeyError` deep in the judge after a refactor.
  - Priority: High.

- **Broad-except degradation paths untested**
  - What's not tested: That a NIM/Tor/WHOIS failure produces a verdict that *reflects* the missing evidence rather than a falsely-clean score.
  - Files: `elliot/agents/scout.py`, `elliot/agents/graph_investigator.py`, `elliot/agents/vision.py`, `elliot/core/nodes/security.py:115`, `elliot/core/nodes/graph.py:78`
  - Risk: Production failure mode (fail-open) is exactly the dangerous one for a trust-auditing tool.
  - Priority: High.

- **judge.py threshold-key completeness untested**
  - What's not tested: `deliberate()` against partial `JUDGE_THRESHOLDS` per-tier overrides — currently a `KeyError` waiting to happen.
  - Files: `elliot/agents/judge.py:278-417`, `elliot/config/settings.py:295-326`
  - Risk: Mid-audit crash when thresholds are tuned.
  - Priority: Medium.

- **Backend API contract / auth-absence not asserted**
  - What's not tested: `backend/tests/` covers persistence, route contract, and runner queue, but nothing asserts the (intentional or not) absence of auth, or CORS behavior.
  - Files: `backend/main.py`, `backend/routes/audit.py`, `backend/tests/`
  - Risk: Security posture changes silently.
  - Priority: Medium.

- **stdout-marker IPC fallback path lightly covered**
  - What's not tested: The `##PROGRESS:` stdout-parsing fallback (vs. the well-covered Queue IPC) against interleaved/garbage stdout lines.
  - Files: `elliot/core/ipc.py`, `backend/services/audit_runner.py:191-222`, `elliot/__main__.py`
  - Risk: A stray `print()` breaking progress streaming goes unnoticed.
  - Priority: Medium.

- **Darknet OSINT sources may be static placeholders**
  - What's not tested: Whether `elliot/osint/sources/darknet_alpha.py`, `darknet_dream.py`, `darknet_empire.py`, `darknet_hansa.py`, `darknet_wallstreet.py` are real feeds or hardcoded known-onion lookups returning `None` for everything else.
  - Files: `elliot/osint/sources/darknet_*.py`
  - Risk: Shipping stub intelligence as if it were live threat data.
  - Priority: Medium.

---
*Concerns audit: 2026-05-14*
