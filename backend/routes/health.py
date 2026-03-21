"""Health check endpoint with dependency verification."""

import logging
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

logger = logging.getLogger("veritas.routes.health")

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Comprehensive health check endpoint.

    Returns service status and checks for critical dependencies:
    - Database connectivity
    - Configuration status
    """
    health: dict[str, Any] = {
        "status": "ok",
        "service": "veritas-api",
        "version": "2.0.0",
    }

    # Check database connectivity if persistence is enabled
    try:
        from veritas.config.settings import should_use_db_persistence
        if should_use_db_persistence():
            from veritas.db import get_db
            async for db in get_db():
                await db.execute(text("SELECT 1"))
                health["database"] = "connected"
                break
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        health["database"] = "disconnected"
        health["status"] = "degraded"

    # Check critical configuration
    try:
        from veritas.config.settings import NIM_API_KEY
        health["nim_configured"] = bool(NIM_API_KEY)

        if not NIM_API_KEY:
            health["status"] = "degraded"
            health["warnings"] = ["NVIDIA NIM API key not configured"]
    except Exception as e:
        logger.warning(f"Config check failed: {e}")
        health["nim_configured"] = False
        health["status"] = "degraded"

    return health