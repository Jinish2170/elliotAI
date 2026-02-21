# Phase 3: LangGraph State Machine Investigation - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

## Phase Boundary

Investigate root cause of Python 3.14 CancelledError blocking LangGraph ainvoke() execution. Enable proper LangGraph StateGraph execution with debugging, visualization, and checkpointing. If root cause cannot be fixed, document sequential execution with detailed fallback strategy.

## Implementation Decisions

### Investigation approach
- **Comprehensive code analysis**: Full orchestrator code and LangGraph integration, not simplified modules
- **Full audit test**: Complete audit with mocked NIMClient to observe actual behavior and event flow
- **Minimal reproduction test**: Isolated test case to isolate CancelledError root cause
- **Evidence-based conclusions**: Use behavioral differences as key evidence of root cause

### Root cause analysis scope
- **All three components**: Analyze LangGraph internals, NIMClient interaction, and subprocess orchestrator comprehensively
- **LangGraph internals**: StateGraph lifecycle, async event handling, ainvoke() implementation
- **NIMClient interaction**: How NIM async operations interact with LangGraph state machine
- **Subprocess orchestrator**: How subprocess isolation affects LangGraph execution on Windows + Python 3.14

### Priority determination
- **Claude discretion**: Let planner decide investigation priority based on findings and code analysis
- **Evidence-driven**: Focus on areas where behavioral differences are most informative

### Root cause threshold
- **Behavioral differences**: Full audit showing different behaviors between proper LangGraph and sequential execution
- **Observable effects**: Event order, state transitions, error propagation differences
- **Evidence strength**: Clear, reproducible differences that indicate root cause location

### Resolution approach
- **Fix if possible**: Primary goal is to identify and fix root cause enabling proper LangGraph ainvoke()
- **Sequential with detailed fallback**: If root cause cannot be fixed (e.g., Python version incompatibility), document sequential execution with detailed logging and mode tracking
- **Version pin consideration**: Evaluate if Python 3.12/3.13 pin resolves issue
- **Hybrid execution**: Test LangGraph for simple cases, sequential for complex flows (if appropriate)

### Success criteria
- Isolated reproduction test documents CancelledError root cause
- Resolution documented: fix, version pin, hybrid execution, or sequential with tracking
- Sequential execution fallback maintained for instant rollback
- LangGraph reproduction test covers Python 3.14 async behavior
- Behavioral evidence clearly shows where CancelledError originates

### Claude's Discretion
- Exact test design for minimal reproduction case
- Which Python versions to test for version pin hypothesis (3.12, 3.13, 3.15)
- Detailed fallback logging granularity (event-level, state-level, step-level)
- Hybrid execution boundaries (which parts use LangGraph vs sequential)
- Sequential execution tracking implementation details

## Specific Ideas

- "Use behavioral differences as the primary evidence - where does execution diverge?"
- "Don't just run code - observe event flow, state transitions, async task lifecycle"
- "Full audit test with mocked NIMClient shows real execution path without external dependencies"
- "Isolated test should strip away everything but minimal StateGraph with async operations"

## Deferred Ideas

- Advanced LangGraph features (conditional branching, loops) - defer to v2 milestone
- Real-time debugging UI - focus on root cause investigation first
- Performance optimization of sequential execution - out of scope for this phase
- Alternative orchestration frameworks - LangGraph is locked technology choice

---

*Phase: 03-langgraph-state-machine-investigation*
*Context gathered: 2026-02-21*
