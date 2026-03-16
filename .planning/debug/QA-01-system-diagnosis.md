# QA-01: Deep Working State Analysis - Veritas System Diagnosis

**Date:** 2026-03-16
**Status:** INVESTIGATION COMPLETE
**Tests:** Backend: 13/13 PASS | Frontend: BUILD OK

---

## Executive Summary

Multiple interconnected issues cause the reported symptoms. The backend tests pass because they test isolated components with mocks. The actual end-to-end data flow has several broken points that cause the "processes failing, results wrong, sequence broken, UI broken" symptoms.

---

## Root Causes Identified

### 1. EVENT SEQUENCING Mismatch (CRITICAL)
**Symptom:** "sequence is also fucked"

**Root Cause:** Backend sends `seq` field, frontend expects `sequence` field

**Evidence:**
- Backend ProgressEmitter (veritas/core/progress/emitter.py:98): sends `"seq": self.sequence_number`
- Frontend Store (store.ts:386): looks for `event.sequence`:
  ```typescript
  const sequence = event.sequence as number | undefined;
  if (sequence !== undefined) {
    const sequencer = getEventSequencer();
    // ...
  }
  ```
- EventSequencer (useEventSequencer.ts): expects `sequence` field in SequencedEvent interface

**Impact:**
- Frontend never receives sequence numbers from ProgressEmitter
- Event ordering works by accident (immediate processing) but race conditions can occur
- WebSocket messages may arrive out-of-order and be processed incorrectly
- Components may receive data in wrong order (e.g., findings before screenshots)

**Files Involved:**
- `veritas/core/progress/emitter.py` - sends wrong field name
- `frontend/src/hooks/useEventSequencer.ts` - expects correct field name
- `frontend/src/lib/store.ts` - checks `event.sequence` not `event.seq`

---

### 2. Data Type Mismatch in Verdict Panel (HIGH)
**Symptom:** "results are wrong", "trust scores wrong"

**Root Cause:** Field name mismatch for narrative/summary

**Evidence:**
- Backend audit_runner.py line 595 sends: `verdict_nontechnical.summary`
- Frontend VerdictPanel.tsx line 47 expects: `verdict.verdict_nontechnical.executive_summary`
- Debug: Score rendering (line 58): `score.toFixed(1)` - potential undefined crash

**Impact:**
- Summary/executive summary not displayed correctly
- Trust score may display as "0" or NaN if data missing
- Risk level may be incorrect due to bad data

**Files Involved:**
- `backend/services/audit_runner.py` - sends event data
- `frontend/src/components/terminal/VerdictPanel.tsx` - reads wrong field

---

### 3. Event Data Payload Type Mismatch (HIGH)
**Symptom:** "findings missing"

**Root Cause:** Audit result fields don't match frontend type expectations

**Evidence:**
- Backend sends `audit_result` with various fields including `judge_decision`, `trust_score`, `risk_level`
- Frontend AuditStore expects: `result.trust_score`, `result.risk_level`, `result.narrative`, `result.signal_scores`
- audit_runner.py line 618-638 builds enriched_summary - may have incorrect field names

**Field Mapping Analysis (audit_runner.py line 618-638):**
```python
enriched_summary = {
    **summary,  # Contains trust_score, risk_level, narrative
    "trust_score_result": trust if trust else None,
    "dual_verdict": {...},
    "judge_decision": {...},
}
```

**Impact:**
- Trust score may not display (undefined)
- Signal scores may be empty or missing
- Frontend shows empty/incomplete results despite backend having data

---

### 4. Frontend Error Boundaries Missing
**Symptom:** "UI crashes", "components not updating"

**Root Cause:** No React error boundaries to catch component failures

**Evidence:**
- Search for `ErrorBoundary` or `componentDidCatch` in frontend: NONE FOUND
- VerdictPanel.tsx line 58: `.toFixed(1)` will throw if score is undefined/NaN
- Multiple components assume data is always properly typed

**Impact:**
- Single component error crashes entire page
- No graceful degradation when data missing
- Poor UX - page freezes or shows blank on error

---

### 5. No Integration/E2E Tests (MEDIUM)
**Symptom:** "processes are failing" - appears at runtime

**Root Cause:** Backend tests mock everything

**Evidence:**
- All 13 backend tests PASSED
- Tests in: `backend/tests/test_audit_persistence.py`, `test_audit_route_contract.py`, `test_audit_runner_queue.py`
- Tests mock: IPC, queue, event handling - none actually run agents end-to-end
- No test creates an actual audit, sends real WebSocket events, verifies frontend receives correct data

**Impact:**
- Unit tests pass but system fails in production
- No way to catch data flow issues before deployment

---

## Detailed Findings by Symptom

### Symptom 1: "Processes are failing"
**Analysis:** Unclear if it's actual agent crashes or just bad UI. Agent code looks structurally sound.
- Scout, Vision, Graph, Judge agents have proper try/catch
- Fallback mechanisms exist in orchestrator
- BUT: No error visualization - errors go to backend logs only

### Symptom 2: "Results are wrong"
**Confirmed Causes:**
1. Event field name mismatch `summary` vs `executive_summary`
2. Missing trust_score propagation in some code paths
3. dual_verdict structure may be incorrect

### Symptom 3: "Sequence is also fucked"
**Root Cause:** Sequence number field mismatch (`seq` vs `sequence`)

### Symptom 4: "UI frontend ux is major loose"
**Confirmed Causes:**
1. No error boundaries (crashes affect whole page)
2. Event data type mismatches cause components to not render
3. VerdictPanel can throw on score.toFixed(1) with undefined

---

## Priority Order Fixes

### PRIORITY 1 (Critical - Fix Immediately)
1. **Fix sequence field name** in `veritas/core/progress/emitter.py`:
   - Change `seq` to `sequence` on line 98
2. **Verify AuditRunner sends sequence numbers** - add to send() calls in audit_runner.py for critical events

### PRIORITY 2 (High - Fix within 24h)
3. **Fix VerdictPanel field mapping** in `VerdictPanel.tsx`:
   - Change `executive_summary` to `summary`
   - Add defensive check for undefined score before `.toFixed()`
4. **AuditResult field mapping** - verify all fields match between backend `enriched_summary` and frontend `AuditResult` type

### PRIORITY 3 (Medium - Fix within week)
5. **Add React Error Boundaries** around terminal components
6. **Add E2E test** that runs real audit and verifies WebSocket events
7. **Add WebSocket event validation** in frontend store

---

## Field Mapping Reference

### Backend sends (audit_runner.py):
```
audit_result:
  - trust_score (from summary)
  - risk_level (from summary)
  - narrative (from summary)
  - signal_scores
  - green_flags
  - judge_decision
    - action
    - narrative
    - recommendations
    - trust_score_result
  - dual_verdict
    - verdict_technical
    - verdict_nontechnical
```

### Frontend expects (store.ts, types.ts):
```
result:
  - trust_score: number
  - risk_level: string
  - narrative: string
  - signal_scores: Record<string, number>
  - verdict_nontechnical.summary (NOT executive_summary)
```

---

## Evidence Summary

| Evidence Type | Location | Finding |
|---------------|----------|---------|
| Code diff | emitter.py:98 vs store.ts:386 | Field name mismatch: `seq` vs `sequence` |
| Code diff | VerdictPanel.tsx:47 | Wrong field: `executive_summary` vs `summary` |
| Unit test | backend/tests/ | 13/13 pass but mock everything |
| Build success | next build | Frontend compiles OK |
| Type mismatch | VerdictPanel.tsx:58 | Potential undefined.toFixed() crash |

---

## Recommended Fixes (Implementation Hints)

### Fix 1: Emit correct sequence field
```python
# veritas/core/progress/emitter.py line 98
# BEFORE:
"seq": self.sequence_number,
# AFTER:
"sequence": self.sequence_number,
```

### Fix 2: Add error boundary in audit page
```tsx
// src/app/audit/[id]/page.tsx
class ErrorBoundary extends React.Component<{children: React.ReactNode}> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) return <div>Error loading terminal</div>;
    return this.props.children;
  }
}
```

### Fix 3: Defensive VerdictPanel
```tsx
// VerdictPanel.tsx
const score = trustScore ?? (verdict?.verdict_nontechnical?.trust_score ?? verdict?.verdict_technical?.trust_score ?? 0);
const summaryStr = verdict?.verdict_nontechnical?.summary || verdict?.verdict_nontechnical?.executive_summary || "Awaiting...";
```

---

## Files Requiring Changes

| File | Change | Priority |
|------|--------|----------|
| `veritas/core/progress/emitter.py` | Field `seq` -> `sequence` | P1 |
| `frontend/src/components/terminal/VerdictPanel.tsx` | Fix field mapping, add error handling | P2 |
| `backend/services/audit_runner.py` | Add sequence numbers to events | P1 |
| `frontend/src/app/audit/[id]/page.tsx` | Add error boundary | P3 |
| `frontend/src/lib/store.ts` | Add event validation | P3 |

---

## Conclusion

The system has design-level issues hidden by passing unit tests. The primary issues are:
1. **Frontend-backend field name mismatches** (sequence, summary fields)
2. **Missing error handling** in React components
3. **No integration tests** to catch these issues

The fixes are straightforward but need to be prioritized and tested with actual end-to-end audits after implementation.