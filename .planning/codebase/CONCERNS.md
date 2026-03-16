# Codebase Concerns
**Analysis Date:** 2026-03-16

## Tech Debt

**Frontend-Backend Event Wiring Incomplete:**
- Issue: `audit_result` event lacks fields that exist in backend `judge_decision`
- Files: `frontend/src/lib/types.ts:820-823` (TODO markers)
- Impact: UI cannot display `trust_score_result`, `dual_verdict`, `judge_decision` data
- Fix approach: Extend WebSocket event forward in `backend/routes/audit.py` to include these fields

**Empty Return Patterns (Stub Implementations):**
- Files: `veritas/agents/graph_investigator.py:109,507,551,555,568,572,585-587,649,1024`, `veritas/analysis/pattern_matcher.py:192,203,228,423,430,434,438`, `backend/services/audit_runner.py:269`
- Issue: Silent fallback to empty results instead of raising errors
- Impact: Failures mask as "no findings" rather than surfacing issues
- Fix approach: Replace `return None`/`return []` with proper error propagation

**OSINT Sources Incomplete:**
- Files: `.planning/phases/08-osint-cti-integration/FUTURE_EXPANSION.md` (lines 11-179)
- Issue: 9 external sources stubbed as TODO (alienvault, spamhaus, virustotal, etc.)
- Impact: Limited threat intelligence - only darknet sources active
- Fix approach: Implement source adapters per phase plan

## Known Issues

**Database Persistence Not Fully Operational:**
- Issue: Phase 05 implementation incomplete - audit results may not persist
- Files: `.planning/phases/05-persistent-audit-storage/05-02-PLAN.md:148-154`
- Impact: Audit history lost on restart; no audit history for re-judging
- Fix approach: Enable `should_use_db_persistence()` and complete repository wiring

**Graph Investigator Error Handling:**
- Issue: Broad `except Exception` handlers returning empty dicts
- Files: `veritas/agents/graph_investigator.py:412-422,497-505,541-555`
- Impact: Network/API errors silently fail; no retry or fallback paths visible
- Fix approach: Add circuit breaker and error categorization

## Security Concerns

**Input Validation on Audit Endpoint:**
- Files: `backend/routes/audit.py:40-44` (AuditStartRequest)
- Issue: Minimal validation on `url` and `tier` parameters
- Current: Uses Pydantic but allows any string for tier
- Recommendation: Add enum validation and URL sanitization before passing to agents

**Environment Secrets Management:**
- Note: `.env` file present at `veritas/.env` (loaded via `load_dotenv`)
- Risk: If `.env` committed to git, secrets exposed
- Current: `.gitignore` checked - ensure it excludes `.env`
- Recommendation: Verify no secrets in committed files

## Fragile Areas

**IPC Layer State Consistency:**
- Files: `veritas/core/ipc.py`, `backend/services/audit_runner.py`
- Risk: In-memory audit state (`_audits` dict in audit.py) not persisted
- Trigger: Server restart loses all audit metadata
- Test coverage: Low - only basic IPC tests exist

**Orchestrator Complexity:**
- Files: `veritas/core/orchestrator.py` (200+ lines, multi-agent coordination)
- Issue: Max iterations/cycles could exhaust resources on malicious targets
- Current mitigation: Budget controls exist but not tested
- Safe modification: Requires extensive integration testing