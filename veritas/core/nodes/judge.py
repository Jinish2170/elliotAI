"""
Veritas — Judge Node

Forensic verdict synthesis node for the audit graph.
Moved from veritas.core.orchestrator as part of Phase 13-04 refactoring.
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from veritas.agents.judge import AuditEvidence, JudgeAgent, JudgeDecision
from veritas.agents.scout import ScoutResult
from veritas.agents.vision import VisionAgent, VisionResult
from veritas.config import settings
from veritas.core.nim_client import NIMClient

if TYPE_CHECKING:
    from veritas.core.orchestrator import AuditState

logger = logging.getLogger("veritas.orchestrator")


async def judge_node(state: AuditState) -> dict:
    """
    JUDGE node: Synthesize all evidence into a verdict or request more investigation.
    """
    url = state.get("url", "")
    iteration = state.get("iteration", 0) + 1
    max_iterations = state.get("max_iterations", settings.MAX_ITERATIONS)

    # Reconstruct ScoutResult objects from serialized dicts
    scout_results = []
    for sr_dict in state.get("scout_results", []):
        scout_results.append(ScoutResult(**{
            k: v for k, v in sr_dict.items()
            if k in ScoutResult.__dataclass_fields__
        }))

    # Reconstruct VisionResult from serialized dict
    vision_result = None
    vr_dict = state.get("vision_result")
    if vr_dict:
        from veritas.agents.vision import DarkPatternFinding, TemporalFinding
        dark_patterns = []
        for p in vr_dict.get("findings", []):
            dark_patterns.append(DarkPatternFinding(
                category_id=p.get("category", p.get("category_id", "")),
                pattern_type=p.get("sub_type", p.get("pattern_type", "")),
                confidence=p.get("confidence", 0),
                severity=p.get("severity", "medium"),
                evidence=p.get("evidence", ""),
                screenshot_path=p.get("screenshot_path", ""),
                raw_vlm_response=p.get("raw_vlm_response", ""),
                model_used=p.get("model_used", ""),
                fallback_mode=p.get("fallback_mode", False),
            ))
        temporal_findings = []
        for tf in vr_dict.get("temporal_findings", []):
            temporal_findings.append(TemporalFinding(
                finding_type=tf.get("finding_type", ""),
                value_at_t0=tf.get("value_at_t0", ""),
                value_at_t_delay=tf.get("value_at_t_delay", ""),
                delta_seconds=tf.get("delta_seconds", 0),
                is_suspicious=tf.get("is_suspicious", False),
                explanation=tf.get("explanation", ""),
                confidence=tf.get("confidence", 0),
            ))
        vision_result = VisionResult(
            visual_score=vr_dict.get("visual_score", 0.5),
            temporal_score=vr_dict.get("temporal_score", 0.5),
            dark_patterns=dark_patterns,
            temporal_findings=temporal_findings,
            screenshots_analyzed=vr_dict.get("screenshots_analyzed", 0),
            prompts_sent=vr_dict.get("prompts_sent", 0),
            nim_calls_made=vr_dict.get("nim_calls_made", 0),
            fallback_used=vr_dict.get("fallback_used", False),
            errors=vr_dict.get("errors", []),
        )

    # Reconstruct GraphResult from serialized dict
    graph_result = None
    gr_dict = state.get("graph_result")
    if gr_dict:
        from veritas.agents.graph_investigator import (DomainIntel, EntityClaim,
                                               GraphInconsistency,
                                               VerificationResult)
        from veritas.agents.graph_investigator import GraphResult
        claims = [EntityClaim(**c) for c in gr_dict.get("claims_extracted", [])]
        verifications = [
            VerificationResult(
                claim=EntityClaim(
                    entity_type=v["entity_type"],
                    entity_value=v["entity_value"],
                    source_page=url,
                ),
                status=v["status"],
                evidence_source=v.get("evidence_source", ""),
                evidence_detail=v.get("evidence_detail", ""),
                confidence=v.get("confidence", 0.5),
            )
            for v in gr_dict.get("verifications", [])
        ]
        inconsistencies = [
            GraphInconsistency(**inc)
            for inc in gr_dict.get("inconsistencies", [])
        ]

        di_dict = gr_dict.get("domain_intel")
        domain_intel = DomainIntel(
            domain=di_dict.get("domain", ""),
            registrar=di_dict.get("registrar", ""),
            age_days=di_dict.get("age_days", -1),
            ssl_issuer=di_dict.get("ssl_issuer", ""),
            is_privacy_protected=di_dict.get("is_privacy_protected", False),
        ) if di_dict else None

        graph_result = GraphResult(
            domain_intel=domain_intel,
            claims_extracted=claims,
            verifications=verifications,
            inconsistencies=inconsistencies,
            graph_score=gr_dict.get("graph_score", 0.5),
            meta_score=gr_dict.get("meta_score", 0.5),
            graph_node_count=gr_dict.get("graph_node_count", 0),
            graph_edge_count=gr_dict.get("graph_edge_count", 0),
            tavily_searches=gr_dict.get("tavily_searches", 0),
            errors=gr_dict.get("errors", []),
            # Phase 8: OSINT/CTI fields
            osint_sources=gr_dict.get("osint_sources", {}),
            osint_consensus=gr_dict.get("osint_consensus", {}),
            osint_indicators=gr_dict.get("osint_indicators", []),
            cti_techniques=gr_dict.get("cti_techniques", []),
            threat_attribution=gr_dict.get("threat_attribution", {}),
            threat_level=gr_dict.get("threat_level", "none"),
            osint_confidence=gr_dict.get("osint_confidence", 0.0),
        )

    # Build evidence bundle
    evidence = AuditEvidence(
        url=url,
        scout_results=scout_results,
        vision_result=vision_result,
        graph_result=graph_result,
        iteration=iteration,
        max_iterations=max_iterations,
        max_pages=state.get("max_pages", 5),
        pages_investigated=len(state.get("investigated_urls", [])),
        site_type=state.get("site_type", ""),
        site_type_confidence=state.get("site_type_confidence", 0.0),
        verdict_mode=state.get("verdict_mode", "expert"),
        security_results=state.get("security_results", {}),
    )

    logger.info(f"Judge deliberating | iteration={iteration}/{max_iterations}")

    try:
        nim = NIMClient()
        judge = JudgeAgent(nim_client=nim)
        decision = await judge.analyze(evidence, use_dual_verdict=True)

        if decision.action == "REQUEST_MORE_INVESTIGATION":
            logger.info(f"Judge: need more investigation -> {decision.investigate_urls}")
            return {
                "iteration": iteration,
                "pending_urls": decision.investigate_urls,
                "judge_decision": {
                    "action": decision.action,
                    "reason": decision.reason,
                    "investigate_urls": decision.investigate_urls,
                },
            }
        else:
            # RENDER_VERDICT
            logger.info(
                f"Judge verdict: {decision.final_score}/100 "
                f"({decision.risk_level.value if decision.risk_level else 'unknown'})"
            )

            judge_dict = {
                "action": decision.action,
                "reason": decision.reason,
                "narrative": decision.forensic_narrative,
                "simple_narrative": getattr(decision, 'simple_narrative', ''),
                "recommendations": decision.recommendations,
                "simple_recommendations": getattr(decision, 'simple_recommendations', []),
                "dark_pattern_summary": decision.dark_pattern_summary,
                "entity_verification_summary": decision.entity_verification_summary,
                "evidence_timeline": decision.evidence_timeline,
                "site_type": getattr(decision, 'site_type', ''),
                "verdict_mode": getattr(decision, 'verdict_mode', 'expert'),
                # Phase 9: dual-tier verdict (technical + non-technical)
                "dual_verdict": getattr(decision, 'dual_verdict', None),
            }

            if decision.trust_score_result:
                tsr = decision.trust_score_result
                judge_dict["trust_score_result"] = {
                    "final_score": tsr.final_score,
                    "risk_level": tsr.risk_level.value,
                    "pre_override_score": tsr.pre_override_score,
                    "weighted_breakdown": tsr.weighted_breakdown,
                    "overrides_applied": [r.name for r in tsr.overrides_applied],
                    "sub_signals": {
                        s.name: {
                            "raw_score": s.raw_score,
                            "confidence": s.confidence,
                            "weighted_value": tsr.weighted_breakdown.get(s.name, 0),
                        }
                        for s in tsr.sub_signals
                    },
                    "explanation": tsr.explanation,
                }

            return {
                "iteration": iteration,
                "judge_decision": judge_dict,
                "status": "completed",
                "elapsed_seconds": time.time() - state.get("start_time", time.time()),
            }

    except Exception as e:
        logger.error(f"Judge exception: {e}", exc_info=True)
        return {
            "iteration": iteration,
            "errors": state.get("errors", []) + [f"Judge exception: {str(e)}"],
            "status": "aborted",
            "judge_decision": {
                "action": "RENDER_VERDICT",
                "reason": f"Judge failed: {str(e)}",
                "error": str(e),
            },
        }
