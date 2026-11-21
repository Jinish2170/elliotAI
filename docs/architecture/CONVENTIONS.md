# Coding Conventions
**Analysis Date:** 2026-05-14

## Naming Patterns

**Files:** Use `snake_case.py` for all Python modules — `scout.py`, `circuit_breaker.py`, `audit_runner.py`, `onion_detector.py`. Group related modules into packages with `__init__.py` (`elliot/agents/`, `elliot/core/`, `elliot/core/nodes/`, `backend/routes/`). Test files are prefixed `test_` (`test_onion_detector.py`, `test_audit_route_contract.py`). Frontend uses TypeScript with the Next.js convention (`eslint.config.mjs`).

**Functions:** `snake_case` for all functions and methods. Private/internal methods are prefixed with a single underscore — `_safe_navigate`, `_create_stealth_context`, `_extract_metadata`, `_handle_screenshot_event`. Async functions are plain `async def` with no naming suffix. Pydantic validators use the `validate_*` prefix (`validate_url`, `validate_tier`).

**Variables:** `snake_case` for locals and instance attributes (`audit_id`, `nav_time`, `scroll_result`). Module-level constants are `UPPER_SNAKE_CASE`, and module-private constants get a leading underscore — `_DESKTOP_USER_AGENTS`, `_CAPTCHA_CONTENT_INDICATORS`, `_STEALTH_SCRIPT`, `_URL_PATTERN`, `_VALID_TIERS`. Private instance attributes use a leading underscore (`self._browser`, `self._evidence_dir`, `self._ioc_detector`).

**Types:** `PascalCase` for classes, dataclasses, Pydantic models, and Enums — `StealthScout`, `ScoutResult`, `PageMetadata`, `CircuitBreakerConfig`, `AuditStartRequest`, `CircuitState`, `MarketplaceType`. Enums subclass `str, Enum` so values serialize cleanly (`class CircuitState(str, Enum)`). `TypedDict` is used for LangGraph state (`AuditState`).

## Code Style

**Formatting:** No autoformatter is configured for Python (no `black`, `ruff`, or `pyproject.toml` present). Code follows 4-space indentation, PEP 8 by hand. Heavy use of banner comments to section files: `# ===...===` blocks with a centered title (see `elliot/agents/scout.py`, `elliot/core/circuit_breaker.py`). Module docstrings are mandatory and describe purpose, capabilities, and provenance. Keep this style for new files. Frontend is linted/formatted via ESLint 9 (`frontend/eslint.config.mjs`) using `eslint-config-next` (core-web-vitals + typescript), 2-space indent.

**Linting:** Python has **no linter config** — no `.flake8`, `ruff.toml`, `mypy.ini`, or `setup.cfg`. Type hints are used pervasively but not enforced by a checker. Frontend: ESLint 9 via `npm run lint` (`"lint": "eslint"` in `frontend/package.json`), extending Next.js core-web-vitals and TypeScript rulesets.

## Import Organization

**Order:** Three-group ordering — stdlib first, then third-party, then first-party `elliot.*` / `backend.*`, separated by blank lines (see `backend/routes/audit.py` lines 5-22, `elliot/agents/judge.py` lines 20-36). Type-only imports are isolated inside `TYPE_CHECKING` blocks to break circular imports (`elliot/agents/scout.py` lines 32-33). Optional dependencies are wrapped in `try/except ImportError` with an availability flag — `_IOC_AVAILABLE`, `DUAL_VERDICT_AVAILABLE`, `CONSENSUS_AVAILABLE` — and a `logger.warning` on failure (`elliot/agents/scout.py` lines 46-65, `elliot/agents/judge.py` lines 40-64). Heavy/rarely-used imports are done lazily inside functions (`from elliot.analysis.dom_analyzer import DOMAnalyzer` inside `investigate()`).

**Path Aliases:** No package install — agent modules run `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` at the top of the file to make `elliot.*` importable (`elliot/agents/scout.py` line 38, `elliot/agents/judge.py` line 27). Prefer absolute imports `from elliot.config import settings`; some test code uses the shortened `from core.orchestrator import ...` form after the path insert, but new code should use the fully-qualified `elliot.*` form.

## Error Handling

**Patterns:** Defensive, non-fatal-by-default. Optional sub-steps are wrapped in `try/except Exception as e:` and log a warning/debug with the suffix `(non-critical)` then continue — e.g. DOM analysis, form validation, IOC detection, scrolling in `elliot/agents/scout.py`. Public agent methods catch top-level exceptions and return a structured result object with `status="ERROR"` and `error_message=str(e)` rather than raising (`StealthScout.investigate` lines 770-781). FastAPI routes raise `HTTPException(status_code=..., detail=...)` for client errors (`backend/routes/audit.py` lines 247, 343-346). Use `logger.error(..., exc_info=True)` when capturing unexpected exceptions. Config objects validate in `__post_init__` and raise `ValueError` with a descriptive message (`CircuitBreakerConfig.__post_init__`). Pydantic `@field_validator` raises `ValueError` for invalid request input. Custom exception classes exist for domain failures (e.g. `NIMCreditExhausted`).

## Logging

**Framework:** Python stdlib `logging`. Every module creates a namespaced logger at import time: `logger = logging.getLogger("elliot.scout")`, `logging.getLogger("elliot.routes.audit")`, `logging.getLogger("elliot.core.circuit_breaker")`. Use the `elliot.<area>` / `elliot.routes.<name>` naming scheme for new modules. Frontend has minimal logging (no `console.log`).

**Patterns:** f-strings for interpolation (`logger.info(f"StealthScout: TOR SOCKS5 proxy enabled ({tor_host}:{tor_port})")`). Level discipline: `debug` for fine-grained progress, `info` for lifecycle milestones, `warning` for recoverable/optional failures, `error` (with `exc_info=True`) for unexpected exceptions. Route handlers prefix log lines with the audit id: `logger.info(f"[{audit_id}] Audit persisted to database")`.

## Comments

**When to Comment:** Comment the *why*, not the *what*. Inline comments tag provenance (`# From RAGv5 scrapers.py pattern`), plan references (`# (Plan 13-01)`, `# (Plan 05-04)`), and rationale for non-obvious choices (`# Truncate to 500KB`, `# Slight randomization to avoid viewport fingerprinting`). Banner comments (`# ===...===`) divide files into labeled sections. Avoid restating code.

**JSDoc/TSDoc (or docstrings):** Docstrings are required and prevalent. Every module opens with a triple-quoted docstring describing purpose, capabilities, and (often) which legacy code the patterns were merged from. Classes have docstrings, frequently with a `Usage:` example block (`StealthScout`). Public methods use a structured docstring with `Args:` / `Returns:` sections (`StealthScout.investigate`, `_navigate_with_timeout`, `on_audit_started`). Dataclass docstrings sometimes include an `Attributes:` block (`CircuitBreakerConfig`). Use Google-style `Args:`/`Returns:` sections for new public functions.

## Function Design

**Size:** Mostly small, single-responsibility helpers (`_safe_title`, `_apply_stealth`, `_take_screenshot`). The major exception is orchestration methods like `StealthScout.investigate` (~450 lines) which sequence many steps; new code should prefer extracting steps into private `_helper` methods as the rest of the file does.

**Parameters:** Type-hinted. Optional params have defaults and use `Optional[X]` (`evidence_dir: Optional[Path] = None`). Forward-referenced types use string literals (`progress_emitter: Optional["ProgressEmitter"]`). Public agent entrypoints take many keyword args with sensible defaults (`viewport: str = "desktop"`, `enable_scrolling: bool = True`, `max_sections: int = 5`); callers pass them by keyword.

**Return Values:** Prefer returning structured dataclasses (`ScoutResult`, `PageMetadata`, `JudgeDecision`, `TrustScoreResult`) over loose tuples/dicts. Helpers that may fail return `Optional[...]` and `None` on failure (`_take_screenshot -> Optional[str]`). FastAPI route handlers return a plain `dict` or a Pydantic `response_model`. Error paths return the same result type with an error status, never `None` unexpectedly.

## Module Design

**Exports:** No `__all__` declarations — public surface is implied by non-underscore names. Modules are organized as: docstring → imports → optional-import guards → module constants → dataclasses/enums → classes/functions. Keep underscore-prefixing for anything internal.

**Barrel Files (or __init__.py usage):** Python `__init__.py` files exist for every package but are intentionally thin — most contain only a package docstring and **no re-exports** (`elliot/agents/__init__.py`, `elliot/tests/integration/__init__.py`). Consumers import directly from the concrete module (`from elliot.agents.scout import StealthScout`), not from the package. Do not turn `__init__.py` into a barrel file. (Note: the frontend *does* use barrel `index.ts` files, e.g. `src/components/terminal/index.ts` — that convention is TypeScript-only and does not apply to Python.)

---
*Convention analysis: 2026-05-14*
