"""
News and blog site-type scoring strategy.

Emphasizes source credibility, clickbait detection, and
content authenticity assessment.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class NewsBlogScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for news websites and blogs.

    Prioritizes:
    - Metadata (0.25) - source credibility, authorship, publication info
    - Visual signals (0.20) - clickbait detection, design professionalism
    - Graph signals (0.20) - source reputation and network analysis
    - Structural analysis (0.15) - article structure and citations
    - Temporal analysis (0.10) - content freshness
    - Security signals (0.10) - basic security

    Key concerns:
    - Clickbait headlines and sensationalism
    - Paywalled content masquerading as free
    - Fake news indicators
    - Source credibility issues
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return NEWS_BLOG site type."""
        return ExtendedSiteType.NEWS_BLOG

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "News Blog Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for news/blog context.

        News/Blog specific concerns:
        - Clickbait headline detection
        - Source credibility and reputation
        - Content authenticity and originality
        - Paywall issues and fake sources

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with news/blog-specific logic
        """
        # Base weight adjustments prioritizing metadata and visual
        weight_adjustments = {
            "visual": 0.20,
            "structural": 0.15,
            "temporal": 0.10,
            "graph": 0.20,
            "meta": 0.25,
            "security": 0.10,
        }

        # Severity modifications for content integrity
        severity_modifications = {
            "clickbait_headlines": "MEDIUM",
            "sensationalist_content": "MEDIUM",
            "fake_sources": "HIGH",
            "paywalled_fake": "LOW",
            "misleading_citations": "MEDIUM",
        }

        custom_findings = []

        # Clickbait detection (through visual analysis of headlines)
        if "clickbait" in context.dark_pattern_types:
            custom_findings.append(("clickbait_headlines", "MEDIUM", 15))

        # Fake source detection (via graph analysis)
        if context.graph_score < 50 and context.meta_score < 60:
            custom_findings.append(("fake_sources", "HIGH", 20))

        # Paywalled content that claims to be free
        if "paywall_trap" in context.dark_pattern_types:
            custom_findings.append(("paywalled_fake", "LOW", 5))

        # SSL is important but not critical
        if not context.has_ssl:
            custom_findings.append(("missing_ssl", "LOW", 5))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "MEDIUM", 20) for trigger in critical_triggers]
            )

        # Narrative template
        narrative_template = "News/blog site"

        if context.meta_score > 75 and context.graph_score > 70:
            narrative_template += ": Credible source detected"
        elif context.meta_score >= 50:
            narrative_template += ": Source credibility moderate"
        else:
            narrative_template += ": Source credibility concerns"

        explanation = (
            "News/blog evaluation prioritizes metadata signals (0.25) for source credibility, "
            "authorship verification, and publication information. "
            "Visual signals (0.20) detect clickbait headlines and sensationalist content. "
            "Graph signals (0.20) verify source reputation and network legitimacy. "
            "Clickbait triggers MEDIUM severity (15-point deduction). "
            "Fake sources flagged as HIGH (20-point deduction). "
            "Focus on content authenticity and original editorial standards."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
