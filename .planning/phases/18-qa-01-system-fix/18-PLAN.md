# Phase 18 Plan: QA-01 System Fix

## Objective

Fix all critical issues in VERITAS system: backend processes, results accuracy, sequence ordering, and frontend UX.

## Steps

### Step 1: Test Audit Pipeline (COMPLETED ✓)
- [x] Backend tests pass: 13/13
- [x] Frontend build succeeds
- [x] Sequence field fix applied
- [x] VerdictPanel field fallback added
- [ ] Runtime audit test (pending)

### Step 2: Runtime Verification
- [ ] Start backend server
- [ ] Run test audit against known site
- [ ] Verify WebSocket events have correct sequence
- [ ] Verify verdict data displays correctly

### Step 3: Additional Field Mapping Fixes
- [ ] AuditResult fields match backend output
- [ ] Trust score displays correctly
- [ ] Risk level displays correctly

### Step 4: Error Boundary Implementation
- [ ] Add PanelErrorBoundary to audit page
- [ ] Add graceful degradation for missing data

### Step 5: Integration Testing
- [ ] Full E2E test of audit flow
- [ ] Verify all UI components render correctly

## Success Criteria

- Backend audit completes without crash
- WebSocket sequence numbers appear in events
- Verdict panel shows summary text
- No undefined value crashes in UI
- Trust score displays numerically

## Files Modified So Far

- `veritas/core/progress/emitter.py` - sequence field
- `frontend/src/components/terminal/VerdictPanel.tsx` - field fallback
- `frontend/src/components/terminal/KnowledgeGraph.tsx` - TS fix