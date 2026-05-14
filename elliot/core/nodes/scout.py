"""
Elliot — Scout Node

Browser reconnaissance node for the audit graph.
Moved from elliot.core.orchestrator as part of Phase 13-04 refactoring.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from elliot.agents.scout import ScoutResult, StealthScout
from elliot.config import settings

if TYPE_CHECKING:
    from elliot.core.orchestrator import AuditState

logger = logging.getLogger("elliot.orchestrator")

# Pages most likely to carry trust-relevant evidence (entity claims, policies,
# dark patterns). Used to rank internal links for first-pass prefetch.
_PREFETCH_PRIORITY_PATTERNS = (
    "/about", "/contact", "/terms", "/privacy", "/pricing",
    "/refund", "/cancel", "/team", "/legal", "/faq",
)


def _serialize_scout_result(result: ScoutResult) -> dict:
    """Serialize a ScoutResult into the plain-dict form stored in AuditState."""
    return {
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
        "site_type": getattr(result, "site_type", ""),
        "site_type_confidence": getattr(result, "site_type_confidence", 0.0),
        "dom_analysis": getattr(result, "dom_analysis", {}),
        "form_validation": getattr(result, "form_validation", {}),
        # Phase 12 darknet fields
        "ioc_detected": getattr(result, "ioc_detected", False),
        "ioc_indicators": getattr(result, "ioc_indicators", []),
        "onion_detected": getattr(result, "onion_detected", False),
        "onion_addresses": getattr(result, "onion_addresses", []),
        # Phase 13-01: Real page content and response headers
        "page_content": getattr(result, "page_content", ""),
        "response_headers": getattr(result, "response_headers", {}),
        # Phase 17: Scroll & section screenshot metadata
        "scroll_result": getattr(result, "scroll_result", {}),
    }


def _select_prefetch_urls(base_url: str, primary_result: ScoutResult, limit: int) -> list[str]:
    """Pick up to `limit` priority internal links from the primary page, so the
    first Vision/Graph pass has multi-page evidence without the Judge looping."""
    if limit <= 0:
        return []
    metadata = primary_result.page_metadata or {}
    raw_links = metadata.get("internal_links") or []
    if not isinstance(raw_links, list):
        return []

    base_host = urlparse(base_url).netloc
    seen: set[str] = {base_url.rstrip("/")}
    priority: list[str] = []
    other: list[str] = []
    for link in raw_links:
        if not isinstance(link, str) or not link:
            continue
        absolute = urljoin(base_url, link)
        # Stay on the same host — never prefetch off-domain.
        if urlparse(absolute).netloc != base_host:
            continue
        key = absolute.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        if any(p in absolute.lower() for p in _PREFETCH_PRIORITY_PATTERNS):
            priority.append(absolute)
        else:
            other.append(absolute)

    # Priority pages first; backfill with other on-domain links if needed.
    return (priority + other)[:limit]


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

        # Adaptive section capture budget:
        # reserve baseline scout screenshots (t0, t-delay, fullpage) and allocate the
        # remaining screenshot budget across pages left in this tier.
        max_screenshots = int(tier_config.get("screenshots", 20) or 20)
        tier_pages = int(state.get("max_pages", tier_config.get("pages", 1)) or 1)
        pages_left = max(1, tier_pages - len(investigated))
        captured_so_far = sum(len((sr or {}).get("screenshots", [])) for sr in scout_results if isinstance(sr, dict))
        remaining_screenshot_budget = max(3, max_screenshots - captured_so_far)
        per_page_budget = max(3, remaining_screenshot_budget // pages_left)
        baseline_per_page = 3
        max_sections = max(0, per_page_budget - baseline_per_page)

        prefetch_results: list[ScoutResult] = []
        async with StealthScout(use_tor=use_tor) as scout:
            # First URL gets full temporal investigation
            if len(investigated) == 0:
                result = await scout.investigate(
                    url, progress_emitter=state.get("_progress_emitter"), max_sections=max_sections
                )
                # Eagerly fetch a few priority internal links on the first pass so
                # Vision and Graph have multi-page evidence before the first Judge
                # call — instead of the Judge looping just to gather it.
                if result.status == "SUCCESS":
                    prefetch_urls = _select_prefetch_urls(
                        url, result, settings.SCOUT_PREFETCH_LINKS
                    )
                    for sub_url in prefetch_urls:
                        try:
                            sub_result = await scout.navigate_subpage(
                                sub_url,
                                progress_emitter=state.get("_progress_emitter"),
                                max_sections=min(max_sections, 2),
                            )
                            prefetch_results.append(sub_result)
                            logger.info(
                                f"Scout prefetched: {sub_url} | status={sub_result.status}"
                            )
                        except Exception as sub_e:
                            # Prefetch is best-effort — never fail the audit over it.
                            logger.warning(f"Scout prefetch failed for {sub_url}: {sub_e}")
            else:
                result = await scout.navigate_subpage(
                    url, progress_emitter=state.get("_progress_emitter"), max_sections=max_sections
                )

        # Serialize primary + any prefetched results for state storage
        result_dict = _serialize_scout_result(result)
        prefetch_dicts = [_serialize_scout_result(r) for r in prefetch_results]
        prefetched_urls = [r.url for r in prefetch_results]

        new_scout_results = scout_results + [result_dict] + prefetch_dicts
        new_investigated = investigated + [url] + prefetched_urls

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
            logger.info(
                f"Scout SUCCESS: {url} | screenshots={len(result.screenshots)}"
                + (f" | prefetched {len(prefetch_dicts)} priority pages" if prefetch_dicts else "")
            )
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
