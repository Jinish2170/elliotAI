"""
Veritas — Graph Node

Entity verification and knowledge graph node for the audit graph.
Moved from veritas.core.orchestrator as part of Phase 13-04 refactoring.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from veritas.agents.graph_investigator import GraphInvestigator, GraphResult
from veritas.config import settings
from veritas.core.nim_client import NIMClient

if TYPE_CHECKING:
    from veritas.core.orchestrator import AuditState

logger = logging.getLogger("veritas.orchestrator")


async def graph_node(state: AuditState) -> dict:
    """
    GRAPH node: Run entity verification and build knowledge graph.
    """
    scout_results = state.get("scout_results", [])
    errors = state.get("errors", [])
    url = state.get("url", "")

    if not scout_results:
        return {"errors": errors + ["Graph: no scout results"]}

    # Gather metadata from the primary scout result
    primary = scout_results[0]
    metadata = primary.get("page_metadata", {})

    # Gather page text from all scout results (titles + descriptions)
    page_texts = []
    for sr in scout_results:
        if sr.get("page_title"):
            page_texts.append(sr["page_title"])
        meta = sr.get("page_metadata", {})
        if meta.get("description"):
            page_texts.append(meta["description"])
    page_text = "\n".join(page_texts)

    # External links
    external_links = primary.get("links", [])

    # Tier-aware OSINT depth
    audit_tier = state.get("audit_tier", "standard_audit")
    tier_config = settings.AUDIT_TIERS.get(audit_tier, settings.AUDIT_TIERS["standard_audit"])

    logger.info(f"Graph investigating {url} | text_length={len(page_text)} | tier={audit_tier}")

    try:
        nim = NIMClient()
        agent = GraphInvestigator(nim_client=nim)
        graph_timeout_s = tier_config.get("graph_timeout_s", max(10, int(getattr(settings, "GRAPH_PHASE_TIMEOUT_S", 90))))

        # Progress callback — logs sub-phase updates for frontend visibility
        def _on_progress(step: str, detail: str):
            logger.info(f"[GRAPH:{audit_tier}] {step} — {detail}")

        try:
            async with asyncio.timeout(graph_timeout_s):
                result = await agent.investigate(
                    url=url,
                    page_metadata=metadata,
                    page_text=page_text,
                    external_links=external_links,
                    site_type=state.get("site_type", ""),
                    form_validation=primary.get("form_validation"),
                    progress_callback=_on_progress,
                )
        except TimeoutError:
            timeout_msg = f"Graph phase timeout after {graph_timeout_s}s"
            logger.error(timeout_msg)
            fallback_graph = {
                "graph_score": 0.5,
                "meta_score": 0.5,
                "meta_analysis": {},
                "ip_geolocation": {},
                "domain_age_days": -1,
                "has_ssl": False,
                "claims_extracted": [],
                "verifications": [],
                "inconsistencies": [],
                "graph_data": {"nodes": [], "edges": []},
                "graph_node_count": 0,
                "graph_edge_count": 0,
                "domain_intel": None,
                "tavily_searches": 0,
                "errors": [timeout_msg],
            }
            return {
                "graph_result": fallback_graph,
                "errors": errors + [timeout_msg],
            }

        # Serialize GraphResult (graph is exported separately)
        graph_dict = {
            "graph_score": result.graph_score,
            "meta_score": result.meta_score,
            "meta_analysis": getattr(result, 'meta_analysis', {}),
            "ip_geolocation": getattr(result, 'ip_geolocation', {}),
            "domain_age_days": result.domain_age_days,
            "has_ssl": result.has_ssl,
            "claims_extracted": [
                {"entity_type": c.entity_type, "entity_value": c.entity_value, "source_page": c.source_page}
                for c in result.claims_extracted
            ],
            "verifications": [
                {
                    "entity_type": v.claim.entity_type,
                    "entity_value": v.claim.entity_value,
                    "status": v.status,
                    "evidence_source": v.evidence_source,
                    "evidence_detail": v.evidence_detail,
                    "confidence": v.confidence,
                }
                for v in result.verifications
            ],
            "inconsistencies": [
                {
                    "claim_text": inc.claim_text,
                    "evidence_text": inc.evidence_text,
                    "inconsistency_type": inc.inconsistency_type,
                    "severity": inc.severity,
                    "confidence": inc.confidence,
                    "explanation": inc.explanation,
                }
                for inc in result.inconsistencies
            ],
            "graph_data": agent.export_graph_data(result.graph) if result.graph else {"nodes": [], "edges": []},
            "graph_node_count": result.graph_node_count,
            "graph_edge_count": result.graph_edge_count,
            "domain_intel": {
                "domain": result.domain_intel.domain if result.domain_intel else "",
                "registrar": result.domain_intel.registrar if result.domain_intel else "",
                "age_days": result.domain_intel.age_days if result.domain_intel else -1,
                "ssl_issuer": result.domain_intel.ssl_issuer if result.domain_intel else "",
                "is_privacy_protected": result.domain_intel.is_privacy_protected if result.domain_intel else False,
            } if result.domain_intel else None,
            "tavily_searches": result.tavily_searches,
            "osint_sources": result.osint_sources,
            "osint_consensus": result.osint_consensus,
            "osint_indicators": result.osint_indicators,
            "cti_techniques": result.cti_techniques,
            "threat_attribution": result.threat_attribution,
            "threat_level": result.threat_level,
            "osint_confidence": result.osint_confidence,
            "errors": result.errors,
        }

        return {
            "graph_result": graph_dict,
            "nim_calls_used": state.get("nim_calls_used", 0) + result.tavily_searches,
        }

    except Exception as e:
        logger.error(f"Graph node exception: {e}", exc_info=True)
        return {
            "errors": errors + [f"Graph exception: {str(e)}"],
            "graph_result": {
                "graph_score": 0.5,
                "meta_score": 0.5,
                "domain_age_days": -1,
                "has_ssl": False,
                "claims_extracted": [],
                "verifications": [],
                "inconsistencies": [],
                "graph_data": {"nodes": [], "edges": []},
                "errors": [str(e)],
            },
        }
