"""
Veritas Reporting — PDF Report Generator

Renders audit results into a professional PDF report using
Jinja2 templates and WeasyPrint.

Architecture:
    1. Jinja2 renders HTML from template + audit data
    2. WeasyPrint converts HTML → PDF (CSS @page support)
    3. Optional: embed screenshots as base64 or file:// URIs

Fallback:
    If WeasyPrint is not installed (system dependency issues on some OS),
    falls back to saving the rendered HTML directly.
"""

import base64
import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings

logger = logging.getLogger("veritas.reporting")

# Jinja2 is lightweight — always available
try:
    from jinja2 import Environment, FileSystemLoader
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False
    logger.warning("jinja2 not installed — PDF reporting unavailable")

# WeasyPrint requires system libs — optional
try:
    from weasyprint import HTML as WeasyHTML
    HAS_WEASYPRINT = True
except (ImportError, OSError):
    HAS_WEASYPRINT = False
    logger.info("WeasyPrint not available — will output HTML instead of PDF")


class ReportGenerator:
    """
    Generate PDF audit reports from Veritas audit results.

    Usage:
        gen = ReportGenerator()
        path = gen.generate(audit_result, url="https://example.com", tier="standard_audit")
        print(f"Report saved to: {path}")
    """

    def __init__(self, template_dir: Optional[Path] = None):
        self._template_dir = template_dir or settings.TEMPLATES_DIR
        self._output_dir = settings.REPORTS_DIR
        self._output_dir.mkdir(parents=True, exist_ok=True)

        if HAS_JINJA2:
            self._env = Environment(
                loader=FileSystemLoader(str(self._template_dir)),
                autoescape=True,
            )
        else:
            self._env = None

    def generate(
        self,
        audit_result: dict,
        url: str = "",
        tier: str = "standard_audit",
        output_format: str = "pdf",
    ) -> Path:
        """
        Generate an audit report.

        Args:
            audit_result: The full audit state dict from the orchestrator.
            url: Target URL.
            tier: Audit tier name.
            output_format: "pdf" (default) or "html" (fallback).

        Returns:
            Path to the generated report file.
        """
        if not HAS_JINJA2:
            return self._fallback_json(audit_result, url)

        # --- Build template context ---
        context = self._build_context(audit_result, url, tier)

        # --- Render HTML ---
        try:
            template = self._env.get_template("audit_report.html")
        except Exception:
            logger.warning("Template not found, trying inline template")
            return self._fallback_json(audit_result, url)

        html_str = template.render(**context)

        # --- Generate filename ---
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"veritas_{domain}_{timestamp}"

        # --- Output ---
        if output_format == "pdf" and HAS_WEASYPRINT:
            return self._render_pdf(html_str, base_name)
        else:
            return self._render_html(html_str, base_name)

    def _build_context(self, result: dict, url: str, tier: str) -> dict:
        """Build Jinja2 template context from audit result."""
        now = datetime.now()

        # Extract judge decision
        judge = result.get("judge_decision", {})
        if not isinstance(judge, dict):
            judge = {}

        trust_result = judge.get("trust_score_result", {})
        if not isinstance(trust_result, dict):
            trust_result = {}

        final_score = trust_result.get("final_score", 0)
        risk_level = trust_result.get("risk_level", "suspicious")

        # Score CSS class (0-100 scale) — matches UI thresholds
        if final_score < 20:
            score_class = "score-critical"
        elif final_score < 40:
            score_class = "score-high"
        elif final_score < 60:
            score_class = "score-medium"
        elif final_score < 80:
            score_class = "score-low"
        else:
            score_class = "score-safe"

        # Risk level → badge CSS class mapping (matches UI)
        badge_class = {
            "likely_fraudulent": "badge-critical",
            "high_risk": "badge-high",
            "suspicious": "badge-medium",
            "probably_safe": "badge-low",
            "trusted": "badge-safe",
        }.get(str(risk_level).lower().replace(" ", "_"), "badge-medium")

        # Sub-signals with colours
        raw_signals = trust_result.get("sub_signals", {})
        sub_signals = []
        signal_colors = {
            "visual": "#8B5CF6",
            "structural": "#3B82F6",
            "temporal": "#F59E0B",
            "graph": "#10B981",
            "meta": "#6366F1",
        }
        for name, data in raw_signals.items():
            if isinstance(data, dict):
                sub_signals.append({
                    "name": name,
                    "raw_score": data.get("raw_score", 0),
                    "confidence": data.get("confidence", 0),
                    "color": signal_colors.get(name, "#6B7280"),
                })

        # Overrides
        overrides = trust_result.get("overrides_applied", [])

        # Findings
        vision_result = result.get("vision_result", {})
        if not isinstance(vision_result, dict):
            vision_result = {}
        raw_findings = vision_result.get("findings", [])
        findings = []
        for f in raw_findings:
            if isinstance(f, dict):
                findings.append(f)
            else:
                findings.append({
                    "category": getattr(f, "category", "unknown"),
                    "sub_type": getattr(f, "sub_type", ""),
                    "severity": getattr(f, "severity", "medium"),
                    "confidence": getattr(f, "confidence", 0),
                    "evidence": getattr(f, "evidence", ""),
                })

        # Sort findings by severity (critical first)
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: sev_order.get(f.get("severity", "medium"), 2))

        # Graph data
        graph_result = result.get("graph_result", {})
        if not isinstance(graph_result, dict):
            graph_result = {}

        domain_intel = graph_result.get("domain_intel", {})
        if not isinstance(domain_intel, dict):
            domain_intel = {}

        entities_raw = graph_result.get("verified_entities", graph_result.get("verifications", []))
        entities = []
        for e in entities_raw:
            if isinstance(e, dict):
                entities.append({
                    "name": e.get("entity_name", e.get("name", "?")),
                    "claim": e.get("claim_text", e.get("claim", "")),
                    "verified": e.get("is_verified", False),
                    "source": e.get("source", ""),
                })
            else:
                entities.append({
                    "name": getattr(e, "entity_name", "?"),
                    "claim": getattr(e, "claim_text", ""),
                    "verified": getattr(e, "is_verified", False),
                    "source": getattr(e, "source", ""),
                })

        inconsistencies_raw = graph_result.get("inconsistencies", [])
        inconsistencies = []
        for inc in inconsistencies_raw:
            if isinstance(inc, dict):
                inconsistencies.append(inc)
            else:
                inconsistencies.append({
                    "type": getattr(inc, "inconsistency_type", "unknown"),
                    "severity": getattr(inc, "severity", "medium"),
                    "description": getattr(inc, "description", str(inc)),
                })

        # Screenshots — extract from scout_results (same as UI)
        screenshots = []
        for sr in result.get("scout_results", []):
            paths = sr.get("screenshots", [])
            labels = sr.get("screenshot_labels", [])
            for i, path_str in enumerate(paths):
                p = Path(str(path_str)) if path_str else None
                if p and p.exists():
                    lbl = labels[i] if i < len(labels) else f"shot_{i}"
                    screenshots.append({
                        "label": lbl,
                        "path": str(p.resolve()),
                        "timestamp": "",
                    })

        # Fallback: check evidence directory for jpg/png
        if not screenshots:
            evidence_dir = settings.EVIDENCE_DIR
            if evidence_dir.exists():
                for img in sorted(list(evidence_dir.glob("*.jpg")) + list(evidence_dir.glob("*.png")))[:6]:
                    screenshots.append({
                        "label": img.stem,
                        "path": str(img.resolve()),
                    })

        # Pages visited — use investigated_urls list (matches JSON)
        investigated = result.get("investigated_urls", [])
        pages_visited = len(investigated) if isinstance(investigated, list) else 0

        # SSL from scout metadata + graph
        has_ssl = False
        for sr in result.get("scout_results", []):
            sm = sr.get("page_metadata", {})
            if sm.get("has_ssl"):
                has_ssl = True
                break
        if not has_ssl:
            has_ssl = result.get("graph_result", {}).get("has_ssl", False)

        return {
            "url": url or result.get("url", "unknown"),
            "tier": tier,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "year": now.year,
            "report_id": str(uuid.uuid4())[:8].upper(),

            "trust_score": final_score,
            "risk_level": risk_level,
            "badge_class": badge_class,
            "score_class": score_class,
            "sub_signals": sub_signals,
            "overrides": overrides,
            "has_ssl": has_ssl,

            "narrative": judge.get("narrative", ""),
            "recommendations": judge.get("recommendations", []),

            "findings": findings,

            "domain_intel": domain_intel,
            "entities": entities,
            "inconsistencies": inconsistencies,

            "screenshots": screenshots,

            "iterations": result.get("iteration", 0),
            "pages_visited": pages_visited,
            "nim_calls": result.get("nim_calls_used", 0),
            "elapsed_seconds": result.get("elapsed_seconds", 0),
        }

    def _render_pdf(self, html_str: str, base_name: str) -> Path:
        """Render HTML to PDF via WeasyPrint."""
        pdf_path = self._output_dir / f"{base_name}.pdf"
        try:
            WeasyHTML(string=html_str).write_pdf(str(pdf_path))
            logger.info(f"PDF report saved: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"PDF generation failed, falling back to HTML: {e}")
            return self._render_html(html_str, base_name)

    def _render_html(self, html_str: str, base_name: str) -> Path:
        """Save rendered HTML directly (fallback)."""
        html_path = self._output_dir / f"{base_name}.html"
        html_path.write_text(html_str, encoding="utf-8")
        logger.info(f"HTML report saved: {html_path}")
        return html_path

    def _fallback_json(self, result: dict, url: str) -> Path:
        """Last resort: dump raw JSON."""
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = self._output_dir / f"veritas_{domain}_{ts}.json"
        json_path.write_text(
            json.dumps(result, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(f"JSON fallback report saved: {json_path}")
        return json_path

    def get_available_reports(self) -> list[Path]:
        """List all generated reports in the output directory."""
        reports = []
        for ext in ("*.pdf", "*.html", "*.json"):
            reports.extend(self._output_dir.glob(ext))
        return sorted(reports, key=lambda p: p.stat().st_mtime, reverse=True)
