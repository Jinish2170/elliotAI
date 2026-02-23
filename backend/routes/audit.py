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
from veritas.db import get_db
from veritas.db.models import Audit, AuditStatus
from veritas.db.repositories import AuditRepository

logger = logging.getLogger("veritas.routes.audit")

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
    """Check audit status."""
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


# Database event handlers (to be implemented in Plan 05-04)
async def on_audit_started(audit_id: str, data: dict, db: AsyncSession) -> None:
    """Handle audit started event - save to database."""
    # TODO: Save to database in Plan 04
    pass


async def on_audit_completed(audit_id: str, result: dict, db: AsyncSession) -> None:
    """Handle audit completed event - save result to database."""
    # TODO: Save to database in Plan 04
    pass


async def on_audit_error(audit_id: str, error: str, db: AsyncSession) -> None:
    """Handle audit error event - save error to database."""
    # TODO: Save to database in Plan 04
    pass
