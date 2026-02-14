"""
Veritas UI — Streamlit Application

Single-page dashboard for running web audits.

Features:
    - URL input with tier selection
    - Live audit progress log
    - Trust score gauge + risk level badge
    - Evidence timeline with screenshot viewer
    - Dark pattern findings list
    - Graph entity viewer
    - PDF report download trigger

Run:
    cd veritas
    streamlit run ui/app.py
"""

import asyncio
import json
import logging
# Fix imports for package-relative usage
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from config.dark_patterns import DARK_PATTERN_TAXONOMY
from core.orchestrator import VeritasOrchestrator

logger = logging.getLogger("veritas.ui")

# ============================================================
# Page config
# ============================================================
st.set_page_config(
    page_title="Veritas — Forensic Web Auditor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Custom CSS
# ============================================================
st.markdown("""
<style>
    /* Trust score gauge colours */
    .trust-critical { color: #DC2626; font-weight: bold; }
    .trust-high     { color: #EA580C; font-weight: bold; }
    .trust-medium   { color: #CA8A04; font-weight: bold; }
    .trust-low      { color: #2563EB; font-weight: bold; }
    .trust-safe     { color: #16A34A; font-weight: bold; }

    /* Badge styling */
    .risk-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-critical { background: #FEE2E2; color: #991B1B; }
    .badge-high     { background: #FFEDD5; color: #9A3412; }
    .badge-medium   { background: #FEF9C3; color: #854D0E; }
    .badge-low      { background: #DBEAFE; color: #1E40AF; }
    .badge-safe     { background: #DCFCE7; color: #166534; }

    /* Evidence card */
    .evidence-card {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        background: #FAFAFA;
    }

    /* Log container */
    .log-container {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.78rem;
        line-height: 1.5;
        background: #0F172A;
        color: #E2E8F0;
        padding: 12px;
        border-radius: 8px;
        max-height: 300px;
        overflow-y: auto;
    }
    .log-info    { color: #93C5FD; }
    .log-warning { color: #FDE047; }
    .log-error   { color: #FCA5A5; }
    .log-success { color: #86EFAC; }

    /* Metric card */
    .metric-row {
        display: flex;
        gap: 12px;
        margin-bottom: 12px;
    }
    .metric-card {
        flex: 1;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #6B7280;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Session state initialisation
# ============================================================
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = []
if "history" not in st.session_state:
    st.session_state.history = []


# ============================================================
# Helper functions
# ============================================================

def risk_level_badge(risk_level: str) -> str:
    """Return HTML badge for a risk level."""
    css_class = {
        "likely_fraudulent": "badge-critical",
        "high_risk": "badge-high",
        "suspicious": "badge-medium",
        "probably_safe": "badge-low",
        "trusted": "badge-safe",
    }.get(risk_level, "badge-medium")
    label = risk_level.replace("_", " ").title()
    return f'<span class="risk-badge {css_class}">{label}</span>'


def trust_score_color(score: float) -> str:
    """Return CSS class for trust score value (0-100 scale)."""
    if score < 20:
        return "trust-critical"
    elif score < 40:
        return "trust-high"
    elif score < 60:
        return "trust-medium"
    elif score < 80:
        return "trust-low"
    return "trust-safe"


def format_log_entry(msg: str, level: str = "info") -> str:
    """Format a log entry with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    css = f"log-{level}"
    return f'<span class="{css}">[{ts}] {msg}</span>'


def add_log(msg: str, level: str = "info"):
    """Append to session audit log."""
    st.session_state.audit_logs.append(format_log_entry(msg, level))


class StreamlitLogHandler(logging.Handler):
    """Route Python logger to Streamlit audit logs."""
    def emit(self, record):
        level_map = {
            logging.DEBUG: "info",
            logging.INFO: "info",
            logging.WARNING: "warning",
            logging.ERROR: "error",
            logging.CRITICAL: "error",
        }
        level = level_map.get(record.levelno, "info")
        add_log(record.getMessage(), level)


async def run_audit(url: str, tier: str) -> dict:
    """Run the Veritas audit pipeline asynchronously."""
    orchestrator = VeritasOrchestrator()
    result = await orchestrator.audit(url, tier)
    return result


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/security-checked--v1.png", width=64)
    st.title("VERITAS")
    st.caption("Autonomous Forensic Web Auditor")

    st.divider()

    # API Key check
    nim_key_status = "✅ Configured" if settings.NIM_API_KEY else "❌ Missing"
    tavily_status = "✅ Configured" if settings.TAVILY_API_KEY else "⚠️ Optional"

    st.markdown("**API Status**")
    st.text(f"NIM API Key: {nim_key_status}")
    st.text(f"Tavily Key:  {tavily_status}")

    st.divider()

    # Settings
    st.markdown("**Settings**")
    headless = st.checkbox("Headless Browser", value=True)
    show_screenshots = st.checkbox("Show Screenshots", value=True)
    verbose_logs = st.checkbox("Verbose Logging", value=False)

    st.divider()

    # Audit history
    st.markdown("**Recent Audits**")
    if st.session_state.history:
        for h in st.session_state.history[-5:]:
            score = h.get("trust_score", "?")
            url = h.get("url", "?")
            st.text(f"{'🔴' if isinstance(score, (int, float)) and score < 0.4 else '🟢'} {url[:30]}… → {score}")
    else:
        st.caption("No audits yet.")


# ============================================================
# Main content
# ============================================================

st.markdown("# 🔍 Veritas — Forensic Web Auditor")
st.markdown(
    "Enter a URL to begin an autonomous dark-pattern & trust analysis."
)

# --- Input row ---
col_url, col_tier, col_btn = st.columns([5, 2, 1])

with col_url:
    url = st.text_input(
        "Target URL",
        placeholder="https://example.com",
        label_visibility="collapsed",
    )

with col_tier:
    tier = st.selectbox(
        "Audit Tier",
        options=list(settings.AUDIT_TIERS.keys()),
        index=1,
        format_func=lambda t: {
            "quick_scan": "⚡ Quick Scan",
            "standard_audit": "🔍 Standard Audit",
            "deep_forensic": "🔬 Deep Forensic",
        }.get(t, t),
        label_visibility="collapsed",
    )

with col_btn:
    start_clicked = st.button(
        "🚀 Audit",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.is_running,
    )

# --- Tier info ---
tier_info = settings.AUDIT_TIERS.get(tier, {})
st.caption(
    f"**{tier_info.get('description', '')}** — "
    f"Up to {tier_info.get('pages', '?')} pages, "
    f"~{tier_info.get('nim_calls', '?')} NIM calls, "
    f"~{tier_info.get('estimated_credits', '?')} credits"
)

st.divider()

# ============================================================
# Audit execution
# ============================================================
if start_clicked and url:
    st.session_state.is_running = True
    st.session_state.audit_logs = []
    st.session_state.audit_result = None

    # Attach log handler
    root_logger = logging.getLogger("veritas")
    handler = StreamlitLogHandler()
    handler.setLevel(logging.DEBUG if verbose_logs else logging.INFO)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if verbose_logs else logging.INFO)

    add_log(f"Starting {tier} audit for: {url}", "info")
    add_log(f"Budget: {tier_info.get('pages', '?')} pages, {tier_info.get('nim_calls', '?')} NIM calls", "info")

    with st.spinner("Audit in progress…"):
        progress = st.progress(0, text="Initialising…")
        log_area = st.empty()

        try:
            add_log("Initialising orchestrator…", "info")
            progress.progress(5, text="Starting Scout agent…")

            result = asyncio.run(run_audit(url, tier))
            st.session_state.audit_result = result

            add_log("Audit completed successfully!", "success")
            progress.progress(100, text="Complete!")

            # Add to history
            trust_score = None
            if result and isinstance(result, dict):
                decision = result.get("judge_decision", {})
                if isinstance(decision, dict):
                    ts_result = decision.get("trust_score_result", {})
                    if isinstance(ts_result, dict):
                        trust_score = ts_result.get("final_score")
                    elif hasattr(ts_result, "final_score"):
                        trust_score = ts_result.final_score

            st.session_state.history.append({
                "url": url,
                "tier": tier,
                "trust_score": trust_score,
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            add_log(f"Audit failed: {e}", "error")
            st.error(f"Audit failed: {e}")
            logger.exception("Audit error")

        finally:
            root_logger.removeHandler(handler)
            st.session_state.is_running = False

    st.rerun()


# ============================================================
# Results display
# ============================================================
if st.session_state.audit_result:
    result = st.session_state.audit_result

    # --- Log viewer (collapsible) ---
    if st.session_state.audit_logs:
        with st.expander("📋 Audit Log", expanded=False):
            log_html = "<div class='log-container'>" + "<br>".join(
                st.session_state.audit_logs
            ) + "</div>"
            st.markdown(log_html, unsafe_allow_html=True)

    # --- Extract key data ---
    judge_decision = result.get("judge_decision", {})
    if isinstance(judge_decision, dict):
        trust_result = judge_decision.get("trust_score_result", {})
        narrative = judge_decision.get("narrative", "")
        recommendations = judge_decision.get("recommendations", [])
        risk_level = ""
        final_score = 0.5

        if isinstance(trust_result, dict):
            final_score = trust_result.get("final_score", 0.5)
            risk_level = trust_result.get("risk_level", "medium_risk")
        elif hasattr(trust_result, "final_score"):
            final_score = trust_result.final_score
            risk_level = trust_result.risk_level
    else:
        final_score = 0.5
        risk_level = "medium_risk"
        narrative = ""
        recommendations = []
        trust_result = {}

    # --- Top metrics row ---
    st.markdown("### Audit Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        color_class = trust_score_color(final_score)
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value {color_class}'>{final_score}/100</div>"
            f"<div class='metric-label'>Trust Score</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{risk_level_badge(risk_level)}</div>"
            f"<div class='metric-label'>Risk Level</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col3:
        investigated = result.get("investigated_urls", [])
        pages_visited = len(investigated) if isinstance(investigated, list) else 0
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{pages_visited}</div>"
            f"<div class='metric-label'>Pages Scanned</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col4:
        iterations = result.get("iteration", 0)
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{iterations}</div>"
            f"<div class='metric-label'>Iterations</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # --- Two-column layout ---
    left_col, right_col = st.columns([3, 2])

    # ---- Left: Narrative + Findings ----
    with left_col:
        # Narrative
        st.markdown("#### 📝 Analysis Narrative")
        if narrative:
            st.markdown(narrative)
        else:
            st.info("No narrative generated.")

        # Dark pattern findings
        st.markdown("#### 🚨 Dark Pattern Findings")
        vision_result = result.get("vision_result", {})
        if isinstance(vision_result, dict):
            findings = vision_result.get("findings", [])
        elif hasattr(vision_result, "findings"):
            findings = vision_result.findings
        else:
            findings = []

        if findings:
            for i, f in enumerate(findings):
                if isinstance(f, dict):
                    cat = f.get("category", "unknown")
                    sub = f.get("sub_type", "")
                    sev = f.get("severity", "medium")
                    conf = f.get("confidence", 0)
                    desc = f.get("evidence", f.get("description", ""))
                else:
                    cat = getattr(f, "category", "unknown")
                    sub = getattr(f, "sub_type", "")
                    sev = getattr(f, "severity", "medium")
                    conf = getattr(f, "confidence", 0)
                    desc = getattr(f, "evidence", "")

                sev_emoji = {"low": "🟡", "medium": "🟠", "high": "🔴", "critical": "⛔"}.get(sev, "🟠")

                with st.expander(f"{sev_emoji} {cat}/{sub} — {sev} ({conf:.0%})", expanded=(sev in ("high", "critical"))):
                    st.markdown(desc)
        else:
            st.success("No dark patterns detected!")

        # Recommendations
        if recommendations:
            st.markdown("#### 💡 Recommendations")
            for rec in recommendations:
                st.markdown(f"- {rec}")

    # ---- Right: Trust breakdown + Graph + Screenshots ----
    with right_col:
        # Trust score breakdown
        st.markdown("#### 📊 Trust Score Breakdown")
        if isinstance(trust_result, dict):
            sub_signals = trust_result.get("sub_signals", {})
            overrides = trust_result.get("overrides_applied", [])
        elif hasattr(trust_result, "sub_signals"):
            sub_signals = trust_result.sub_signals or {}
            overrides = trust_result.overrides_applied or []
        else:
            sub_signals = {}
            overrides = []

        if sub_signals:
            for signal_name, signal_data in sub_signals.items():
                if isinstance(signal_data, dict):
                    val = signal_data.get("weighted_value", 0)
                    raw = signal_data.get("raw_score", 0)
                    conf = signal_data.get("confidence", 0)
                else:
                    val = getattr(signal_data, "weighted_value", 0)
                    raw = getattr(signal_data, "raw_score", 0)
                    conf = getattr(signal_data, "confidence", 0)

                label = signal_name.replace("_", " ").title()
                st.progress(
                    min(1.0, max(0.0, raw)),
                    text=f"{label}: {raw:.0%} (conf: {conf:.0%})"
                )

        if overrides:
            st.markdown("**Override rules applied:**")
            for o in overrides:
                st.warning(f"⚠️ {o}")

        # Graph entities
        st.markdown("#### 🕸️ Entity Graph")
        graph_result = result.get("graph_result", {})
        if isinstance(graph_result, dict):
            entities = graph_result.get("verified_entities", graph_result.get("verifications", []))
            inconsistencies = graph_result.get("inconsistencies", [])
            domain_intel = graph_result.get("domain_intel", {})
        elif hasattr(graph_result, "verified_entities"):
            entities = graph_result.verified_entities or []
            inconsistencies = graph_result.inconsistencies or []
            domain_intel = graph_result.domain_intel or {}
        else:
            entities = []
            inconsistencies = []
            domain_intel = {}

        if domain_intel:
            di = domain_intel if isinstance(domain_intel, dict) else {}
            if di:
                st.caption(
                    f"Domain age: {di.get('domain_age_days', '?')} days | "
                    f"SSL: {'✅' if di.get('has_ssl') else '❌'} | "
                    f"Registrar: {di.get('registrar', 'Unknown')}"
                )

        if entities:
            for ent in entities[:10]:
                if isinstance(ent, dict):
                    name = ent.get("entity_name", ent.get("name", "?"))
                    verified = ent.get("is_verified", False)
                    icon = "✅" if verified else "❓"
                else:
                    name = getattr(ent, "entity_name", "?")
                    verified = getattr(ent, "is_verified", False)
                    icon = "✅" if verified else "❓"
                st.text(f"  {icon} {name}")

        if inconsistencies:
            st.markdown("**Inconsistencies found:**")
            for inc in inconsistencies[:5]:
                if isinstance(inc, dict):
                    desc = inc.get("description", str(inc))
                else:
                    desc = getattr(inc, "description", str(inc))
                st.error(f"⚠️ {desc}")

        # Screenshots
        if show_screenshots:
            st.markdown("#### 📸 Screenshots")
            screenshots = result.get("screenshots", {})
            evidence_dir = settings.EVIDENCE_DIR

            if isinstance(screenshots, dict):
                for label, path_str in screenshots.items():
                    p = Path(path_str) if path_str else None
                    if p and p.exists():
                        st.image(str(p), caption=label, use_container_width=True)
            else:
                # Try loading from evidence directory
                if evidence_dir.exists():
                    pngs = sorted(evidence_dir.glob("*.png"))[:6]
                    if pngs:
                        for png in pngs:
                            st.image(str(png), caption=png.stem, use_container_width=True)
                    else:
                        st.caption("No screenshots captured.")

    st.divider()

    # --- Download buttons ---
    col_dl1, col_dl2, col_dl3 = st.columns(3)

    with col_dl1:
        # Raw JSON download
        raw_json = json.dumps(result, indent=2, default=str)
        st.download_button(
            "📄 Download Raw JSON",
            data=raw_json,
            file_name=f"veritas_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

    with col_dl2:
        # PDF report trigger (Phase 5)
        st.button("📋 Generate PDF Report", disabled=True, help="Coming in Phase 5")

    with col_dl3:
        # New audit button
        if st.button("🔄 New Audit"):
            st.session_state.audit_result = None
            st.session_state.audit_logs = []
            st.rerun()


# ============================================================
# Empty state (before any audit)
# ============================================================
elif not st.session_state.is_running:
    st.markdown("---")

    # About section
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### How It Works")
        st.markdown("""
        1. **Scout Agent** — Stealth browser navigates the target, capturing
           screenshots at t₀ and t₀+Δ for temporal analysis
        2. **Vision Agent** — VLM analyzes screenshots against 15+ dark pattern
           types using NVIDIA NIM inference
        3. **Graph Investigator** — WHOIS, DNS, and Tavily search verify
           entity claims and build a knowledge graph
        4. **Judge Agent** — Synthesises all evidence, applies weighted
           trust formula with override rules, renders verdict
        """)

    with col_b:
        st.markdown("### Dark Pattern Categories")
        for cat_name, cat_data in DARK_PATTERN_TAXONOMY.items():
            sub_count = len(cat_data.sub_types)
            st.markdown(f"- **{cat_name.replace('_', ' ').title()}** ({sub_count} sub-types)")

        st.markdown("### Audit Tiers")
        for tier_name, tier_data in settings.AUDIT_TIERS.items():
            st.markdown(
                f"- **{tier_name}** — {tier_data['description']} "
                f"({tier_data['pages']} pg, ~{tier_data['estimated_credits']} credits)"
            )

    st.markdown("---")
    st.caption(
        "Veritas — Autonomous Multi-Modal Forensic Web Auditor | "
        "Built with NVIDIA NIM, LangGraph, Playwright, and Streamlit"
    )
