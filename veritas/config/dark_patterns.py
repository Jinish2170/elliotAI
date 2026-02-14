"""
Veritas — Dark Pattern Classification Taxonomy

Comprehensive taxonomy of deceptive UX patterns organized into 5 top-level
categories, each with sub-types, descriptions, detection methods, and
pre-built VLM prompts.

This module is the single source of truth for what Veritas can detect.
VLM prompts are engineered for structured JSON output from NVIDIA NIM models.
"""

from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# Data Structures
# ============================================================

@dataclass
class DarkPatternSubType:
    """A specific dark pattern variant within a category."""
    id: str
    name: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    examples: list = field(default_factory=list)


@dataclass
class DarkPatternCategory:
    """A top-level dark pattern category with detection configuration."""
    id: str
    name: str
    description: str
    sub_types: list  # List[DarkPatternSubType]
    detection_method: str  # "visual", "temporal", "structural", "combined"
    vlm_prompts: list  # List[str] — prompts to send to vision model
    structural_signals: list = field(default_factory=list)  # DOM-based detection hints


# ============================================================
# The Taxonomy
# ============================================================

DARK_PATTERN_TAXONOMY: dict[str, DarkPatternCategory] = {

    # ---------------------------------------------------------
    # Category 1: Visual Interference
    # ---------------------------------------------------------
    "visual_interference": DarkPatternCategory(
        id="visual_interference",
        name="Visual Interference",
        description="UI elements designed to mislead users through visual hierarchy manipulation — making desired actions prominent and undesired actions hidden.",
        detection_method="visual",
        sub_types=[
            DarkPatternSubType(
                id="hidden_unsubscribe",
                name="Hidden Unsubscribe/Cancel",
                description="Unsubscribe or cancel buttons made visually small, low-contrast, or hidden below the fold",
                severity="high",
                examples=["Gray 8px 'unsubscribe' text on gray background", "Cancel link hidden in footer with no visual weight"],
            ),
            DarkPatternSubType(
                id="misdirected_click",
                name="Misdirected Click Target",
                description="Accept/Agree buttons are visually dominant (large, colorful) while Decline/Reject is suppressed (small, gray, text-only)",
                severity="high",
                examples=["'Accept All Cookies' is a large green button, 'Manage Preferences' is a tiny text link"],
            ),
            DarkPatternSubType(
                id="disguised_ads",
                name="Disguised Advertisements",
                description="Advertisements styled to look like content, navigation elements, or system notifications",
                severity="medium",
                examples=["'Download' button that is actually an ad", "Sponsored content without clear labeling"],
            ),
            DarkPatternSubType(
                id="trick_questions",
                name="Trick Questions / Double Negatives",
                description="Confusing double-negative phrasing in opt-in/opt-out checkboxes designed to make users choose the opposite of their intent",
                severity="high",
                examples=["'Uncheck this box if you do NOT want to NOT receive emails'"],
            ),
            DarkPatternSubType(
                id="visual_hierarchy_manipulation",
                name="Visual Hierarchy Manipulation",
                description="Using color, size, or positioning to guide users toward the business-preferred action",
                severity="medium",
                examples=["Premium plan highlighted with color while free plan is grayed out"],
            ),
        ],
        vlm_prompts=[
            (
                "Analyze the visual prominence of all clickable buttons on this page. "
                "For each button pair that represents opposing actions (e.g., Accept/Decline, Subscribe/Cancel, "
                "Buy/Skip), compare their: (1) size in pixels, (2) color contrast against background, "
                "(3) position on page. Report if one action is significantly more prominent than the other. "
                "Respond in JSON: {\"findings\": [{\"pair\": [\"button1\", \"button2\"], \"dominant\": \"button1\", "
                "\"size_ratio\": 2.5, \"contrast_difference\": \"high\", \"pattern_type\": \"misdirected_click\", "
                "\"confidence\": 0.85}]}"
            ),
            (
                "Is there any clickable element on this page that is unusually small (appears under 12px font), "
                "has very low contrast against its background, or is positioned in a way that makes it hard to find? "
                "Focus on: unsubscribe links, cancel buttons, close/dismiss buttons, opt-out checkboxes. "
                "Respond in JSON: {\"findings\": [{\"element\": \"description\", \"issue\": \"low_contrast|tiny_size|hidden_position\", "
                "\"estimated_size\": \"8px\", \"pattern_type\": \"hidden_unsubscribe\", \"confidence\": 0.9}]}"
            ),
            (
                "Are there any elements on this page that look like content or navigation but are actually "
                "advertisements? Look for: fake download buttons, sponsored content without clear labels, "
                "ad units styled like article cards. "
                "Respond in JSON: {\"findings\": [{\"element\": \"description\", \"pattern_type\": \"disguised_ads\", "
                "\"confidence\": 0.7}]}"
            ),
        ],
        structural_signals=[
            "a[href*='unsubscribe'] with font-size < 12px",
            "button.decline, button.reject, button.cancel with opacity < 0.7",
            ".ad, .sponsored, .promoted without aria-label containing 'ad'",
        ],
    ),

    # ---------------------------------------------------------
    # Category 2: False Urgency
    # ---------------------------------------------------------
    "false_urgency": DarkPatternCategory(
        id="false_urgency",
        name="False Urgency",
        description="Fake time pressure tactics designed to force hasty decisions — countdown timers that reset, fake scarcity messages, fabricated social proof.",
        detection_method="temporal",
        sub_types=[
            DarkPatternSubType(
                id="fake_countdown",
                name="Fake Countdown Timer",
                description="Countdown timers that reset on page refresh or have no real deadline",
                severity="critical",
                examples=["'Sale ends in 00:04:59' that resets to 00:05:00 on refresh"],
            ),
            DarkPatternSubType(
                id="fake_scarcity",
                name="Fake Scarcity",
                description="'Only X left!' messages that never change or reset to the same value",
                severity="high",
                examples=["'Only 2 left in stock!' that always says 2", "'Limited availability' with no actual limit"],
            ),
            DarkPatternSubType(
                id="fake_social_proof",
                name="Fake Social Proof / Activity",
                description="'X people viewing this right now' or 'Y people bought this today' with no real data",
                severity="high",
                examples=["'15 people are viewing this right now' that shows the same number always"],
            ),
            DarkPatternSubType(
                id="expiring_offer",
                name="Fake Expiring Offer",
                description="'This offer expires today!' messages that appear every day",
                severity="medium",
                examples=["'Flash sale — today only!' banner that runs indefinitely"],
            ),
        ],
        vlm_prompts=[
            (
                "Look at this screenshot carefully. Is there a countdown timer, urgency indicator, "
                "or time-limited offer displayed anywhere? If yes, read its EXACT current value "
                "(e.g., '04:59', '2 hours left', 'Ends today'). "
                "Respond in JSON: {\"timer_found\": true/false, \"timer_value\": \"exact text\", "
                "\"timer_location\": \"description of where on page\", \"confidence\": 0.9}"
            ),
            (
                "Is there any 'limited stock', 'only X left', 'X people viewing/buying', or similar "
                "scarcity/social proof indicator on this page? Read its EXACT value. "
                "Respond in JSON: {\"scarcity_found\": true/false, \"scarcity_text\": \"exact text\", "
                "\"scarcity_type\": \"stock|viewers|purchases|other\", \"confidence\": 0.8}"
            ),
        ],
        structural_signals=[
            "elements with class containing 'timer', 'countdown', 'clock', 'urgency'",
            "elements with class containing 'stock', 'availability', 'remaining'",
            "JavaScript intervals/timeouts manipulating timer elements",
        ],
    ),

    # ---------------------------------------------------------
    # Category 3: Forced Continuity
    # ---------------------------------------------------------
    "forced_continuity": DarkPatternCategory(
        id="forced_continuity",
        name="Forced Continuity",
        description="Making it deliberately difficult to cancel, unsubscribe, or delete an account — the 'Roach Motel' pattern.",
        detection_method="visual",
        sub_types=[
            DarkPatternSubType(
                id="hidden_cancel",
                name="Hidden Cancellation",
                description="Cancel subscription button buried deep in settings, requiring multiple clicks",
                severity="critical",
                examples=["Cancel button only accessible via Settings > Account > Subscription > Advanced > Cancel"],
            ),
            DarkPatternSubType(
                id="guilt_tripping",
                name="Guilt Tripping / Confirmshaming",
                description="Using emotional or guilt-inducing language to discourage cancellation",
                severity="high",
                examples=["'Are you sure? You'll lose all your progress!'", "'No thanks, I don't want to save money'"],
            ),
            DarkPatternSubType(
                id="roach_motel",
                name="Roach Motel (Easy In, Hard Out)",
                description="Sign-up is 1 click but cancellation requires calling a phone number or sending a letter",
                severity="critical",
                examples=["Online signup but must call to cancel", "Account deletion requires emailing support"],
            ),
            DarkPatternSubType(
                id="forced_registration",
                name="Forced Account Creation",
                description="Requiring account creation to perform basic actions like viewing content or checking out",
                severity="medium",
                examples=["Must create account to see prices", "Guest checkout not available"],
            ),
        ],
        vlm_prompts=[
            (
                "Is there a clearly visible 'Cancel', 'Unsubscribe', or 'Delete Account' option on this page? "
                "If yes, how many clicks/steps does it appear to require? Is it visually prominent or hidden? "
                "Respond in JSON: {\"cancel_visible\": true/false, \"cancel_prominence\": \"prominent|subtle|hidden\", "
                "\"estimated_steps\": 1, \"pattern_type\": \"hidden_cancel|none\", \"confidence\": 0.8}"
            ),
            (
                "Does this page use emotional, guilt-inducing, or manipulative language to discourage "
                "the user from leaving, cancelling, or declining? Look for phrases like 'You'll miss out', "
                "'Are you sure?', 'No thanks, I don't want [positive thing]'. "
                "Respond in JSON: {\"guilt_language_found\": true/false, \"phrases\": [\"exact phrases found\"], "
                "\"pattern_type\": \"guilt_tripping\", \"confidence\": 0.85}"
            ),
        ],
        structural_signals=[
            "absence of cancel/unsubscribe links on account pages",
            "multi-step forms for cancellation (more than 2 pages)",
            "phone number as only cancellation method",
        ],
    ),

    # ---------------------------------------------------------
    # Category 4: Sneaking
    # ---------------------------------------------------------
    "sneaking": DarkPatternCategory(
        id="sneaking",
        name="Sneaking",
        description="Adding items, charges, or commitments without explicit user consent — hidden costs, pre-selected options, bait-and-switch pricing.",
        detection_method="visual",
        sub_types=[
            DarkPatternSubType(
                id="hidden_costs",
                name="Hidden Costs / Drip Pricing",
                description="Additional fees, taxes, or charges revealed only at checkout — not shown on product/pricing pages",
                severity="critical",
                examples=["Service fee added at checkout", "'From $9.99' but actual price is $19.99 with fees"],
            ),
            DarkPatternSubType(
                id="pre_selected_options",
                name="Pre-Selected Add-ons",
                description="Add-on products, insurance, or subscriptions pre-checked in the cart/checkout",
                severity="high",
                examples=["'Add extended warranty' checkbox pre-selected", "Newsletter subscription pre-opted-in"],
            ),
            DarkPatternSubType(
                id="bait_and_switch",
                name="Bait and Switch",
                description="Advertised price or product differs from what is actually offered at checkout",
                severity="critical",
                examples=["'$0/month' changes to '$9.99/month after trial' in fine print"],
            ),
            DarkPatternSubType(
                id="hidden_subscription",
                name="Hidden Subscription",
                description="Free trial that auto-converts to paid subscription without clear disclosure",
                severity="critical",
                examples=["'Start free trial' button with auto-billing in tiny print below"],
            ),
        ],
        vlm_prompts=[
            (
                "Examine this page for pre-selected checkboxes, pre-opted-in options, or add-ons that are "
                "already checked/selected without user action. List ALL pre-selected items. "
                "Respond in JSON: {\"pre_selected_found\": true/false, \"items\": [{\"description\": \"what is pre-selected\", "
                "\"is_additional_cost\": true/false}], \"pattern_type\": \"pre_selected_options\", \"confidence\": 0.9}"
            ),
            (
                "Is the total price clearly visible on this page? Are there any additional fees, charges, "
                "or costs shown in smaller text, lighter color, or below the fold? Compare the prominently "
                "displayed price with the actual total (if visible). "
                "Respond in JSON: {\"price_transparent\": true/false, \"displayed_price\": \"$X\", "
                "\"actual_total\": \"$Y or unknown\", \"hidden_fees\": [\"list of additional charges\"], "
                "\"pattern_type\": \"hidden_costs\", \"confidence\": 0.8}"
            ),
            (
                "Does this page mention a 'free trial', 'free' offer, or '$0' pricing? If yes, is there "
                "a requirement for credit card or payment information? Is the auto-renewal/billing clearly "
                "disclosed at the same visual prominence as the 'free' claim? "
                "Respond in JSON: {\"free_claim\": true/false, \"requires_payment_info\": true/false, "
                "\"auto_renewal_disclosed\": true/false, \"disclosure_prominence\": \"prominent|subtle|hidden\", "
                "\"pattern_type\": \"hidden_subscription\", \"confidence\": 0.85}"
            ),
        ],
        structural_signals=[
            "input[type='checkbox'][checked] in forms",
            "price elements with different font-size (large headline vs small total)",
            "'.fine-print', '.terms', '.disclaimer' near pricing",
        ],
    ),

    # ---------------------------------------------------------
    # Category 5: Social Engineering
    # ---------------------------------------------------------
    "social_engineering": DarkPatternCategory(
        id="social_engineering",
        name="Social Engineering / Fake Trust",
        description="Manipulating trust signals to appear more legitimate — fake reviews, unverifiable trust badges, fabricated authority claims.",
        detection_method="combined",
        sub_types=[
            DarkPatternSubType(
                id="fake_reviews",
                name="Fake Reviews / Testimonials",
                description="Testimonials using stock photos, AI-generated faces, or suspiciously similar writing patterns",
                severity="high",
                examples=["Testimonials with obviously stock photo headshots", "All reviews are 5 stars with generic text"],
            ),
            DarkPatternSubType(
                id="fake_badges",
                name="Fake Trust Badges",
                description="Trust badges (Norton Secured, BBB, SSL Secured) that are just images with no verification link",
                severity="critical",
                examples=["Norton Secured badge that doesn't link to Norton verification", "BBB A+ image with no BBB profile"],
            ),
            DarkPatternSubType(
                id="fake_authority",
                name="Fake Authority Claims",
                description="Claims of awards, certifications, partnerships, or endorsements with no verifiable proof",
                severity="high",
                examples=["'As seen on CNN/Forbes' with no actual media coverage", "'Award-winning' with no award name"],
            ),
            DarkPatternSubType(
                id="fake_counters",
                name="Fake User/Sales Counters",
                description="'1,000,000+ happy customers' or '50,000+ reviews' with no verifiable source",
                severity="medium",
                examples=["'Trusted by 2M+ users' on a website registered 2 weeks ago"],
            ),
        ],
        vlm_prompts=[
            (
                "Examine the testimonials/reviews section of this page. Do the profile photos appear to be "
                "stock photos or AI-generated faces? Are the review texts suspiciously similar in tone or length? "
                "Are all ratings 5 stars? "
                "Respond in JSON: {\"testimonials_found\": true/false, \"stock_photos_suspected\": true/false, "
                "\"uniform_ratings\": true/false, \"similar_writing_style\": true/false, "
                "\"pattern_type\": \"fake_reviews\", \"confidence\": 0.75}"
            ),
            (
                "Are there trust badges, certification logos, or security seals on this page "
                "(e.g., Norton, McAfee, BBB, SSL, TRUSTe)? If yes, do they appear to be clickable links "
                "to a verification page, or are they just static images? "
                "Respond in JSON: {\"badges_found\": true/false, \"badges\": [{\"name\": \"badge name\", "
                "\"appears_clickable\": true/false, \"appears_verifiable\": true/false}], "
                "\"pattern_type\": \"fake_badges\", \"confidence\": 0.8}"
            ),
            (
                "Does this page claim any awards, media features ('As seen on...'), partnerships, "
                "or endorsements? If yes, list each claim and whether there appears to be a link or "
                "proof supporting the claim. "
                "Respond in JSON: {\"authority_claims\": [{\"claim\": \"text of claim\", "
                "\"proof_visible\": true/false, \"link_present\": true/false}], "
                "\"pattern_type\": \"fake_authority\", \"confidence\": 0.7}"
            ),
        ],
        structural_signals=[
            "img[src] in testimonial sections (check if stock photo domains)",
            "trust badge images without parent <a> links",
            "'.award', '.featured', '.as-seen' sections without external links",
        ],
    ),
}


# ============================================================
# Helper Functions
# ============================================================

def get_all_vlm_prompts() -> list[dict]:
    """
    Get all VLM prompts flattened as dicts with category info.
    Useful for batch-processing screenshots.
    """
    prompts = []
    for cat_id, category in DARK_PATTERN_TAXONOMY.items():
        for prompt in category.vlm_prompts:
            prompts.append({"category": cat_id, "prompt": prompt})
    return prompts


def get_prompts_for_category(category_id: str) -> list[str]:
    """Get VLM prompts for a specific category."""
    category = DARK_PATTERN_TAXONOMY.get(category_id)
    if category:
        return category.vlm_prompts
    return []


def get_temporal_categories() -> list[str]:
    """Get category IDs that require temporal (time-series) detection."""
    return [
        cat_id for cat_id, cat in DARK_PATTERN_TAXONOMY.items()
        if cat.detection_method == "temporal"
    ]


def get_all_sub_types() -> list[DarkPatternSubType]:
    """Flatten all sub-types across all categories."""
    result = []
    for category in DARK_PATTERN_TAXONOMY.values():
        result.extend(category.sub_types)
    return result


def get_severity_weight(severity_or_category: str, sub_type: str = "") -> float:
    """
    Map severity to numerical weight for scoring.

    Can be called two ways:
        get_severity_weight("high")                        → 0.75
        get_severity_weight("false_urgency", "fake_timer") → looks up sub_type severity → weight
    """
    severity_map = {
        "low": 0.25,
        "medium": 0.5,
        "high": 0.75,
        "critical": 1.0,
    }
    # Two-arg form: look up sub-type severity from taxonomy
    if sub_type:
        cat = DARK_PATTERN_TAXONOMY.get(severity_or_category)
        if cat:
            for st in cat.sub_types:
                if st.id == sub_type:
                    return severity_map.get(st.severity, 0.5)
        return 0.5
    # One-arg form: severity string directly
    return severity_map.get(severity_or_category, 0.5)
