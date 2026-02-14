"""
Veritas — Website Type Classification & Per-Type Audit Profiles

Classifies websites into 5 operational categories, each with tailored:
  - Signal weight overrides (shift scoring emphasis)
  - Priority dark patterns (which sub-types matter most)
  - Severity adjustments (bump/demote based on context)
  - Narrative focus (what the Judge emphasizes)
  - Extra security checks to activate

The Scout agent runs classify_site_type() on extracted metadata.
The result threads through the entire pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum


class SiteType(Enum):
    """Website operational category."""
    ECOMMERCE = "ecommerce"
    COMPANY_PORTFOLIO = "company_portfolio"
    FINANCIAL = "financial"
    SAAS_SUBSCRIPTION = "saas_subscription"
    DARKNET_SUSPICIOUS = "darknet_suspicious"


@dataclass
class SiteTypeProfile:
    """Full audit profile for a detected website type."""
    site_type: SiteType
    name: str
    description: str

    # Signal weight overrides (keys: visual, structural, temporal, graph, meta, security)
    # Applied on top of defaults. Only include signals being changed.
    weight_overrides: dict[str, float] = field(default_factory=dict)

    # Dark pattern sub-type IDs that are especially important for this site type
    priority_patterns: list[str] = field(default_factory=list)

    # Severity bumps: {sub_type_id: new_severity}
    severity_adjustments: dict[str, str] = field(default_factory=dict)

    # What the Judge narrative should emphasize
    narrative_focus: str = ""

    # Simple-mode verdict focus: what matters most to a non-technical user
    simple_focus: str = ""

    # Which optional security modules to activate by default
    extra_checks: list[str] = field(default_factory=list)


# ============================================================
# Site Type Profiles
# ============================================================

SITE_TYPE_PROFILES: dict[SiteType, SiteTypeProfile] = {

    SiteType.ECOMMERCE: SiteTypeProfile(
        site_type=SiteType.ECOMMERCE,
        name="E-commerce / Product",
        description="Online stores, marketplaces, product listing sites",
        weight_overrides={
            "visual": 0.25,
            "structural": 0.15,
            "temporal": 0.15,
            "graph": 0.20,
            "meta": 0.05,
            "security": 0.20,
        },
        priority_patterns=[
            "hidden_costs", "pre_selected_options", "fake_scarcity",
            "fake_countdown", "bait_and_switch", "hidden_subscription",
            "fake_reviews", "fake_badges", "trick_questions",
        ],
        severity_adjustments={
            "hidden_costs": "critical",
            "pre_selected_options": "critical",
            "fake_scarcity": "critical",
            "bait_and_switch": "critical",
        },
        narrative_focus=(
            "Focus on pricing transparency, checkout fairness, return policy visibility, "
            "hidden fees, pre-selected add-ons, scarcity manipulation, and review authenticity."
        ),
        simple_focus=(
            "Is it safe to buy from this site? Are there hidden fees? "
            "Can I trust the reviews? Will I be charged for things I didn't want?"
        ),
        extra_checks=["security_headers", "phishing_db", "form_validation"],
    ),

    SiteType.COMPANY_PORTFOLIO: SiteTypeProfile(
        site_type=SiteType.COMPANY_PORTFOLIO,
        name="Company / Portfolio",
        description="Business websites, corporate portals, agency sites",
        weight_overrides={
            "visual": 0.15,
            "structural": 0.10,
            "temporal": 0.05,
            "graph": 0.35,
            "meta": 0.15,
            "security": 0.20,
        },
        priority_patterns=[
            "fake_badges", "fake_authority", "fake_reviews",
            "fake_counters", "fake_social_proof",
        ],
        severity_adjustments={
            "fake_badges": "critical",
            "fake_authority": "critical",
        },
        narrative_focus=(
            "Focus on entity verification, claimed certifications and awards, "
            "team member authenticity, address validation, and business registration."
        ),
        simple_focus=(
            "Is this a real company? Can I trust their claimed certifications? "
            "Are the team members real? Is their address legitimate?"
        ),
        extra_checks=["security_headers", "phishing_db"],
    ),

    SiteType.FINANCIAL: SiteTypeProfile(
        site_type=SiteType.FINANCIAL,
        name="Financial / Banking",
        description="Banks, fintech, payment processors, investment platforms",
        weight_overrides={
            "visual": 0.10,
            "structural": 0.25,
            "temporal": 0.05,
            "graph": 0.20,
            "meta": 0.10,
            "security": 0.30,
        },
        priority_patterns=[
            "hidden_costs", "hidden_subscription", "pre_selected_options",
            "roach_motel", "hidden_cancel", "fake_badges",
        ],
        severity_adjustments={
            "hidden_costs": "critical",
            "hidden_cancel": "critical",
            "roach_motel": "critical",
            "hidden_subscription": "critical",
        },
        narrative_focus=(
            "ZERO TOLERANCE for missing SSL, cross-domain form submissions, "
            "and unverified financial claims. Emphasize regulatory compliance indicators, "
            "encryption standards, and form security."
        ),
        simple_focus=(
            "Is it safe to enter my financial information? Is this site encrypted? "
            "Could this be a phishing site? Are there hidden charges?"
        ),
        extra_checks=[
            "security_headers", "phishing_db", "form_validation",
            "redirect_chain", "js_analysis",
        ],
    ),

    SiteType.SAAS_SUBSCRIPTION: SiteTypeProfile(
        site_type=SiteType.SAAS_SUBSCRIPTION,
        name="SaaS / Subscription",
        description="Software-as-a-service, subscription services, online tools",
        weight_overrides={
            "visual": 0.20,
            "structural": 0.15,
            "temporal": 0.15,
            "graph": 0.20,
            "meta": 0.10,
            "security": 0.20,
        },
        priority_patterns=[
            "forced_registration", "hidden_cancel", "roach_motel",
            "guilt_tripping", "hidden_subscription", "fake_countdown",
            "expiring_offer",
        ],
        severity_adjustments={
            "hidden_cancel": "critical",
            "roach_motel": "critical",
            "forced_registration": "high",
        },
        narrative_focus=(
            "Focus on cancellation transparency, trial-to-paid conversion clarity, "
            "pricing page honesty, forced account creation, and subscription trap indicators."
        ),
        simple_focus=(
            "Can I easily cancel? Will I be charged after a free trial? "
            "Is the pricing transparent? Am I being tricked into signing up?"
        ),
        extra_checks=["security_headers", "phishing_db", "form_validation"],
    ),

    SiteType.DARKNET_SUSPICIOUS: SiteTypeProfile(
        site_type=SiteType.DARKNET_SUSPICIOUS,
        name="Darknet / High-Risk",
        description="Suspicious domains, very new sites, known risky patterns",
        weight_overrides={
            "visual": 0.15,
            "structural": 0.15,
            "temporal": 0.10,
            "graph": 0.20,
            "meta": 0.10,
            "security": 0.30,
        },
        priority_patterns=[
            "fake_badges", "fake_authority", "hidden_costs",
            "bait_and_switch", "hidden_subscription", "fake_reviews",
            "fake_countdown", "fake_scarcity",
        ],
        severity_adjustments={
            "fake_badges": "critical",
            "fake_authority": "critical",
            "hidden_costs": "critical",
        },
        narrative_focus=(
            "MAXIMUM PARANOIA. Every claim must be externally verified. "
            "Assume adversarial intent. Weight absence of evidence as negative evidence. "
            "Check for bulletproof hosting, privacy-protected WHOIS, obfuscated code."
        ),
        simple_focus=(
            "This site has multiple red flags. Do NOT enter personal information. "
            "Do NOT make purchases. The site may be designed to steal your data."
        ),
        extra_checks=[
            "security_headers", "phishing_db", "form_validation",
            "redirect_chain", "js_analysis",
        ],
    ),
}


# ============================================================
# Classification Logic
# ============================================================

# Detection signals: keyword lists for each type
_ECOMMERCE_SIGNALS = {
    "url_patterns": ["shop", "store", "product", "buy", "cart", "checkout", "marketplace"],
    "meta_keywords": [
        "shop", "store", "buy", "price", "product", "cart", "checkout",
        "shipping", "delivery", "order", "add to cart", "basket",
        "sale", "discount", "deal", "offer", "free shipping",
    ],
    "dom_signals": ["has_price_elements", "has_cart", "has_checkout_form"],
}

_FINANCIAL_SIGNALS = {
    "url_patterns": ["bank", "finance", "pay", "invest", "crypto", "trading", "loan", "credit"],
    "meta_keywords": [
        "bank", "banking", "finance", "financial", "payment", "invest",
        "trading", "loan", "credit", "insurance", "mortgage", "account",
        "transfer", "deposit", "withdraw", "portfolio", "stock",
        "cryptocurrency", "bitcoin", "forex", "wire transfer",
    ],
    "dom_signals": ["has_password_form", "has_cc_form", "has_financial_forms"],
}

_SAAS_SIGNALS = {
    "url_patterns": ["app", "dashboard", "pricing", "subscribe", "trial", "saas"],
    "meta_keywords": [
        "pricing", "subscription", "subscribe", "plan", "trial",
        "free trial", "premium", "pro", "enterprise", "monthly",
        "annually", "per month", "per year", "sign up", "get started",
        "saas", "software", "platform", "tool", "api",
    ],
    "dom_signals": ["has_pricing_table", "has_signup_form"],
}

_COMPANY_SIGNALS = {
    "url_patterns": ["about", "team", "services", "portfolio", "contact", "careers"],
    "meta_keywords": [
        "about us", "our team", "services", "portfolio", "contact",
        "company", "agency", "solutions", "consulting", "partners",
        "careers", "mission", "vision", "founded", "headquarters",
    ],
    "dom_signals": ["has_about_section", "has_team_section"],
}


def classify_site_type(
    url: str,
    title: str = "",
    description: str = "",
    keywords: str = "",
    has_ssl: bool = True,
    domain_age_days: int | None = None,
    has_password_form: bool = False,
    has_cc_form: bool = False,
    has_price_elements: bool = False,
    scripts_count: int = 0,
    external_links_count: int = 0,
    forms_count: int = 0,
    cookies_count: int = 0,
    privacy_protected: bool = False,
) -> tuple[SiteType, float]:
    """
    Classify a website into one of the 5 operational types.

    Returns (SiteType, confidence: 0.0-1.0).
    Uses a weighted keyword + signal scoring approach.
    """
    combined_text = f"{url} {title} {description} {keywords}".lower()

    scores: dict[SiteType, float] = {st: 0.0 for st in SiteType}

    # --- Keyword matching ---
    for kw in _ECOMMERCE_SIGNALS["meta_keywords"]:
        if kw in combined_text:
            scores[SiteType.ECOMMERCE] += 1.0
    for pat in _ECOMMERCE_SIGNALS["url_patterns"]:
        if pat in url.lower():
            scores[SiteType.ECOMMERCE] += 2.0

    for kw in _FINANCIAL_SIGNALS["meta_keywords"]:
        if kw in combined_text:
            scores[SiteType.FINANCIAL] += 1.0
    for pat in _FINANCIAL_SIGNALS["url_patterns"]:
        if pat in url.lower():
            scores[SiteType.FINANCIAL] += 2.0

    for kw in _SAAS_SIGNALS["meta_keywords"]:
        if kw in combined_text:
            scores[SiteType.SAAS_SUBSCRIPTION] += 1.0
    for pat in _SAAS_SIGNALS["url_patterns"]:
        if pat in url.lower():
            scores[SiteType.SAAS_SUBSCRIPTION] += 2.0

    for kw in _COMPANY_SIGNALS["meta_keywords"]:
        if kw in combined_text:
            scores[SiteType.COMPANY_PORTFOLIO] += 1.0
    for pat in _COMPANY_SIGNALS["url_patterns"]:
        if pat in url.lower():
            scores[SiteType.COMPANY_PORTFOLIO] += 2.0

    # --- DOM signal bonuses ---
    if has_price_elements:
        scores[SiteType.ECOMMERCE] += 5.0
    if has_cc_form:
        scores[SiteType.FINANCIAL] += 4.0
        scores[SiteType.ECOMMERCE] += 3.0
    if has_password_form:
        scores[SiteType.FINANCIAL] += 2.0
        scores[SiteType.SAAS_SUBSCRIPTION] += 2.0

    # --- Suspicion signals for darknet classification ---
    suspicion = 0.0
    if not has_ssl:
        suspicion += 3.0
    if domain_age_days is not None and domain_age_days < 30:
        suspicion += 3.0
    if domain_age_days is not None and domain_age_days < 7:
        suspicion += 4.0
    if privacy_protected and domain_age_days is not None and domain_age_days < 90:
        suspicion += 2.0
    if scripts_count > 30:
        suspicion += 1.5
    if cookies_count > 20:
        suspicion += 1.0

    scores[SiteType.DARKNET_SUSPICIOUS] = suspicion

    # --- Find winner ---
    best_type = max(scores, key=scores.get)  # type: ignore[arg-type]
    best_score = scores[best_type]
    total_score = sum(scores.values())

    if total_score == 0:
        return SiteType.COMPANY_PORTFOLIO, 0.3  # Safe fallback

    confidence = min(best_score / max(total_score, 1), 1.0)

    # If no type scored meaningfully, default to company/portfolio
    if best_score < 2.0 and best_type != SiteType.DARKNET_SUSPICIOUS:
        return SiteType.COMPANY_PORTFOLIO, 0.3

    return best_type, round(confidence, 2)


def get_profile(site_type: SiteType) -> SiteTypeProfile:
    """Get the full audit profile for a site type."""
    return SITE_TYPE_PROFILES[site_type]


def get_adjusted_severity(site_type: SiteType, sub_type_id: str, default_severity: str) -> str:
    """Get the adjusted severity for a dark pattern sub-type given the site type."""
    profile = SITE_TYPE_PROFILES[site_type]
    return profile.severity_adjustments.get(sub_type_id, default_severity)


def is_priority_pattern(site_type: SiteType, sub_type_id: str) -> bool:
    """Check if a dark pattern sub-type is a priority for this site type."""
    profile = SITE_TYPE_PROFILES[site_type]
    return sub_type_id in profile.priority_patterns
