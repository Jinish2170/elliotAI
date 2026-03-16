# Coding Conventions
**Analysis Date:** 2026-03-16

## Naming Patterns

### Files

**TypeScript/React:**
- Components: PascalCase (e.g., `TerminalPanel.tsx`, `KnowledgeGraph.tsx`, `AgentStatus.tsx`)
- Utility files: camelCase (e.g., `utils.ts`, `store.ts`, `types.ts`)
- Hooks: camelCase with `use` prefix (e.g., `useAuditStream.ts`, `useEventSequencer.ts`)
- Config files: camelCase (e.g., `agent_personalities.ts`, `agents.ts`)
- Pages: kebab-case with `page.tsx` or `layout.tsx` suffix

**Python:**
- Modules: snake_case (e.g., `audit_runner.py`, `test_audit_persistence.py`)
- Classes: PascalCase (e.g., `AuditRunner`, `AuditRepository`)
- Functions: snake_case (e.g., `generate_audit_id()`, `determine_ipc_mode()`)
- Constants: SCREAMING_SNAKE_CASE (e.g., `IPC_MODE_QUEUE`, `IPC_MODE_STDOUT`)

### Functions

**TypeScript:**
- Use camelCase for functions (e.g., `useCallback`, `handleEvent`, `connect`)
- Export named functions primarily; default exports for pages
- Async functions marked with `async` keyword

**Python:**
- Use snake_case for all functions
- Methods on classes: first parameter is always `self` or `cls`
- Use type hints (e.g., `def _find_venv_python() -> str`)

### Variables

**TypeScript:**
- Use camelCase (e.g., `auditId`, `wsRef`, `store`)
- Use `const` for immutable references, `let` for mutable
- Interface/Type names: PascalCase
- Prop names: camelCase

**Python:**
- Use snake_case (e.g., `audit_id`, `test_engine`, `db_session`)
- Private variables: prefix with underscore (e.g., `_repo_cache`, `_mgr`)
- Constants: SCREAMING_SNAKE_CASE

### Types

**TypeScript:**
- Use TypeScript interfaces for shapes (e.g., `interface TerminalPanelProps`)
- Use `type` for unions, aliases (e.g., `type Phase = "init" | "scout" | "security"`)
- Export types explicitly: `export interface Finding { ... }`, `export type PhaseStatus = ...`

**Python:**
- Use type hints throughout
- Pydantic models for request/response validation (e.g., `class AuditStartRequest(BaseModel)`)
- SQLAlchemy models for database entities

## Code Style

### Formatting

**TypeScript/React:**
- Tool: Not explicitly configured, relies on Next.js defaults
- Uses Tailwind CSS for styling with custom CSS variables
- File paths use `@/` alias (defined in `tsconfig.json` paths)
- No enforcedPrettier config detected

**Python:**
- Tool: Not explicitly configured, relies on PEP8
- Django-style docstring formatting
- Indentation: 4 spaces
- Max line length: Not explicitly enforced

### Linting

**TypeScript/React:**
- Tool: ESLint with Next.js configuration
- Config file: `frontend/eslint.config.mjs`
- Extends: `eslint-config-next/core-web-vitals` and `eslint-config-next/typescript`
- Rules: Managed by Next.js ESLint config; custom overrides in config (e.g., `eslint-disable-line react-hooks/exhaustive-deps` in `useAuditStream.ts`)

**Python:**
- Tool: Not explicitly configured
- Note: `pytest.ini` exists with custom markers (`integration`, `slow`)

## Import Organization

### TypeScript/React

**Order:**
1. React/Next.js imports
2. Path alias imports (`@/components/...`, `@/lib/...`, `@/hooks/...`)
3. External library imports (e.g., `from "react"`, `from "next/navigation"`)
4. Relative imports if any

**Example from `page.tsx`:**
```typescript
"use client";

import { CommandInput } from "@/components/landing/CommandInput";
import { AgentStatus } from "@/components/landing/AgentStatus";
import { RecentAudits } from "@/components/landing/RecentAudits";
import { ParticleField } from "@/components/ambient/ParticleField";
```

**Path Aliases:**
- `@/*` maps to `./src/*` (as defined in `tsconfig.json`)
- Used for all internal modules

### Python

**Order:**
1. Standard library imports (alphabetical within group)
2. Third-party imports (alphabetical)
3. Local/application imports
4. Relative imports

**Example from `audit.py`:**
```python
import asyncio
import json
import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.audit_runner import AuditRunner, generate_audit_id
from veritas.config.settings import should_use_db_persistence
from veritas.db import get_db
from veritas.db.models import Audit, AuditFinding, AuditScreenshot, AuditStatus
from veritas.db.repositories import AuditRepository
from veritas.screenshots.storage import ScreenshotStorage
```

## Error Handling

### TypeScript/React

**Pattern: Try-catch with fallback**
```typescript
ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    store.handleEvent(data);
  } catch {
    // ignore malformed messages
  }
};
```

**Pattern: Error Boundaries**
```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class PanelErrorBoundary extends React.Component<{ children: React.ReactNode }, ErrorBoundaryState> {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  // ...
}
```

**Pattern: Status checking**
```typescript
if (store.status !== "complete" && store.status !== "error") {
  if (event.code !== 1000) {
    store.setStatus("error");
  }
}
```

### Python

**Pattern: Try-except with logging**
```python
async def _read_queue_and_stream(self, send: Callable):
  if self.progress_queue is None:
    return
  while True:
    try:
      event = await asyncio.to_thread(self.progress_queue.get, timeout=1.0)
      # process event...
    except queue.Empty:
      continue
    except asyncio.CancelledError:
      break
    except Exception as exc:
      logger.error("[%s] queue read error: %s", self.audit_id, exc)
```

**Pattern: Fallback/Recovery**
```python
try:
  req = urllib.request.Request(self.url, method="HEAD", headers={'User-Agent': 'Veritas/(+https://github.com)'})
  await asyncio.to_thread(urllib.request.urlopen, req, timeout=5.0)
except URLError as e:
  # Revert to standard GET in case HEAD is blocked
  try:
    # fallback logic...
  except Exception as e2:
    # error handling...
```

**Pattern: Immediate error propagation**
```python
await send({"type": "phase_error", "phase": "scout", "error": err_msg})
# Critical: Emit audit_error immediately so Frontend Terminals abort
await send({"type": "audit_error", "audit_id": self.audit_id, "error": err_msg})
return
```

## Logging

**TypeScript/React:**
- No explicit logging framework detected
- Console logging likely used during development
- Uses Zustand store for state management (see `frontend/src/lib/store.ts`)
- UI state management centralizes operational data

**Python:**
- Framework: `logging` module with named loggers
- Pattern: Logger per module (`logger = logging.getLogger("veritas.audit_runner")`)
- Usage:
  ```python
  logger = logging.getLogger("veritas.routes.audit")
  logger.error("[%s] queue read error: %s", self.audit_id, exc)
  ```

## Comments

### When to Comment

**TypeScript:**
- JSDoc for functions/components (limited usage detected)
- Inline comments for tricky logic (e.g., `"// ignore malformed messages"`)
- Eslint-disable comments for edge cases (`// eslint-disable-line react-hooks/exhaustive-deps`)
- CSS custom properties documented in comments

**Python:**
- Module-level docstrings (e.g., in `audit.py`: `"""Audit routes — Start + WebSocket stream."""`)
- Function-level docstrings (e.g., in `main.py`: `"""Startup / shutdown lifecycle."""`)
- Inline comments for complex logic (e.g., `"# Critical: Emit audit_error immediately"`)
- Configuration comments (e.g., `"# Load .env from veritas directory"`)

### JSDoc/TSDoc

**Usage:** Minimal. Only basic documentation detected.

**Example (from `types.ts`):**
```typescript
/* ========================================
 Veritas — TypeScript Type Definitions
 ======================================== */
```

### Python Docstrings

**Format:** Google-style or simple descriptions

**Example (from `main.py`):**
```python
"""Veritas Backend — FastAPI Application

Provides REST + WebSocket API for the Next.js frontend.
Routes:
 GET /api/health → Health check
 POST /api/audit/start → Start a new audit, returns audit_id
 WS /api/audit/stream/{id} → Stream real-time audit events
"""
```

## Function Design

### Size

**TypeScript:**
- Components typically 30-100 lines
- Hooks: Single responsibility (e.g., focused on WebSocket management)
- Utility functions: Small, composable (e.g., `cn()` in `utils.ts`)

**Python:**
- Methods typically <50 lines
- Larger functions separated into smaller methods
- Class `AuditRunner` is large (~400+ lines) but logically organized

### Parameters

**TypeScript:**
```typescript
export function TerminalPanel({
  title,
  status,
  children,
  className = ""
}: TerminalPanelProps)
```

**Python:**
```python
def __init__(self, audit_id: str, url: str, tier: str,
             verdict_mode: str = "expert",
             security_modules: Optional[list[str]] = None):
```

### Return Values

**TypeScript:**
- Functional components return JSX
- Hooks return state/getters
- Return types explicit in function signatures

**Python:**
- Async functions use `async def`
- Return type hints used throughout
- FastAPI route handlers use `response_model`

## Module Design

### Exports

**TypeScript:**
```typescript
export function TerminalPanel(...) { ... }
export class PanelErrorBoundary extends React.Component { ... }
export function GhostPanel(...)
```

**Python:**
```python
from backend.routes.audit import router as audit_router
router = APIRouter(tags=["audit"])
```

**Pattern:** Re-export with aliases to avoid conflicts

### Barrel Files

**TypeScript:**
- `components/terminal/index.ts` exists for re-exports
- Not actively used across codebase (direct imports preferred)

**Python:**
- `__init__.py` files mark packages but minimal re-exports
- Direct imports from modules preferred

### Dependency Injection

**Python (FastAPI):**
```python
DbSession = Annotated[AsyncSession, Depends(get_db)]

@router.post("/audit/start", response_model=AuditStartResponse)
async def start_audit(req: AuditStartRequest, db: DbSession):
```

**Usage:** Database sessions, repositories injected via FastAPI dependency system

### Environment Configuration

**TypeScript:**
- Environment variables via `process.env` (e.g., `NEXT_PUBLIC_WS_URL`)
- Configuration files in `frontend/src/config/` (e.g., `agent_personalities.ts`)

**Python:**
- `.env` files loaded via `python-dotenv`
- Settings from `veritas.config.settings`
- File: `backend/.env`

---

*Convention analysis: 2026-03-16*