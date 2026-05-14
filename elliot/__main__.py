"""
Elliot — CLI Entry Point

Usage:
    # Run Streamlit UI
    streamlit run elliot/ui/app.py

    # Run audit via CLI
    python -m elliot https://example.com --tier standard_audit

    # Run audit and generate PDF report
    python -m elliot https://example.com --tier deep_forensic --report pdf
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

# Add elliot root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from elliot.config import settings
from elliot.core.ipc import determine_ipc_mode, IPC_MODE_QUEUE, IPC_MODE_STDOUT, IPC_MODE_VALIDATE
from elliot.core.orchestrator import ElliotOrchestrator
from elliot.reporting.report_generator import ReportGenerator


# When the backend spawns this CLI as a subprocess, stdout is reserved for the
# `##PROGRESS:` JSON markers + the final `--json` payload. Decorative prints
# ("🔍 Elliot Audit", recommendation bullets, etc.) must go to stderr instead,
# otherwise the backend's stdout parser sees them as malformed events.
#
# Triggers for "subprocess mode":
#   - ELLIOT_SUBPROCESS=1 in env (preferred — backend sets this explicitly)
#   - stdout is not a TTY (catches naive pipe redirection)
_SUBPROCESS_MODE: bool = (
    os.environ.get("ELLIOT_SUBPROCESS") == "1"
    or not sys.stdout.isatty()
)


def say(message: str = "") -> None:
    """Print a decorative / human-facing message.

    Routes to stderr in subprocess mode so it doesn't contaminate the
    stdout IPC channel. In an interactive terminal this is identical to
    print() — so nothing changes for users running ``python -m elliot``.
    """
    stream = sys.stderr if _SUBPROCESS_MODE else sys.stdout
    print(message, file=stream, flush=True)


def setup_logging(verbose: bool = False):
    """Configure logging for CLI usage.

    Explicitly binds the handler to stderr — basicConfig() defaults there
    already, but being explicit prevents future regressions if a library
    we depend on swaps the default mid-execution (some did historically).
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


async def run_audit(url: str, tier: str, verdict_mode: str = "expert",
                    enabled_security_modules: list = None) -> dict:
    """Run the audit pipeline."""
    orchestrator = ElliotOrchestrator()
    return await orchestrator.audit(
        url, tier,
        verdict_mode=verdict_mode,
        enabled_security_modules=enabled_security_modules,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Elliot — Autonomous Forensic Web Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m elliot https://suspicious-site.com
  python -m elliot https://store.example.com --tier deep_forensic --report pdf
  python -m elliot https://example.com --tier quick_scan --json
        """,
    )

    # IPC mode flags (highest priority for mode selection)
    parser.add_argument(
        "--use-queue-ipc",
        action="store_true",
        help="Use multiprocessing.Queue for IPC instead of stdout parsing"
    )
    parser.add_argument(
        "--use-stdout",
        action="store_true",
        help="Force stdout mode (disable Queue IPC)"
    )
    parser.add_argument(
        "--validate-ipc",
        action="store_true",
        help="Run both Queue and stdout modes and compare results"
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

    # Determine IPC mode based on CLI, environment, and rollout
    # Priority: CLI flags > Environment variables > Default (10% rollout)
    ipc_mode = determine_ipc_mode(
        cli_use_queue_ipc=args.use_queue_ipc,
        cli_use_stdout=args.use_stdout,
        cli_validate_ipc=args.validate_ipc,
    )

    logger = logging.getLogger("elliot.cli")
    if ipc_mode == IPC_MODE_VALIDATE:
        logger.info("IPC mode: VALIDATE (running both Queue and stdout)")
    elif ipc_mode == IPC_MODE_QUEUE:
        logger.info("IPC mode: Queue")
    else:
        logger.info("IPC mode: Stdout")

    # Validate API key
    if not settings.NIM_API_KEY:
        say("⚠️  Warning: NVIDIA_NIM_API_KEY not set. NIM calls will fail.")
        say("   Set it in elliot/.env or as an environment variable.\n")

    # Run audit
    say(f"\n🔍 Elliot Audit — {args.url}")
    say(f"   Tier: {args.tier}")
    say(f"   Budget: {settings.AUDIT_TIERS[args.tier]['pages']} pages, "
        f"{settings.AUDIT_TIERS[args.tier]['nim_calls']} NIM calls\n")

    result = None
    sec_modules = [m.strip() for m in args.security_modules.split(",") if m.strip()] if args.security_modules else None
    try:
        result = asyncio.run(run_audit(args.url, args.tier, args.verdict_mode, sec_modules))
    except (KeyboardInterrupt, SystemExit):
        say("\n⚠️  Audit interrupted.")
    except BaseException as e:
        say(f"\n⚠️  Audit error: {e}")

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
    say("=" * 60)
    if isinstance(score, (int, float)):
        say(f"  🎯 Trust Score: {score}/100")
    else:
        say(f"  🎯 Trust Score: {score}")
    say(f"  ⚠️  Risk Level: {risk}")
    say("=" * 60)

    if narrative:
        say(f"\n📝 {narrative}\n")

    # Recommendations
    recs = judge.get("recommendations", []) if isinstance(judge, dict) else []
    if recs:
        say("💡 Recommendations:")
        for r in recs:
            say(f"   • {r}")
        say()

    # JSON output to stdout — intentional data channel, ALWAYS goes to stdout
    # (this is what the subprocess parent reads).
    if args.json:
        print(json.dumps(result, indent=2, default=str), flush=True)

    # JSON output to file
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        say(f"\n💾 Result JSON saved: {out_path}")

    # Report generation
    if args.report != "none":
        gen = ReportGenerator()
        path = gen.generate(result, url=args.url, tier=args.tier, output_format=args.report)
        say(f"\n📄 Report saved: {path}")

    # Status & error summary
    status = result.get("status", "unknown")
    errors = result.get("errors", [])
    if errors:
        say(f"\n⚠️  Errors ({len(errors)}):")
        for e in errors[:5]:
            say(f"   • {e}")

    return 0 if status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
