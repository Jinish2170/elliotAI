"""
Audit routes — Start + WebSocket stream.
"""

import asyncio
import base64
import contextlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services import guards
from backend.services.audit_runner import AuditRunner, generate_audit_id
from elliot.config.settings import should_use_db_persistence
from elliot.db import get_db
from elliot.db.models import Audit, AuditFinding, AuditScreenshot, AuditStatus
from elliot.db.repositories import AuditRepository
from elliot.screenshots.storage import ScreenshotStorage

logger = logging.getLogger("elliot.routes.audit")

# Screenshot storage instance
screenshot_storage = ScreenshotStorage()

router = APIRouter(tags=["audit"])

# Dependency injection type for database sessions
DbSession = Annotated[AsyncSession, Depends(get_db)]

# In-memory store of running / completed audits
_audits: dict[str, dict] = {}


# URL validation regex pattern
_URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$',
    re.IGNORECASE
)

_VALID_TIERS = {"quick_scan", "standard_audit", "deep_forensic", "darknet_investigation"}
_VALID_VERDICT_MODES = {"simple", "expert"}


class AuditStartRequest(BaseModel):
    url: str
    tier: str = "standard_audit"
    verdict_mode: str = "expert"
    security_modules: Optional[list[str]] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v or not _URL_PATTERN.match(v):
            raise ValueError('Invalid URL format. Must be a valid HTTP/HTTPS URL.')
        return v

    @field_validator('tier')
    @classmethod
    def validate_tier(cls, v: str) -> str:
        if v not in _VALID_TIERS:
            raise ValueError(f'Invalid tier. Must be one of: {", ".join(_VALID_TIERS)}')
        return v

    @field_validator('verdict_mode')
    @classmethod
    def validate_verdict_mode(cls, v: str) -> str:
        if v not in _VALID_VERDICT_MODES:
            raise ValueError(f'Invalid verdict_mode. Must be one of: {", ".join(_VALID_VERDICT_MODES)}')
        return v


class AuditStartResponse(BaseModel):
    audit_id: str
    status: str
    ws_url: str


@router.post("/audit/start", response_model=AuditStartResponse)
async def start_audit(req: AuditStartRequest, request: Request, db: DbSession):
    """Create an audit and return the ID + WebSocket URL."""
    tiers = guards.allowed_tiers()
    if tiers and req.tier not in tiers:
        raise HTTPException(403, f"Tier '{req.tier}' is disabled on this deployment ({', '.join(sorted(tiers))})")
    if guards.block_private_targets() and await asyncio.to_thread(guards.target_is_private, req.url):
        raise HTTPException(400, "Target resolves to a private or reserved address; refusing (SSRF guard)")
    limit = guards.max_concurrent_audits()
    if limit and sum(1 for a in _audits.values() if a.get("status") == "running") >= limit:
        raise HTTPException(429, "Too many audits running; try again in a minute")
    ip = guards.client_ip(request.headers, request.client.host if request.client else "unknown")
    if not guards.rate_limiter.allow(ip):
        raise HTTPException(429, "Hourly audit limit reached for this client")

    audit_id = generate_audit_id()

    _audits[audit_id] = {
        "url": req.url,
        "tier": req.tier,
        "verdict_mode": req.verdict_mode,
        "security_modules": req.security_modules,
        "status": "queued",
        "result": None,
        "error": None,
    }

    return AuditStartResponse(
        audit_id=audit_id,
        status="queued",
        ws_url=f"/api/audit/stream/{audit_id}",
    )


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_EVENTS_DIR = _DATA_DIR / "events"
_AUDIT_ID_RE = re.compile(r"^vrts_[0-9a-f]{8}$")


def _screenshot_roots() -> list[Path]:
    from elliot.config import settings
    return [(_DATA_DIR / "screenshots").resolve(), Path(settings.EVIDENCE_DIR).resolve()]


def _save_event_log(audit_id: str, events: list[dict]) -> None:
    """Persist the event log so a finished audit replays fully after a restart
    (History links used to open an empty, all-ABORTED dashboard)."""
    if not _AUDIT_ID_RE.match(audit_id):
        return
    try:
        _EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(_EVENTS_DIR / f"{audit_id}.jsonl", "w", encoding="utf-8") as fh:
            for ev in events:
                if ev.get("type") == "screenshot":
                    ev = {k: v for k, v in ev.items() if k != "data"}  # image stays on disk
                fh.write(json.dumps(ev, default=str) + "\n")
    except Exception as e:
        logger.warning(f"[{audit_id}] could not persist event log: {e}")


def _load_event_log(audit_id: str) -> Optional[list[dict]]:
    if not _AUDIT_ID_RE.match(audit_id):
        return None
    path = _EVENTS_DIR / f"{audit_id}.jsonl"
    if not path.is_file():
        return None
    roots = _screenshot_roots()
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "screenshot" and ev.get("url"):
            img = Path(str(ev["url"])).resolve()
            # Only re-read images from our own screenshot folders.
            if img.is_file() and any(img.is_relative_to(r) for r in roots):
                ev["data"] = base64.b64encode(img.read_bytes()).decode("ascii")
        events.append(ev)
    return events


# Completed audits whose full event log (incl. screenshots) stays in memory
# for replay. Older ones fall back to replaying just the stored result.
_EVENT_LOG_KEEP = 5


def _evict_event_logs() -> None:
    done = [a for a in _audits.values() if a.get("events") is not None and a.get("status") != "running"]
    for info in done[:-_EVENT_LOG_KEEP]:
        info["events"] = None


async def _run_audit(audit_id: str, audit_info: dict) -> None:
    """Run one audit to completion, independent of any WebSocket.

    Every event is appended to audit_info["events"] and fanned out to the
    connected subscribers. A client that disconnects (page refresh, network
    blip, React StrictMode remount) only stops listening; it used to cancel
    the run, which threw away minutes of work and left the row "running".
    """
    from elliot.db import AsyncSessionLocal  # own session: the request's closes with its socket

    def publish(event: Optional[dict]) -> None:
        if event is not None and audit_info.get("events") is not None:
            audit_info["events"].append(event)
        for queue in list(audit_info["subscribers"]):
            queue.put_nowait(event)

    async with AsyncSessionLocal() as db:
        await on_audit_started(audit_id, audit_info, db)
        runner = AuditRunner(
            audit_id=audit_id,
            url=audit_info["url"],
            tier=audit_info["tier"],
            verdict_mode=audit_info["verdict_mode"],
            security_modules=audit_info.get("security_modules"),
        )

        async def send_event(data: dict):
            event_type = data.get("type")
            if event_type == "audit_result":
                audit_info["result"] = data.get("result")
            elif event_type == "audit_error":
                audit_info["error"] = data.get("error")
            elif event_type == "screenshot":
                await _handle_screenshot_event(audit_id, data, db)
            publish(data)

        try:
            await runner.run(send_event)
            if audit_info.get("result"):
                audit_info["status"] = "completed"
                await on_audit_completed(audit_id, audit_info["result"], db)
            else:
                audit_info["status"] = "error"
                await on_audit_error(audit_id, audit_info.get("error") or "Audit produced no result", db)
        except asyncio.CancelledError:
            audit_info["status"] = "error"
            raise
        except Exception as e:
            error_msg = str(e)
            if isinstance(e, TimeoutError) or "timed out" in error_msg.lower():
                error_msg = f"Audit timed out while scanning {audit_info.get('url', 'target')}. The site may be too slow or blocking automated requests."
            logger.error(f"[{audit_id}] Audit failed: {error_msg}", exc_info=True)
            audit_info["status"] = "error"
            await on_audit_error(audit_id, error_msg, db)
            publish({"type": "audit_error", "audit_id": audit_id, "error": error_msg})
        finally:
            publish(None)  # end of stream for every listener
            if audit_info.get("events"):
                await asyncio.to_thread(_save_event_log, audit_id, list(audit_info["events"]))
            _evict_event_logs()


@router.websocket("/audit/stream/{audit_id}")
async def stream_audit(ws: WebSocket, audit_id: str):
    """Stream an audit's events. The first connection starts the run; later
    connections (reloads, reconnects) get every event so far, then live ones."""
    await ws.accept()

    audit_info = _audits.get(audit_id)
    if not audit_info or (audit_info.get("status") != "queued" and audit_info.get("events") is None):
        # Not running here (finished earlier, or the server restarted):
        # replay the persisted event log so every panel fills in again.
        log = await asyncio.to_thread(_load_event_log, audit_id)
        if log:
            for event in log:
                await ws.send_json(event)
            if not any(e.get("type") == "audit_complete" for e in log):
                await ws.send_json({"type": "audit_complete", "audit_id": audit_id, "replayed": True})
            await ws.close()
            return
    if not audit_info:
        await ws.send_json({"type": "audit_error", "error": "Audit ID not found"})
        await ws.close()
        return

    if audit_info.get("task") is None and audit_info.get("status") == "queued":
        audit_info["status"] = "running"
        audit_info["events"] = []
        audit_info["subscribers"] = set()
        audit_info["task"] = asyncio.create_task(_run_audit(audit_id, audit_info))

    task = audit_info.get("task")
    events = audit_info.get("events")
    if task is None or (task.done() and events is None):
        # Finished earlier (or before a restart) and its event log is gone:
        # replay the stored result instead of re-running the audit.
        if audit_info.get("result"):
            await ws.send_json({"type": "audit_result", "audit_id": audit_id, "result": audit_info["result"]})
            await ws.send_json({"type": "audit_complete", "audit_id": audit_id, "replayed": True})
        elif audit_info.get("error"):
            await ws.send_json({"type": "audit_error", "audit_id": audit_id, "error": audit_info["error"]})
        await ws.close()
        return

    # Snapshot + subscribe with no await in between: no event can fall in the gap.
    queue: asyncio.Queue = asyncio.Queue()
    backlog = list(events or [])
    live = not task.done()
    if live:
        audit_info["subscribers"].add(queue)

    async def wait_for_disconnect():
        while (await ws.receive())["type"] != "websocket.disconnect":
            pass

    disconnect = asyncio.create_task(wait_for_disconnect())
    try:
        for event in backlog:
            await ws.send_json(event)
        while live:
            getter = asyncio.create_task(queue.get())
            done, _ = await asyncio.wait({getter, disconnect}, return_when=asyncio.FIRST_COMPLETED)
            if getter not in done:
                getter.cancel()
                break  # client left; the run carries on
            event = getter.result()
            if event is None:
                break
            await ws.send_json(event)
    except (WebSocketDisconnect, RuntimeError):
        pass
    except Exception as e:
        logger.warning(f"[{audit_id}] stream send failed: {e}")
    finally:
        disconnect.cancel()
        audit_info.get("subscribers", set()).discard(queue)
        with contextlib.suppress(Exception):
            await ws.close()


@router.get("/audit/{audit_id}/status")
async def audit_status(audit_id: str, db: DbSession):
    """Check audit status.

    Prefers the full in-memory result (url, findings, trace_summary, verdicts…)
    while this process still holds it; the DB row only stores a subset of the
    result, so a DB-rebuilt result is the fallback after a restart.
    """
    response_data = None

    info = _audits.get(audit_id)
    if info and info.get("status") == "completed" and info.get("result"):
        return {"audit_id": audit_id, "status": "completed", "url": info["url"],
                "result": info["result"], "error": info.get("error")}

    # Try database first if persistence is enabled
    if should_use_db_persistence():
        repo = AuditRepository(db)
        audit = await repo.get_by_id(audit_id)
        if audit:
            response_data = {
                "audit_id": audit.id,
                "status": audit.status.value,
                "url": audit.url,
                "result": {
                    "url": audit.url,
                    "audit_tier": audit.audit_tier,
                    "verdict_mode": audit.verdict_mode,
                    "screenshots_count": audit.screenshots_count,
                    "errors": audit.errors or [],
                    "findings": [
                        {"id": f.id, "pattern_type": f.pattern_type, "category": f.category,
                         "severity": f.severity, "confidence": f.confidence,
                         "description": f.description, "plain_english": f.plain_english}
                        for f in audit.findings
                    ],
                    "trust_score": audit.trust_score,
                    "risk_level": audit.risk_level,
                    "signal_scores": audit.signal_scores,
                    "score_breakdown": audit.score_breakdown or {},
                    "narrative": audit.narrative,
                    "site_type": audit.site_type,
                    "site_type_confidence": audit.site_type_confidence,
                    "security_results": audit.security_results,
                    "pages_scanned": audit.pages_scanned,
                    "elapsed_seconds": audit.elapsed_seconds,
                    "dark_pattern_summary": {
                        "findings": [
                            {
                                "id": f.id,
                                "pattern_type": f.pattern_type,
                                "category": f.category,
                                "severity": f.severity,
                                "confidence": f.confidence,
                                "description": f.description,
                                "plain_english": f.plain_english,
                                "screenshot_index": f.screenshot_index,
                            }
                            for f in audit.findings
                        ]
                    },
                    "screenshots": [
                        {
                            "id": s.id,
                            "url": f"/api/audit/{audit_id}/screenshot/{s.id}" if hasattr(s, 'id') else s.file_path,
                            "label": s.label,
                            "index": s.index_num,
                            "file_size": s.file_size_bytes
                        }
                        for s in getattr(audit, "screenshots", [])
                    ] if getattr(audit, "screenshots", []) else []
                } if audit.status == AuditStatus.COMPLETED else None,
                "error": audit.error_message,
                "created_at": audit.created_at.isoformat() if audit.created_at else None,
                "started_at": audit.started_at.isoformat() if audit.started_at else None,
                "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
            }

    # Fallback to in-memory store
    if not response_data:
        info = _audits.get(audit_id)
        if not info:
            raise HTTPException(status_code=404, detail="Audit not found")
        response_data = {
            "audit_id": audit_id,
            "status": info["status"],
            "url": info["url"],
            "result": info.get("result"),
            "error": info.get("error"),
        }
        
    return response_data



@router.get("/audits/history")
async def get_audit_history(
    db: DbSession,
    limit: int = Query(20, ge=1, le=100, description="Number of audits to return (1-100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status_filter: Optional[str] = Query(None, description="Filter by audit status"),
    risk_level_filter: Optional[str] = Query(None, description="Filter by risk level")
):
    """
    Get paginated audit history with optional filters.

    Returns list of audits sorted by created_at descending (newest first).
    Supports filtering by status and risk_level.
    """
    repo = AuditRepository(db)

    # Build query with filters
    query = select(Audit).order_by(Audit.created_at.desc())

    if status_filter:
        try:
            status = AuditStatus(status_filter)
            query = query.where(Audit.status == status)
        except ValueError:
            pass  # Invalid status, ignore filter

    if risk_level_filter:
        query = query.where(Audit.risk_level == risk_level_filter)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    audits = result.scalars().all()

    # Convert to response format
    return {
        "audits": [
            {
                "audit_id": a.id,
                "url": a.url,
                "status": a.status.value,
                "audit_tier": a.audit_tier,
                "verdict_mode": a.verdict_mode,
                "trust_score": a.trust_score,
                "risk_level": a.risk_level,
                "signal_scores": a.signal_scores,
                "site_type": a.site_type,
                "site_type_confidence": a.site_type_confidence,
                "pages_scanned": a.pages_scanned,
                "screenshots_count": a.screenshots_count,
                "elapsed_seconds": a.elapsed_seconds,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "started_at": a.started_at.isoformat() if a.started_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in audits
        ],
        "count": len(audits),
        "limit": limit,
        "offset": offset,
    }


class AuditCompareRequest(BaseModel):
    audit_ids: list[str]


@router.post("/audits/compare")
async def compare_audits(
    request: AuditCompareRequest,
    db: DbSession,
):
    """
    Compare multiple audits to detect changes over time.

    Accepts a list of audit_ids and returns:
    - Full audit data for each ID
    - Trust score delta between consecutive audits
    - Risk level changes
    - Pattern changes (in findings counts)
    """
    audit_ids = request.audit_ids

    if not audit_ids:
        raise HTTPException(status_code=400, detail="audit_ids list is required")

    if len(audit_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 audit IDs required for comparison")

    repo = AuditRepository(db)

    # Fetch all audits with their findings
    audits_data = []
    for audit_id in audit_ids:
        audit = await repo.get_by_id(audit_id)
        if not audit:
            continue  # Skip missing audits

        # Count findings by severity
        findings_summary = {
            "total": len(audit.findings),
            "critical": sum(1 for f in audit.findings if f.severity == "critical"),
            "high": sum(1 for f in audit.findings if f.severity == "high"),
            "medium": sum(1 for f in audit.findings if f.severity == "medium"),
            "low": sum(1 for f in audit.findings if f.severity == "low"),
        }

        # Format audit summary
        audits_data.append({
            "audit_id": audit.id,
            "url": audit.url,
            "status": audit.status.value,
            "trust_score": audit.trust_score,
            "risk_level": audit.risk_level,
            "site_type": audit.site_type,
            "created_at": audit.created_at.isoformat() if audit.created_at else None,
            "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
            "findings_summary": findings_summary,
            "screenshots_count": audit.screenshots_count,
        })

    if not audits_data:
        raise HTTPException(status_code=404, detail="No valid audits found")

    # Sort by created_at (earliest first for delta calculation)
    audits_data.sort(key=lambda a: a["created_at"] or "")

    # Calculate deltas
    trust_score_deltas = []
    for i in range(1, len(audits_data)):
        prev_score = audits_data[i-1]["trust_score"] or 0
        curr_score = audits_data[i]["trust_score"] or 0
        delta = curr_score - prev_score
        trust_score_deltas.append({
            "from_audit_id": audits_data[i-1]["audit_id"],
            "to_audit_id": audits_data[i]["audit_id"],
            "delta": delta,
            "percentage_change": (delta / prev_score * 100) if prev_score != 0 else None,
        })

    # Detect risk level changes
    risk_level_changes = []
    for i in range(1, len(audits_data)):
        prev_risk = audits_data[i-1]["risk_level"]
        curr_risk = audits_data[i]["risk_level"]
        if prev_risk != curr_risk:
            risk_level_changes.append({
                "from_audit_id": audits_data[i-1]["audit_id"],
                "to_audit_id": audits_data[i]["audit_id"],
                "from": prev_risk or "unknown",
                "to": curr_risk or "unknown",
            })

    return {
        "audits": audits_data,
        "trust_score_deltas": trust_score_deltas,
        "risk_level_changes": risk_level_changes,
    }


# Database event handlers (Plan 05-04 implementation)


async def on_audit_started(audit_id: str, data: dict, db: AsyncSession) -> None:
    """Handle audit started event - save to database.

    Creates a new Audit record with QUEUED status when audit is started.
    Writes to database only if USE_DB_PERSISTENCE flag is enabled.

    Args:
        audit_id: Unique audit identifier
        data: Audit metadata (url, tier, verdict_mode, security_modules)
        db: Database session
    """
    if not should_use_db_persistence():
        return

    repo = AuditRepository(db)

    # Try to fetch existing audit first to handle React Strict Mode reconnects
    existing = await repo.get_by_id(audit_id)
    if existing:
        existing.status = AuditStatus.RUNNING
        await repo.update(existing)
        logger.info(f"[{audit_id}] Audit re-connected and updated in database")
        return

    # Create audit record
    audit = Audit(
        id=audit_id,
        url=data.get("url", ""),
        status=AuditStatus.RUNNING,  # Already running by the time this is called
        audit_tier=data.get("tier", "standard_audit"),
        verdict_mode=data.get("verdict_mode", "expert"),
    )

    try:
        await repo.create(audit)
    except IntegrityError:
        # Lost the race with a concurrent connection (React StrictMode opens
        # the stream twice; both see no row, both INSERT). The row exists now.
        await db.rollback()
        await repo.update_status(audit_id, AuditStatus.RUNNING)
        logger.info(f"[{audit_id}] Audit row created concurrently; marked running")
        return
    logger.info(f"[{audit_id}] Audit persisted to database")


async def on_audit_completed(audit_id: str, result: dict, db: AsyncSession) -> None:
    """Handle audit completed event - save result to database.

    Updates audit record with final results including trust score,
    findings, screenshots, and other metadata.

    Args:
        audit_id: Unique audit identifier
        result: Final audit result from runner
        db: Database session
    """
    if not should_use_db_persistence():
        return

    repo = AuditRepository(db)

    # Fetch existing audit
    audit = await repo.get_by_id(audit_id)
    if not audit:
        logger.warning(f"[{audit_id}] Audit not found in database for completion")
        return

    # Update audit fields from result
    if result:
        audit.trust_score = result.get("trust_score")
        audit.risk_level = result.get("risk_level")
        audit.narrative = result.get("narrative")
        audit.signal_scores = result.get("signal_scores", {})
        audit.score_breakdown = result.get("score_breakdown") or None
        audit.site_type = result.get("site_type")
        audit.site_type_confidence = result.get("site_type_confidence")
        audit.security_results = result.get("security_results", {})
        audit.pages_scanned = result.get("pages_scanned", 0)
        audit.elapsed_seconds = result.get("elapsed_seconds", 0)
        audit.screenshots_count = result.get("screenshots_count", 0)
        audit.status = AuditStatus.COMPLETED
        audit.completed_at = result.get("completed_at") or datetime.utcnow()

        # Add findings from result
        dark_pattern_summary = result.get("dark_pattern_summary") or {}
        findings_data = dark_pattern_summary.get("findings", []) if isinstance(dark_pattern_summary, dict) else []
        for finding_data in findings_data:
            if not isinstance(finding_data, dict):
                continue
            finding = AuditFinding(
                audit_id=audit_id,
                pattern_type=finding_data.get("pattern_type", "unknown"),
                category=finding_data.get("category", "unknown"),
                severity=finding_data.get("severity", "medium"),
                confidence=finding_data.get("confidence", 0.5),
                description=finding_data.get("description", ""),
                plain_english=finding_data.get("plain_english", ""),
                screenshot_index=finding_data.get("screenshot_index", -1),
            )
            audit.findings.append(finding)

    await repo.update(audit)
    logger.info(f"[{audit_id}] Audit result persisted to database")


async def on_audit_error(audit_id: str, error: str, db: AsyncSession) -> None:
    """Handle audit error event - save error to database.

    Updates audit status to ERROR and stores error message.

    Args:
        audit_id: Unique audit identifier
        error: Error message or exception string
        db: Database session
    """
    if not should_use_db_persistence():
        return

    repo = AuditRepository(db)

    # Try to fetch existing audit - create if not found
    audit = await repo.get_by_id(audit_id)
    if audit:
        audit.status = AuditStatus.ERROR
        audit.error_message = error
        await repo.update(audit)
    else:
        # Create audit record if it doesn't exist (e.g., error during start)
        audit = Audit(
            id=audit_id,
            url="",
            status=AuditStatus.ERROR,
            error_message=error,
        )
        await repo.create(audit)

    logger.info(f"[{audit_id}] Audit error persisted to database")


async def _handle_screenshot_event(audit_id: str, event: dict, db: AsyncSession) -> None:
    """Handle screenshot event - save to filesystem and database.

    Args:
        audit_id: Unique audit identifier
        event: Screenshot event dict with data, index, label
        db: Database session
    """
    if not should_use_db_persistence():
        return

    # Extract screenshot data
    base64_data = event.get("data")
    index = event.get("index", 0)
    label = event.get("label", f"screenshot_{index}")

    if not base64_data:
        return

    try:
        # Save to filesystem
        file_path, file_size = await screenshot_storage.save(
            audit_id=audit_id,
            index=index,
            label=label,
            base64_data=base64_data,
        )

        # Create database record
        repo = AuditRepository(db)
        audit = await repo.get_by_id(audit_id)
        if audit:
            screenshot = AuditScreenshot(
                audit_id=audit_id,
                file_path=file_path,
                label=label,
                index_num=index,
                file_size_bytes=file_size,
            )
            audit.screenshots.append(screenshot)
            await repo.update(audit)
            logger.debug(f"[{audit_id}] Screenshot {index} saved to {file_path}")
    except Exception as e:
        logger.error(f"[{audit_id}] Failed to save screenshot: {e}", exc_info=True)
