# QA-01 Runtime Test Plan

## Objective
Run real audit, trace ALL data from backend through WebSocket to frontend, identify missing/invalid mappings.

## Tier Definitions
| Tier | Description | Features |
|------|-------------|----------|
| standard | Basic URL analysis | Scout + Vision + basic scoring |
| premium | Advanced security | Standard + Security modules |
| enterprise | Full audit suite | Premium + OSINT + Darknet |
| darknet | Darknet monitoring | Enterprise + Tor + marketplace |

## Data Flow
```
Backend (58+ event types)
    ↓ WebSocket with sequence numbers
Frontend Store (processSingleEvent)
    ↓ State updates
UI Components (VerdictPanel, KnowledgeGraph, etc.)
```

## Phase 1: Backend Audit Test
1. Start backend server
2. Run audit on test URL (example.com)
3. Capture ALL WebSocket events
4. Log data structure of each event

## Phase 2: Frontend Data Tracing
1. Check each event type in store.ts
2. Map to UI component usage
3. Identify missing handlers

## Phase 3: Data-UI Mapping
| Event Type | Store Field | UI Component | Status |
|------------|-------------|--------------|--------|
| phase_start | currentPhase | AgentProcState | ? |
| log_entry | logs | SysLogStream | ? |
| screenshot | screenshots | ScreenshotGrid | ? |
| finding | darkPatternFindings | FindingPanel | ? |
| knowledge_graph | graphData | KnowledgeGraph | ? |
| verdict_technical | result | VerdictPanel | ? |
| verdict_nontechnical | result | VerdictPanel | ? |
| audit_result | result | FinalReport | ? |
| ... | ... | ... | ? |

## Phase 4: Issue Resolution
Fix each identified mapping issue

## Success Criteria
- All backend events properly consumed by frontend
- All UI components receive correct data
- No undefined/null crashes in UI