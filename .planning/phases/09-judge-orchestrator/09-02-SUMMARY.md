---
id: 09-02
phase: 9
wave: 1
autonomous: true

title: "Smart Orchestrator with Adaptive Timeouts and Circuit Breakers"
one_liner: "TimeoutManager, CircuitBreaker, FallbackManager, ComplexityAnalyzer integrated into Orchestrator for adaptive timeouts, graceful degradation, and estimated completion time calculation"

subsystem: "Core Orchestrator"
tags: ["timeout", "circuit-breaker", "degradation", "complexity", "adaptive"]

# Dependency Graph (requires/provides/affects)
requires:
  - "Phase 7: Scout Agent complexity metrics (DOM depth, script count, lazy-load)"
  - "Existing orchestrator.py base orchestration logic"

provides:
  - "Adaptive timeout calculation based on complexity scores"
  - "Circuit breaker pattern with CLOSED/OPEN/HALF_OPEN states"
  - "Graceful degradation with DegradedResult and quality penalties"
  - "Historical learning for execution time estimation"
  - "Estimated completion time calculation for remaining agents"

affects:
  - "veritas/core/orchestrator.py (main integration point)"
  - "All agent executions (vision, graph, security, judge, osint)"

# Tech Stack
tech_stack_added:
  - "ComplexityAnalyzer: Extracts 15 metrics from agent results"
  - "TimeoutManager: Adaptive timeout calculation with historical learning"
  - "CircuitBreaker: State machine with exponential backoff"
  - "FallbackManager: Per-agent circuit breakers with graceful degradation"

tech_stack_patterns:
  - "Circuit breaker pattern with state transitions"
  - "Weighted sum complexity scoring (DOM 35%, Script 25%, Lazy 20%, Iframe 10%, Load 10%)"
  - "Rolling average historical learning (deque maxlen=10)"
  - "Quality penalty accumulation (0.2 fallback, 0.5 timeout, 0.7 total failure)"
  - "Strategy enum (FAST/STANDARD/CONSERVATIVE/ADAPTIVE)"

# Key Files Created/Modified
key_files_created:
  - "veritas/core/timeout_manager.py (509 lines) - TimeoutStrategy, ComplexityMetrics, TimeoutConfig, TimeoutManager"
  - "veritas/core/circuit_breaker.py (477 lines) - CircuitState, CircuitBreaker, ResultWithFallback"
  - "veritas/core/degradation.py (435 lines) - FallbackMode, DegradedResult, FallbackManager"
  - "veritas/core/complexity_analyzer.py (499 lines) - ComplexityAnalyzer with 15 metric extractors"

key_files_modified:
  - "veritas/core/orchestrator.py (+389/-14 lines) - Integrated all 4 new components"

# Decisions
decisions:
  - "09-02-01: Use complexity thresholds (0.30, 0.60) for timeout strategy selection (FAST/STANDARD/CONSERVATIVE)"
  - "09-02-02: Historical learning uses rolling average (deque maxlen=10) with 20% buffer"
  - "09-02-03: Circuit breaker with exponential backoff (OPEN -> HALF_OPEN -> CLOSED)"
  - "09-02-04: Per-agent default configs: vision 60s, graph 30s, security 45s, osint 90s"
  - "09-02-05: Quality penalty applied to final trust score (0.2 fallback, 0.5 timeout, 0.7 total failure)"
  - "09-02-06: Backward compatibility maintained via opt-in flags (use_adaptive_timeout, use_circuit_breaker)"

# Metrics
execution_metrics:
  duration_minutes: "7"
  tasks_completed: 5
  files_created: 4
  files_modified: 1
  lines_added: 2310
  lines_deleted: 14

# Deviations
deviations: "None - plan executed exactly as written."
---

# Phase 9 Plan 2: Smart Orchestrator Summary

## Overview

Successfully implemented smart orchestrator with adaptive timeout management, circuit breaker pattern, and graceful degradation. The orchestrator now calculates timeouts based on page complexity, protects against cascading failures with circuit breakers, and provides partial results even when agents fail ("show must go on" policy).

## Implementation Details

### 1. TimeoutManager (veritas/core/timeout_manager.py)

**Components Created:**
- `TimeoutStrategy` enum (FAST, STANDARD, CONSERVATIVE, ADAPTIVE)
- `ComplexityMetrics` dataclass with 15 fields (URL, site_type, DOM metrics, performance metrics)
- `TimeoutConfig` dataclass with 6 agent-specific timeouts (scout, vision, security, graph, judge, osint)
- `TIMEOUT_STRATEGIES` dict with 3 predefined configs
- `TimeoutManager` class with adaptive timeout calculation

**Key Features:**
- `calculate_complexity_score()`: Weighted sum scoring (DOM 35%, Script 25%, Lazy load 20%, Iframe 10%, Load time 10%)
- `calculate_timeout_config()`: Selects strategy based on complexity score (FAST < 0.30, STANDARD 0.30-0.60, CONSERVATIVE > 0.60)
- `_apply_historical_adjustment()`: Historical averages with 20% buffer
- `record_execution()`: Tracks execution times in deque(maxlen=10)
- `get_estimated_remaining_time()`: Estimates time for remaining agents

### 2. CircuitBreaker (veritas/core/circuit_breaker.py)

**Components Created:**
- `CircuitState` enum (CLOSED, OPEN, HALF_OPEN)
- `CircuitBreakerConfig` dataclass (failure_threshold, timeout_ms, half_open_max_calls, success_threshold)
- `ResultWithFallback` dataclass (value, is_fallback, fallback_reason, primary_error)
- `CircuitBreaker` class with state machine

**Key Features:**
- `call()`: Executes primary with timeout and circuit protection
- Circuit trips OPEN after failure_threshold failures
- Circuit enters HALF_OPEN after timeout_ms elapsed
- Circuit closes after success_threshold successes in HALF_OPEN
- `get_state()`: Returns current circuit state
- `reset()`: Manually closes circuit to CLOSED

### 3. FallbackManager (veritas/core/degradation.py)

**Components Created:**
- `FallbackMode` enum (NONE, SIMPLIFIED, CACHED, PARTIAL, ALTERNATIVE)
- `DegradedResult` dataclass (result_data, degraded_agent, fallback_mode, missing_data, quality_penalty, error_message)
- `FallbackManager` class with per-agent circuit breakers

**Key Features:**
- `register_fallback()`: Registers fallback function with CircuitBreaker
- `execute_with_fallback()`: Executes primary with circuit protection
- Quality penalty tracking (0.2 fallback, 0.5 timeout, 0.7 total failure)
- Default configs per agent (vision 60s, graph 30s, security 45s, osint 90s)
- "Show must go on" policy: DegradedResult always contains result_data dict (never None)

### 4. ComplexityAnalyzer (veritas/core/complexity_analyzer.py)

**Components Created:**
- `ComplexityAnalyzer` class with 15 metric extractors

**Key Features:**
- Extracts DOM metrics from ScoutResult (dom_depth, dom_node_count, script_count, stylesheet_count, inline_style_count, iframes_count)
- Detects lazy loading (has_lazy_load, lazy_load_threshold)
- Extracts performance metrics (initial_load_time_ms, network_idle_time_ms, dom_content_loaded_time_ms, total_load_time_ms)
- Extracts screenshot_count, viewport_changes
- Handles missing fields gracefully with defaults
- `get_timeout_suggestion()`: Returns FAST/STANDARD/CONSERVATIVE based on complexity thresholds

### 5. Orchestrator Refactoring (veritas/core/orchestrator.py)

**Changes Made:**
- Added imports for all 4 new components
- Added `use_adaptive_timeout` and `use_circuit_breaker` parameters to `__init__` (backward compatible)
- Conditionally initialize TimeoutManager, FallbackManager, ComplexityAnalyzer
- Implemented `_register_fallback_functions()` for 5 agent types
- Implemented `_execute_agent_smart()` wrapper for timeout + circuit breaker execution
- Added complexity analysis after Scout completes (once per audit)
- Added timeout calculation and application to each agent execution
- Added historical recording for learning
- Added quality penalty tracking and accumulation
- Added quality penalty application to final trust score
- Added estimated remaining time calculation and emission

**Agent Execution Integration:**
- Vision: Uses adaptive timeout, circuit breaker with fallback
- Graph: Uses adaptive timeout, circuit breaker with fallback
- Security: Uses adaptive timeout, circuit breaker with fallback
- Judge: Uses adaptive timeout, circuit breaker with fallback
- All agents track execution time for historical learning

## Requirements Coverage

### ORCH-01: Advanced Time Management
- [x] Adaptive timeout calculation based on complexity scores
- [x] Timeout strategy selection (FAST/STANDARD/CONSERVATIVE)
- [x] Agent-specific timeouts (scout, vision, security, graph, judge, osint)
- [x] Historical learning for execution time estimation
- [x] Estimated completion time for remaining agents

### ORCH-02: Comprehensive Error Handling
- [x] Circuit breaker pattern with CLOSED/OPEN/HALF_OPEN states
- [x] Automatic fallback when circuit trips or primary fails
- [x] Graceful degradation with DegradedResult
- [x] "Show must go on" policy: partial results even when agents fail
- [x] Per-agent circuit breaker configurations

### ORCH-03: Complexity-Aware Orchestration
- [x] ComplexityMetrics with 15 factors (DOM, scripts, performance, etc.)
- [x] Complexity score calculation with weighted factors
- [x] Threshold-based timeout selection (0.30, 0.60)
- [x] Analysis simplification via DegradedResult (SIMPLIFIED fallback mode)
- [x] Scout agent complexity collection integrated with orchestration

## Verification

### Files Created
- [x] veritas/core/timeout_manager.py (509 lines)
- [x] veritas/core/circuit_breaker.py (477 lines)
- [x] veritas/core/degradation.py (435 lines)
- [x] veritas/core/complexity_analyzer.py (499 lines)

### Files Modified
- [x] veritas/core/orchestrator.py (+389/-14 lines)

### All Tests Passed
- [x] TimeoutManager calculates complexity scores 0.0-1.0 from DOM metrics
- [x] Adaptive timeout selection: FAST (<0.30), STANDARD (0.30-0.60), CONSERVATIVE (>0.60)
- [x] TimeoutConfig has 6 agent-specific timeouts (scout, vision, security, graph, judge, osint)
- [x] CircuitBreaker implements CLOSED/OPEN/HALF_OPEN state machine
- [x] Circuit trips OPEN after failure_threshold failures
- [x] Circuit enters HALF_OPEN after timeout_ms elapsed
- [x] Circuit closes after success_threshold successes in HALF_OPEN
- [x] FallbackManager provides DegradedResult on agent failure
- [x] "Show must go on" policy: DegradedResult always contains usable data
- [x] Quality penalty applied: 0.2 (fallback), 0.5 (no fallback), 0.7 (total failure)
- [x] ComplexityAnalyzer extracts 15 complexity metrics from Scout/Vision/Security results
- [x] Orchestrator integrates adaptive timeouts when use_adaptive_timeout=True
- [x] Orchestrator integrates circuit breakers when use_circuit_breaker=True
- [x] Historical learning tracks execution times for estimation
- [x] Estimated completion time calculated and emitted via progress events
- [x] Backward compatible when both flags=False

## Extension Points
- New complexity factors can be added to ComplexityMetrics for more sophisticated scoring
- Fallback strategies can be customized per agent type (currently using simplified/empty)
- Timeout strategies can be overridden per site type (currently uses ADAPTIVE strategy)
- Historical learning can persist to database for cross-session learning (currently in-memory)
- Quality penalty thresholds can be tuned for different risk profiles

## Deviations from Plan

None - plan executed exactly as written.

## Commits

1. `6ec3e36` feat(09-02): create TimeoutManager with adaptive timeouts
2. `2bedcda` feat(09-02): create CircuitBreaker with state machine
3. `a27cd9e` feat(09-02): create FallbackManager with graceful degradation
4. `5c0cb02` feat(09-02): create ComplexityAnalyzer for metrics collection
5. `ee88a66` feat(09-02): refactor orchestrator to integrate adaptive timeouts and circuit breakers
