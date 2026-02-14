"""
Veritas — Trust Score Weights & Override Rules

Implements the weighted multi-signal scoring formula:

    TrustScore = Σ(wi × Si) for i in [visual, structural, temporal, graph, meta]

With hard-stop override rules that can cap or force scores regardless of
the weighted calculation.

This module is the single source of truth for all scoring parameters.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ============================================================
# Risk Levels
# ============================================================

class RiskLevel(Enum):
    """Trust score → risk level mapping."""
    TRUSTED = "trusted"
    PROBABLY_SAFE = "probably_safe"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    LIKELY_FRAUDULENT = "likely_fraudulent"


RISK_LEVEL_THRESHOLDS: dict[RiskLevel, tuple[int, int]] = {
    RiskLevel.TRUSTED:            (90, 100),
    RiskLevel.PROBABLY_SAFE:      (70, 89),
    RiskLevel.SUSPICIOUS:         (40, 69),
    RiskLevel.HIGH_RISK:          (20, 39),
    RiskLevel.LIKELY_FRAUDULENT:  (0, 19),
}


def score_to_risk_level(score: int) -> RiskLevel:
    """Convert a 0-100 trust score to a risk level."""
    score = max(0, min(100, score))
    for level, (low, high) in RISK_LEVEL_THRESHOLDS.items():
        if low <= score <= high:
            return level
    return RiskLevel.LIKELY_FRAUDULENT


# ============================================================
# Signal Weights
# ============================================================

@dataclass
class SignalWeights:
    """
    Weights for each sub-signal in the trust score formula.
    Must sum to 1.0.

    Rationale:
    - graph (0.25):     Most reliable — real-world entity verification is hard to fake
    - visual (0.20):    High impact but VLM can hallucinate — needs graph cross-check
    - security (0.20):  HTTP headers, phishing DBs, form validation, JS analysis
    - structural (0.15): Reliable DOM analysis but can be gamed by sophisticated sites
    - temporal (0.10):  Unique signal (timer resets), very hard to fake, but narrow scope
    - meta (0.10):      Easy to check (SSL, domain age), hard to fake, but limited depth
    """
    visual: float = 0.20
    structural: float = 0.15
    temporal: float = 0.10
    graph: float = 0.25
    meta: float = 0.10
    security: float = 0.20

    def validate(self) -> bool:
        """Ensure weights sum to 1.0 (with floating point tolerance)."""
        total = (
            self.visual + self.structural + self.temporal
            + self.graph + self.meta + self.security
        )
        return abs(total - 1.0) < 0.001

    def as_dict(self) -> dict[str, float]:
        return {
            "visual": self.visual,
            "structural": self.structural,
            "temporal": self.temporal,
            "graph": self.graph,
            "meta": self.meta,
            "security": self.security,
        }

    @classmethod
    def from_overrides(cls, overrides: dict[str, float]) -> 'SignalWeights':
        """
        Create weights from a site-type override dict.
        The override dict must contain all 6 keys and sum to 1.0.
        """
        return cls(
            visual=overrides.get("visual", 0.20),
            structural=overrides.get("structural", 0.15),
            temporal=overrides.get("temporal", 0.10),
            graph=overrides.get("graph", 0.25),
            meta=overrides.get("meta", 0.10),
            security=overrides.get("security", 0.20),
        )


# Default weights instance
DEFAULT_WEIGHTS = SignalWeights()


# ============================================================
# Override Rules (Hard Stops)
# ============================================================

@dataclass
class OverrideRule:
    """
    A hard-stop rule that can cap or force the trust score.
    Evaluated AFTER the weighted calculation.
    """
    id: str
    name: str
    description: str
    condition: str  # Human-readable condition description
    action: str     # "cap_at", "force_below", "deduct"
    value: int      # The score value for the action
    priority: int   # Lower = evaluated first (1 = highest priority)


OVERRIDE_RULES: list[OverrideRule] = [
    OverrideRule(
        id="no_ssl",
        name="No SSL Certificate",
        description="Sites without HTTPS cannot score above 50",
        condition="ssl_status == False",
        action="cap_at",
        value=50,
        priority=1,
    ),
    OverrideRule(
        id="new_domain_low_graph",
        name="New Domain + Low Graph Score",
        description="Domain < 7 days old AND graph verification score < 0.3 → force below 30",
        condition="domain_age_days < 7 AND graph_score < 0.3",
        action="force_below",
        value=30,
        priority=2,
    ),
    OverrideRule(
        id="fake_timer_detected",
        name="Fake Timer Detected",
        description="Temporal analysis detected a resetting countdown timer → deduct 25 points",
        condition="temporal_findings contain 'fake_countdown'",
        action="deduct",
        value=25,
        priority=3,
    ),
    OverrideRule(
        id="domain_blacklisted",
        name="Domain is Blacklisted",
        description="Domain appears in known scam/phishing databases → force below 15",
        condition="domain in blacklist_databases",
        action="force_below",
        value=15,
        priority=1,
    ),
    OverrideRule(
        id="all_fake_badges",
        name="All Trust Badges are Unverifiable",
        description="Site displays trust badges but none are clickable/verifiable → deduct 15 points",
        condition="fake_badges_count > 0 AND verified_badges_count == 0",
        action="deduct",
        value=15,
        priority=4,
    ),
    OverrideRule(
        id="captcha_only",
        name="CAPTCHA Blocked (Partial Analysis)",
        description="Site blocked automated analysis with CAPTCHA — cap but don't penalize",
        condition="scout_status == 'CAPTCHA_BLOCKED'",
        action="cap_at",
        value=65,
        priority=5,
    ),
]


# ============================================================
# Paranoia Override Rules (DARKNET_SUSPICIOUS only)
# ============================================================

PARANOIA_OVERRIDES: list[OverrideRule] = [
    OverrideRule(
        id="paranoia_no_ssl",
        name="[PARANOIA] No SSL",
        description="In paranoia mode, no SSL caps at 25",
        condition="ssl_status == False",
        action="cap_at",
        value=25,
        priority=1,
    ),
    OverrideRule(
        id="paranoia_new_domain",
        name="[PARANOIA] New Domain (<30 days)",
        description="Paranoia mode caps new domains at 40",
        condition="domain_age_days < 30",
        action="cap_at",
        value=40,
        priority=2,
    ),
    OverrideRule(
        id="paranoia_hidden_whois_new",
        name="[PARANOIA] Hidden WHOIS + New Domain",
        description="Privacy-protected WHOIS on domain < 90 days caps at 35",
        condition="is_privacy_protected AND domain_age_days < 90",
        action="cap_at",
        value=35,
        priority=3,
    ),
    OverrideRule(
        id="paranoia_phishing_hit",
        name="[PARANOIA] Phishing DB Hit",
        description="Any phishing database match forces below 5",
        condition="is_phishing == True",
        action="force_below",
        value=5,
        priority=1,
    ),
    OverrideRule(
        id="paranoia_js_obfuscation",
        name="[PARANOIA] JS Obfuscation",
        description="High JS obfuscation score (>0.7) deducts 30 points",
        condition="js_risk_score > 0.7",
        action="deduct",
        value=30,
        priority=4,
    ),
    OverrideRule(
        id="paranoia_cross_domain_forms",
        name="[PARANOIA] Cross-Domain Sensitive Forms",
        description="Forms with passwords/CC submitting cross-domain",
        condition="has_cross_domain_sensitive_forms",
        action="deduct",
        value=25,
        priority=3,
    ),
]


# ============================================================
# Scoring Functions
# ============================================================

@dataclass
class SubSignal:
    """A single sub-signal contributing to the trust score."""
    name: str        # "visual", "structural", "temporal", "graph", "meta"
    raw_score: float # 0.0 to 1.0
    confidence: float = 1.0  # How confident we are in this signal (0-1)
    evidence_count: int = 0  # Number of evidence pieces behind this signal
    details: dict = field(default_factory=dict)  # Breakdown for the report


@dataclass
class TrustScoreResult:
    """Complete trust score computation result."""
    final_score: int                # 0-100
    risk_level: RiskLevel
    sub_signals: list               # List[SubSignal]
    weighted_breakdown: dict        # {signal_name: weighted_contribution}
    overrides_applied: list         # List[OverrideRule] that fired
    pre_override_score: int         # Score before any overrides
    explanation: str                # Human-readable explanation


def compute_trust_score(
    signals: dict[str, SubSignal],
    weights: Optional[SignalWeights] = None,
    domain_age_days: Optional[int] = None,
    ssl_status: Optional[bool] = None,
    temporal_findings: Optional[list[str]] = None,
    is_blacklisted: bool = False,
    scout_status: str = "SUCCESS",
    fake_badges_count: int = 0,
    verified_badges_count: int = 0,
    paranoia_mode: bool = False,
    is_phishing: bool = False,
    js_risk_score: float = 1.0,
    is_privacy_protected: bool = False,
    has_cross_domain_sensitive_forms: bool = False,
) -> TrustScoreResult:
    """
    Compute the final trust score from sub-signals.

    Args:
        signals: Dict mapping signal names to SubSignal objects.
                 Expected keys: "visual", "structural", "temporal", "graph", "meta"
        weights: Signal weights (defaults to DEFAULT_WEIGHTS)
        domain_age_days: Age of the domain in days (for override rules)
        ssl_status: Whether the site has SSL (for override rules)
        temporal_findings: List of temporal finding IDs (for override rules)
        is_blacklisted: Whether the domain is in a blacklist
        scout_status: Status from the Scout agent
        fake_badges_count: Number of unverifiable trust badges found
        verified_badges_count: Number of verified trust badges found

    Returns:
        TrustScoreResult with full breakdown
    """
    w = weights or DEFAULT_WEIGHTS
    assert w.validate(), f"Weights must sum to 1.0, got {sum(w.as_dict().values())}"

    weight_map = w.as_dict()

    # Step 1: Weighted sum
    weighted_breakdown = {}
    raw_total = 0.0
    for signal_name, weight in weight_map.items():
        signal = signals.get(signal_name)
        if signal:
            # Apply confidence weighting: low-confidence signals contribute less
            effective_score = signal.raw_score * signal.confidence
            contribution = weight * effective_score
            weighted_breakdown[signal_name] = round(contribution, 4)
            raw_total += contribution
        else:
            # Missing signal: assume neutral (0.5) with low confidence
            contribution = weight * 0.5 * 0.5
            weighted_breakdown[signal_name] = round(contribution, 4)
            raw_total += contribution

    # Convert to 0-100 scale
    pre_override = int(round(raw_total * 100))
    pre_override = max(0, min(100, pre_override))
    final_score = pre_override

    # Step 2: Apply override rules (sorted by priority)
    overrides_applied = []
    temporal_findings = temporal_findings or []

    for rule in sorted(OVERRIDE_RULES, key=lambda r: r.priority):
        fired = False

        if rule.id == "no_ssl" and ssl_status is False:
            fired = True
        elif rule.id == "new_domain_low_graph":
            graph_signal = signals.get("graph")
            graph_score = graph_signal.raw_score if graph_signal else 0
            if domain_age_days is not None and domain_age_days < 7 and graph_score < 0.3:
                fired = True
        elif rule.id == "fake_timer_detected" and "fake_countdown" in temporal_findings:
            fired = True
        elif rule.id == "domain_blacklisted" and is_blacklisted:
            fired = True
        elif rule.id == "all_fake_badges" and fake_badges_count > 0 and verified_badges_count == 0:
            fired = True
        elif rule.id == "captcha_only" and scout_status == "CAPTCHA_BLOCKED":
            fired = True

        if fired:
            overrides_applied.append(rule)
            if rule.action == "cap_at":
                final_score = min(final_score, rule.value)
            elif rule.action == "force_below":
                final_score = min(final_score, rule.value)
            elif rule.action == "deduct":
                final_score = max(0, final_score - rule.value)

    # Step 2b: Apply paranoia overrides (if paranoia_mode is active)
    if paranoia_mode:
        for rule in sorted(PARANOIA_OVERRIDES, key=lambda r: r.priority):
            fired = False
            if rule.id == "paranoia_no_ssl" and ssl_status is False:
                fired = True
            elif rule.id == "paranoia_new_domain":
                if domain_age_days is not None and domain_age_days < 30:
                    fired = True
            elif rule.id == "paranoia_hidden_whois_new":
                if is_privacy_protected and domain_age_days is not None and domain_age_days < 90:
                    fired = True
            elif rule.id == "paranoia_phishing_hit" and is_phishing:
                fired = True
            elif rule.id == "paranoia_js_obfuscation" and js_risk_score < 0.3:
                # js_risk_score is 0-1 where 1=clean, so <0.3 means >0.7 risk
                fired = True
            elif rule.id == "paranoia_cross_domain_forms" and has_cross_domain_sensitive_forms:
                fired = True

            if fired:
                overrides_applied.append(rule)
                if rule.action == "cap_at":
                    final_score = min(final_score, rule.value)
                elif rule.action == "force_below":
                    final_score = min(final_score, rule.value)
                elif rule.action == "deduct":
                    final_score = max(0, final_score - rule.value)

    final_score = max(0, min(100, final_score))
    risk_level = score_to_risk_level(final_score)

    # Step 3: Generate explanation
    explanations = []
    for name, contrib in sorted(weighted_breakdown.items(), key=lambda x: x[1], reverse=True):
        signal = signals.get(name)
        if signal:
            explanations.append(
                f"  {name}: {signal.raw_score:.2f} × {weight_map[name]:.2f} "
                f"(confidence: {signal.confidence:.0%}) → {contrib:.4f}"
            )
    if overrides_applied:
        explanations.append(f"\n  Overrides applied: {[r.name for r in overrides_applied]}")

    explanation = (
        f"Trust Score: {final_score}/100 ({risk_level.value})\n"
        f"Pre-override score: {pre_override}\n"
        f"Signal breakdown:\n" + "\n".join(explanations)
    )

    return TrustScoreResult(
        final_score=final_score,
        risk_level=risk_level,
        sub_signals=list(signals.values()),
        weighted_breakdown=weighted_breakdown,
        overrides_applied=overrides_applied,
        pre_override_score=pre_override,
        explanation=explanation,
    )
