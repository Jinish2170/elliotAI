"""
Audit routes — Start + WebSocket stream.
"""

import asyncio
import json
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from services.audit_runner import AuditRunner, generate_audit_id
from veritas.config.settings import should_use_db_persistence
from veritas.db import get_db
from veritas.db.models import Audit, AuditFinding, AuditScreenshot, AuditStatus
from veritas.db.repositories import AuditRepository
from veritas.screenshots.storage import ScreenshotStorage

logger = logging.getLogger("veritas.routes.audit")

# Screenshot storage instance
screenshot_storage = ScreenshotStorage()

# Lazy-initialized repository (per-request via DbSession)
_repo_cache: dict[str, AuditRepository] = {}

router = APIRouter(tags=["audit"])

# Dependency injection type for database sessions
DbSession = Annotated[AsyncSession, Depends(get_db)]

# In-memory store of running / completed audits
_audits: dict[str, dict] = {}


class AuditStartRequest(BaseModel):
    url: str
    tier: str = "standard_audit"
    verdict_mode: str = "expert"
    security_modules: Optional[list[str]] = None


class AuditStartResponse(BaseModel):
    audit_id: str
    status: str
    ws_url: str


@router.post("/audit/start", response_model=AuditStartResponse)
async def start_audit(req: AuditStartRequest, db: DbSession):
    """Create an audit and return the ID + WebSocket URL."""
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


@router.websocket("/audit/stream/{audit_id}")
async def stream_audit(ws: WebSocket, audit_id: str, db: DbSession):
    """
    WebSocket endpoint that runs the audit and streams events.
    The audit starts when the client connects.
    """
    await ws.accept()

    audit_info = _audits.get(audit_id)
    if not audit_info:
        await ws.send_json({"type": "audit_error", "error": "Audit ID not found"})
        await ws.close()
        return

    audit_info["status"] = "running"
    # Save to database when audit starts (implementation in Plan 05-04)
    await on_audit_started(audit_id, audit_info, db)

    runner = AuditRunner(
        audit_id=audit_id,
        url=audit_info["url"],
        tier=audit_info["tier"],
        verdict_mode=audit_info["verdict_mode"],
        security_modules=audit_info.get("security_modules"),
    )

    async def send_event(data: dict):
        """Send a JSON event to the WebSocket client."""
        event_type = data.get("type")
        if event_type == "audit_result":
            audit_info["result"] = data.get("result")
        elif event_type == "audit_error":
            audit_info["error"] = data.get("error")
        elif event_type == "screenshot":
            # Handle screenshot persistence (Plan 05-04)
            await _handle_screenshot_event(audit_id, data, db)

        try:
            await ws.send_json(data)
        except Exception as e:
            logger.warning(f"[{audit_id}] Failed to send WS event: {e}")

    try:
        await runner.run(send_event)
        audit_info["status"] = "completed" if audit_info.get("result") else "error"
        if audit_info["status"] == "completed":
            # Save result to database when audit completes (implementation in Plan 05-04)
            await on_audit_completed(audit_id, audit_info.get("result"), db)
    except WebSocketDisconnect:
        logger.info(f"[{audit_id}] Client disconnected")
        audit_info["status"] = "disconnected"
    except Exception as e:
        logger.error(f"[{audit_id}] Audit failed: {e}", exc_info=True)
        audit_info["status"] = "error"
        # Save error to database when audit fails (implementation in Plan 05-04)
        await on_audit_error(audit_id, str(e), db)
        try:
            await ws.send_json({"type": "audit_error", "error": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@router.get("/audit/{audit_id}/status")
async def audit_status(audit_id: str, db: DbSession):
    """Check audit status. Reads from database first if persistence enabled."""
    # Try database first if persistence is enabled
    if should_use_db_persistence():
        repo = AuditRepository(db)
        audit = await repo.get_by_id(audit_id)
        if audit:
            return {
                "audit_id": audit.id,
                "status": audit.status.value,
                "url": audit.url,
                "result": {
                    "trust_score": audit.trust_score,
                    "risk_level": audit.risk_level,
                    "signal_scores": audit.signal_scores,
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
                    }
                } if audit.status == AuditStatus.COMPLETED else None,
                "error": audit.error_message,
                "created_at": audit.created_at.isoformat() if audit.created_at else None,
                "started_at": audit.started_at.isoformat() if audit.started_at else None,
                "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
            }

    # Fallback to in-memory store
    info = _audits.get(audit_id)
    if not info:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {
        "audit_id": audit_id,
        "status": info["status"],
        "url": info["url"],
        "result": info.get("result"),
        "error": info.get("error"),
    }


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

    # Create audit record
    audit = Audit(
        id=audit_id,
        url=data.get("url", ""),
        status=AuditStatus.RUNNING,  # Already running by the time this is called
        audit_tier=data.get("tier", "standard_audit"),
        verdict_mode=data.get("verdict_mode", "expert"),
    )

    await repo.create(audit)
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
        audit.site_type = result.get("site_type")
        audit.site_type_confidence = result.get("site_type_confidence")
        audit.security_results = result.get("security_results", {})
        audit.pages_scanned = result.get("pages_scanned", 0)
        audit.elapsed_seconds = result.get("elapsed_seconds", 0)
        audit.status = AuditStatus.COMPLETED
        audit.completed_at = result.get("completed_at")  # Will be set by default if None

        # Add findings from result
        findings_data = result.get("dark_pattern_summary", {}).get("findings", [])
        for finding_data in findings_data:
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
