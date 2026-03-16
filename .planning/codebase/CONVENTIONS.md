# Coding Conventions

**Analysis Date:** 2026-03-16

## Code Style Guidelines

- **TypeScript/React**: ESLint with Next.js (`eslint-config-next/core-web-vitals`, `typescript`), 2-space indent, Tailwind CSS, "use client" for client components
- **Python**: 4-space indent, type hints throughout, dataclasses for data, TypedDict for state, docstrings on classes/functions

## Naming Conventions

- **Files (TS/React)**: `camelCase.ts` (.tsx for components) - `useAuditStream.ts`, `TerminalPanel.tsx`
- **Components**: PascalCase - `TerminalPanel`, `PanelErrorBoundary`, `GhostPanel`
- **Hooks**: `use` prefix - `useAuditStream`, `useEventSequencer`
- **Functions**: camelCase - `connect()`, `disconnect()`
- **Python modules**: snake_case - `orchestrator.py`, `circuit_breaker.py`
- **Python classes**: PascalCase - `NIMClient`, `AuditState`, `OnionDetector`
- **Constants**: UPPER_SNAKE_CASE - `NIM_API_KEY`, `WS_BASE`

## Common Patterns

- **Barrel exports**: `index.ts` aggregates exports (e.g., `src/components/terminal/index.ts`)
- **Functional components**: React components use hooks with explicit return types
- **Error Boundaries**: Class components with `getDerivedStateFromError()` for graceful degradation
- **State Management**: Zustand store (`src/lib/store.ts`) with WebSocket refs

## Error Handling Approach

- **Python**: Try/except blocks with graceful degradation, custom exception classes (`NIMCreditExhausted`), circuit breaker pattern, module-level loggers
- **React**: Error boundaries catch rendering failures, WebSocket message parsing wrapped in try/catch, optional chaining for defensive access
- **Logging**: Python modules use `logging.getLogger("veritas.{module}")`; frontend has minimal logging (no console.log)

---

*Convention analysis: 2026-03-16*