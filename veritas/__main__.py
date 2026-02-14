"""
Veritas — CLI Entry Point

Usage:
    # Run Streamlit UI
    streamlit run veritas/ui/app.py

    # Run audit via CLI
    python -m veritas https://example.com --tier standard_audit

    # Run audit and generate PDF report
    python -m veritas https://example.com --tier deep_forensic --report pdf
"""

import argparse
import asyncio
import io
import json
import logging
import os
import sys
from pathlib import Path

# Force UTF-8 output on Windows (prevents UnicodeEncodeError with emojis
# when stdout is a pipe, e.g. subprocess.run(capture_output=True))
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Add veritas root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from core.orchestrator import VeritasOrchestrator
from reporting.report_generator import ReportGenerator


def setup_logging(verbose: bool = False):
    """Configure logging for CLI usage."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def run_audit(url: str, tier: str, verdict_mode: str = "expert",
                    enabled_security_modules: list = None) -> dict:
    """Run the audit pipeline."""
    orchestrator = VeritasOrchestrator()
    return await orchestrator.audit(
        url, tier,
        verdict_mode=verdict_mode,
        enabled_security_modules=enabled_security_modules,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Veritas — Autonomous Forensic Web Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m veritas https://suspicious-site.com
  python -m veritas https://store.example.com --tier deep_forensic --report pdf
  python -m veritas https://example.com --tier quick_scan --json
        """,
    )

    parser.add_argument("url", help="Target URL to audit")
    parser.add_argument(
        "--tier", "-t",
        choices=list(settings.AUDIT_TIERS.keys()),
        default="standard_audit",
        help="Audit tier (default: standard_audit)",
    )
    parser.add_argument(
        "--report", "-r",
        choices=["pdf", "html", "none"],
        default="none",
        help="Generate a report (default: none)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON result")
    parser.add_argument("--output", "-o", help="Write full JSON result to this file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--verdict-mode",
        choices=["simple", "expert"],
        default="expert",
        help="Verdict mode: simple (non-technical) or expert (forensic detail)",
    )
    parser.add_argument(
        "--security-modules",
        type=str, default="",
        help="Comma-separated security modules to enable (e.g. security_headers,phishing_db,redirect_chain,js_analysis,form_validation)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Validate API key
    if not settings.NIM_API_KEY:
        print("⚠️  Warning: NVIDIA_NIM_API_KEY not set. NIM calls will fail.")
        print("   Set it in veritas/.env or as an environment variable.\n")

    # Run audit
    print(f"\n🔍 Veritas Audit — {args.url}")
    print(f"   Tier: {args.tier}")
    print(f"   Budget: {settings.AUDIT_TIERS[args.tier]['pages']} pages, "
          f"{settings.AUDIT_TIERS[args.tier]['nim_calls']} NIM calls\n")

    result = None
    sec_modules = [m.strip() for m in args.security_modules.split(",") if m.strip()] if args.security_modules else None
    try:
        result = asyncio.run(run_audit(args.url, args.tier, args.verdict_mode, sec_modules))
    except (KeyboardInterrupt, SystemExit):
        print("\n⚠️  Audit interrupted.")
    except BaseException as e:
        print(f"\n⚠️  Audit error: {e}")

    if result is None:
        result = {"status": "error", "errors": ["Audit process crashed or was interrupted"],
                  "url": args.url, "audit_tier": args.tier}

    # Extract verdict
    judge = result.get("judge_decision", {})
    if isinstance(judge, dict):
        trust_result = judge.get("trust_score_result", {})
        if isinstance(trust_result, dict):
            score = trust_result.get("final_score", "?")
            risk = trust_result.get("risk_level", "?")
        else:
            score = "?"
            risk = "?"
        narrative = judge.get("narrative", "No narrative generated.")
    else:
        score = "?"
        risk = "?"
        narrative = ""

    # Display results
    print("=" * 60)
    if isinstance(score, (int, float)):
        print(f"  🎯 Trust Score: {score}/100")
    else:
        print(f"  🎯 Trust Score: {score}")
    print(f"  ⚠️  Risk Level: {risk}")
    print("=" * 60)

    if narrative:
        print(f"\n📝 {narrative}\n")

    # Recommendations
    recs = judge.get("recommendations", []) if isinstance(judge, dict) else []
    if recs:
        print("💡 Recommendations:")
        for r in recs:
            print(f"   • {r}")
        print()

    # JSON output to stdout
    if args.json:
        print(json.dumps(result, indent=2, default=str))

    # JSON output to file
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"\n💾 Result JSON saved: {out_path}")

    # Report generation
    if args.report != "none":
        gen = ReportGenerator()
        path = gen.generate(result, url=args.url, tier=args.tier, output_format=args.report)
        print(f"\n📄 Report saved: {path}")

    # Status & error summary
    status = result.get("status", "unknown")
    errors = result.get("errors", [])
    if errors:
        print(f"\n⚠️  Errors ({len(errors)}):")
        for e in errors[:5]:
            print(f"   • {e}")

    return 0 if status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
