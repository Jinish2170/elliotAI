# Phase 1: IPC Communication Stabilization - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

## Phase Boundary

Replace fragile stdout marker parsing (`##PROGRESS:`) with multiprocessing.Queue for structured subprocess communication between backend and Veritas subprocess. Maintain fallback capability for instant rollback during gradual rollout.

## Implementation Decisions

### Migration strategy

- **Dual-mode rollout**: Run stdout and Queue modes in parallel initially, use percentage-based gradual rollout controlled by environment variables
- **Default behavior**: Queue mode is default when nothing specified (safer to use Queue mode with 10% staged rollout)
- **Validation approach**: Lightweight validation - run 10-20 audits in each mode to verify Queue mode works before advancing staging
- **Staging percentages**: 10% → 25% → 50% → 75% → 100% (timed stages, approximately 1 week per stage)
- **Validation success criteria**: Exact match between stdout and Queue mode audit results (all events, final state, screenshots)
- **Fallback behavior**: Auto fallback to stdout mode if Queue mode fails during audit
- **Fallback removal**: Remove stdout fallback after 100% Queue stage and confidence reached
- **Rollback configuration**: Environment variables only (no config file), using separate vars for different settings

### CLI flags

- **Primary flag**: `--use-queue-ipc` to enable Queue mode explicitly
- **Fallback flag**: `--use-stdout` to explicitly choose stdout/fallback mode
- **Validation flag**: `--validate-ipc` to run both modes and compare results for testing
- **Flag priority**: CLI flags override environment variables (highest priority)
- **Conflict handling**: `--use-queue-ipc` takes precedence over `--use-stdout` if both specified
- **No explicit flag**: Queue mode is default (with 10% rollout rate)
- **Debugging**: Use general `-vv` or `--verbose` flag for IPC debugging (no dedicated `--debug-ipc` flag)

### Environment variables

- **Rollout rate**: `QUEUE_IPC_ROLLOUT` (float 0.0-1.0, e.g., 0.1 for 10%)
- **Mode selection**: `QUEUE_IPC_MODE` (string: "queue", "stdout", or "fallback")
- **Separate variables**: Use distinct environment variables for different controls (not combined)
- **CLI override**: CLI flags always override environment variables when both specified

### Error handling

- **Queue creation failure**: Auto fallback to stdout mode immediately with error log
- **Queue communication failure**: Auto fallback to stdout mode for current audit
- **Queue timeout**: Fallback to stdout mode and continue audit (not fail the audit)
- **Logging levels**: Selective - use ERROR for critical failures, WARNING for fallback events, INFO for mode switching
- **Metrics tracking**: Track all metrics - success rate, mode usage percentage, performance metrics, failure counts

### Staging and rollback

- **Timed stages**: Advance staging percentages based on time (1 week per stage), not audit count
- **Stage validation**: Each stage requires lightweight validation before advancing
- **Exact match**: Validation compares audit results between modes for exact equality
- **Monitoring**: Detailed metrics collection during rollout - mode choice, success/failure rates, performance metrics
- **Fallback removal**: Remove stdout fallback code after 100% Queue stage completed and validated
- **Rollback path**: Keep fallback available through all stages until 100% Queue adoption

### Claude's Discretion

- Exact timing for stage advancement (within roughly 1 week guideline)
- Specific metric storage format and dashboard visualization
- Log message wording and formatting for different failure types
- Performance metric thresholds and alerting thresholds
- Configuration of Queue size limits, backpressure handling, timeouts (unless discussed)

## Specific Ideas

- "I want to be able to gradually rollout Queue mode without risking production audits"
- "Fallback should be automatic - don't fail the audit just because Queue mode has issues"
- "Need validation that Queue mode produces exactly the same results as stdout mode"
- "Monitor the rollout percentage and success rate to know when to advance stages"

## Deferred Ideas

- Queue size limits, backpressure handling - defer to implementation decisions or discuss in Phase 3 (LangGraph) if infrastructure patterns emerge
- Advanced monitoring dashboards - basic metrics tracking is sufficient for v1.0
- Automated stage advancement based on metrics - manual time-based stages are fine

---

*Phase: 01-ipc-communication-stabilization*
*Context gathered: 2026-02-20*
