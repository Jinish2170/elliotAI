# Ralph Loop: Iteration 2 - Deep Data Pipeline Issues

## Bugs Found in Current Iteration

---

### BUG 8: MitreGrid - Null tactic causes crash
**File:** `frontend/src/components/terminal/MitreGrid.tsx`
**Line:** 24
**Issue:** Calling `.replace()` on potentially undefined `t.tactic`
```tsx
{t.tactic.replace("x-mitre-tactic-", "").replace(/-/g, " ")}
```
**Severity:** HIGH - Will crash if tactics missing
**Fix:** Add optional chaining

---

### BUG 9: DarknetOsintGrid - Missing null safety
**File:** `frontend/src/components/terminal/DarknetOsintGrid.tsx`
**Lines:** 44, 45, 62
**Issue:**
- Line 44: `t.de_anon_risk.toUpperCase()` - no null check
- Line 45: `t.gateway_domains[0]` - could be empty array causing undefined
- Line 62: `m.marketplace_type` needs optional chaining

**Severity:** MEDIUM - Potential runtime errors

---

### BUG 10: ScoutImagery - Missing image data validation
**File:** `frontend/src/components/terminal/ScoutImagery.tsx`
**Line:** 35
**Issue:** Accessing `currentImg.data || currentImg.url` but both could be undefined
```tsx
<Image src={`data:image/jpeg;base64,${currentImg.data || currentImg.url}`} ... />
```

**Severity:** HIGH - Broken image display

---

### BUG 11: Report page - No error feedback
**File:** `frontend/src/app/report/[id]/page.tsx`
**Lines:** 57-58
**Issue:** Silent error handling
```tsx
catch {
  // silently handle
}
```

**Severity:** LOW - UX issue

---

### BUG 12: KnowledgeGraph - Potential infinite loop or NaN
**File:** `frontend/src/components/terminal/KnowledgeGraph.tsx`
**Line:** 105
**Issue:** `distSq > 0 && distSq < 8000` - if distSq is extremely close to 0, dividing causes huge force

**Severity:** MEDIUM - Could cause nodes to fly off screen

---

### BUG 13: History page - Missing status validation
**File:** `frontend/src/app/history/page.tsx`
**Lines:** 145-149
**Issue:** Navigates to `/report/` or `/audit/` without checking if status is actually valid for that route

**Severity:** LOW - Incorrect routing edge case

---

## Summary - Iteration 2

| Bug | Severity | File | Component |
|-----|----------|------|-----------|
| 8 | HIGH | MitreGrid.tsx:24 | Null crash |
| 9 | MEDIUM | DarknetOsintGrid.tsx:44,45,62 | Missing null safety |
| 10 | HIGH | ScoutImagery.tsx:35 | Missing validation |
| 11 | LOW | report/page.tsx | UX |
| 12 | MEDIUM | KnowledgeGraph.tsx:105 | Edge case |
| 13 | LOW | history/page.tsx:145-149 | Edge case |

## Total: 13 bugs found (6 new this iteration)