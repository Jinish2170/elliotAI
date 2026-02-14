"""
Veritas UI v3 — Masterclass Forensic Audit Dashboard

Psychology-driven engagement: live agent streaming, skeleton loading,
agent flexing, progressive reveal, animations, consistent design system.

The user sees every agent working in real-time — screenshots appearing,
findings ticking up, logs streaming, pipeline nodes transitioning.
Nothing is hidden behind a spinner.

Run:
    cd veritas
    streamlit run ui/app.py
"""

import base64
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from config.dark_patterns import DARK_PATTERN_TAXONOMY

logger = logging.getLogger("veritas.ui")

# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="Veritas — Forensic Web Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Design System — CSS
# ============================================================

DESIGN_CSS = """
<style>
/* ===== Design Tokens ===== */
:root {
    --v-bg: #0B0F19;
    --v-surface: #131825;
    --v-surface-2: #1A2035;
    --v-border: #2A3150;
    --v-text: #E2E8F0;
    --v-text-dim: #8892A8;
    --v-accent: #3B82F6;
    --v-accent-glow: rgba(59,130,246,0.15);
    --v-green: #22C55E;
    --v-red: #EF4444;
    --v-orange: #F97316;
    --v-yellow: #EAB308;
    --v-purple: #A855F7;
    --v-cyan: #06B6D4;
    --v-radius: 12px;
    --v-font: 'Inter', 'Segoe UI', system-ui, sans-serif;
    --v-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
}

/* ===== Global Dark Theme Override ===== */
.stApp { background: var(--v-bg) !important; }
.block-container { padding: 1.5rem 2rem 3rem !important; max-width: 1400px !important; }
header[data-testid="stHeader"] { background: transparent !important; }
.stMarkdown, .stMarkdown p, .stMarkdown li { color: var(--v-text) !important; }
h1, h2, h3, h4, h5 { color: var(--v-text) !important; }
.stCaption, .stCaption p { color: var(--v-text-dim) !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--v-surface) !important;
    border-right: 1px solid var(--v-border) !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li { color: var(--v-text) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--v-border); }
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--v-text-dim) !important;
    padding: 8px 16px; border-radius: 8px 8px 0 0; font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: var(--v-surface-2) !important; color: var(--v-accent) !important;
    border-bottom: 2px solid var(--v-accent);
}

/* ===== Trust Gauge ===== */
.v-gauge-wrap {
    display: flex; flex-direction: column; align-items: center;
    padding: 24px; background: var(--v-surface); border: 1px solid var(--v-border);
    border-radius: var(--v-radius);
}
.v-gauge { position: relative; width: 180px; height: 180px; }
.v-gauge svg { transform: rotate(-90deg); }
.v-gauge circle { fill: none; stroke-width: 10; }
.v-gauge .bg { stroke: var(--v-border); }
.v-gauge .fill { stroke-linecap: round; animation: gaugeIn 1.5s ease-out forwards; }
@keyframes gaugeIn {
    from { stroke-dashoffset: 408; }
}
.v-gauge-center {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%); text-align: center;
}
.v-gauge-score {
    font-size: 2.8rem; font-weight: 800; line-height: 1;
    font-family: var(--v-font);
}
.v-gauge-label {
    font-size: 0.65rem; color: var(--v-text-dim);
    text-transform: uppercase; letter-spacing: 2px; margin-top: 4px;
}
.v-risk-badge {
    display: inline-block; padding: 6px 18px; border-radius: 20px;
    font-weight: 700; font-size: 0.8rem; letter-spacing: 0.5px;
    margin-top: 12px;
}
.vb-critical  { background: rgba(239,68,68,0.15); color: #FCA5A5; border: 1px solid rgba(239,68,68,0.3); }
.vb-high      { background: rgba(249,115,22,0.15); color: #FDBA74; border: 1px solid rgba(249,115,22,0.3); }
.vb-medium    { background: rgba(234,179,8,0.15);  color: #FDE047; border: 1px solid rgba(234,179,8,0.3); }
.vb-low       { background: rgba(59,130,246,0.15); color: #93C5FD; border: 1px solid rgba(59,130,246,0.3); }
.vb-safe      { background: rgba(34,197,94,0.15);  color: #86EFAC; border: 1px solid rgba(34,197,94,0.3); }

/* ===== Metric Cards ===== */
.v-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.v-metric {
    background: var(--v-surface); border: 1px solid var(--v-border);
    border-radius: var(--v-radius); padding: 16px; text-align: center;
}
.v-metric-val {
    font-size: 1.8rem; font-weight: 700; color: var(--v-text);
    font-family: var(--v-font); line-height: 1.2;
}
.v-metric-lbl { font-size: 0.7rem; color: var(--v-text-dim); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }

/* ===== Pipeline Tracker ===== */
.v-pipeline {
    display: flex; align-items: center; justify-content: center;
    gap: 0; padding: 16px; background: var(--v-surface);
    border: 1px solid var(--v-border); border-radius: var(--v-radius);
    margin-bottom: 20px;
}
.v-pipe-node {
    display: flex; flex-direction: column; align-items: center;
    padding: 10px 20px; border-radius: 10px; min-width: 100px;
    text-align: center; font-size: 0.75rem; font-weight: 600;
    transition: all 0.4s ease;
}
.v-pipe-icon { font-size: 1.5rem; margin-bottom: 4px; }
.v-pipe-sub { font-size: 0.6rem; color: var(--v-text-dim); margin-top: 2px; max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.v-pipe-arrow { font-size: 1.2rem; color: #4A5568; margin: 0 6px; }
.vp-done    { background: rgba(34,197,94,0.12); color: #86EFAC; }
.vp-active  { background: rgba(59,130,246,0.15); color: #93C5FD; animation: vpulse 2s infinite; }
.vp-pending { background: var(--v-surface-2); color: #4A5568; }
.vp-error   { background: rgba(239,68,68,0.12); color: #FCA5A5; }
@keyframes vpulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.4); }
    50%      { box-shadow: 0 0 0 10px rgba(59,130,246,0); }
}

/* ===== Section Card ===== */
.v-card {
    background: var(--v-surface); border: 1px solid var(--v-border);
    border-radius: var(--v-radius); padding: 20px 24px; margin-bottom: 16px;
}
.v-card-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--v-border);
}
.v-card-title { font-size: 1rem; font-weight: 700; color: var(--v-text); }
.v-card-badge {
    background: var(--v-accent-glow); color: var(--v-accent);
    padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;
}

/* ===== Finding Cards ===== */
.v-finding {
    border-left: 4px solid var(--v-border); padding: 14px 18px;
    margin: 10px 0; border-radius: 0 var(--v-radius) var(--v-radius) 0;
    background: var(--v-surface-2);
    animation: slideIn 0.4s ease forwards; opacity: 0;
    transform: translateX(-10px);
}
.v-finding:nth-child(1) { animation-delay: 0.1s; }
.v-finding:nth-child(2) { animation-delay: 0.2s; }
.v-finding:nth-child(3) { animation-delay: 0.3s; }
.v-finding:nth-child(4) { animation-delay: 0.4s; }
.v-finding:nth-child(5) { animation-delay: 0.5s; }
@keyframes slideIn {
    to { opacity: 1; transform: translateX(0); }
}
.vf-critical { border-left-color: var(--v-red); }
.vf-high     { border-left-color: var(--v-orange); }
.vf-medium   { border-left-color: var(--v-yellow); }
.vf-low      { border-left-color: var(--v-accent); }
.v-finding-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 8px;
}
.v-finding-title { font-weight: 700; color: var(--v-text); font-size: 0.9rem; }
.v-sev-badge {
    padding: 2px 10px; border-radius: 10px; font-size: 0.7rem;
    font-weight: 700; text-transform: uppercase;
}
.vs-critical { background: rgba(239,68,68,0.15); color: #FCA5A5; }
.vs-high     { background: rgba(249,115,22,0.15); color: #FDBA74; }
.vs-medium   { background: rgba(234,179,8,0.15);  color: #FDE047; }
.vs-low      { background: rgba(59,130,246,0.15); color: #93C5FD; }
.v-finding-body { font-size: 0.82rem; color: var(--v-text-dim); line-height: 1.5; }
.v-conf-bar {
    height: 4px; border-radius: 2px; background: var(--v-border);
    margin-top: 8px; overflow: hidden;
}
.v-conf-fill { height: 100%; border-radius: 2px; transition: width 0.8s ease; }

/* ===== Signal Bars ===== */
.v-signal-row {
    display: flex; align-items: center; gap: 12px; padding: 8px 0;
    border-bottom: 1px solid rgba(42,49,80,0.5);
}
.v-signal-name { min-width: 80px; font-size: 0.8rem; color: var(--v-text-dim); text-transform: capitalize; }
.v-signal-bar { flex: 1; height: 8px; background: var(--v-border); border-radius: 4px; overflow: hidden; }
.v-signal-fill { height: 100%; border-radius: 4px; animation: barGrow 0.8s ease-out forwards; }
@keyframes barGrow { from { width: 0 !important; } }
.v-signal-val { min-width: 45px; text-align: right; font-size: 0.8rem; font-weight: 600; color: var(--v-text); }
.v-signal-conf { min-width: 55px; text-align: right; font-size: 0.7rem; color: var(--v-text-dim); }

/* ===== Domain Intel ===== */
.v-di-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.v-di-item {
    display: flex; justify-content: space-between; padding: 10px 14px;
    background: var(--v-surface-2); border-radius: 8px;
}
.v-di-label { color: var(--v-text-dim); font-size: 0.8rem; }
.v-di-val { color: var(--v-text); font-weight: 600; font-size: 0.85rem; }

/* ===== Log Viewer ===== */
.v-log {
    font-family: var(--v-mono); font-size: 0.72rem; line-height: 1.7;
    background: #080C14; color: #8892A8;
    padding: 14px; border-radius: var(--v-radius);
    max-height: 350px; overflow-y: auto;
    border: 1px solid var(--v-border);
}
.v-log .l-info    { color: #60A5FA; }
.v-log .l-warn    { color: #FBBF24; }
.v-log .l-err     { color: #F87171; }
.v-log .l-ok      { color: #4ADE80; }
.v-log .l-agent   { color: #C084FC; font-weight: 600; }
.v-log .l-dim     { color: #4A5568; }

/* ===== Live Agent Card (during audit) ===== */
.v-agent-live {
    background: var(--v-surface); border: 1px solid var(--v-border);
    border-radius: var(--v-radius); padding: 20px; margin-bottom: 16px;
    position: relative; overflow: hidden;
}
.v-agent-live::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--v-accent), var(--v-purple), var(--v-cyan));
    animation: shimmerBar 2s linear infinite;
    background-size: 200% 100%;
}
@keyframes shimmerBar {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
.v-agent-name {
    font-size: 1rem; font-weight: 700; color: var(--v-accent);
    margin-bottom: 8px;
}
.v-agent-detail { font-size: 0.82rem; color: var(--v-text-dim); line-height: 1.6; }
.v-agent-stat {
    display: inline-block; background: var(--v-surface-2);
    padding: 4px 12px; border-radius: 8px; margin: 4px 4px 0 0;
    font-size: 0.75rem; color: var(--v-text); font-weight: 600;
}

/* ===== Evidence Timeline ===== */
.v-timeline { position: relative; padding-left: 30px; }
.v-timeline::before {
    content: ''; position: absolute; left: 12px; top: 0; bottom: 0;
    width: 2px; background: var(--v-border);
}
.v-tl-item {
    position: relative; margin-bottom: 16px; padding: 12px 16px;
    background: var(--v-surface-2); border-radius: var(--v-radius);
    animation: slideIn 0.3s ease forwards; opacity: 0;
}
.v-tl-item:nth-child(1) { animation-delay: 0.1s; }
.v-tl-item:nth-child(2) { animation-delay: 0.25s; }
.v-tl-item:nth-child(3) { animation-delay: 0.4s; }
.v-tl-item:nth-child(4) { animation-delay: 0.55s; }
.v-tl-dot {
    position: absolute; left: -24px; top: 16px;
    width: 10px; height: 10px; border-radius: 50%;
    border: 2px solid var(--v-accent); background: var(--v-bg);
}
.v-tl-dot.done { background: var(--v-green); border-color: var(--v-green); }
.v-tl-dot.error { background: var(--v-red); border-color: var(--v-red); }
.v-tl-agent { font-weight: 700; color: var(--v-accent); font-size: 0.85rem; }
.v-tl-action { color: var(--v-text-dim); font-size: 0.8rem; margin-top: 2px; }
.v-tl-result { color: var(--v-text); font-size: 0.8rem; margin-top: 4px; font-weight: 600; }

/* ===== Screenshot caption ===== */
.v-ss-caption { text-align: center; font-size: 0.72rem; color: var(--v-text-dim); margin-top: 6px; }

/* ===== Skeleton Loading ===== */
.v-skeleton {
    background: linear-gradient(90deg, var(--v-surface-2) 25%, var(--v-border) 50%, var(--v-surface-2) 75%);
    background-size: 400px 100%; animation: shimmer 1.5s infinite;
    border-radius: 8px; height: 20px; margin: 8px 0;
}
@keyframes shimmer {
    0% { background-position: -200px 0; }
    100% { background-position: 200px 0; }
}

/* ===== Hero Section ===== */
.v-hero {
    text-align: center; padding: 40px 20px;
    background: linear-gradient(180deg, var(--v-surface) 0%, var(--v-bg) 100%);
    border: 1px solid var(--v-border); border-radius: 16px;
    margin-bottom: 24px;
}
.v-hero h2 { font-size: 1.8rem; font-weight: 800; margin-bottom: 8px; color: var(--v-text); }
.v-hero p { color: var(--v-text-dim); font-size: 0.95rem; max-width: 600px; margin: 0 auto; }

/* ===== Feature Cards ===== */
.v-feat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }
.v-feat {
    background: var(--v-surface); border: 1px solid var(--v-border);
    border-radius: var(--v-radius); padding: 20px; text-align: center;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.v-feat:hover { transform: translateY(-3px); border-color: var(--v-accent); }
.v-feat-icon { font-size: 2rem; margin-bottom: 8px; }
.v-feat-name { font-weight: 700; color: var(--v-text); font-size: 0.9rem; margin-bottom: 4px; }
.v-feat-desc { color: var(--v-text-dim); font-size: 0.75rem; line-height: 1.4; }
</style>
"""

st.markdown(DESIGN_CSS, unsafe_allow_html=True)


# ============================================================
# Session State
# ============================================================
_defaults = {
    "audit_result": None, "is_running": False, "audit_logs": [],
    "history": [], "live_progress": {}, "live_screenshots": [],
    "live_findings_count": 0, "live_agent": "",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# Helper Functions
# ============================================================

def _score_color(score) -> str:
    s = int(score) if score else 0
    if s >= 80: return "#22C55E"
    if s >= 60: return "#3B82F6"
    if s >= 40: return "#EAB308"
    if s >= 20: return "#F97316"
    return "#EF4444"


def _risk_badge_class(risk_level: str) -> str:
    return {
        "likely_fraudulent": "vb-critical", "high_risk": "vb-high",
        "suspicious": "vb-medium", "probably_safe": "vb-low", "trusted": "vb-safe",
    }.get(str(risk_level).lower().replace(" ", "_"), "vb-medium")


def _gauge_html(score, risk_level: str = "") -> str:
    s = int(score) if score else 0
    color = _score_color(s)
    circ = 2 * 3.14159 * 65
    offset = circ * (1 - s / 100)
    badge_cls = _risk_badge_class(risk_level)
    label = str(risk_level).replace("_", " ").title()
    return (
        f'<div class="v-gauge-wrap">'
        f'<div class="v-gauge">'
        f'<svg width="180" height="180" viewBox="0 0 180 180">'
        f'<circle class="bg" cx="90" cy="90" r="65"/>'
        f'<circle class="fill" cx="90" cy="90" r="65" stroke="{color}" '
        f'stroke-dasharray="{circ}" stroke-dashoffset="{offset}"/>'
        f'</svg>'
        f'<div class="v-gauge-center">'
        f'<div class="v-gauge-score" style="color:{color}">{s}</div>'
        f'<div class="v-gauge-label">Trust Score</div>'
        f'</div></div>'
        f'<span class="v-risk-badge {badge_cls}">{label}</span>'
        f'</div>'
    )


def _pipeline_html(phases: dict) -> str:
    """Render pipeline with per-node state. phases = {name: (status, detail)}"""
    nodes = [
        ("🔭", "Scout", "Stealth recon"),
        ("�", "Security", "Sec checks"),
        ("👁️", "Vision", "VLM analysis"),
        ("🕸️", "Graph", "OSINT verify"),
        ("⚖️", "Judge", "Trust verdict"),
    ]
    node_keys = ["scout", "security", "vision", "graph", "judge"]
    html = '<div class="v-pipeline">'
    for i, (icon, name, default_sub) in enumerate(nodes):
        if i > 0:
            html += '<span class="v-pipe-arrow">→</span>'
        status, detail = phases.get(node_keys[i], ("pending", default_sub))
        css = {"done": "vp-done", "active": "vp-active", "error": "vp-error"}.get(status, "vp-pending")
        check = " ✓" if status == "done" else ""
        sub = detail or default_sub
        html += (
            f'<div class="v-pipe-node {css}">'
            f'<span class="v-pipe-icon">{icon}</span>{name}{check}'
            f'<span class="v-pipe-sub">{sub}</span>'
            f'</div>'
        )
    html += '</div>'
    return html


def _metric_html(value, label: str, icon: str = "") -> str:
    return (
        f'<div class="v-metric">'
        f'<div class="v-metric-val">{icon} {value}</div>'
        f'<div class="v-metric-lbl">{label}</div></div>'
    )


def _log_entry(msg: str, level: str = "info") -> str:
    ts = datetime.now().strftime("%H:%M:%S")
    css = {"info": "l-info", "warning": "l-warn", "error": "l-err",
           "success": "l-ok", "agent": "l-agent"}.get(level, "l-info")
    return f'<span class="{css}">[{ts}] {msg}</span>'


def _add_log(msg: str, level: str = "info"):
    st.session_state.audit_logs.append(_log_entry(msg, level))


def _get_screenshots(result: dict) -> list[dict]:
    shots = []
    for sr in result.get("scout_results", []):
        paths = sr.get("screenshots", [])
        labels = sr.get("screenshot_labels", [])
        url = sr.get("url", "")
        for i, path_str in enumerate(paths):
            p = Path(path_str) if path_str else None
            if p and p.exists():
                lbl = labels[i] if i < len(labels) else f"shot_{i}"
                shots.append({"path": p, "label": lbl, "url": url})
    return shots


def _get_judge(result: dict) -> dict:
    jd = result.get("judge_decision") or {}
    if not isinstance(jd, dict):
        jd = {}
    tr = jd.get("trust_score_result") or {}
    if not isinstance(tr, dict):
        if hasattr(tr, "final_score"):
            rl = tr.risk_level
            rl_str = rl.value if hasattr(rl, "value") else str(rl)
            tr = {"final_score": tr.final_score, "risk_level": rl_str,
                  "sub_signals": getattr(tr, "sub_signals", {}),
                  "overrides_applied": getattr(tr, "overrides_applied", [])}
        else:
            tr = {}
    return {
        "score": tr.get("final_score", 0),
        "risk": tr.get("risk_level", "suspicious"),
        "sub_signals": tr.get("sub_signals", {}),
        "overrides": tr.get("overrides_applied", []),
        "narrative": jd.get("narrative", ""),
        "simple_narrative": jd.get("simple_narrative", ""),
        "recommendations": jd.get("recommendations", []),
        "simple_recommendations": jd.get("simple_recommendations", []),
        "dark_pattern_summary": jd.get("dark_pattern_summary", []),
        "evidence_timeline": jd.get("evidence_timeline", []),
        "site_type": jd.get("site_type", ""),
        "verdict_mode": jd.get("verdict_mode", "expert"),
    }


def _get_findings(result: dict) -> list[dict]:
    vr = result.get("vision_result") or {}
    if not isinstance(vr, dict):
        vr = {}
    raw = vr.get("findings", [])
    out = []
    for f in raw:
        if isinstance(f, dict):
            out.append(f)
        else:
            out.append({
                "category": getattr(f, "category", "?"),
                "sub_type": getattr(f, "sub_type", ""),
                "severity": getattr(f, "severity", "medium"),
                "confidence": getattr(f, "confidence", 0),
                "evidence": getattr(f, "evidence", ""),
            })
    sev_ord = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    out.sort(key=lambda x: sev_ord.get(x.get("severity", "medium"), 2))
    return out


def _get_graph(result: dict) -> dict:
    gr = result.get("graph_result") or {}
    if not isinstance(gr, dict):
        gr = {}
    di = gr.get("domain_intel") or {}
    if not isinstance(di, dict):
        di = {}
    return {
        "domain_intel": di,
        "verifications": gr.get("verified_entities", gr.get("verifications", [])),
        "inconsistencies": gr.get("inconsistencies", []),
        "graph_score": gr.get("graph_score"),
        "meta_score": gr.get("meta_score"),
        "graph_data": gr.get("graph_data", {}),
    }


def _find_python_exe() -> str:
    exe = Path(sys.executable)
    if exe.stem.lower().startswith("python"):
        return str(exe)
    scripts_dir = exe.parent
    for name in ["python.exe", "python3.exe", "python"]:
        candidate = scripts_dir / name
        if candidate.exists():
            return str(candidate)
    return str(exe)


def _run_audit_streaming(url: str, tier: str, progress_container, log_container,
                         pipeline_placeholder, stats_placeholder,
                         verdict_mode: str = "expert", enabled_security_modules: list = None):
    """
    Run audit as streaming subprocess — parse ##PROGRESS markers in real-time.
    Updates pipeline tracker, live agent cards, log viewer, and stats as data arrives.
    """
    veritas_root = Path(__file__).resolve().parent.parent
    python_exe = _find_python_exe()

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, dir=str(settings.CACHE_DIR))
    tmp_path = tmp.name
    tmp.close()

    cmd = [python_exe, "-m", "veritas", url, "--tier", tier, "--output", tmp_path,
           "--verdict-mode", verdict_mode]
    if enabled_security_modules:
        cmd.extend(["--security-modules", ",".join(enabled_security_modules)])
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    _add_log(f"Launching audit: {tier} -> {url}", "agent")
    _add_log(f"Python: {python_exe}", "info")

    phases = {"scout": ("pending", ""), "security": ("pending", ""), "vision": ("pending", ""), "graph": ("pending", ""), "judge": ("pending", "")}
    agent_descriptions = {
        "scout": ("🔭 Scout Agent", "Deploying stealth Playwright browser to navigate the target. Capturing screenshots at t₀ and t₀+Δ for temporal manipulation detection..."),
        "security": ("🔒 Security Node", "Running HTTP header analysis, phishing database checks, redirect chain tracing, JS obfuscation detection, and form validation..."),
        "vision": ("👁️ Vision Agent", "Feeding screenshots to NVIDIA NIM VLM (meta/llama-3.2-90b-vision-instruct). Analyzing against 15+ dark pattern categories with confidence scoring..."),
        "graph": ("🕸️ Graph Investigator", "Running WHOIS lookups, DNS resolution, SSL certificate inspection. Building knowledge graph from entity claims. Cross-referencing via web search..."),
        "judge": ("⚖️ Judge Agent", "Synthesizing all evidence through weighted trust formula. Applying hard-stop override rules. Computing final trust score with 6-signal breakdown..."),
    }
    live_stats = {"screenshots": 0, "findings": 0, "nim_calls": 0, "elapsed": 0}
    start_time = time.time()

    try:
        proc = subprocess.Popen(
            cmd, cwd=str(veritas_root.parent),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", env=env,
            bufsize=1,
        )

        # Stream stdout line by line
        for line in iter(proc.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue

            live_stats["elapsed"] = int(time.time() - start_time)

            # Parse progress markers
            if line.startswith("##PROGRESS:"):
                try:
                    data = json.loads(line[11:])
                    phase = data.get("phase", "")
                    step = data.get("step", "")
                    detail = data.get("detail", "")
                    pct = data.get("pct", 0)

                    if phase in phases:
                        if step == "done":
                            phases[phase] = ("done", detail)
                        elif step == "error":
                            phases[phase] = ("error", detail)
                        else:
                            phases[phase] = ("active", detail)
                            # Mark subsequent phases as pending
                            phase_order = ["scout", "security", "vision", "graph", "judge"]
                            idx = phase_order.index(phase) if phase in phase_order else -1
                            for p in phase_order[idx+1:]:
                                if phases[p][0] not in ("done", "error"):
                                    phases[p] = ("pending", "")

                    # Update live stats
                    if "screenshots" in data:
                        live_stats["screenshots"] = data["screenshots"]
                    if "findings" in data:
                        live_stats["findings"] = data["findings"]
                    if "nim_calls" in data:
                        live_stats["nim_calls"] = data["nim_calls"]

                    # Update pipeline tracker
                    pipeline_placeholder.markdown(_pipeline_html(phases), unsafe_allow_html=True)

                    # Update progress bar
                    progress_container.progress(min(pct / 100, 0.99), text=detail)

                    # Update live stats display
                    elapsed_str = f"{live_stats['elapsed']}s"
                    stats_html = (
                        f'<div class="v-metrics">'
                        f'{_metric_html(live_stats["screenshots"], "Screenshots", "📸")}'
                        f'{_metric_html(live_stats["findings"], "Findings", "🚨")}'
                        f'{_metric_html(live_stats["nim_calls"], "NIM Calls", "🧠")}'
                        f'{_metric_html(elapsed_str, "Elapsed", "⏱️")}'
                        f'</div>'
                    )
                    stats_placeholder.markdown(stats_html, unsafe_allow_html=True)

                    # Show live agent card
                    if phase in agent_descriptions and step not in ("done", "error"):
                        a_name, a_desc = agent_descriptions[phase]
                        agent_html = (
                            f'<div class="v-agent-live">'
                            f'<div class="v-agent-name">{a_name}</div>'
                            f'<div class="v-agent-detail">{a_desc}</div>'
                            f'<div style="margin-top:8px">'
                            f'<span class="v-agent-stat">Phase: {phase}</span>'
                            f'<span class="v-agent-stat">Step: {step}</span>'
                            f'<span class="v-agent-stat">Progress: {pct}%</span>'
                            f'</div></div>'
                        )
                        log_container.markdown(agent_html, unsafe_allow_html=True)

                    _add_log(f"[{phase.upper()}] {detail}", "agent")
                except (json.JSONDecodeError, ValueError):
                    pass
            elif len(line) < 500:
                _add_log(line, "info")

        proc.stdout.close()
        stderr = proc.stderr.read()
        proc.stderr.close()
        proc.wait()

        if stderr:
            for sl in stderr.splitlines():
                if len(sl) < 500 and sl.strip():
                    _add_log(sl.strip(), "warning")

        # Read result
        result_path = Path(tmp_path)
        if result_path.exists() and result_path.stat().st_size > 10:
            result = json.loads(result_path.read_text(encoding="utf-8"))
            _add_log("Audit result loaded successfully!", "success")
            progress_container.progress(1.0, text="Audit complete!")
            return result
        else:
            _add_log(f"No result file (rc={proc.returncode})", "error")
            return {"status": "error", "errors": [stderr or "No output"]}

    except Exception as e:
        _add_log(f"Subprocess error: {e}", "error")
        return {"status": "error", "errors": [str(e)]}
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 🛡️ VERITAS")
    st.caption("Autonomous Forensic Web Auditor")
    st.markdown("---")

    nim_ok = bool(settings.NIM_API_KEY)
    web_src = "Tavily" if settings.TAVILY_API_KEY else "Custom Scraper"
    st.markdown(f"**NIM API:** {'🟢 Connected' if nim_ok else '🔴 Missing'}")
    st.markdown(f"**Web Intel:** 🟢 {web_src}")
    st.markdown(f"**VLM Model:** `{settings.NIM_VISION_MODEL.split('/')[-1]}`")
    st.markdown("---")

    show_screenshots = st.checkbox("📸 Show Screenshots", value=True)
    show_raw_vlm = st.checkbox("🧠 Show VLM Responses", value=False)
    verbose = st.checkbox("📋 Verbose Logging", value=False)
    st.markdown("---")

    # === Verdict Mode Toggle ===
    st.markdown("**🎯 Verdict Mode**")
    verdict_mode = st.radio(
        "Verdict Mode",
        ["expert", "simple"],
        format_func=lambda x: "🔬 Expert (Technical)" if x == "expert" else "🧑 Simple (Plain Language)",
        label_visibility="collapsed",
        horizontal=True,
    )
    st.caption("Expert: forensic detail. Simple: jargon-free language.")
    st.markdown("---")

    # === Security Modules Panel ===
    with st.expander("🔒 Security Modules", expanded=False):
        st.caption("Toggle extra security checks (runs between Scout & Vision)")
        sec_headers = st.checkbox("🛡️ HTTP Security Headers", value=True)
        sec_phishing = st.checkbox("🎣 Phishing Database Check", value=True)
        sec_redirect = st.checkbox("🔄 Redirect Chain Analysis", value=False)
        sec_js = st.checkbox("⚡ JS Obfuscation Detection", value=False)
        sec_forms = st.checkbox("📝 Form Validation", value=False)

    enabled_sec = []
    if sec_headers: enabled_sec.append("security_headers")
    if sec_phishing: enabled_sec.append("phishing_db")
    if sec_redirect: enabled_sec.append("redirect_chain")
    if sec_js: enabled_sec.append("js_analysis")
    if sec_forms: enabled_sec.append("form_validation")

    st.markdown("---")

    st.markdown("**📂 Load Previous Result**")
    uploaded = st.file_uploader("Upload JSON", type=["json"], label_visibility="collapsed")
    if uploaded is not None:
        try:
            loaded = json.loads(uploaded.read().decode("utf-8"))
            st.session_state.audit_result = loaded
            jinfo = _get_judge(loaded)
            st.session_state.history.append({
                "url": loaded.get("url", "?"), "tier": loaded.get("audit_tier", "?"),
                "trust_score": jinfo["score"], "timestamp": datetime.now().isoformat(),
            })
            st.success("Result loaded!")
            st.rerun()
        except Exception as e:
            st.error(f"Invalid JSON: {e}")
    st.markdown("---")

    st.markdown("**📜 Audit History**")
    if st.session_state.history:
        for h in reversed(st.session_state.history[-8:]):
            s = h.get("trust_score")
            u = h.get("url", "?")[:30]
            dot = "🟢" if isinstance(s, (int, float)) and s >= 60 else "🔴" if isinstance(s, (int, float)) else "⚪"
            stxt = f"{int(s)}/100" if isinstance(s, (int, float)) else "?"
            st.markdown(f"{dot} `{u}` → **{stxt}**")
    else:
        st.caption("No audits yet — run one to get started")

    st.markdown("---")
    st.caption("NVIDIA NIM · LangGraph · Playwright")


# ============================================================
# HEADER + INPUT
# ============================================================

st.markdown("# 🛡️ Veritas — Forensic Web Auditor")
st.markdown("*Autonomous dark-pattern detection & trust analysis powered by NVIDIA NIM vision models*")

c_url, c_tier, c_btn = st.columns([5, 2, 1])
with c_url:
    url = st.text_input("URL", placeholder="https://example.com", label_visibility="collapsed")
with c_tier:
    tier = st.selectbox(
        "Tier", list(settings.AUDIT_TIERS.keys()), index=1,
        format_func=lambda t: {"quick_scan": "⚡ Quick Scan", "standard_audit": "🔍 Standard",
                                "deep_forensic": "🔬 Deep Forensic"}.get(t, t),
        label_visibility="collapsed")
with c_btn:
    start = st.button("🚀 Audit", type="primary", use_container_width=True,
                       disabled=st.session_state.is_running)

ti = settings.AUDIT_TIERS.get(tier, {})
st.caption(f"**{ti.get('description', '')}** — up to {ti.get('pages', '?')} pages, ~{ti.get('nim_calls', '?')} NIM calls")
st.markdown("---")


# ============================================================
# AUDIT EXECUTION — LIVE STREAMING
# ============================================================

if start and url:
    st.session_state.is_running = True
    st.session_state.audit_logs = []
    st.session_state.audit_result = None

    # Create live UI containers
    pipeline_placeholder = st.empty()
    progress_bar = st.empty()
    stats_placeholder = st.empty()
    agent_card = st.empty()

    # Show initial pipeline state
    init_phases = {"scout": ("pending", "Waiting..."), "security": ("pending", "Waiting..."),
                   "vision": ("pending", "Waiting..."), "graph": ("pending", "Waiting..."),
                   "judge": ("pending", "Waiting...")}
    pipeline_placeholder.markdown(_pipeline_html(init_phases), unsafe_allow_html=True)
    progress_bar.progress(0, text="Initializing audit pipeline...")

    # Initial skeleton stats
    stats_html = (
        f'<div class="v-metrics">'
        f'{_metric_html("—", "Screenshots", "📸")}'
        f'{_metric_html("—", "Findings", "🚨")}'
        f'{_metric_html("—", "NIM Calls", "🧠")}'
        f'{_metric_html("0s", "Elapsed", "⏱️")}'
        f'</div>'
    )
    stats_placeholder.markdown(stats_html, unsafe_allow_html=True)

    result = _run_audit_streaming(url, tier, progress_bar, agent_card, pipeline_placeholder, stats_placeholder,
                                       verdict_mode=verdict_mode, enabled_security_modules=enabled_sec)

    st.session_state.audit_result = result
    st.session_state.is_running = False

    if result.get("status") != "error":
        jinfo = _get_judge(result)
        st.session_state.history.append({
            "url": url, "tier": tier,
            "trust_score": jinfo["score"], "timestamp": datetime.now().isoformat(),
        })

    st.rerun()


# ============================================================
# RESULTS DISPLAY
# ============================================================

if st.session_state.audit_result:
    result = st.session_state.audit_result

    # ---- Error State ----
    if result.get("status") == "error":
        st.error("**Audit Failed**")
        for err in result.get("errors", []):
            st.code(str(err)[:500], language="text")
        if st.session_state.audit_logs:
            with st.expander("📋 Audit Log", expanded=True):
                html = '<div class="v-log">' + "<br>".join(st.session_state.audit_logs) + '</div>'
                st.markdown(html, unsafe_allow_html=True)
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            if st.button("🔄 Retry"):
                st.session_state.audit_result = None
                st.session_state.audit_logs = []
                st.rerun()
        with c2:
            st.download_button("📄 Raw JSON", data=json.dumps(result, indent=2, default=str),
                               file_name="veritas_error.json", mime="application/json")

    # ---- Success State ----
    else:
        judge = _get_judge(result)
        findings = _get_findings(result)
        graph_data = _get_graph(result)
        screenshots = _get_screenshots(result)

        # ===== Pipeline Tracker (completed) =====
        # Site type indicator
        site_type_str = judge.get("site_type", "")
        if site_type_str:
            site_type_icons = {"ecommerce": "🛒", "company_portfolio": "🏢", "financial": "🏦",
                               "saas_subscription": "📦", "darknet_suspicious": "💀"}
            st_icon = site_type_icons.get(site_type_str.lower(), "🌐")
            st.markdown(f'<div class="v-card" style="padding:8px 16px;text-align:center;margin-bottom:12px">{st_icon} <strong>Site Type:</strong> {site_type_str.replace("_", " ").title()}</div>', unsafe_allow_html=True)

        # Security results summary
        sec_results = result.get("security_results") or {}

        done_phases = {
            "scout": ("done", f"{len(result.get('scout_results', []))} pages scanned"),
            "security": ("done", f"{len(sec_results)} checks run"),
            "vision": ("done", f"{len(findings)} patterns found"),
            "graph": ("done", f"{(graph_data.get('graph_data') or {}).get('nodes', []).__len__()} nodes"),
            "judge": ("done", f"Score: {judge['score']}/100"),
        }
        st.markdown(_pipeline_html(done_phases), unsafe_allow_html=True)

        # ===== Hero Row: Gauge + Metrics + Signals =====
        col_gauge, col_right = st.columns([1, 2])

        with col_gauge:
            st.markdown(_gauge_html(judge["score"], judge["risk"]), unsafe_allow_html=True)

        with col_right:
            # Metrics row
            el = result.get("elapsed_seconds", 0)
            nim_used = result.get("nim_calls_used", 0)
            metrics_html = (
                f'<div class="v-metrics">'
                f'{_metric_html(len(result.get("investigated_urls", [])), "Pages Scanned", "📄")}'
                f'{_metric_html(len(findings), "Dark Patterns", "🚨")}'
                f'{_metric_html(nim_used, "NIM VLM Calls", "🧠")}'
                f'{_metric_html(f"{el:.0f}s" if el else "—", "Audit Duration", "⏱️")}'
                f'</div>'
            )
            st.markdown(metrics_html, unsafe_allow_html=True)

            # Signal breakdown
            st.markdown("")
            sigs = judge["sub_signals"]
            if isinstance(sigs, dict) and sigs:
                signal_colors = {
                    "visual": "#A855F7", "structural": "#3B82F6",
                    "temporal": "#EAB308", "graph": "#22C55E", "meta": "#06B6D4",
                    "security": "#EF4444",
                }
                sig_html = '<div class="v-card" style="margin-top:12px; padding:14px 18px">'
                sig_html += '<div style="font-size:0.8rem;font-weight:700;color:#8892A8;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px">Signal Breakdown</div>'
                for name, data in sigs.items():
                    raw = data.get("raw_score", 0) if isinstance(data, dict) else 0
                    conf = data.get("confidence", 0) if isinstance(data, dict) else 0
                    color = signal_colors.get(name, "#6B7280")
                    pct = round(raw * 100)
                    sig_html += (
                        f'<div class="v-signal-row">'
                        f'<span class="v-signal-name">{name}</span>'
                        f'<div class="v-signal-bar"><div class="v-signal-fill" style="width:{pct}%;background:{color}"></div></div>'
                        f'<span class="v-signal-val">{pct}%</span>'
                        f'<span class="v-signal-conf">conf {round(conf*100)}%</span>'
                        f'</div>'
                    )
                sig_html += '</div>'
                st.markdown(sig_html, unsafe_allow_html=True)

        st.markdown("---")

        # ===== Content Tabs =====
        tab_story, tab_findings, tab_evidence, tab_graph, tab_security, tab_timeline, tab_raw = st.tabs(
            ["📝 Analysis", "🚨 Findings", "📸 Evidence", "🌐 Intel", "🔒 Security", "⏱️ Timeline", "📋 Data"]
        )

        # ======== TAB: Analysis / Narrative ========
        with tab_story:
            # Choose narrative based on verdict mode
            active_mode = judge.get("verdict_mode", verdict_mode)
            if active_mode == "simple" and judge.get("simple_narrative"):
                display_narrative = judge["simple_narrative"]
                narrative_title = "🧑 Plain-Language Analysis"
            else:
                display_narrative = judge["narrative"]
                narrative_title = "🔍 Forensic Analysis Narrative"

            if display_narrative:
                st.markdown(f'<div class="v-card"><div class="v-card-header"><span class="v-card-title">{narrative_title}</span></div>', unsafe_allow_html=True)
                st.markdown(display_narrative)
                st.markdown('</div>', unsafe_allow_html=True)
                # Show toggle to see the other mode
                if active_mode == "simple" and judge["narrative"]:
                    with st.expander("🔬 Show Expert Narrative"):
                        st.markdown(judge["narrative"])
                elif active_mode == "expert" and judge.get("simple_narrative"):
                    with st.expander("🧑 Show Simple Narrative"):
                        st.markdown(judge["simple_narrative"])
            else:
                st.info("No narrative was generated for this audit.")

            # Choose recommendations based on verdict mode
            if active_mode == "simple" and judge.get("simple_recommendations"):
                display_recs = judge["simple_recommendations"]
                rec_title = "💡 What You Should Do"
            else:
                display_recs = judge["recommendations"]
                rec_title = "💡 Recommendations"

            if display_recs:
                st.markdown(f'<div class="v-card"><div class="v-card-header"><span class="v-card-title">{rec_title}</span><span class="v-card-badge">{len(display_recs)}</span></div>', unsafe_allow_html=True)
                for rec in display_recs:
                    st.markdown(f"- {rec}")
                st.markdown('</div>', unsafe_allow_html=True)

            if judge["overrides"]:
                st.markdown("**⚠️ Override Rules Applied:**")
                for o in judge["overrides"]:
                    txt = o.get("name", str(o)) if isinstance(o, dict) else str(o)
                    st.warning(txt)

        # ======== TAB: Findings ========
        with tab_findings:
            if findings:
                st.markdown(
                    f'<div class="v-card-header"><span class="v-card-title">🚨 Dark Pattern Findings</span>'
                    f'<span class="v-card-badge">{len(findings)} detected</span></div>',
                    unsafe_allow_html=True
                )
                for f in findings:
                    sev = f.get("severity", "medium")
                    cat = f.get("category", "?").replace("_", " ").title()
                    sub = f.get("sub_type", "").replace("_", " ").title()
                    conf = f.get("confidence", 0)
                    desc = f.get("evidence", f.get("description", ""))
                    model = f.get("model_used", "")
                    emoji = {"critical": "⛔", "high": "🔴", "medium": "🟠", "low": "🟡"}.get(sev, "🟠")
                    conf_color = "#EF4444" if conf >= 0.8 else "#EAB308" if conf >= 0.5 else "#22C55E"

                    card_html = (
                        f'<div class="v-finding vf-{sev}">'
                        f'<div class="v-finding-header">'
                        f'<span class="v-finding-title">{emoji} {cat} — {sub}</span>'
                        f'<span class="v-sev-badge vs-{sev}">{sev.upper()} · {conf:.0%}</span>'
                        f'</div>'
                        f'<div class="v-finding-body">{desc[:300]}</div>'
                        f'<div class="v-conf-bar"><div class="v-conf-fill" style="width:{conf*100:.0f}%;background:{conf_color}"></div></div>'
                    )
                    if model:
                        card_html += f'<div style="margin-top:6px;font-size:0.65rem;color:#4A5568">Model: {model}</div>'
                    card_html += '</div>'
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Optionally show raw VLM response
                    if show_raw_vlm and f.get("raw_vlm_response"):
                        with st.expander(f"🧠 Raw VLM Response — {sub}"):
                            st.text(f["raw_vlm_response"][:1000])
            else:
                st.success("✅ No dark patterns detected — this site appears clean.")

        # ======== TAB: Evidence (Screenshots) ========
        with tab_evidence:
            if screenshots and show_screenshots:
                st.markdown(
                    f'<div class="v-card-header"><span class="v-card-title">📸 Screenshot Evidence</span>'
                    f'<span class="v-card-badge">{len(screenshots)} captures</span></div>',
                    unsafe_allow_html=True
                )
                by_url: dict[str, list] = {}
                for ss in screenshots:
                    by_url.setdefault(ss["url"], []).append(ss)

                for page_url, shots in by_url.items():
                    st.markdown(f"**Target: `{page_url}`**")

                    t0 = [s for s in shots if s["label"] == "t0"]
                    td = [s for s in shots if s["label"].startswith("t") and s["label"] != "t0" and "full" not in s["label"]]
                    fp = [s for s in shots if "full" in s["label"].lower()]

                    if t0 and td:
                        st.markdown("##### 🕐 Temporal Analysis — Before vs After")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.image(str(t0[0]["path"]), use_container_width=True)
                            st.markdown('<div class="v-ss-caption">t₀ — Initial page load capture</div>', unsafe_allow_html=True)
                        with c2:
                            st.image(str(td[0]["path"]), use_container_width=True)
                            delay_label = td[0]["label"]
                            st.markdown(f'<div class="v-ss-caption">{delay_label} — After temporal delay</div>', unsafe_allow_html=True)
                        st.caption("Scout captures the page at two points in time to detect dynamic manipulation — pop-ups, fake urgency timers, bait-and-switch content changes.")
                    elif t0:
                        st.image(str(t0[0]["path"]), caption="Initial page capture (t₀)", use_container_width=True)

                    if fp:
                        with st.expander("📜 Full-page screenshot — complete page content"):
                            st.image(str(fp[0]["path"]), use_container_width=True)
                    st.markdown("---")

                # Temporal findings
                vr = result.get("vision_result") or {}
                temporal = vr.get("temporal_findings", [])
                if temporal:
                    st.markdown("##### 🕐 Temporal Analysis Results")
                    for tf in temporal:
                        if isinstance(tf, dict):
                            ftype = tf.get("finding_type", "?")
                            suspicious = tf.get("is_suspicious", False)
                            explanation = tf.get("explanation", "")
                            delta = tf.get("delta_seconds", 0)
                            icon = "⚠️" if suspicious else "✅"
                            st.markdown(f"{icon} **{ftype}** (Δ{delta}s) — {explanation}")

            elif not screenshots:
                st.info("No screenshots were captured for this audit.")
            else:
                st.info("Screenshots hidden — enable in sidebar.")

        # ======== TAB: Intel (Graph / Domain) ========
        with tab_graph:
            di = graph_data["domain_intel"]
            if di:
                st.markdown(
                    '<div class="v-card-header"><span class="v-card-title">🌐 Domain Intelligence</span></div>',
                    unsafe_allow_html=True
                )
                # Pull extra data from graph nodes and scout results
                gr_raw = result.get("graph_result") or {}
                graph_nodes = (gr_raw.get("graph_data") or {}).get("nodes", [])
                main_node = graph_nodes[0] if graph_nodes else {}
                scout_meta = {}
                for sr in result.get("scout_results", []):
                    scout_meta = sr.get("page_metadata", {})
                    break

                rows = [
                    ("🌍 Domain", di.get('domain', '—')),
                    ("📅 Domain Age", f"{di.get('age_days', '?')} days"),
                    ("🗓️ Created", str(main_node.get('creation_date', di.get('creation_date', '—')))),
                    ("🏢 Registrar", di.get('registrar', '—')),
                    ("🔒 SSL Issuer", str(di.get('ssl_issuer', '—'))[:80]),
                    ("📡 IP Address", main_node.get('ip', di.get('ip_address', '—'))),
                    ("🛡️ Has SSL", "✅ Yes" if scout_meta.get('has_ssl', di.get('has_ssl')) else "❌ No"),
                    ("👁️ Privacy Protected", "🔒 Yes" if di.get('is_privacy_protected') else "Public"),
                ]
                di_html = '<div class="v-di-grid">'
                for lbl, val in rows:
                    if val and str(val) not in ("?", "—", "None", "none", "? days"):
                        di_html += f'<div class="v-di-item"><span class="v-di-label">{lbl}</span><span class="v-di-val">{val}</span></div>'
                di_html += '</div>'
                st.markdown(di_html, unsafe_allow_html=True)

            # Graph & Meta scores
            gs = graph_data.get("graph_score")
            ms = graph_data.get("meta_score")
            if gs is not None or ms is not None:
                st.markdown("")
                sc1, sc2 = st.columns(2)
                if gs is not None:
                    with sc1:
                        st.metric("🕸️ Graph Trust Score", f"{gs:.2f}")
                if ms is not None:
                    with sc2:
                        st.metric("📊 Meta Trust Score", f"{ms:.2f}")

            # Knowledge graph nodes
            gd = graph_data.get("graph_data", {})
            nodes = gd.get("nodes", [])
            edges = gd.get("edges", [])
            if nodes:
                st.markdown(f"##### 🗺️ Knowledge Graph ({len(nodes)} nodes, {len(edges)} edges)")
                for node in nodes[:10]:
                    ntype = node.get("node_type", "Unknown")
                    nlabel = node.get("label", node.get("id", "?"))
                    st.markdown(f"- **{ntype}**: `{nlabel}`")

            # Verifications
            vf = graph_data["verifications"]
            if vf:
                st.markdown("##### ✅ Entity Verifications")
                for ent in vf:
                    if isinstance(ent, dict):
                        claim = ent.get("claim", {})
                        etype = claim.get("entity_type", "?") if isinstance(claim, dict) else getattr(claim, "entity_type", "?")
                        evalue = claim.get("entity_value", "?") if isinstance(claim, dict) else getattr(claim, "entity_value", "?")
                        status = ent.get("status", "?")
                        conf = ent.get("confidence", 0)
                        detail = ent.get("evidence_detail", "")
                    else:
                        c = getattr(ent, "claim", None)
                        etype = getattr(c, "entity_type", "?") if c else "?"
                        evalue = getattr(c, "entity_value", "?") if c else "?"
                        status = getattr(ent, "status", "?")
                        conf = getattr(ent, "confidence", 0)
                        detail = getattr(ent, "evidence_detail", "")
                    s_icon = {"confirmed": "✅", "denied": "❌", "contradicted": "⚠️"}.get(status, "❓")
                    st.markdown(f"- {s_icon} **{etype}**: `{evalue}` — {status} ({conf:.0%})")
                    if detail:
                        st.caption(f"   {detail[:200]}")

            # Inconsistencies
            inc = graph_data["inconsistencies"]
            if inc:
                st.markdown("##### ⚠️ Inconsistencies Detected")
                for item in inc:
                    desc = item.get("description", str(item)) if isinstance(item, dict) else str(item)
                    st.error(desc)

        # ======== TAB: Security ========
        with tab_security:
            if sec_results:
                st.markdown(
                    f'<div class="v-card-header"><span class="v-card-title">🔒 Security Analysis Results</span>'
                    f'<span class="v-card-badge">{len(sec_results)} modules</span></div>',
                    unsafe_allow_html=True
                )

                # Security Headers
                sh = sec_results.get("security_headers", {})
                if sh:
                    st.markdown("##### 🛡️ HTTP Security Headers")
                    overall = sh.get("overall_score", 0)
                    st.metric("Header Security Score", f"{overall:.0%}")
                    headers_checked = sh.get("headers", {})
                    if isinstance(headers_checked, dict):
                        for hname, hdata in headers_checked.items():
                            if isinstance(hdata, dict):
                                present = hdata.get("present", False)
                                icon = "✅" if present else "❌"
                                val = hdata.get("value", "Not set")[:80]
                                strength = hdata.get("strength", "")
                                strength_badge = f" ({strength})" if strength else ""
                                st.markdown(f"{icon} **{hname}**: {val}{strength_badge}")

                # Phishing
                ph = sec_results.get("phishing_db", {})
                if ph:
                    st.markdown("##### 🎣 Phishing Database Check")
                    is_phishing = ph.get("is_phishing", False)
                    if is_phishing:
                        st.error("⛔ **PHISHING DETECTED** — This URL was flagged by phishing databases!")
                    else:
                        st.success("✅ No phishing flags detected.")
                    sources = ph.get("sources_checked", [])
                    if sources:
                        st.caption(f"Sources checked: {', '.join(sources)}")
                    heuristics = ph.get("heuristic_flags", [])
                    if heuristics:
                        st.markdown("**Heuristic Warnings:**")
                        for hf in heuristics:
                            st.warning(f"⚠️ {hf}")

                # Redirect Chain
                rc = sec_results.get("redirect_chain", {})
                if rc:
                    st.markdown("##### 🔄 Redirect Chain")
                    chain = rc.get("chain", [])
                    suspicious = rc.get("is_suspicious", False)
                    if suspicious:
                        st.warning(f"⚠️ Suspicious redirect chain detected ({len(chain)} hops)")
                    else:
                        st.success(f"✅ Clean redirect chain ({len(chain)} hops)")
                    flags = rc.get("flags", [])
                    for fl in flags:
                        st.markdown(f"- ⚠️ {fl}")
                    if chain:
                        with st.expander("Show full chain"):
                            for i, hop in enumerate(chain):
                                st.markdown(f"{i+1}. `{hop}`")

                # JS Analysis
                js = sec_results.get("js_analysis", {})
                if js:
                    st.markdown("##### ⚡ JavaScript Obfuscation")
                    risk = js.get("risk_score", 0)
                    risk_pct = f"{risk*100:.0f}%" if isinstance(risk, float) else str(risk)
                    st.metric("JS Risk Score", risk_pct)
                    issues = js.get("issues", [])
                    if issues:
                        for iss in issues:
                            st.warning(f"⚠️ {iss}")
                    miners = js.get("crypto_miners_detected", [])
                    if miners:
                        st.error(f"⛔ Crypto miners detected: {', '.join(miners)}")

                # Form Validation
                fv = sec_results.get("form_validation", {})
                if fv:
                    st.markdown("##### 📝 Form Security")
                    total = fv.get("total_forms", 0)
                    risky = fv.get("risky_forms", 0)
                    st.metric("Forms Analyzed", total)
                    if risky > 0:
                        st.warning(f"⚠️ {risky} form(s) with security concerns")
                    else:
                        st.success("✅ All forms appear safe.")
                    form_issues = fv.get("issues", [])
                    for fi in form_issues:
                        st.markdown(f"- ⚠️ {fi}")
            else:
                st.info("No security modules were enabled for this audit.")

        # ======== TAB: Timeline (Agent Activity) ========
        with tab_timeline:
            et = judge.get("evidence_timeline", [])
            if et:
                st.markdown(
                    f'<div class="v-card-header"><span class="v-card-title">⏱️ Agent Evidence Timeline</span>'
                    f'<span class="v-card-badge">{len(et)} steps</span></div>',
                    unsafe_allow_html=True
                )
                tl_html = '<div class="v-timeline">'
                for step_data in et:
                    if isinstance(step_data, dict):
                        step_num = step_data.get("step", "?")
                        agent = step_data.get("agent", "?")
                        action = step_data.get("action", "")
                        status = step_data.get("status", "?")
                        step_result = step_data.get("result", "")
                        duration = step_data.get("duration_ms", "")
                        dot_cls = "done" if status in ("SUCCESS", "COMPLETE") else "error"
                        dur_str = f' · {duration:.0f}ms' if isinstance(duration, (int, float)) else ""
                        tl_html += (
                            f'<div class="v-tl-item">'
                            f'<div class="v-tl-dot {dot_cls}"></div>'
                            f'<div class="v-tl-agent">Step {step_num}: {agent} Agent</div>'
                            f'<div class="v-tl-action">{action}{dur_str}</div>'
                            f'<div class="v-tl-result">{step_result}</div>'
                            f'</div>'
                        )
                tl_html += '</div>'
                st.markdown(tl_html, unsafe_allow_html=True)
            else:
                st.info("No evidence timeline data available.")

            # Also show VLM analysis stats
            vr = result.get("vision_result") or {}
            if isinstance(vr, dict) and vr:
                st.markdown("##### 🧠 Vision Agent Statistics")
                vc1, vc2, vc3 = st.columns(3)
                with vc1:
                    st.metric("Screenshots Analyzed", vr.get("screenshots_analyzed", 0))
                with vc2:
                    st.metric("NIM Prompts Sent", vr.get("prompts_sent", 0))
                with vc3:
                    st.metric("Fallback Used", "Yes" if vr.get("fallback_used") else "No")

        # ======== TAB: Raw Data ========
        with tab_raw:
            if st.session_state.audit_logs:
                with st.expander("📋 Live Audit Log", expanded=True):
                    html = '<div class="v-log">' + "<br>".join(st.session_state.audit_logs) + '</div>'
                    st.markdown(html, unsafe_allow_html=True)

            # Audit metadata card
            st.markdown(
                '<div class="v-card-header"><span class="v-card-title">📊 Audit Metadata</span></div>',
                unsafe_allow_html=True
            )
            meta_items = [
                ("URL", result.get("url", "?")),
                ("Tier", result.get("audit_tier", "?")),
                ("Status", result.get("status", "?")),
                ("Iterations", result.get("iteration", 0)),
                ("Pages", len(result.get("investigated_urls", []))),
                ("NIM Calls", result.get("nim_calls_used", 0)),
                ("Elapsed", f"{result.get('elapsed_seconds', 0):.1f}s"),
                ("Errors", len(result.get("errors", []))),
            ]
            meta_html = '<div class="v-di-grid">'
            for lbl, val in meta_items:
                meta_html += f'<div class="v-di-item"><span class="v-di-label">{lbl}</span><span class="v-di-val">{val}</span></div>'
            meta_html += '</div>'
            st.markdown(meta_html, unsafe_allow_html=True)

            # Download buttons
            st.markdown("")
            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.download_button("📄 Download JSON",
                                   data=json.dumps(result, indent=2, default=str),
                                   file_name=f"veritas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                   mime="application/json")
            with dc2:
                try:
                    from reporting.report_generator import ReportGenerator
                    gen = ReportGenerator()
                    rpath = gen.generate(result, url=result.get("url", ""), tier=result.get("audit_tier", "quick_scan"), output_format="html")
                    if rpath and rpath.exists():
                        st.download_button("📋 HTML Report", data=rpath.read_bytes(),
                                           file_name=rpath.name, mime="text/html")
                except Exception as e:
                    st.button("📋 Report N/A", disabled=True, help=str(e))
            with dc3:
                if st.button("🔄 New Audit"):
                    st.session_state.audit_result = None
                    st.session_state.audit_logs = []
                    st.rerun()


# ============================================================
# EMPTY STATE — Landing Page
# ============================================================

elif not st.session_state.is_running:
    st.markdown(
        '<div class="v-hero">'
        '<h2>Autonomous Multi-Modal Forensic Web Auditor</h2>'
        '<p>4 AI agents work together to detect dark patterns, verify entity claims, '
        'and compute a forensic trust score with 6-signal analysis — all powered by NVIDIA NIM vision models.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="v-feat-grid">'
        '<div class="v-feat"><div class="v-feat-icon">🔭</div>'
        '<div class="v-feat-name">Scout Agent</div>'
        '<div class="v-feat-desc">Stealth Playwright browser captures temporal screenshots at t₀ and t₀+Δ. '
        'Detects pop-ups, cookie walls, and dynamic content manipulation.</div></div>'
        '<div class="v-feat"><div class="v-feat-icon">👁️</div>'
        '<div class="v-feat-name">Vision Agent</div>'
        '<div class="v-feat-desc">NVIDIA NIM VLM analyzes screenshots against 15+ dark pattern types with '
        'confidence scoring. Uses meta/llama-3.2-90b-vision-instruct.</div></div>'
        '<div class="v-feat"><div class="v-feat-icon">🕸️</div>'
        '<div class="v-feat-name">Graph Investigator</div>'
        '<div class="v-feat-desc">WHOIS, DNS, SSL verification. Cross-references entity claims via web search. '
        'Builds a knowledge graph of evidence nodes.</div></div>'
        '<div class="v-feat"><div class="v-feat-icon">⚖️</div>'
        '<div class="v-feat-name">Judge Agent</div>'
        '<div class="v-feat-desc">Synthesizes all evidence through a 6-signal weighted trust formula with '
        'hard-stop override rules. Generates forensic narrative in Expert or Simple mode.</div></div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🎯 Detection Coverage")
        for cat_name, cat_data in DARK_PATTERN_TAXONOMY.items():
            n = len(cat_data.sub_types)
            emoji = {"visual_interference": "🎨", "false_urgency": "⏰",
                     "forced_continuity": "🔒", "sneaking": "🐍",
                     "social_engineering": "🎭"}.get(cat_name, "📌")
            st.markdown(f"- {emoji} **{cat_name.replace('_', ' ').title()}** — {n} sub-types")

    with c2:
        st.markdown("### ⚡ Audit Tiers")
        for tn, td in settings.AUDIT_TIERS.items():
            icon = {"quick_scan": "⚡", "standard_audit": "🔍", "deep_forensic": "🔬"}.get(tn, "📋")
            st.markdown(f"- {icon} **{tn.replace('_', ' ').title()}** — {td['description']} ({td['pages']} pages, ~{td['nim_calls']} NIM)")

        st.markdown("")
        st.markdown("### 🧠 Technology Stack")
        st.markdown("- **NVIDIA NIM** — Vision Language Models (VLM)")
        st.markdown("- **LangGraph** — Multi-agent orchestration")
        st.markdown("- **Playwright** — Stealth browser automation")
        st.markdown("- **WHOIS/DNS** — Domain intelligence")

    st.markdown("---")
    st.caption("Veritas v4.0 — Autonomous Multi-Modal Forensic Web Auditor · Built with NVIDIA NIM, LangGraph, Playwright & Streamlit")
