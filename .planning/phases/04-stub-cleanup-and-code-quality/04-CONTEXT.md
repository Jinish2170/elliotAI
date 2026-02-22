# Phase 4: Stub Cleanup & Code Quality - Context

**Gathered:** 2026-02-22
**Status:** Ready for planning

## Phase Boundary

Replace all empty return stubs in the codebase with `NotImplementedError` or proper implementations to eliminate silent failures. This affects evidence_store.py, judge.py, dom_analyzer.py, and dark_patterns.py at specific line numbers.

---

## Implementation Decisions

### Error handling approach
- Use context-specific error types, not just `NotImplementedError` everywhere
- Common error types to use: `NotImplementedError`, `ValueError` (for bad input), `RuntimeError` (for state issues)
- Error messages should be informative with context + reason (e.g., "validate(): cannot run without initialization")
- Message format varies by method based on complexity — no rigid template, but all messages must be informative

### Migration considerations
- Apply stub changes atomically (all at once, not gradual)
- Before making changes, search for existing callers of stub methods using grep/ruff
- If existing callers are found, update those callers first before modifying the stub
- If callers expect specific return values from stubs, research whether the method can be fully implemented now (turn stub into real implementation if feasible)

### Claude's Discretion
- Exact error message wording per method
- Which specific error type applies to each stub context
- Callers search methodology (grep patterns, ruff checks, etc.)
- How to present the caller analysis results before proceeding

---

## Specific Ideas

No specific requirements — open to standard approaches for error handling and code quality improvements.

---

## Deferred Ideas

None — discussion stayed within phase scope.

---

*Phase: 04-stub-cleanup-and-code-quality*
*Context gathered: 2026-02-22*
