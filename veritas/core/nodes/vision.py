"""
Veritas — Vision Node

Visual forensics node for the audit graph.
Moved from veritas.core.orchestrator as part of Phase 13-04 refactoring.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from veritas.agents.vision import VisionAgent, VisionResult
from veritas.config import settings
from veritas.core.nim_client import NIMClient

if TYPE_CHECKING:
    from veritas.core.orchestrator import AuditState

logger = logging.getLogger("veritas.orchestrator")


async def vision_node(state: AuditState) -> dict:
    """
    VISION node: Analyze all screenshots from Scout results.
    """
    scout_results = state.get("scout_results", [])
    errors = state.get("errors", [])

    if not scout_results:
        return {"errors": errors + ["Vision: no scout results to analyze"]}

    # Collect all screenshots and labels from all scout results
    all_screenshots = []
    all_labels = []
    for sr in scout_results:
        all_screenshots.extend(sr.get("screenshots", []))
        all_labels.extend(sr.get("screenshot_labels", []))

    if not all_screenshots:
        logger.warning("Vision node: no screenshots available")
        return {
            "vision_result": {
                "visual_score": 0.5,
                "temporal_score": 0.5,
                "dark_patterns": [],
                "temporal_findings": [],
                "screenshots_analyzed": 0,
                "fallback_used": False,
                "errors": ["No screenshots available"],
            }
        }

    logger.info(f"Vision analyzing {len(all_screenshots)} screenshots")

    try:
        nim = NIMClient()
        agent = VisionAgent(nim_client=nim)

        # Tier-aware pass count and NIM budget
        audit_tier = state.get("audit_tier", "standard_audit")
        tier_config = settings.AUDIT_TIERS.get(audit_tier, settings.AUDIT_TIERS["standard_audit"])
        max_passes = tier_config.get("vision_passes", 3)
        nim_budget = tier_config.get("vision_nim", tier_config.get("nim_calls", 8)) - state.get("nim_calls_used", 0)
        use_5_pass = max_passes >= 5

        result = await agent.analyze(
            screenshots=all_screenshots,
            screenshot_labels=all_labels,
            url=state.get("url", ""),
            site_type=state.get("site_type", ""),
            use_5_pass_pipeline=use_5_pass,
            max_passes=max_passes,
            nim_budget=max(nim_budget, 1),
        )

        # Serialize VisionResult
        vision_dict = {
            "visual_score": result.visual_score,
            "temporal_score": result.temporal_score,
            "findings": [
                {
                    "category": p.category_id,
                    "sub_type": p.pattern_type,
                    "confidence": p.confidence,
                    "severity": p.severity,
                    "evidence": p.evidence,
                    "screenshot_path": p.screenshot_path,
                    "model_used": p.model_used,
                    "fallback_mode": p.fallback_mode,
                    "raw_vlm_response": p.raw_vlm_response,
                }
                for p in result.dark_patterns
            ],
            "temporal_findings": [
                {
                    "finding_type": tf.finding_type,
                    "value_at_t0": tf.value_at_t0,
                    "value_at_t_delay": tf.value_at_t_delay,
                    "delta_seconds": tf.delta_seconds,
                    "is_suspicious": tf.is_suspicious,
                    "explanation": tf.explanation,
                    "confidence": tf.confidence,
                }
                for tf in result.temporal_findings
            ],
            "screenshots_analyzed": result.screenshots_analyzed,
            "prompts_sent": result.prompts_sent,
            "nim_calls_made": result.nim_calls_made,
            "fallback_used": result.fallback_used,
            "errors": result.errors,
        }

        return {
            "vision_result": vision_dict,
            "nim_calls_used": state.get("nim_calls_used", 0) + result.nim_calls_made,
        }

    except Exception as e:
        logger.error(f"Vision node exception: {e}", exc_info=True)
        return {
            "errors": errors + [f"Vision exception: {str(e)}"],
            "vision_result": {
                "visual_score": 0.5,
                "temporal_score": 0.5,
                "dark_patterns": [],
                "temporal_findings": [],
                "screenshots_analyzed": 0,
                "fallback_used": True,
                "errors": [str(e)],
            },
        }
