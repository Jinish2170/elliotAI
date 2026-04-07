# Ralph Loop: Functionality & Integration Bugs Report

## Iteration 1: Code Review Complete - FIXES APPLIED

### BUG 1: Null Safety - History Page (CRASH) ✅ FIXED
**File:** `frontend/src/app/history/page.tsx`
**Line:** 237
**Issue:** Calling `.replace()` on potentially null/undefined `audit.audit_tier`

**Fix Applied:**
```tsx
{(audit.audit_tier || "standard").replace(/_/g, " ")}
```

---

### BUG 2: WebSocket URL Construction (POTENTIAL BUG) ✅ FIXED
**File:** `frontend/src/hooks/useAuditStream.ts`
**Line:** 6-7
**Issue:** If `NEXT_PUBLIC_WS_URL` is set without protocol (e.g., "localhost:8000"), WebSocket fails

**Fix Applied:** Ensure protocol prefix:
```typescript
const _wsBase = process.env.NEXT_PUBLIC_WS_URL || "localhost:8000";
const WS_BASE = _wsBase.startsWith("ws") ? _wsBase : `ws://${_wsBase}`;
```

---

### BUG 3: useCallback Missing Dependencies (STALE CLOSURE) ✅ FIXED
**File:** `frontend/src/hooks/useAuditStream.ts`
**Line:** 53
**Issue:** `connect` function uses `url`, `tier`, and `store` but not in dependency array

**Fix Applied:** Added proper dependencies:
```typescript
}, [auditId, url, tier, store, checkFinalStatus]);
```

---

### BUG 4: Frontend Ignores Backend `ws_url` Response ⚠️ LOW PRIORITY - Not fixed
Not critical - works but redundant

---

### BUG 5: WebSocket Close Handler Logic ✅ FIXED
**File:** `frontend/src/hooks/useAuditStream.ts`
**Lines:** 43-50
**Issue:** UI stuck in "running" state when WS closes normally mid-audit

**Fix Applied:** Added REST API fallback to check final status:
```typescript
ws.onclose = async (event) => {
  if (store.status === "running") {
    if (event.code !== 1000) {
      store.setStatus("error");
    } else {
      await checkFinalStatus(auditId);
    }
  }
};
```

Added helper function:
```typescript
const checkFinalStatus = useCallback(async (id: string) => {
  try {
    const res = await fetch(`${API_URL}/api/audit/${id}/status`);
    // Check final state...
  } catch { /* ignore */ }
}, [store]);
```

---

### BUG 6: Report Page - Missing Error State ⚠️ LOW PRIORITY - Not fixed
User sees blank page on failure - minor UX issue

---

### BUG 7: History Page - Score Null Check ✅ FIXED
**File:** `frontend/src/app/history/page.tsx`
**Line:** 213
**Issue:** Using score without ensuring it's within bounds

**Fix Applied:**
```typescript
width: `${Math.min(Math.max(score ?? 0, 0), 100)}%`
```

---

## SUMMARY

| Bug | File | Severity | Status |
|-----|------|----------|--------|
| 1 | history/page.tsx:237 | HIGH | ✅ FIXED |
| 2 | useAuditStream.ts:6-7 | MEDIUM | ✅ FIXED |
| 3 | useAuditStream.ts:53 | MEDIUM | ✅ FIXED |
| 4 | CommandInput + useAuditStream | LOW | ⚠️ Skipped |
| 5 | useAuditStream.ts:43-50 | MEDIUM | ✅ FIXED |
| 6 | report/[id]/page.tsx:57 | LOW | ⚠️ Skipped |
| 7 | history/page.tsx:213 | LOW | ✅ FIXED |

---

## Remaining Work (If Any)

- Bug 4: Could optionally use backend's `ws_url` instead of constructing own URL
- Bug 6: Add error toast/notification in report page fetch error handler

---

*This iteration fixed 5 of 7 bugs (all HIGH and MEDIUM severity). The remaining bugs are LOW priority UX polish items.*