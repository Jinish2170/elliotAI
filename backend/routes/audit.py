"""
Audit routes — Start + WebSocket stream.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.audit_runner import AuditRunner, generate_audit_id

logger = logging.getLogger("veritas.routes.audit")

router = APIRouter(tags=["audit"])

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
async def start_audit(req: AuditStartRequest):
    """Create an audit and return the ID + WebSocket URL."""
    audit_id = generate_audit_id()

    _audits[audit_id] = {
        "url": req.url,
        "tier": req.tier,
        "verdict_mode": req.verdict_mode,
        "security_modules": req.security_modules,
        "status": "queued",
    }

    return AuditStartResponse(
        audit_id=audit_id,
        status="queued",
        ws_url=f"/api/audit/stream/{audit_id}",
    )


@router.websocket("/audit/stream/{audit_id}")
async def stream_audit(ws: WebSocket, audit_id: str):
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

    runner = AuditRunner(
        audit_id=audit_id,
        url=audit_info["url"],
        tier=audit_info["tier"],
        verdict_mode=audit_info["verdict_mode"],
        security_modules=audit_info.get("security_modules"),
    )

    async def send_event(data: dict):
        """Send a JSON event to the WebSocket client."""
        try:
            await ws.send_json(data)
        except Exception as e:
            logger.warning(f"[{audit_id}] Failed to send WS event: {e}")

    try:
        await runner.run(send_event)
        audit_info["status"] = "completed"
    except WebSocketDisconnect:
        logger.info(f"[{audit_id}] Client disconnected")
        audit_info["status"] = "disconnected"
    except Exception as e:
        logger.error(f"[{audit_id}] Audit failed: {e}", exc_info=True)
        audit_info["status"] = "error"
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
async def audit_status(audit_id: str):
    """Check audit status."""
    info = _audits.get(audit_id)
    if not info:
        return {"error": "Audit not found"}, 404
    return {"audit_id": audit_id, "status": info["status"], "url": info["url"]}
