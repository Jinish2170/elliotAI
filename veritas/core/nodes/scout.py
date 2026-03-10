"""
Veritas — Scout Node

Browser reconnaissance node for the audit graph.
Moved from veritas.core.orchestrator as part of Phase 13-04 refactoring.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from veritas.agents.scout import ScoutResult, StealthScout
from veritas.config import settings

if TYPE_CHECKING:
    from veritas.core.orchestrator import AuditState

logger = logging.getLogger("veritas.orchestrator")


async def scout_node(state: AuditState) -> dict:
    """
    SCOUT node: Navigate the next URL and capture evidence.
    Processes one URL per invocation from pending_urls.
    """
    pending = state.get("pending_urls", [])
    investigated = state.get("investigated_urls", [])
    scout_results = state.get("scout_results", [])
    scout_failures = state.get("scout_failures", 0)
    errors = state.get("errors", [])

    if not pending:
        logger.warning("Scout node invoked with no pending URLs")
        return {"status": "running", "errors": errors + ["Scout: no pending URLs"]}

    url = pending[0]
    remaining = pending[1:]

    logger.info(f"Scout investigating: {url}")

    try:
        # Read tier config for TOR routing
        audit_tier = state.get("audit_tier", "standard_audit")
        tier_config = settings.AUDIT_TIERS.get(audit_tier, settings.AUDIT_TIERS["standard_audit"])
        use_tor = bool(tier_config.get("enable_tor", False))

        async with StealthScout(use_tor=use_tor) as scout:
            # First URL gets full temporal investigation
            if len(investigated) == 0:
                result = await scout.investigate(url)
            else:
                result = await scout.navigate_subpage(url)

        # Serialize ScoutResult for state storage
        result_dict = {
            "url": result.url,
            "status": result.status,
            "screenshots": result.screenshots,
            "screenshot_timestamps": result.screenshot_timestamps,
            "screenshot_labels": result.screenshot_labels,
            "page_title": result.page_title,
            "page_metadata": result.page_metadata,
            "links": result.links,
            "forms_detected": result.forms_detected,
            "captcha_detected": result.captcha_detected,
            "error_message": result.error_message,
            "navigation_time_ms": result.navigation_time_ms,
            "viewport_used": result.viewport_used,
            "user_agent_used": result.user_agent_used,
            "trust_modifier": result.trust_modifier,
            "trust_notes": result.trust_notes,
            # V2 fields
            "site_type": getattr(result, 'site_type', ''),
            "site_type_confidence": getattr(result, 'site_type_confidence', 0.0),
            "dom_analysis": getattr(result, 'dom_analysis', {}),
            "form_validation": getattr(result, 'form_validation', {}),
            # Phase 12 darknet fields
            "ioc_detected": getattr(result, 'ioc_detected', False),
            "ioc_indicators": getattr(result, 'ioc_indicators', []),
            "onion_detected": getattr(result, 'onion_detected', False),
            "onion_addresses": getattr(result, 'onion_addresses', []),
            # Phase 13-01: Real page content and response headers
            "page_content": getattr(result, 'page_content', ''),
            "response_headers": getattr(result, 'response_headers', {}),
        }

        new_scout_results = scout_results + [result_dict]
        new_investigated = investigated + [url]

        # Extract site_type from primary (first) scout result
        update = {
            "scout_results": new_scout_results,
            "pending_urls": remaining,
            "investigated_urls": new_investigated,
        }
        if len(scout_results) == 0:  # First result: set site_type
            update["site_type"] = getattr(result, 'site_type', '')
            update["site_type_confidence"] = getattr(result, 'site_type_confidence', 0.0)

        if result.status == "SUCCESS":
            logger.info(f"Scout SUCCESS: {url} | screenshots={len(result.screenshots)}")
            update["scout_failures"] = 0
            update["iteration"] = state.get("iteration", 0)
            return update
        elif result.status == "CAPTCHA_BLOCKED":
            logger.info(f"Scout CAPTCHA_BLOCKED: {url}")
            update["scout_failures"] = 0
            return update
        else:
            logger.warning(f"Scout failed: {url} | status={result.status} | error={result.error_message}")
            update["scout_failures"] = scout_failures + 1
            update["errors"] = errors + [f"Scout failed on {url}: {result.error_message}"]
            return update

    except Exception as e:
        logger.error(f"Scout exception on {url}: {e}", exc_info=True)
        return {
            "pending_urls": remaining,
            "investigated_urls": investigated + [url],
            "scout_failures": scout_failures + 1,
            "errors": errors + [f"Scout exception: {str(e)}"],
        }
