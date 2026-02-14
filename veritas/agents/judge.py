"""
Veritas Agent 4 — The Judge (Orchestrator's Brain)

The "Brain" of Veritas. Synthesizes evidence from all other agents into
a final verdict with Trust Score, risk level, and actionable recommendations.

Responsibilities:
    1. Receive evidence from Scout (metadata), Vision (dark patterns), Graph (entity verification)
    2. Determine if more investigation is needed (request additional pages)
    3. Compute the final Trust Score via trust_weights.compute_trust_score()
    4. Generate a forensic narrative explaining the verdict
    5. Produce structured report data for the reporting module

Decision Logic:
    - If confidence < threshold AND iteration budget remains → REQUEST_MORE_INVESTIGATION
    - If all evidence gathered OR budget exhausted → RENDER_VERDICT
    - Multi-model voting: Vision says trusted but Graph says fraud → Graph wins
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.graph_investigator import GraphResult
from agents.scout import ScoutResult
from agents.vision import VisionResult
from config import settings
from config.trust_weights import (DEFAULT_WEIGHTS, RiskLevel, SignalWeights,
                                  SubSignal, TrustScoreResult,
                                  compute_trust_score)
from core.nim_client import NIMClient

logger = logging.getLogger("veritas.judge")


# ============================================================
# Data Structures
# ============================================================

@dataclass
class JudgeDecision:
    """The Judge's decision: either request more investigation or render a verdict."""
    action: str               # "RENDER_VERDICT" | "REQUEST_MORE_INVESTIGATION"
    reason: str               # Why this decision was made

    # Only for REQUEST_MORE_INVESTIGATION
    investigate_urls: list[str] = field(default_factory=list)
    investigate_reason: str = ""

    # Only for RENDER_VERDICT
    trust_score_result: Optional[TrustScoreResult] = None
    forensic_narrative: str = ""
    simple_narrative: str = ""          # Plain-language narrative for non-technical users
    recommendations: list[str] = field(default_factory=list)
    simple_recommendations: list[str] = field(default_factory=list)  # Jargon-free recommendations
    dark_pattern_summary: list[dict] = field(default_factory=list)
    entity_verification_summary: list[dict] = field(default_factory=list)
    evidence_timeline: list[dict] = field(default_factory=list)
    site_type: str = ""                # Detected site type
    verdict_mode: str = "expert"       # "simple" | "expert"

    @property
    def final_score(self) -> int:
        if self.trust_score_result:
            return self.trust_score_result.final_score
        return -1

    @property
    def risk_level(self) -> Optional[RiskLevel]:
        if self.trust_score_result:
            return self.trust_score_result.risk_level
        return None


@dataclass
class AuditEvidence:
    """All evidence collected during an audit, passed to the Judge."""
    url: str
    scout_results: list[ScoutResult] = field(default_factory=list)
    vision_result: Optional[VisionResult] = None
    graph_result: Optional[GraphResult] = None
    iteration: int = 0
    max_iterations: int = 5

    # Extended fields for v2
    site_type: str = ""                # From scout classification
    site_type_confidence: float = 0.0
    verdict_mode: str = "expert"       # "simple" | "expert"
    security_results: dict = field(default_factory=dict)   # From security modules


# ============================================================
# Judge Agent
# ============================================================

class JudgeAgent:
    """
    Agent 4: Synthesizes all evidence into a verdict.

    Usage:
        judge = JudgeAgent()

        evidence = AuditEvidence(
            url="https://suspicious-site.com",
            scout_results=[scout_result],
            vision_result=vision_result,
            graph_result=graph_result,
            iteration=1,
            max_iterations=5,
        )

        decision = await judge.deliberate(evidence)

        if decision.action == "RENDER_VERDICT":
            print(f"Score: {decision.final_score}")
            print(decision.forensic_narrative)
        elif decision.action == "REQUEST_MORE_INVESTIGATION":
            print(f"Need to check: {decision.investigate_urls}")
    """

    def __init__(self, nim_client: Optional[NIMClient] = None):
        self._nim = nim_client or NIMClient()

    # ================================================================
    # Public: Main Deliberation
    # ================================================================

    async def deliberate(self, evidence: AuditEvidence) -> JudgeDecision:
        """
        Main entry point. Examines all evidence and decides next action.

        Decision tree:
        1. Check if we have minimum evidence to judge
        2. If evidence is thin AND budget allows → request more investigation
        3. Otherwise → compute trust score and render verdict
        """
        logger.info(
            f"Judge deliberating on {evidence.url} | "
            f"iteration={evidence.iteration}/{evidence.max_iterations} | "
            f"scout_pages={len(evidence.scout_results)} | "
            f"has_vision={evidence.vision_result is not None} | "
            f"has_graph={evidence.graph_result is not None}"
        )

        # -----------------------------------------------------------
        # Check: Do we need more investigation?
        # -----------------------------------------------------------
        if self._should_investigate_more(evidence):
            return await self._request_more_investigation(evidence)

        # -----------------------------------------------------------
        # We have enough evidence — render verdict
        # -----------------------------------------------------------
        return await self._render_verdict(evidence)

    # ================================================================
    # Private: Decision Logic
    # ================================================================

    def _should_investigate_more(self, evidence: AuditEvidence) -> bool:
        """
        Determine if more investigation is needed.

        Conditions for requesting more:
        1. Haven't hit max iterations
        2. Haven't analyzed enough pages yet
        3. Evidence is ambiguous (conflicting signals)
        """
        # Budget exhausted — must judge now
        if evidence.iteration >= evidence.max_iterations:
            logger.info("Budget exhausted — forcing verdict")
            return False

        # No vision data yet — can't judge without eyes
        if evidence.vision_result is None:
            return True

        # No graph data yet — can't judge without background check
        if evidence.graph_result is None and evidence.iteration < 2:
            return True

        # Check for ambiguous signals (vision says safe but only checked homepage)
        if evidence.vision_result and evidence.graph_result:
            vision_score = evidence.vision_result.visual_score
            graph_score = evidence.graph_result.graph_score

            # If vision and graph strongly disagree, investigate more
            if abs(vision_score - graph_score) > 0.4 and evidence.iteration < 3:
                logger.info(
                    f"Signal conflict: vision={vision_score:.2f} vs graph={graph_score:.2f} — "
                    f"requesting more investigation"
                )
                return True

        # Only checked 1 page — should check more for standard/deep audits
        if len(evidence.scout_results) == 1 and evidence.iteration < 2:
            # Check if there are important subpages to investigate
            scout = evidence.scout_results[0]
            if scout.status == "SUCCESS" and scout.page_metadata:
                # Has forms or many links — worth deeper look
                if scout.forms_detected > 0:
                    return True

        return False

    async def _request_more_investigation(
        self, evidence: AuditEvidence,
    ) -> JudgeDecision:
        """
        Generate a request for more investigation with specific URLs.
        Uses NIM LLM to intelligently select which pages to check next.
        """
        # Collect available links from scout results
        available_links = []
        for scout in evidence.scout_results:
            if scout.page_metadata:
                internal_links = scout.page_metadata.get("internal_links", [])
                if isinstance(internal_links, int):
                    internal_links = []
                available_links.extend(internal_links)
            available_links.extend(scout.links or [])

        # Deduplicate
        seen_urls = {s.url for s in evidence.scout_results}
        candidate_urls = [u for u in set(available_links) if u not in seen_urls]

        if not candidate_urls:
            # No more URLs to check — force verdict
            return await self._render_verdict(evidence)

        # Priority pages for fraud investigation
        priority_patterns = [
            "/about", "/contact", "/terms", "/privacy", "/cancel",
            "/unsubscribe", "/refund", "/pricing", "/checkout",
            "/team", "/leadership", "/legal",
        ]

        priority_urls = []
        other_urls = []
        for url in candidate_urls:
            url_lower = url.lower()
            if any(p in url_lower for p in priority_patterns):
                priority_urls.append(url)
            else:
                other_urls.append(url)

        # Select top URLs to investigate (max 2 per iteration)
        investigate = (priority_urls + other_urls)[:2]

        reason = self._build_investigation_reason(evidence)

        logger.info(f"Judge requesting investigation of: {investigate} | reason: {reason}")

        return JudgeDecision(
            action="REQUEST_MORE_INVESTIGATION",
            reason=reason,
            investigate_urls=investigate,
            investigate_reason=reason,
        )

    def _build_investigation_reason(self, evidence: AuditEvidence) -> str:
        """Build a human-readable reason for requesting more investigation."""
        reasons = []

        if evidence.vision_result is None:
            reasons.append("No visual analysis completed yet")
        if evidence.graph_result is None:
            reasons.append("No entity verification completed yet")
        if len(evidence.scout_results) == 1:
            reasons.append("Only homepage analyzed — need subpages for thorough audit")

        if evidence.vision_result and evidence.graph_result:
            v = evidence.vision_result.visual_score
            g = evidence.graph_result.graph_score
            if abs(v - g) > 0.4:
                reasons.append(
                    f"Conflicting signals (visual={v:.2f}, graph={g:.2f}) — "
                    f"need more evidence to resolve"
                )

        return "; ".join(reasons) if reasons else "Standard multi-page audit protocol"

    # ================================================================
    # Private: Verdict Rendering
    # ================================================================

    async def _render_verdict(self, evidence: AuditEvidence) -> JudgeDecision:
        """
        Compute Trust Score, generate forensic narrative, and produce final verdict.
        """
        # -----------------------------------------------------------
        # Step 1: Build sub-signals for trust score computation
        # -----------------------------------------------------------
        signals = self._build_signals(evidence)

        # -----------------------------------------------------------
        # Step 2: Gather metadata for override rules
        # -----------------------------------------------------------
        domain_age_days = None
        ssl_status = None
        is_blacklisted = False
        scout_status = "SUCCESS"
        temporal_findings = []
        fake_badges_count = 0
        verified_badges_count = 0

        if evidence.graph_result:
            domain_age_days = evidence.graph_result.domain_age_days
            ssl_status = evidence.graph_result.has_ssl

        if evidence.scout_results:
            primary_scout = evidence.scout_results[0]
            scout_status = primary_scout.status
            if primary_scout.page_metadata:
                ssl_from_scout = primary_scout.page_metadata.get("has_ssl")
                if ssl_status is None:
                    ssl_status = ssl_from_scout

        if evidence.vision_result:
            temporal_findings = evidence.vision_result.temporal_finding_ids
            # Count badge findings
            for p in evidence.vision_result.dark_patterns:
                if p.pattern_type == "fake_badges":
                    fake_badges_count += 1

        # -----------------------------------------------------------
        # Step 3: Compute Trust Score — with site-type weight overrides
        # -----------------------------------------------------------
        # Apply site-type weight overrides if available
        weights = DEFAULT_WEIGHTS
        paranoia_mode = False
        try:
            from config.site_types import SITE_TYPE_PROFILES, SiteType
            if evidence.site_type:
                st = SiteType(evidence.site_type)
                profile = SITE_TYPE_PROFILES.get(st)
                if profile and profile.weight_overrides:
                    weights = SignalWeights.from_overrides(profile.weight_overrides)
                    logger.info(f"Using weight overrides for site_type={evidence.site_type}")
                if st == SiteType.DARKNET_SUSPICIOUS:
                    paranoia_mode = True
        except Exception:
            pass

        # Gather paranoia params from security results
        is_phishing = False
        js_risk_score = 0.0
        is_privacy_protected = False
        has_cross_domain_forms = False

        sec = evidence.security_results
        if sec:
            phishing = sec.get("phishing", {})
            is_phishing = phishing.get("is_phishing", False)
            js = sec.get("js_analysis", {})
            js_risk_score = js.get("risk_score", 0.0)
        if evidence.graph_result and evidence.graph_result.domain_intel:
            is_privacy_protected = evidence.graph_result.domain_intel.is_privacy_protected

        # Check form validation from scout
        for scout in evidence.scout_results:
            fv = getattr(scout, 'form_validation', {})
            if fv and fv.get("critical_count", 0) > 0:
                has_cross_domain_forms = True

        trust_result = compute_trust_score(
            signals=signals,
            weights=weights,
            domain_age_days=domain_age_days,
            ssl_status=ssl_status,
            temporal_findings=temporal_findings,
            is_blacklisted=is_blacklisted,
            scout_status=scout_status,
            fake_badges_count=fake_badges_count,
            verified_badges_count=verified_badges_count,
            paranoia_mode=paranoia_mode,
            is_phishing=is_phishing,
            js_risk_score=js_risk_score,
            is_privacy_protected=is_privacy_protected,
            has_cross_domain_sensitive_forms=has_cross_domain_forms,
        )

        logger.info(
            f"Trust Score computed: {trust_result.final_score}/100 "
            f"({trust_result.risk_level.value}) | "
            f"pre_override={trust_result.pre_override_score} | "
            f"overrides={[r.name for r in trust_result.overrides_applied]}"
        )

        # -----------------------------------------------------------
        # Step 4: Generate forensic narrative via NIM LLM
        #         ALWAYS generate expert narrative
        # -----------------------------------------------------------
        narrative = await self._generate_narrative(evidence, trust_result)

        # -----------------------------------------------------------
        # Step 4b: Generate simple-mode narrative
        #          (always generated so both modes are available)
        # -----------------------------------------------------------
        simple_narrative = await self._generate_simple_narrative(evidence, trust_result)

        # -----------------------------------------------------------
        # Step 5: Generate recommendations (both expert and simple)
        # -----------------------------------------------------------
        recommendations = self._generate_recommendations(trust_result, evidence)
        simple_recs = self._generate_simple_recommendations(trust_result, evidence)

        # -----------------------------------------------------------
        # Step 6: Build evidence summaries for the report
        # -----------------------------------------------------------
        dark_pattern_summary = self._summarize_dark_patterns(evidence)
        entity_summary = self._summarize_entity_verification(evidence)
        timeline = self._build_evidence_timeline(evidence)

        return JudgeDecision(
            action="RENDER_VERDICT",
            reason=f"Trust Score: {trust_result.final_score}/100 ({trust_result.risk_level.value})",
            trust_score_result=trust_result,
            forensic_narrative=narrative,
            simple_narrative=simple_narrative,
            recommendations=recommendations,
            simple_recommendations=simple_recs,
            dark_pattern_summary=dark_pattern_summary,
            entity_verification_summary=entity_summary,
            evidence_timeline=timeline,
            site_type=evidence.site_type,
            verdict_mode=evidence.verdict_mode,
        )

    # ================================================================
    # Private: Signal Construction
    # ================================================================

    def _build_signals(self, evidence: AuditEvidence) -> dict[str, SubSignal]:
        """Build SubSignal objects from all collected evidence."""
        signals = {}

        # --- Visual Signal ---
        if evidence.vision_result:
            vr = evidence.vision_result
            signals["visual"] = SubSignal(
                name="visual",
                raw_score=vr.visual_score,
                confidence=0.85 if not vr.fallback_used else 0.5,
                evidence_count=vr.total_patterns_found,
                details={
                    "patterns_found": vr.total_patterns_found,
                    "critical_patterns": len(vr.critical_patterns),
                    "screenshots_analyzed": vr.screenshots_analyzed,
                    "fallback_used": vr.fallback_used,
                },
            )
        else:
            signals["visual"] = SubSignal(
                name="visual", raw_score=0.5, confidence=0.2,
                details={"note": "No visual analysis available"},
            )

        # --- Temporal Signal ---
        if evidence.vision_result and evidence.vision_result.temporal_findings:
            vr = evidence.vision_result
            signals["temporal"] = SubSignal(
                name="temporal",
                raw_score=vr.temporal_score,
                confidence=0.9 if vr.has_fake_timers else 0.7,
                evidence_count=len(vr.temporal_findings),
                details={
                    "has_fake_timers": vr.has_fake_timers,
                    "findings": [
                        {"type": tf.finding_type, "suspicious": tf.is_suspicious}
                        for tf in vr.temporal_findings
                    ],
                },
            )
        else:
            signals["temporal"] = SubSignal(
                name="temporal", raw_score=0.5, confidence=0.3,
                details={"note": "No temporal data — single screenshot or no timers detected"},
            )

        # --- Graph Signal ---
        if evidence.graph_result:
            gr = evidence.graph_result
            signals["graph"] = SubSignal(
                name="graph",
                raw_score=gr.graph_score,
                confidence=min(0.9, 0.5 + len(gr.verifications) * 0.1),
                evidence_count=len(gr.verifications) + len(gr.inconsistencies),
                details={
                    "verifications": len(gr.verifications),
                    "inconsistencies": len(gr.inconsistencies),
                    "confirmed": sum(1 for v in gr.verifications if v.status == "confirmed"),
                    "denied": sum(1 for v in gr.verifications if v.status in ("denied", "contradicted")),
                    "graph_nodes": gr.graph_node_count,
                    "graph_edges": gr.graph_edge_count,
                },
            )
        else:
            signals["graph"] = SubSignal(
                name="graph", raw_score=0.5, confidence=0.2,
                details={"note": "No graph investigation completed"},
            )

        # --- Meta Signal ---
        if evidence.graph_result:
            gr = evidence.graph_result
            signals["meta"] = SubSignal(
                name="meta",
                raw_score=gr.meta_score,
                confidence=0.85,
                evidence_count=1,
                details={
                    "domain_age_days": gr.domain_age_days,
                    "has_ssl": gr.has_ssl,
                    "whois_available": gr.domain_intel is not None,
                },
            )
        else:
            signals["meta"] = SubSignal(
                name="meta", raw_score=0.5, confidence=0.3,
                details={"note": "No domain intelligence available"},
            )

        # --- Structural Signal (from Scout DOM analysis) ---
        structural_score = self._compute_structural_score(evidence)
        signals["structural"] = structural_score

        # --- Security Signal (from security modules) ---
        sec = evidence.security_results
        if sec:
            sec_score = 0.5
            sec_details = {}
            sec_evidence_count = 0

            # Security headers
            headers = sec.get("security_headers", {})
            if headers:
                h_score = headers.get("score", 0.5)
                sec_score = (sec_score + h_score) / 2
                sec_details["headers_score"] = h_score
                sec_details["missing_headers"] = headers.get("missing_headers", [])
                sec_evidence_count += 1

            # Phishing
            phishing = sec.get("phishing", {})
            if phishing:
                if phishing.get("is_phishing"):
                    sec_score = max(0.0, sec_score - 0.4)
                    sec_details["phishing_alert"] = True
                sec_details["phishing_flags"] = phishing.get("flags", [])
                sec_evidence_count += 1

            # Redirect analysis
            redirects = sec.get("redirects", {})
            if redirects:
                if redirects.get("is_suspicious"):
                    sec_score = max(0.0, sec_score - 0.2)
                    sec_details["suspicious_redirects"] = True
                sec_details["redirect_hops"] = redirects.get("total_hops", 0)
                sec_evidence_count += 1

            # JS analysis
            js = sec.get("js_analysis", {})
            if js:
                js_risk = js.get("risk_score", 0.0)
                if js_risk > 0.5:
                    sec_score = max(0.0, sec_score - js_risk * 0.3)
                sec_details["js_risk_score"] = js_risk
                sec_evidence_count += 1

            signals["security"] = SubSignal(
                name="security",
                raw_score=round(max(0.0, min(1.0, sec_score)), 3),
                confidence=0.8 if sec_evidence_count >= 2 else 0.5,
                evidence_count=sec_evidence_count,
                details=sec_details,
            )
        else:
            signals["security"] = SubSignal(
                name="security", raw_score=0.5, confidence=0.2,
                details={"note": "No security modules were run"},
            )

        return signals

    def _compute_structural_score(self, evidence: AuditEvidence) -> SubSignal:
        """
        Compute structural trust signal from Scout's DOM metadata.
        Factors: SSL, forms with passwords, script count, external links ratio.
        """
        score = 0.5
        details = {}
        evidence_count = 0

        for scout in evidence.scout_results:
            if scout.status != "SUCCESS":
                continue

            meta = scout.page_metadata
            if not meta:
                continue

            evidence_count += 1

            # SSL from browser
            if meta.get("has_ssl"):
                score += 0.1
                details["ssl"] = True
            else:
                score -= 0.1
                details["ssl"] = False

            # Password forms without SSL → critical
            forms = meta.get("forms", [])
            has_password_form = any(
                f.get("hasPassword") for f in forms if isinstance(f, dict)
            )
            if has_password_form and not meta.get("has_ssl"):
                score -= 0.2
                details["password_without_ssl"] = True

            # Credit card forms → check SSL
            has_cc_form = any(
                f.get("hasCreditCard") for f in forms if isinstance(f, dict)
            )
            if has_cc_form:
                if not meta.get("has_ssl"):
                    score -= 0.25
                    details["credit_card_without_ssl"] = True
                else:
                    details["has_payment_form"] = True

            # Excessive external scripts → potential trackers/malware
            ext_scripts = meta.get("external_scripts", [])
            if isinstance(ext_scripts, list) and len(ext_scripts) > 20:
                score -= 0.05
                details["excessive_scripts"] = len(ext_scripts)

            # External links ratio
            int_links = meta.get("internal_links_count", 0)
            ext_links = meta.get("external_links_count", 0)
            if isinstance(int_links, int) and isinstance(ext_links, int):
                if int_links + ext_links > 0:
                    ext_ratio = ext_links / (int_links + ext_links)
                    if ext_ratio > 0.8:
                        score -= 0.05
                        details["high_external_link_ratio"] = round(ext_ratio, 2)

            # Apply scout-level trust modifiers
            score += scout.trust_modifier

        score = max(0.0, min(1.0, score))

        return SubSignal(
            name="structural",
            raw_score=round(score, 3),
            confidence=0.7 if evidence_count > 0 else 0.2,
            evidence_count=evidence_count,
            details=details,
        )

    # ================================================================
    # Private: Forensic Narrative
    # ================================================================

    async def _generate_narrative(
        self, evidence: AuditEvidence, trust_result: TrustScoreResult,
    ) -> str:
        """
        Generate a forensic narrative using NIM LLM.
        Written in professional auditor tone, citing specific evidence.
        """
        # Build evidence summary for the LLM
        evidence_summary = self._build_evidence_summary_text(evidence, trust_result)

        prompt = (
            "Write a professional forensic audit narrative for this website investigation. "
            "Use a neutral, evidence-based tone like a financial auditor's report. "
            "Cite specific findings. Do NOT speculate beyond the evidence.\n\n"
            "Structure:\n"
            "1. Opening statement (1-2 sentences: what was audited and final verdict)\n"
            "2. Visual Analysis findings (dark patterns found/not found)\n"
            "3. Entity Verification findings (what was confirmed/denied)\n"
            "4. Domain Intelligence findings (age, SSL, WHOIS)\n"
            "5. Conclusion and risk assessment\n\n"
            f"Evidence:\n{evidence_summary}\n\n"
            "Write 200-400 words. Be precise and factual."
        )

        result = await self._nim.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are a digital forensic auditor writing an official audit report. "
                "Your language is precise, professional, and evidence-based. "
                "You reference specific findings with confidence scores. "
                "You never speculate or use emotional language."
            ),
            max_tokens=1024,
            temperature=0.2,
        )

        response = result.get("response", "")

        # If LLM failed, generate a templated narrative
        if not response or result.get("fallback_mode"):
            response = self._generate_template_narrative(evidence, trust_result)

        return response

    def _build_evidence_summary_text(
        self, evidence: AuditEvidence, trust_result: TrustScoreResult,
    ) -> str:
        """Build a structured text summary of all evidence for the LLM."""
        sections = []

        sections.append(f"URL: {evidence.url}")
        sections.append(f"Trust Score: {trust_result.final_score}/100 ({trust_result.risk_level.value})")
        sections.append(f"Pages analyzed: {len(evidence.scout_results)}")

        # Vision findings
        if evidence.vision_result:
            vr = evidence.vision_result
            sections.append(f"\nVisual Analysis:")
            sections.append(f"  Dark patterns found: {vr.total_patterns_found}")
            sections.append(f"  Critical patterns: {len(vr.critical_patterns)}")
            sections.append(f"  Fake timers detected: {vr.has_fake_timers}")
            for p in vr.dark_patterns[:5]:
                sections.append(f"  - {p.category_id}/{p.pattern_type}: {p.evidence[:100]} (conf={p.confidence:.0%})")

        # Graph findings
        if evidence.graph_result:
            gr = evidence.graph_result
            sections.append(f"\nEntity Verification:")
            sections.append(f"  Domain age: {gr.domain_age_days} days")
            sections.append(f"  Inconsistencies: {len(gr.inconsistencies)}")
            for v in gr.verifications:
                sections.append(f"  - {v.claim.entity_type}='{v.claim.entity_value}': {v.status} (conf={v.confidence:.0%})")
            for inc in gr.inconsistencies:
                sections.append(f"  - INCONSISTENCY ({inc.severity}): {inc.explanation[:100]}")

        # Overrides
        if trust_result.overrides_applied:
            sections.append(f"\nOverride Rules Applied:")
            for r in trust_result.overrides_applied:
                sections.append(f"  - {r.name}: {r.description}")

        return "\n".join(sections)

    def _generate_template_narrative(
        self, evidence: AuditEvidence, trust_result: TrustScoreResult,
    ) -> str:
        """Fallback: generate a templated narrative without LLM."""
        score = trust_result.final_score
        risk = trust_result.risk_level.value.replace("_", " ").title()

        parts = [
            f"Veritas Forensic Audit of {evidence.url}\n",
            f"The automated forensic audit of this website concluded with a Trust Score "
            f"of {score}/100, categorized as '{risk}'.\n",
        ]

        if evidence.vision_result:
            vr = evidence.vision_result
            count = vr.total_patterns_found
            if count > 0:
                parts.append(
                    f"Visual analysis identified {count} potential dark pattern(s) "
                    f"across {vr.screenshots_analyzed} screenshots. "
                    f"{len(vr.critical_patterns)} were rated as critical severity."
                )
            else:
                parts.append("Visual analysis found no significant dark patterns.")

        if evidence.graph_result:
            gr = evidence.graph_result
            parts.append(
                f"Domain intelligence shows the domain is {gr.domain_age_days} days old. "
                f"{len(gr.inconsistencies)} inconsistencies were detected between "
                f"website claims and external evidence."
            )

        if trust_result.overrides_applied:
            names = [r.name for r in trust_result.overrides_applied]
            parts.append(f"Override rules applied: {', '.join(names)}.")

        return "\n".join(parts)

    # ================================================================
    # Private: Recommendations
    # ================================================================

    def _generate_recommendations(
        self, trust_result: TrustScoreResult, evidence: AuditEvidence,
    ) -> list[str]:
        """Generate actionable recommendations based on the verdict."""
        recs = []
        risk = trust_result.risk_level

        if risk in (RiskLevel.LIKELY_FRAUDULENT, RiskLevel.HIGH_RISK):
            recs.append("DO NOT enter personal information or payment details on this site.")
            recs.append("Report this site to relevant authorities (FTC, local consumer protection).")
            recs.append("If you've already transacted, monitor your accounts for unauthorized activity.")

        if risk == RiskLevel.SUSPICIOUS:
            recs.append("Exercise caution. Verify the business through independent channels before transacting.")
            recs.append("Check for the business on official registries (Better Business Bureau, etc.).")

        # Specific recommendations based on findings
        if evidence.vision_result:
            if evidence.vision_result.has_fake_timers:
                recs.append("Fake urgency timers detected — do not feel pressured by countdown timers on this site.")
            for p in evidence.vision_result.dark_patterns:
                if p.pattern_type == "pre_selected_options":
                    recs.append("Check all checkboxes and pre-selected options carefully before completing any purchase.")
                    break
                if p.pattern_type == "hidden_costs":
                    recs.append("Verify the total price including all fees before completing checkout.")
                    break

        if evidence.graph_result:
            if evidence.graph_result.domain_age_days >= 0 and evidence.graph_result.domain_age_days < 30:
                recs.append("This is a very new website. New domains carry higher risk for scam operations.")

        if not recs:
            recs.append("No immediate concerns identified. Standard online safety practices apply.")

        return list(dict.fromkeys(recs))  # Deduplicate while preserving order

    # ================================================================
    # Private: Simple-Mode Narrative (jargon-free)
    # ================================================================

    async def _generate_simple_narrative(
        self, evidence: AuditEvidence, trust_result: TrustScoreResult,
    ) -> str:
        """
        Generate a plain-language narrative for non-technical users.
        Avoids jargon like SSL, WHOIS, DNS, VLM, etc.
        """
        evidence_summary = self._build_evidence_summary_text(evidence, trust_result)

        prompt = (
            "Rewrite the following technical website audit findings into a simple, "
            "friendly explanation that anyone can understand. "
            "Use everyday language. Instead of 'SSL certificate', say 'secure connection'. "
            "Instead of 'WHOIS', say 'website registration records'. "
            "Instead of 'dark patterns', say 'tricks to mislead you'. "
            "Instead of 'domain age', say 'how long this website has existed'. "
            "Instead of 'DNS', say 'website address records'. "
            "Keep it warm but honest. Use 100-200 words.\n\n"
            "Explain:\n"
            "- Is this website safe to use?\n"
            "- What should I watch out for?\n"
            "- What did we find that was good or bad?\n\n"
            f"Technical findings:\n{evidence_summary}"
        )

        result = await self._nim.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are a friendly security advisor explaining website safety to "
                "someone who is not technical. Speak clearly and simply. "
                "Use analogies where helpful. Never use technical jargon."
            ),
            max_tokens=512,
            temperature=0.3,
        )

        response = result.get("response", "")

        if not response or result.get("fallback_mode"):
            # Fallback: generate simple template
            score = trust_result.final_score
            if score >= 70:
                response = (
                    f"We checked this website thoroughly and it looks reasonably safe "
                    f"(scored {score} out of 100). The website appears to be what it "
                    f"claims to be, and we didn't find major tricks or scams."
                )
            elif score >= 40:
                response = (
                    f"We found some concerns with this website (scored {score} out of 100). "
                    f"Be careful when using it — double check prices, read the fine print, "
                    f"and don't rush into any decisions."
                )
            else:
                response = (
                    f"This website raised serious red flags (scored only {score} out of 100). "
                    f"We strongly recommend not entering any personal information or "
                    f"payment details here. Several warning signs point to possible fraud."
                )

        return response

    def _generate_simple_recommendations(
        self, trust_result: TrustScoreResult, evidence: AuditEvidence,
    ) -> list[str]:
        """Generate jargon-free recommendations for non-technical users."""
        recs = []
        risk = trust_result.risk_level

        if risk in (RiskLevel.LIKELY_FRAUDULENT, RiskLevel.HIGH_RISK):
            recs.append("Don't enter your credit card or personal details on this site.")
            recs.append("If you've already made a purchase, check your bank statements carefully.")
            recs.append("Look for the same product/service on well-known websites instead.")
        elif risk == RiskLevel.SUSPICIOUS:
            recs.append("Be careful — this site has some warning signs.")
            recs.append("Search for reviews of this website before buying anything.")
            recs.append("If prices seem too good to be true, they probably are.")
        else:
            recs.append("This website looks okay, but always be mindful online.")

        # Specific plain-language warnings
        if evidence.vision_result:
            if evidence.vision_result.has_fake_timers:
                recs.append("The countdown timers on this site are fake — don't let them rush you.")
            for p in evidence.vision_result.dark_patterns:
                if "hidden" in p.pattern_type:
                    recs.append("Watch out for hidden fees — check the total price carefully at checkout.")
                    break
                if "pre_selected" in p.pattern_type:
                    recs.append("Uncheck any boxes that were already ticked for you — they might add unwanted charges.")
                    break

        if evidence.graph_result:
            if evidence.graph_result.domain_age_days >= 0 and evidence.graph_result.domain_age_days < 30:
                recs.append("This website is very new — brand new sites are more commonly used for scams.")

        return list(dict.fromkeys(recs))

    # ================================================================
    # Private: Report Summaries
    # ================================================================

    def _summarize_dark_patterns(self, evidence: AuditEvidence) -> list[dict]:
        """Build a report-ready summary of dark pattern findings."""
        if not evidence.vision_result:
            return []

        summary = []
        for p in evidence.vision_result.dark_patterns:
            summary.append({
                "category": p.category_id,
                "pattern": p.pattern_type,
                "severity": p.severity,
                "confidence": round(p.confidence, 2),
                "evidence": p.evidence[:200],
                "screenshot": p.screenshot_path,
            })
        return summary

    def _summarize_entity_verification(self, evidence: AuditEvidence) -> list[dict]:
        """Build a report-ready summary of entity verification results."""
        if not evidence.graph_result:
            return []

        summary = []
        for v in evidence.graph_result.verifications:
            summary.append({
                "entity_type": v.claim.entity_type,
                "claimed_value": v.claim.entity_value,
                "status": v.status,
                "confidence": round(v.confidence, 2),
                "evidence": v.evidence_detail[:200],
            })

        for inc in evidence.graph_result.inconsistencies:
            summary.append({
                "entity_type": "inconsistency",
                "claimed_value": inc.claim_text,
                "status": inc.inconsistency_type,
                "confidence": round(inc.confidence, 2),
                "evidence": inc.explanation[:200],
            })

        return summary

    def _build_evidence_timeline(self, evidence: AuditEvidence) -> list[dict]:
        """Build a chronological timeline of evidence collection."""
        timeline = []

        for i, scout in enumerate(evidence.scout_results):
            timeline.append({
                "step": len(timeline) + 1,
                "agent": "Scout",
                "action": f"Navigated to {scout.url}",
                "status": scout.status,
                "result": f"{len(scout.screenshots)} screenshots, {scout.forms_detected} forms",
                "duration_ms": scout.navigation_time_ms,
            })

        if evidence.vision_result:
            vr = evidence.vision_result
            timeline.append({
                "step": len(timeline) + 1,
                "agent": "Vision",
                "action": f"Analyzed {vr.screenshots_analyzed} screenshots",
                "status": "COMPLETE",
                "result": f"{vr.total_patterns_found} dark patterns, {len(vr.temporal_findings)} temporal checks",
            })

        if evidence.graph_result:
            gr = evidence.graph_result
            timeline.append({
                "step": len(timeline) + 1,
                "agent": "Graph",
                "action": f"Investigated {len(gr.claims_extracted)} entity claims",
                "status": "COMPLETE",
                "result": (
                    f"{len(gr.verifications)} verified, "
                    f"{len(gr.inconsistencies)} inconsistencies, "
                    f"domain age={gr.domain_age_days}d"
                ),
            })

        timeline.append({
            "step": len(timeline) + 1,
            "agent": "Judge",
            "action": "Rendered final verdict",
            "status": "COMPLETE",
        })

        return timeline
