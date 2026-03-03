"""
Darknet Analysis UI Components

Streamlit components for darknet threat intelligence display:
- TOR connection status indicator
- Darknet audit toggle/selection
- Marketplace threat intelligence dashboard
- Hidden service discovery results
"""

import asyncio
import logging
from typing import Dict, List, Optional

import streamlit as st

logger = logging.getLogger("veritas.ui.darknet")


# ============================================================
# Darknet Panel Styling
# ============================================================

DARKNET_CSS = """
<style>
.v-darknet-panel {
    background: linear-gradient(135deg, #1A1033 0%, #0D0820 100%);
    border: 1px solid #431E7A;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.v-darknet-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #431E7A;
}
.v-darknet-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #E9D5FF;
}
.v-darknet-badge {
    background: rgba(139, 92, 246, 0.2);
    color: #C4B5FD;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 700;
}
.v-tor-status {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
}
.v-tor-connected {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.3);
}
.v-tor-disconnected {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
}
.v-tor-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
.v-tor-connected .v-tor-indicator {
    background: #22C55E;
    box-shadow: 0 0 10px #22C55E;
}
.v-tor-disconnected .v-tor-indicator {
    background: #EF4444;
}
.v-marketplace-card {
    background: rgba(67, 30, 122, 0.3);
    border: 1px solid rgba(67, 30, 122, 0.5);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
}
.v-marketplace-exit-scam {
    border-left: 3px solid #EF4444;
}
.v-marketplace-shutdown {
    border-left: 3px solid #F97316;
}
.v-onion-ref {
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 6px;
    padding: 8px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #A5B4FC;
    margin: 4px 0;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
</style>
"""


# ============================================================
# Component Functions
# ============================================================

def render_darknet_panel(
    darknet_enabled: bool,
    tor_status: Optional[bool] = None,
    analysis_result: Optional[Dict] = None,
) -> None:
    """
    Render the darknet analysis panel.

    Args:
        darknet_enabled: Whether darknet analysis is enabled
        tor_status: TOR connection status (True=connected, False=disconnected, None=unknown)
        analysis_result: Darknet analysis results from DarknetAnalysisModule
    """
    st.markdown(DARKNET_CSS, unsafe_allow_html=True)

    with st.container():
        # Darknet header with toggle
        col_left, col_right = st.columns([3, 1])

        with col_left:
            st.markdown(f"""
            <div class="v-darknet-header">
                <span>🧅</span>
                <span class="v-darknet-title">Darknet Threat Intelligence</span>
                <span class="v-darknet-badge">READ-ONLY OSINT</span>
            </div>
            """, unsafe_allow_html=True)

        with col_right:
            st.markdown(
                """
            <div style="font-size: 0.7rem; color: #8892A8; text-align: center;">
                Security Research Data<br>
                No Live Access
            </div>
            """,
                unsafe_allow_html=True,
            )

        # TOR Status Indicator
        if tor_status is None:
            status_class = "v-tor-disconnected"
            status_text = "TOR status: Unknown (not checked)"
            indicator_text = "gray"
        elif tor_status:
            status_class = "v-tor-connected"
            status_text = "TOR connected: SOCKS5h proxy active (127.0.0.1:9050)"
            indicator_text = "green"
        else:
            status_class = "v-tor-disconnected"
            status_text = "TOR disconnected: Proxy not available"
            indicator_text = "red"

        st.markdown(
            f"""
        <div class="v-tor-status {status_class}">
            <div class="v-tor-indicator"></div>
            <span style="color: #E2E8F0; font-size: 0.85rem;">{status_text}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Legal disclaimer
        st.info(
            """
            **Legal Compliance**: This analysis uses read-only OSINT from historical security research.
            No live darknet crawling, no marketplace access, no transaction capability.
            Results are for security research and forensic auditing purposes only.
            """
        )

        # Analysis results
        if analysis_result:
            render_analysis_results(analysis_result)


def render_analysis_results(result: Dict) -> None:
    """
    Render darknet analysis results.

    Args:
        result: Analysis result dict from DarknetAnalysisModule
    """
    has_onion = result.get("has_onion_references", False)
    onion_urls = result.get("onion_urls_detected", [])
    marketplace_threats = result.get("marketplace_threats", [])
    tor2web = result.get("tor2web_exposure", False)
    risk_score = result.get("darknet_risk_score", 0.0)
    recommendations = result.get("recommendations", [])

    # Risk Score Gauge
    if risk_score > 0:
        risk_color = get_risk_color(risk_score)
        risk_label = get_risk_label(risk_score)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric(
                "Darknet Risk",
                f"{risk_score:.0%}",
                delta=None,
                delta_color="normal",
            )

        with col2:
            st.markdown(
                f"""
            <div style="background: {risk_color['bg']}; color: {risk_color['text']};
                    padding: 8px 16px; border-radius: 20px; display: inline-block;
                    font-weight: 700; font-size: 0.8rem; border: 1px solid {risk_color['border']};">
                {risk_label}
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Onion References
    if has_onion and onion_urls:
        with st.expander(f"🧅 Found {len(onion_urls)} .onion reference(s)", expanded=True):
            for url in onion_urls:
                anon = anonymize_onion(url)
                st.markdown(f'<div class="v-onion-ref">🔒 {anon}</div>', unsafe_allow_html=True)

    # Marketplace Threats
    if marketplace_threats:
        st.markdown("### 🏴 Marketplace Threat Intelligence")
        for threat in marketplace_threats:
            status = threat.get("status", "unknown")
            marketplace = threat.get("marketplace", "Unknown")
            confidence = threat.get("confidence", 0)

            card_class = "v-marketplace-exit-scam" if status == "exit_scam" else "v-marketplace-shutdown"

            st.markdown(
                f"""
            <div class="v-marketplace-card {card_class}">
                <strong>{marketplace}</strong> — {status.title()}<br/>
                <span style="color: #8892A8; font-size: 0.75rem;">Confidence: {confidence:.0%}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Tor2Web Exposure
    if tor2web:
        st.warning(
            """
            **⚠️ Tor2Web Gateway Detected**

            This site uses Tor2Web gateway URLs (onion.to, onion.link, etc.).
            This compromises TOR anonymity because DNS resolution happens on the gateway server.

            **Recommendation**: Use direct TOR Browser for .onion access.
            """
        )

    # Recommendations
    if recommendations:
        st.markdown("### 📋 Security Recommendations")
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"**{i}.** {rec}")

    # No threats found
    if not has_onion and not marketplace_threats and not tor2web:
        st.success("✅ No darknet threats detected on this site.")


def render_darknet_toggle(selected_categories: List[str]) -> List[str]:
    """
    Render darknet category toggle switch.

    Args:
        selected_categories: Currently selected analysis categories

    Returns:
        Updated list of selected categories
    """
    st.markdown("### 🧅 Premium Analysis Categories")

    col1, col2 = st.columns(2)

    with col1:
        darknet_enabled = st.toggle(
            "Darknet Threat Intelligence",
            value="darknet" in selected_categories,
            key="darknet_toggle",
            help="Enable TOR-aware security analysis with marketplace threat intelligence",
        )

    with col2:
        st.markdown(
            """
            <div style="font-size: 0.75rem; color: #8892A8; padding-top: 20px;">
            Analyzes .onion references, marketplace threats,
            and Tor2Web exposure using historical OSINT data.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Update selected categories
    if darknet_enabled and "darknet" not in selected_categories:
        selected_categories = selected_categories + ["darknet"]
    elif not darknet_enabled and "darknet" in selected_categories:
        selected_categories = [c for c in selected_categories if c != "darknet"]

    return selected_categories


def render_marketplace_intelligence_dashboard(
    marketplace_data: Optional[List[Dict]] = None,
) -> None:
    """
    Render marketplace threat intelligence dashboard.

    Args:
        marketplace_data: List of marketplace threat data entries
    """
    st.markdown(DARKNET_CSS, unsafe_allow_html=True)

    st.markdown(
        """
    <div class="v-darknet-panel">
        <div class="v-darknet-header">
            <span>🏴</span>
            <span class="v-darknet-title">Marketplace Threat Database</span>
            <span class="v-darknet-badge">6 MARKETS</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Exit Scams", "3", "AlphaBay, Empire, Wall Street")

    with col2:
        st.metric("Shutdowns", "2", "Hansa, Dream")

    with col3:
        st.metric("Gateways", "7", "Tor2Web proxy services")

    st.markdown("---")

    # Marketplace reference cards
    markets = [
        {"name": "AlphaBay", "status": "shutdown", "date": "2017-07", "threat": "Seized by LE"},
        {"name": "Hansa", "status": "shutdown", "date": "2017-07", "threat": "Honeypot operation"},
        {"name": "Empire", "status": "exit_scam", "date": "2020-08", "threat": "$30M stolen"},
        {"name": "Dream", "status": "exit_scam", "date": "2019-03", "threat": "Data theft"},
        {"name": "Wall Street", "status": "exit_scam", "date": "2019-05", "threat": "Crypto stolen"},
    ]

    for market in markets:
        status_icon = "🚨" if market["status"] == "exit_scam" else "⚠️"
        status_text = "EXIT SCAM" if market["status"] == "exit_scam" else "SHUTDOWN"

        status_bg = "rgba(239, 68, 68, 0.15)" if market["status"] == "exit_scam" else "rgba(249, 115, 22, 0.15)"
        status_border = "rgba(239, 68, 68, 0.3)" if market["status"] == "exit_scam" else "rgba(249, 115, 22, 0.3)"

        st.markdown(
            f"""
        <div class="v-marketplace-card v-marketplace-{market['status']}"
             style="border-left: 3px solid #{'EF4444' if market['status'] == 'exit_scam' else 'F97316'};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 700; color: #E9D5FF;">{status_icon} {market['name']}</span>
                <span style="background: {status_bg}; color: #FDBA74; padding: 2px 8px;
                       border-radius: 12px; font-size: 0.7rem; font-weight: 700;
                       border: 1px solid {status_border};">
                    {status_text}
                </span>
            </div>
            <div style="color: #8892A8; font-size: 0.75rem; margin-top: 6px;">
                {market['date']} — {market['threat']}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Legal notice
    st.caption(
        """
        **Source**: Historical threat data from security research. Read-only OSINT compliance.
        No live marketplace access or crawling. Results for forensic auditing purposes only.
        """
    )


# ============================================================
# Helper Functions
# ============================================================

def anonymize_onion(onion: str) -> str:
    """
    Anonymize .onion address for display.

    Args:
        onion: Full .onion address

    Returns:
        Anonymized address with middle characters obscured
    """
    if "." not in onion:
        return onion

    parts = onion.split(".")
    name = parts[0]

    if len(name) <= 8:
        return f"{name[:3]}***{name[-3:]}.onion"
    else:
        return f"{name[:4]}***{name[-4:]}.onion"


def get_risk_color(score: float) -> Dict[str, str]:
    """Get color scheme for risk score."""
    if score >= 0.7:
        return {"bg": "rgba(239, 68, 68, 0.15)", "text": "#FCA5A5", "border": "rgba(239, 68, 68, 0.3)"}
    elif score >= 0.4:
        return {"bg": "rgba(249, 115, 22, 0.15)", "text": "#FDBA74", "border": "rgba(249, 115, 22, 0.3)"}
    elif score > 0:
        return {"bg": "rgba(234, 179, 8, 0.15)", "text": "#FDE047", "border": "rgba(234, 179, 8, 0.3)"}
    else:
        return {"bg": "rgba(34, 197, 94, 0.15)", "text": "#86EFAC", "border": "rgba(34, 197, 94, 0.3)"}


def get_risk_label(score: float) -> str:
    """Get risk label for score."""
    if score >= 0.8:
        return "CRITICAL RISK"
    elif score >= 0.6:
        return "HIGH RISK"
    elif score >= 0.4:
        return "MODERATE RISK"
    elif score > 0.1:
        return "LOW THREAT"
    else:
        return "SAFE"


async def check_tor_connection() -> bool:
    """
    Check if TOR SOCKS5h proxy is available.

    Returns:
        True if connected, False otherwise
    """
    try:
        import asyncio
        import socket

        def _check():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            try:
                s.connect(("127.0.0.1", 9050))
                return True
            except (ConnectionRefusedError, OSError, socket.timeout):
                return False
            finally:
                s.close()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _check)
    except Exception:
        return False


# ============================================================
# Public API
# ============================================================

__all__ = [
    "render_darknet_panel",
    "render_analysis_results",
    "render_darknet_toggle",
    "render_marketplace_intelligence_dashboard",
    "check_tor_connection",
    "DARKNET_CSS",
]
